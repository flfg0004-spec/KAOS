import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.quality.agent import record, latest, summary, _heuristic_fallback


def test_heuristic_fallback_empty():
    dims = _heuristic_fallback("")
    assert dims.get("insufficient_data", False)
    assert dims["veracidad"] == 0
    assert dims["coherencia"] == 0
    assert dims["utilidad"] == 0


def test_heuristic_fallback_with_content():
    text = """# Titulo

## Seccion

Contenido extenso con informacion relevante y referencias.

  - lista item 1
  - lista item 2
  - lista item 3

Conclusion con [[wikilink]] y referencias cruzadas."""
    dims = _heuristic_fallback(text)
    assert dims["completitud"] >= 60
    assert not dims.get("insufficient_data", True)


def test_record_persists():
    entry = record("test_agent", "## Output de prueba\n\ncontenido con [[link]]", topic="test")
    assert entry["agent"] == "test_agent"
    assert entry["composite"] > 0
    assert "timestamp" in entry
    assert "veracidad" in entry
    assert "coherencia" in entry


def test_latest_returns_scores():
    scores = latest()
    assert isinstance(scores, list)
    if scores:
        assert "agent" in scores[0]
        assert "composite" in scores[0]


def test_summary_returns_stats():
    s = summary()
    assert "total" in s
    assert "avg_composite" in s
    assert "agents" in s
