"""Tests for ether_v2 eval module — EvalPipeline, evaluate_session, run_batch_eval, get_eval_report."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Setup path
_SCRIPT_DIR = Path(__file__).resolve().parent.parent  # .memory/_scripts/
sys.path.insert(0, str(_SCRIPT_DIR))

from lib.aether.eval import (
    EvalPipeline,
    _get_pipeline,
    auto_eval_if_needed,
)
from lib.aether.quality_store import QualityStore

# ── Test helpers ───────────────────────────────────────────────

errors = []


def check(desc, cond):
    if not cond:
        errors.append(f"FAIL: {desc}")
        print(f"  ❌ {desc}")
    else:
        print(f"  ✅ {desc}")


# Mock LLM judge responses
_GOOD_JUDGE_RESPONSE = json.dumps(
    {
        "scores": {"correctness": 8, "coherence": 7, "hallucination": 9},
        "weighted_score": 8.0,
    }
)


def _mock_llm_call(agent, prompt, **kwargs):
    """Mock LLM call that returns a judge response."""
    return _GOOD_JUDGE_RESPONSE


# ── Tests: EvalPipeline.evaluate_session ──────────────────────


@patch("lib.llm.agent_llm_call", _mock_llm_call)
def test_evaluate_session():
    print("\n── EvalPipeline.evaluate_session ──")
    pipeline = EvalPipeline()

    # Sesión exitosa con respuesta sustancial
    session = {
        "model": "go-flash",
        "task_type": "code_gen",
        "agent": "kratos",
        "prompt": "Write a function to add two numbers",
        "response": "def add(a, b):\n    return a + b",
        "latency_ms": 150,
    }
    result = pipeline.evaluate_session(session)

    check("Result is dict", isinstance(result, dict))
    check("Result has scores", "scores" in result)
    check("Result has weighted_score", "weighted_score" in result)
    check("Result has verdict", "verdict" in result)
    check("Result has dimensions", "dimensions" in result)

    scores = result.get("scores", {})
    check("Scores has correctness", "correctness" in scores)
    check("Scores has coherence", "coherence" in scores)
    check("Scores has hallucination", "hallucination" in scores)

    ws = result.get("weighted_score", 0)
    check("Weighted score is 0-10", 0 <= ws <= 10)
    check("Verdict is valid", result.get("verdict") in ("pass", "warn", "fail"))

    # Sesión vacía
    empty_session = {
        "model": "go-flash",
        "task_type": "general",
        "agent": "",
        "prompt": "Hello",
        "response": "",
    }
    empty_result = pipeline.evaluate_session(empty_session)
    check("Empty response returns fail verdict", empty_result.get("verdict") == "fail")
    check("Empty response has 0 weighted_score", empty_result.get("weighted_score") == 0.0)


@patch("lib.llm.agent_llm_call", _mock_llm_call)
def test_evaluate_session_judge_override():
    """Verificar que judge_model override funciona."""
    print("\n── evaluate_session judge override ──")
    pipeline = EvalPipeline(judge_model="go-pro")
    check("Default judge_model is go-pro", pipeline.judge_model == "go-pro")

    session = {
        "model": "go-mimo",
        "task_type": "code_simple",
        "agent": "kratos",
        "prompt": "Return the sum of 1 and 2",
        "response": "3",
    }
    result = pipeline.evaluate_session(session, judge_model="go-kimi-latest")
    check("Override judge works", result.get("weighted_score", 0) > 0)


# ── Tests: EvalPipeline._parse_judge_response ─────────────────


def test_parse_judge_response():
    print("\n── _parse_judge_response ──")
    pipeline = EvalPipeline()

    # JSON válido
    raw = '{"scores": {"correctness": 8, "coherence": 7}, "weighted_score": 7.5}'
    scores, ws = pipeline._parse_judge_response(raw)
    check("Parses scores dict", isinstance(scores, dict))
    check("Parses correctness", scores.get("correctness") == 8)
    check("Parses coherence", scores.get("coherence") == 7)
    check("Parses weighted_score", ws == 7.5)

    # JSON en bloque de texto
    raw_block = 'Here are the scores:\n```json\n{"scores": {"correctness": 9, "coherence": 8, "hallucination": 7}, "weighted_score": 8.0}\n```'
    scores2, ws2 = pipeline._parse_judge_response(raw_block)
    check("Parses JSON in markdown block", scores2.get("correctness") == 9)
    check("Parses weighted from block", ws2 == 8.0)

    # Respuesta inválida → fallback uniforme
    raw_bad = "I cannot evaluate this response."
    scores3, ws3 = pipeline._parse_judge_response(raw_bad)
    check("Invalid response falls back to 5.0", ws3 == 5.0)
    for dim in ["correctness", "coherence", "hallucination"]:
        check(f"Fallback has {dim}", scores3.get(dim) == 5.0)

    # Scores fuera de rango
    raw_clamped = '{"scores": {"correctness": 15, "coherence": -1}, "weighted_score": 20}'
    scores4, ws4 = pipeline._parse_judge_response(raw_clamped)
    check("Clamps score >10 to 10", scores4.get("correctness") == 10)
    check("Clamps score <1 to 1", scores4.get("coherence") == 1)
    check("Clamps weighted to 10", ws4 == 10.0)


# ── Tests: EvalPipeline._build_result ─────────────────────────


def test_build_result():
    print("\n── _build_result ──")
    # pass (>=7)
    r1 = EvalPipeline._build_result({"correctness": 8, "coherence": 7}, 7.5)
    check("Score 7.5 → verdict pass", r1["verdict"] == "pass")

    # warn (4-6.9)
    r2 = EvalPipeline._build_result({"correctness": 5, "coherence": 6}, 5.5)
    check("Score 5.5 → verdict warn", r2["verdict"] == "warn")

    # fail (<4)
    r3 = EvalPipeline._build_result({"correctness": 2, "coherence": 3}, 2.5)
    check("Score 2.5 → verdict fail", r3["verdict"] == "fail")

    # Límites
    r4 = EvalPipeline._build_result({"correctness": 0, "coherence": 100}, -5)
    check("Negative weighted clamped to 0", r4["weighted_score"] >= 0)
    check("Weighted clamped max 10", r4["weighted_score"] <= 10)


# ── Tests: EvalPipeline.run_batch_eval ───────────────────────


@patch("lib.llm.agent_llm_call", _mock_llm_call)
def test_run_batch_eval():
    print("\n── run_batch_eval ──")
    pipeline = EvalPipeline()

    sessions = [
        {
            "model": "go-flash",
            "task_type": "code_simple",
            "agent": "kratos",
            "prompt": "Add 1+1",
            "response": "2",
        },
        {
            "model": "go-pro",
            "task_type": "research",
            "agent": "aletheia",
            "prompt": "What is AI?",
            "response": "Artificial intelligence is a field of computer science.",
        },
    ]

    # Usar temp dir para output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        results = pipeline.run_batch_eval(sessions, output_path=tmp_path)
        check("Batch returns list", isinstance(results, list))
        check("Batch returns 2 results", len(results) == 2)

        for i, r in enumerate(results):
            check(f"Result {i} has scores", "scores" in r)
            check(f"Result {i} has weighted_score", "weighted_score" in r)
            check(f"Result {i} has verdict", "verdict" in r)

        # Verificar persistencia
        persisted = json.loads(Path(tmp_path).read_text(encoding="utf-8"))
        check("Persisted file has generated_at", "generated_at" in persisted)
        check("Persisted file has total=2", persisted.get("total") == 2)
        check("Persisted file has results", len(persisted.get("results", [])) == 2)
    finally:
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()


# ── Tests: run_batch_eval → QualityStore integration ─────────


@patch("lib.llm.agent_llm_call", _mock_llm_call)
def test_quality_store_integration():
    print("\n── QualityStore Integration ──")
    pipeline = EvalPipeline()

    sessions = [
        {
            "model": "go-mimo",
            "task_type": "code_simple",
            "agent": "kratos",
            "prompt": "List numbers 1-5",
            "response": "1, 2, 3, 4, 5",
        },
    ]

    pipeline.run_batch_eval(sessions)

    # Verificar que QualityStore tiene los datos
    qs = QualityStore()
    task_scores = qs.get_task_scores("code_simple")
    check("QualityStore has code_simple scores", "go-mimo" in task_scores or len(task_scores) > 0)

    summary = qs.get_summary()
    check("QualityStore summary has entries > 0", summary.get("total_entries", 0) > 0)

    # Verificar per_model
    per_model = summary.get("per_model", {})
    check("Summary has per_model data", len(per_model) > 0)


# ── Tests: get_eval_report ───────────────────────────────────


@patch("lib.llm.agent_llm_call", _mock_llm_call)
def test_get_eval_report():
    print("\n── get_eval_report ──")
    pipeline = EvalPipeline()

    # Primero crear datos con run_batch_eval
    sessions = [
        {
            "model": "go-flash",
            "task_type": "code_simple",
            "agent": "test",
            "prompt": "Test prompt",
            "response": "Test response with sufficient length for evaluation purposes here.",
        },
        {
            "model": "go-pro",
            "task_type": "research",
            "agent": "test",
            "prompt": "Another test",
            "response": "Another longer test response that has meaningful content for evaluation.",
        },
    ]

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        pipeline.run_batch_eval(sessions, output_path=tmp_path)
        # Forzar _results_path al tmp para get_eval_report
        pipeline._results_path = Path(tmp_path)

        report = pipeline.get_eval_report()
        check("Report is dict", isinstance(report, dict))
        check("Report has last_run", "last_run" in report)
        check("Report has total_evaluated", "total_evaluated" in report)
        check("Report has avg_scores", "avg_scores" in report)
        check("Report has pass_rate", "pass_rate" in report)
        check("Report has worst_performers", "worst_performers" in report)
        check("Report has best_performers", "best_performers" in report)

        check("total_evaluated > 0", report.get("total_evaluated", 0) > 0)
        check("pass_rate is 0-1", 0 <= report.get("pass_rate", 0) <= 1)

        avg = report.get("avg_scores", {})
        check("avg_scores has correctness", "correctness" in avg)
        check("avg_scores has coherence", "coherence" in avg)
        check("avg_scores has hallucination", "hallucination" in avg)

    finally:
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()

    # Reporte sin datos (usar temp dir para evitar contaminación)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_none:
        none_path = tmp_none.name
    Path(none_path).unlink()  # borrar para que no exista
    empty_pipeline = EvalPipeline()
    empty_pipeline._results_path = Path(none_path)
    empty_report = empty_pipeline.get_eval_report()
    check("Empty report has last_run None", empty_report.get("last_run") is None)
    check("Empty report has total_evaluated 0", empty_report.get("total_evaluated") == 0)


# ── Tests: _get_pipeline singleton ───────────────────────────


def test_pipeline_singleton():
    print("\n── Pipeline Singleton ──")
    p1 = _get_pipeline()
    p2 = _get_pipeline()
    check("_get_pipeline returns same instance", p1 is p2)
    check("Singleton is EvalPipeline", isinstance(p1, EvalPipeline))


# ── Tests: auto_eval_if_needed_v2 ────────────────────────────


def test_auto_eval():
    print("\n── auto_eval_if_needed_v2 ──")

    # Reset contador
    global _AUTO_EVAL_COUNTER
    # No podemos resetear fácilmente, verificamos que no explota
    try:
        result = auto_eval_if_needed_v2()
        # Si no es el intervalo, devuelve None
        check("auto_eval returns None or dict", result is None or isinstance(result, dict))
    except Exception as e:
        check(f"auto_eval does not crash: {e}", False)


# ── Main ───────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  ETHER V2 — EVAL TESTS")
    print("=" * 50)

    test_evaluate_session()
    test_evaluate_session_judge_override()
    test_parse_judge_response()
    test_build_result()
    test_run_batch_eval()
    test_quality_store_integration()
    test_get_eval_report()
    test_pipeline_singleton()
    test_auto_eval()

    print(f"\n{'=' * 50}")
    if errors:
        print(f"\n  FAILURES ({len(errors)}):")
        for e in errors:
            print(f"    ❌ {e}")
        sys.exit(1)
    else:
        print("  ✅ ALL EVAL TESTS PASSED")
        sys.exit(0)
