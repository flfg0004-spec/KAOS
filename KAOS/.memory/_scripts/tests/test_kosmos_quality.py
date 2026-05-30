import os, sys, json, tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"

from lib.quality import agent as kq


def test_heuristic_fallback_honest_for_empty():
    result = kq._heuristic_fallback("")
    assert result.get("insufficient_data", False), "empty text should flag insufficient_data"
    assert result.get("veracidad", 100) == 0, "empty text should score 0"


def test_heuristic_fallback_honest_for_short():
    result = kq._heuristic_fallback("Hi")
    assert result.get("insufficient_data", False), "short text should flag insufficient_data"


def test_heuristic_fallback_good_text():
    text = """## Resumen ejecutivo del analisis
Hallazgo importante con fuente https://example.com que confirma la hipotesis inicial del estudio.
## Conclusiones y recomendaciones
El analisis demuestra que los resultados son consistentes con la literatura existente.
"""
    result = kq._heuristic_fallback(text)
    assert not result.get("insufficient_data", True), "good text should not flag insufficient_data"
    assert result.get("veracidad", 0) > 0, "good text should have positive veracidad"


def test_evaluate_agent_output_returns_dict():
    text = "## Resumen ejecutivo\n" * 20
    result = kq.evaluate_agent_output("aletheia", text)
    assert "composite" in result
    assert "real_metrics" in result
    assert isinstance(result["composite"], (int, float))


def test_record_creates_entry():
    orig_file = kq.TIMESERIES_FILE
    with tempfile.TemporaryDirectory() as tmp:
        kq.TIMESERIES_FILE = Path(tmp) / "test-scores.json"
        entry = kq.record("aletheia", "## Test\nSome content", topic="test-topic")
        assert entry["agent"] == "aletheia"
        assert entry["topic"] == "test-topic"
        assert "composite" in entry
        assert "timestamp" in entry
    kq.TIMESERIES_FILE = orig_file


def test_summary_empty_when_no_data():
    summary = kq.summary()
    assert isinstance(summary, dict), "summary should be a dict"


def test_evaluate_agent_output_deepval_fallback():
    result = kq.evaluate_agent_output("aletheia", "## Short", task_prompt="test")
    assert "composite" in result


def test_latest_empty_is_list():
    result = kq.latest()
    assert isinstance(result, list)
