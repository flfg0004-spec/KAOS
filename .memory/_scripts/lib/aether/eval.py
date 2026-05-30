"""Aether evaluation — DeepEval pipeline with LLM-as-judge fallback.

EvalPipeline class con judge_model, sample_size, auto_interval, metrics.
- evaluate_session() usa LLM-as-judge (DeepEval o mock directo)
- run_batch_eval() persiste resultados y llama a QualityStore.record()
- get_eval_report() resumen agregado de evaluaciones
- Auto-evaluación en cada N llamadas
"""

import json
import logging
import os
import random
import re
from datetime import UTC, date, datetime
from pathlib import Path

from lib.aether.config import (
    ETHER_DEEPEVAL_ENABLED as EVAL_ENABLED_V2,
)
from lib.aether.config import (
    ETHER_EVAL_SAMPLE_SIZE as EVAL_SAMPLE_SIZE_V2,
)
from lib.aether.tracker import EtherTracker

_LOG = logging.getLogger(__name__)

# ── Sampling config ──────────────────────────────────────────
_SAMPLE_RATES = {
    "pro": 0.5,
    "kimi": 0.5,
    "flash": 0.2,
    "mimo": 0.05,
}
_SAMPLE_QUALITY_FEEDBACK = True
_SAMPLE_HIGH_SCORE_THRESHOLD = 8.0
_SAMPLE_REDUCTION_FACTOR = 0.5
_SAMPLE_FAILURE_BOOST = 2.0
_SAMPLE_MIN_SAMPLES = 5
_SAMPLE_MAX_DAILY_JUDGE_USD = 0.05

_DAILY_JUDGE_COST = 0.0
_DAILY_JUDGE_DATE = date.today()

# ── Counter para auto-evaluación ─────────────────────────────
_AUTO_EVAL_COUNTER = 0
_AUTO_EVAL_INTERVAL = int(os.environ.get("ETHER_AUTO_EVAL_INTERVAL", "50"))

# ── Cache paths ──────────────────────────────────────────────
_BASE_CACHE = Path(__file__).resolve().parent.parent.parent.parent.parent / ".memory" / "cache"
_DEEPEVAL_LATEST_PATH = _BASE_CACHE / "deepeval-latest.json"


# ── EvalPipeline ──────────────────────────────────────────────


class EvalPipeline:
    """Pipeline de evaluación de calidad con LLM-as-judge.

    Evalúa sesiones individuales o batches usando un modelo judge
    (por defecto ``go-pro``). Si DeepEval no está instalado, usa
    una llamada LLM directa como fallback.

    Attributes:
        judge_model: Modelo que actúa como judge (default ``"go-pro"``).
        sample_size: Sesiones a muestrear por defecto.
        auto_interval: Cada N calls, trigger auto-eval.
        metrics: Lista de dimensiones a evaluar.
    """

    def __init__(
        self,
        judge_model: str = "go-pro",
        sample_size: int = 10,
        auto_interval: int = 50,
        metrics: list[str] | None = None,
    ):
        self.judge_model = judge_model
        self.sample_size = sample_size
        self.auto_interval = auto_interval
        self.metrics = metrics or ["correctness", "coherence", "hallucination"]

        # Resultados persistentes
        self._results_path = _DEEPEVAL_LATEST_PATH
        self._results_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Sampling Control ────────────────────────────────────

    def should_sample(self, task_type: str = "general", tier: str = "flash") -> bool:
        """Decide if a session should be sampled for evaluation.

        Uses tier-based sample rates, QualityStore feedback,
        and a daily budget cap for judge calls.
        """
        global _DAILY_JUDGE_COST, _DAILY_JUDGE_DATE

        if not EVAL_ENABLED_V2:
            return False

        rate = _SAMPLE_RATES.get(tier, 0.2)

        # Quality feedback: high sustained scores → reduce sampling
        if _SAMPLE_QUALITY_FEEDBACK:
            try:
                from lib.aether.quality_store import QualityStore

                qs = QualityStore()
                task_scores = qs.get_task_scores(task_type)
                if task_scores:
                    recent = list(task_scores.values())[-_SAMPLE_MIN_SAMPLES:]
                    if recent:
                        avg = sum(r.get("avg_score", 0) for r in recent if isinstance(r, dict)) / len(recent)
                        if avg > _SAMPLE_HIGH_SCORE_THRESHOLD:
                            rate *= _SAMPLE_REDUCTION_FACTOR
                        elif avg < 4.0:
                            rate *= _SAMPLE_FAILURE_BOOST
            except Exception:
                pass

        # Daily budget check
        today = date.today()
        if today != _DAILY_JUDGE_DATE:
            _DAILY_JUDGE_COST = 0.0
            _DAILY_JUDGE_DATE = today
        if _DAILY_JUDGE_COST >= _SAMPLE_MAX_DAILY_JUDGE_USD:
            _LOG.debug("Daily judge budget reached ($%.2f)", _SAMPLE_MAX_DAILY_JUDGE_USD)
            return False

        return random.random() < rate

    # ── Session Evaluation ───────────────────────────────────

    def evaluate_session(
        self,
        session: dict,
        judge_model: str | None = None,
    ) -> dict | None:
        """Evalúa una sesión individual usando LLM-as-judge.

        Si la sesión no es ``critical`` y no pasa el sampling,
        retorna ``None`` (sin evaluar).

        Args:
            session: Dict con al menos ``prompt``, ``response`` y
                     opcionalmente ``model``, ``task_type``, ``agent``.
            judge_model: Override del modelo judge para esta llamada.

        Returns:
            dict con scores o None si no se evaluó.
        """
        judge = judge_model or self.judge_model
        prompt = session.get("prompt", "")
        response = session.get("response", "")
        self._current_task_type = session.get("task_type", "general")
        tier = session.get("tier", "flash")

        if not response:
            return {"scores": {m: 0.0 for m in self.metrics}, "weighted_score": 0.0, "verdict": "fail", "dimensions": [], "error": "empty_response"}

        # Sampling: critical sessions always evaluate; others sampled by tier
        if not session.get("critical") and not self.should_sample(task_type=self._current_task_type, tier=tier):
            return None

        # Track judge cost
        global _DAILY_JUDGE_COST
        _DAILY_JUDGE_COST += 0.001  # ~$0.001 estimated per judge call

        # Intentar DeepEval primero
        result = self._eval_with_deepeval(prompt, response, judge)
        if result is not None:
            return result

        # Fallback: EtherJudge
        return self._eval_with_llm_judge(prompt, response, judge)

    def _eval_with_deepeval(self, prompt: str, response: str, judge: str) -> dict | None:
        """Evalúa usando DeepEval si está instalado."""
        try:
            from deepeval import evaluate as deepeval_evaluate
            from deepeval.metrics import GEval
            from deepeval.test_case import LLMTestCase
        except ImportError:
            return None

        try:
            test_case = LLMTestCase(
                input=prompt,
                actual_output=response,
            )
            g_eval = GEval(
                name="Correctness",
                criteria=("Determine if the output correctly addresses the input on a scale of 1-10"),
                model=judge,
            )
            results = deepeval_evaluate([test_case], [g_eval])
            score = results.test_results[0].metrics_data[0].score if results.test_results else 5.0
            return self._build_result(
                scores={m: score for m in self.metrics},
                weighted_score=score,
            )
        except Exception as e:
            _LOG.debug("DeepEval eval failed: %s", e)
            return None

    def _eval_with_llm_judge(self, prompt: str, response: str, judge: str) -> dict:
        """Evalúa usando EtherJudge (LLM-as-judge) en lugar del inline prompt."""
        try:
            from lib.aether.judge import EtherJudge

            ej = EtherJudge(judge_model=judge)
            task_type = getattr(self, '_current_task_type', 'general')
            result = ej.evaluate(prompt=prompt, response=response, task_type=task_type)

            scores = result.get("scores", {m: 5.0 for m in self.metrics})
            weighted = result.get("weighted_score", 5.0)

            out = self._build_result(scores=scores, weighted_score=weighted)
            out["explanation"] = result.get("explanation", "")
            out["strengths"] = result.get("strengths", [])
            out["weaknesses"] = result.get("weaknesses", [])
            return out
        except Exception as e:
            _LOG.debug("EtherJudge evaluation failed: %s", e)
            scores = {m: 5.0 for m in self.metrics}
            weighted = 5.0
            return self._build_result(scores=scores, weighted_score=weighted)

    # ── Helpers ──────────────────────────────────────────────

    @staticmethod
    def _parse_judge_response(raw: str) -> tuple[dict, float]:
        """Parsea la respuesta JSON del modelo judge.

        Busca JSON en bloque markdown, texto plano, o cualquier
        objeto JSON presente en la respuesta.

        Args:
            raw: Texto crudo de la respuesta del judge.

        Returns:
            (scores_dict, weighted_score)
        """
        # 1. Buscar bloque JSON en markdown ```json ... ```
        m = re.search(r"```(?:json)?\s*\n?(\{.*?\})\s*\n?```", raw, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                return EvalPipeline._extract_scores(data)
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        # 2. Buscar objeto JSON con manejo de llaves anidadas
        #    Encuentra el primer { y cuenta profundidad hasta cerrar
        depth = 0
        start = -1
        for i, ch in enumerate(raw):
            if ch == "{":
                if start == -1:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        data = json.loads(raw[start : i + 1])
                        return EvalPipeline._extract_scores(data)
                    except (json.JSONDecodeError, ValueError, TypeError):
                        start = -1  # reset, try next top-level object
        # 3. Fallback: score uniforme
        return {"correctness": 5.0, "coherence": 5.0, "hallucination": 5.0}, 5.0

    @staticmethod
    def _extract_scores(data: dict) -> tuple[dict, float]:
        """Extrae scores normalizados de un dict parseado."""
        scores = data.get("scores", {})
        weighted = float(data.get("weighted_score", 5.0))
        for k in list(scores.keys()):
            try:
                scores[k] = max(1.0, min(10.0, float(scores[k])))
            except (ValueError, TypeError):
                scores[k] = 5.0
        return scores, max(1.0, min(10.0, weighted))

    @staticmethod
    def _build_result(scores: dict, weighted_score: float) -> dict:
        """Construye el dict de resultado normalizado."""
        weighted_score = max(0.0, min(10.0, float(weighted_score)))

        # Verdict basado en weighted_score
        if weighted_score >= 7.0:
            verdict = "pass"
        elif weighted_score >= 4.0:
            verdict = "warn"
        else:
            verdict = "fail"

        dimensions = [
            {
                "name": k,
                "score": max(1.0, min(10.0, float(v))),
                "weight": 1.0 / max(len(scores), 1),
            }
            for k, v in scores.items()
        ]

        return {
            "scores": {k: max(1.0, min(10.0, float(v))) for k, v in scores.items()},
            "weighted_score": round(weighted_score, 2),
            "verdict": verdict,
            "dimensions": dimensions,
        }

    # ── Batch Evaluation ─────────────────────────────────────

    def run_batch_eval(
        self,
        sessions: list[dict],
        output_path: str | Path | None = None,
    ) -> list[dict]:
        """Evalúa un batch de sesiones y persiste los resultados.

        Cada sesión se evalúa individualmente via ``evaluate_session``.
        Los resultados se persisten en ``deepeval-latest.json`` y cada
        evaluación se registra en ``QualityStore``.

        Args:
            sessions: Lista de dicts con session data.
            output_path: Ruta alternativa de salida.

        Returns:
            Lista de dicts con resultados (uno por sesión).
        """
        results = []
        for session in sessions:
            result = self.evaluate_session(session)
            results.append(result)

            # Integrar con QualityStore
            self._record_to_quality_store(session, result)

        # Persistir batch
        output_data = {
            "generated_at": datetime.now(UTC).isoformat(),
            "judge_model": self.judge_model,
            "total": len(results),
            "results": results,
        }
        out_path = Path(output_path) if output_path else self._results_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            tmp = out_path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(output_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp.replace(out_path)
        except Exception as e:
            _LOG.warning("run_batch_eval: persist failed: %s", e)

        return results

    @staticmethod
    def _record_to_quality_store(session: dict, result: dict):
        """Registra un resultado de evaluación en QualityStore.

        Args:
            session: Dict con datos de la sesión (model, task_type, agent…).
            result: Dict con scores, weighted_score, verdict.
        """
        try:
            from lib.aether.quality_store import QualityStore

            qs = QualityStore()
            qs.record(
                model=session.get("model", "unknown"),
                task_type=session.get("task_type", "general"),
                agent=session.get("agent", ""),
                scores=result.get("scores", {}),
                weighted_score=result.get("weighted_score", 0.0),
                verdict=result.get("verdict", "fail"),
                prompt_size=session.get("prompt_size", 0),
            )
        except Exception as e:
            _LOG.debug("QualityStore.record failed: %s", e)

    # ── Report ───────────────────────────────────────────────

    def get_eval_report(self) -> dict:
        """Resumen de las últimas evaluaciones.

        Lee los resultados persistentes de ``deepeval-latest.json``
        y calcula estadísticas agregadas.

        Returns:
            dict con:
            - last_run: timestamp ISO o None
            - total_evaluated: int
            - avg_scores: dict[str, float]
            - pass_rate: float
            - worst_performers: list[dict]
            - best_performers: list[dict]
        """
        if not self._results_path.exists():
            return {
                "last_run": None,
                "total_evaluated": 0,
                "avg_scores": {},
                "pass_rate": 0.0,
                "worst_performers": [],
                "best_performers": [],
            }

        try:
            data = json.loads(self._results_path.read_text(encoding="utf-8"))
        except Exception as e:
            _LOG.warning("get_eval_report: failed to load: %s", e)
            return {
                "last_run": None,
                "total_evaluated": 0,
                "avg_scores": {},
                "pass_rate": 0.0,
                "worst_performers": [],
                "best_performers": [],
            }

        results = data.get("results", [])
        if not results:
            return {
                "last_run": data.get("generated_at"),
                "total_evaluated": 0,
                "avg_scores": {},
                "pass_rate": 0.0,
                "worst_performers": [],
                "best_performers": [],
            }

        # Scores por modelo
        all_weighted = []
        pass_count = 0

        for r in results:
            ws = r.get("weighted_score", 0.0)
            all_weighted.append(ws)
            if r.get("verdict") == "pass":
                pass_count += 1

        # Promedio por dimensión
        dim_keys = self.metrics
        dim_totals: dict[str, float] = {d: 0.0 for d in dim_keys}
        for r in results:
            scores = r.get("scores", {})
            for d in dim_keys:
                dim_totals[d] += scores.get(d, 0.0)

        n = len(results)
        avg_scores = {d: round(dim_totals[d] / n, 2) for d in dim_keys}

        # Peores / mejores (necesitamos los modelos de las sesiones)
        # Como no persistimos sesiones, usamos QualityStore si es posible
        worst_performers = []
        best_performers = []
        try:
            from lib.aether.quality_store import QualityStore

            qs = QualityStore()
            qs_summary = qs.get_summary()
            per_model = qs_summary.get("per_model", {})

            sorted_models = sorted(
                per_model.items(),
                key=lambda x: x[1].get("avg_score", 0),
            )
            worst_performers = [
                {"model": m, "avg_score": d["avg_score"]} for m, d in sorted_models[:3] if d.get("samples", 0) > 0
            ]
            best_performers = [
                {"model": m, "avg_score": d["avg_score"]}
                for m, d in reversed(sorted_models[-3:])
                if d.get("samples", 0) > 0
            ]
        except Exception:
            pass

        return {
            "last_run": data.get("generated_at"),
            "total_evaluated": n,
            "avg_scores": avg_scores,
            "pass_rate": round(pass_count / n, 3) if n else 0.0,
            "worst_performers": worst_performers,
            "best_performers": best_performers,
        }


# ── Singleton global ──────────────────────────────────────────
_PIPELINE: EvalPipeline | None = None


def _get_pipeline() -> EvalPipeline:
    """Singleton de EvalPipeline."""
    global _PIPELINE
    if _PIPELINE is None:
        _PIPELINE = EvalPipeline()
    return _PIPELINE


# ── Public API ──────────────────────────────────────────────


def trigger_eval(sample_size=None, output_path=None) -> dict:
    """Ejecuta DeepEval sobre sesiones recientes del tracker.

    Wrapper que delega en ``EvalPipeline.run_batch_eval``.

    Args:
        sample_size: Número de sesiones a evaluar.
        output_path: Ruta de salida para el reporte.

    Returns:
        dict con scores por métrica, o dict de error.
    """
    if not EVAL_ENABLED_V2:
        return {"status": "disabled", "message": "DeepEval pipeline disabled (aether)"}

    sample_size = sample_size or EVAL_SAMPLE_SIZE_V2

    try:
        from deepeval import evaluate
        from deepeval.metrics import GEval
        from deepeval.test_case import LLMTestCase
    except ImportError:
        # Fallback: usar EvalPipeline con LLM-as-judge
        pipeline = _get_pipeline()
        tracker = EtherTracker()
        sessions = _get_recent_sessions(tracker, sample_size)
        if not sessions:
            return {"status": "no_data", "message": "No sessions to evaluate"}

        results = pipeline.run_batch_eval(sessions, output_path=output_path)
        report = _generate_report(
            {
                "pipeline_eval": {
                    "total": len(results),
                    "avg_score": (sum(r.get("weighted_score", 0) for r in results) / len(results) if results else 0),
                }
            },
            tracker.get_stats(),
        )
        _persist_report(report, output_path)
        return report

    # DeepEval disponible — usar ruta original
    tracker = EtherTracker()
    stats = tracker.get_stats()

    sessions = _get_recent_sessions(tracker, sample_size)
    if not sessions:
        return {"status": "no_data", "message": "No sessions to evaluate"}

    test_cases = []
    for s in sessions:
        test_cases.append(
            LLMTestCase(
                input=s.get("task", ""),
                actual_output=s.get("output", "N/A"),
                expected_output=s.get("expected_output", None),
            )
        )

    results = {}
    try:
        g_eval = GEval(
            name="Correctness",
            criteria="Determine if the output correctly addresses the input task",
            model="go-pro",
        )
        g_results = evaluate(test_cases, [g_eval])
        results["g_eval"] = {
            "score": (g_results.test_results[0].metrics_data[0].score if g_results.test_results else None),
            "total_tests": len(test_cases),
        }
    except Exception as e:
        results["g_eval"] = {"error": str(e)}

    _log_to_langfuse(results)

    report = _generate_report(results, stats)
    _persist_report(report, output_path)
    return report


def run_eval_pipeline(sample_size=None, output_path=None) -> dict:
    """Ejecuta DeepEval scoring pipeline sobre sesiones recientes del tracker.

    Feature flag: ``ETHER_DEEPEVAL_ENABLED`` desde config (default: false).

    Returns:
        dict con scores por métrica o {"status": "disabled", ...} si deshabilitado.
    """
    from lib.aether.config import ETHER_DEEPEVAL_ENABLED as EVAL_ENABLED

    if not EVAL_ENABLED:
        return {"status": "disabled", "message": "DeepEval pipeline disabled"}

    try:
        from deepeval import evaluate
        from deepeval.metrics import GEval
        from deepeval.test_case import LLMTestCase
    except ImportError:
        return {"status": "error", "message": "deepeval not installed"}

    from lib.aether.config import ETHER_EVAL_SAMPLE_SIZE as EVAL_SAMPLE_SIZE
    from lib.aether.tracker import EtherTracker

    sample_size = sample_size or EVAL_SAMPLE_SIZE
    tracker = EtherTracker()
    stats = tracker.get_stats()
    sessions = tracker.get_recent_sessions(sample_size)
    if not sessions:
        return {"status": "no_data", "message": "No sessions to evaluate"}

    test_cases = []
    for s in sessions:
        test_cases.append(
            LLMTestCase(
                input=s.get("task", ""),
                actual_output=s.get("output", "N/A"),
                expected_output=s.get("expected_output", None),
            )
        )

    results = {}
    try:
        g_eval = GEval(
            name="Correctness",
            criteria="Determine if the output correctly addresses the input task",
            model="go-pro",
        )
        g_results = evaluate(test_cases, [g_eval])
        results["g_eval"] = {
            "score": g_results.test_results[0].metrics_data[0].score if g_results.test_results else None,
            "total_tests": len(test_cases),
        }
    except Exception as e:
        results["g_eval"] = {"error": str(e)}

    output_path = output_path or (
        Path(__file__).resolve().parent.parent.parent.parent.parent / ".memory" / "cache" / f"deepeval-{date.today().isoformat()}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    return results


def auto_eval_if_needed(task_type: str = None, tier: str = None) -> dict | None:
    """Auto-evalúa si se alcanzó el intervalo.

    Incrementa un contador global; cada N llamadas ejecuta
    ``trigger_eval`` con sampling por tier.

    Args:
        task_type: Tipo de tarea para sampling adaptativo.
        tier: Tier del modelo para sampling estratificado.

    Returns:
        dict con resultados si se ejecutó, None si no.
    """
    global _AUTO_EVAL_COUNTER
    _AUTO_EVAL_COUNTER += 1

    if _AUTO_EVAL_COUNTER >= _AUTO_EVAL_INTERVAL:
        _AUTO_EVAL_COUNTER = 0
        _LOG.info("Auto-eval triggered (interval=%d, task=%s, tier=%s)", _AUTO_EVAL_INTERVAL, task_type, tier)
        sample_size = EVAL_SAMPLE_SIZE_V2
        # Tier-based sample size override
        if tier:
            rate = _SAMPLE_RATES.get(tier, 0.2)
            sample_size = max(5, int(sample_size * rate))
        return trigger_eval(sample_size=sample_size)

    return None


# ── Internal helpers ──────────────────────────────────────────


def _get_recent_sessions(tracker, n):
    return tracker.get_recent_sessions(n)


def _generate_report(results, stats):
    return {
        "date": datetime.now(UTC).isoformat(),
        "version": "aether",
        "results": results,
        "tracker_stats": {
            "total_calls": stats["total_calls"],
            "total_cost": stats["total_cost_usd"],
        },
    }


def _persist_report(report, output_path=None):
    """Persiste el reporte de evaluación."""
    output_path = output_path or (_BASE_CACHE / f"deepeval-{datetime.now().strftime('%Y-%m-%d')}.json")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        tmp = output_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(output_path)
    except Exception as e:
        _LOG.warning("Failed to persist eval report: %s", e)


def _log_to_langfuse(results):
    try:
        from lib.aether.observability import observe

        observe(
            func_name="deepeval_pipeline",
            model="eval",
            agent="aether",
            task_type="eval",
            prompt_size=0,
            latency_ms=0,
            success="error" not in results,
            tier="pro",
        )
    except Exception as e:
        _LOG.warning("Failed to log eval to langfuse: %s", e)


if __name__ == "__main__":
    result = trigger_eval()
    print(json.dumps(result, indent=2, ensure_ascii=False))
