"""ABTest framework — skeleton for A/B testing model routing decisions.

Permite rutear un porcentaje de tráfico a modelos alternativos
y comparar resultados basados en calidad y costo.
"""

import json
import logging
import os
import random
import threading
from datetime import UTC, datetime
from pathlib import Path

_LOG = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / ".memory" / "cache"
DEFAULT_PATH = CACHE_DIR / "ab_testing.json"
_KAOS_TESTING = os.environ.get("KAOS_TESTING", "").lower() in ("1", "true")


class ABTest:
    """A/B testing framework for model routing decisions.

    Permite comparar dos modelos (control vs variant) para un task_type
    y determinar cuál tiene mejor calidad/costo.

    Configuración vía AB_TEST_CONFIG env var (JSON) o programática.

    Attributes:
        task_type: Tipo de tarea a probar
        control_model: Modelo de control (producción)
        variant_model: Modelo variante (experimento)
        variant_pct: Porcentaje de tráfico a variant (0-100)
    """

    def __init__(
        self,
        task_type: str = "",
        control_model: str = "go-flash",
        variant_model: str = "go-mimo",
        variant_pct: int = 10,
    ):
        self.task_type = task_type
        self.control_model = control_model
        self.variant_model = variant_model
        self.variant_pct = max(0, min(100, variant_pct))
        self._lock = threading.Lock()
        self.path = DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

        _LOG.info(
            "ABTest: task=%s control=%s variant=%s pct=%d%%", task_type, control_model, variant_model, variant_pct
        )

    def _load(self) -> dict:
        if _KAOS_TESTING:
            return {"version": 1, "experiments": []}
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception as e:
                _LOG.warning("ABTest: failed to load: %s", e)
        return {"version": 1, "experiments": []}

    def _save(self):
        if _KAOS_TESTING:
            return
        try:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp.replace(self.path)
        except Exception as e:
            _LOG.warning("ABTest: failed to save: %s", e)

    # ── Routing Decision ─────────────────────────────────────

    def should_route_to_b(self, task_type: str) -> bool:
        """Determina si esta llamada debe ir al modelo variant.

        Args:
            task_type: Tipo de tarea actual

        Returns:
            True si debe usar variant_model, False para control_model
        """
        if task_type != self.task_type:
            return False
        return random.randint(1, 100) <= self.variant_pct

    def get_model_for_task(self, task_type: str) -> str:
        """Obtiene el modelo a usar: control o variant según A/B test.

        Args:
            task_type: Tipo de tarea

        Returns:
            Nombre del modelo a usar
        """
        if self.should_route_to_b(task_type):
            return self.variant_model
        return self.control_model

    # ── Recording ────────────────────────────────────────────

    def record_result(
        self, task_type: str, model: str, quality_score: float, cost_usd: float, success: bool, latency_ms: float = 0.0
    ):
        """Registra el resultado de una llamada para el análisis A/B.

        Args:
            task_type: Tipo de tarea
            model: Modelo usado
            quality_score: Score de calidad (0-10)
            cost_usd: Costo en USD
            success: Si la llamada fue exitosa
            latency_ms: Latencia en milisegundos
        """
        if task_type != self.task_type:
            return

        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "task_type": task_type,
            "model": model,
            "group": "variant" if model == self.variant_model else "control",
            "quality_score": round(quality_score, 2),
            "cost_usd": round(cost_usd, 6),
            "success": success,
            "latency_ms": round(latency_ms, 2),
        }

        with self._lock:
            self._data.setdefault("experiments", []).append(entry)
            # Mantener máx 5000 entries
            if len(self._data["experiments"]) > 5_000:
                self._data["experiments"] = self._data["experiments"][-2_500:]
            self._save()

    # ── Analysis ─────────────────────────────────────────────

    def get_winner(self, task_type: str = "") -> dict | None:
        """Determina el ganador del A/B test basado en calidad.

        Compara quality_score promedio entre control y variant.
        Requiere mínimo 10 muestras por grupo.

        Args:
            task_type: Filtrar por task_type (opcional)

        Returns:
            dict con análisis comparativo o None si datos insuficientes
        """
        tt = task_type or self.task_type
        control_scores = []
        variant_scores = []

        with self._lock:
            for e in self._data.get("experiments", []):
                if e.get("task_type") != tt:
                    continue
                if e.get("model") == self.control_model:
                    control_scores.append(e)
                elif e.get("model") == self.variant_model:
                    variant_scores.append(e)

        if len(control_scores) < 10 or len(variant_scores) < 10:
            _LOG.info(
                "ABTest: insufficient data for winner analysis (control=%d, variant=%d, min=10)",
                len(control_scores),
                len(variant_scores),
            )
            return None

        control_avg = sum(s["quality_score"] for s in control_scores) / len(control_scores)
        variant_avg = sum(s["quality_score"] for s in variant_scores) / len(variant_scores)
        control_cost = sum(s["cost_usd"] for s in control_scores) / len(control_scores)
        variant_cost = sum(s["cost_usd"] for s in variant_scores) / len(variant_scores)
        control_success = sum(1 for s in control_scores if s["success"]) / len(control_scores)
        variant_success = sum(1 for s in variant_scores if s["success"]) / len(variant_scores)

        winner = "control" if control_avg >= variant_avg else "variant"

        return {
            "task_type": tt,
            "control": {
                "model": self.control_model,
                "samples": len(control_scores),
                "avg_quality": round(control_avg, 2),
                "avg_cost_usd": round(control_cost, 6),
                "success_rate": round(control_success, 3),
            },
            "variant": {
                "model": self.variant_model,
                "samples": len(variant_scores),
                "avg_quality": round(variant_avg, 2),
                "avg_cost_usd": round(variant_cost, 6),
                "success_rate": round(variant_success, 3),
            },
            "winner": winner,
            "quality_delta": round(variant_avg - control_avg, 2),
            "cost_delta_pct": round((variant_cost - control_cost) / max(control_cost, 0.0001) * 100, 1),
        }

    def get_experiment_summary(self) -> list:
        """Resumen de todos los experimentos registrados."""
        with self._lock:
            return list(self._data.get("experiments", []))[-50:]

    def reset(self):
        """Limpia todos los datos de experimentos."""
        with self._lock:
            self._data = {"version": 1, "experiments": []}
            self._save()
        _LOG.info("ABTest: reset completed")
