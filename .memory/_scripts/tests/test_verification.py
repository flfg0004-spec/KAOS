"""Tests for verification_hook — event-driven quality scoring."""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.verification_hook import record, latest, summary, _dimension_score


def test_dimension_score_empty():
    dims = _dimension_score("", "aletheia")
    assert dims["veracidad"] == 0
    assert dims["coherencia"] == 0
    assert dims["completitud"] == 0
    assert dims["reproducibilidad"] >= 60
    assert dims["utilidad"] == 0


def test_dimension_score_with_content():
    text = """# Titulo\n\n## Seccion\n\nContenido extenso con informacion relevante y referencias.\n\n" * 20 + "\n\n- lista item 1\n- lista item 2\n- lista item 3\n\nConclusión con [[wikilink]] y referencias cruzadas."""
    dims = _dimension_score(text, "aletheia")
    assert dims["veracidad"] >= 80
    assert dims["coherencia"] >= 20
    assert dims["completitud"] >= 60
    assert dims["reproducibilidad"] >= 90


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
    assert "agents" in s
    assert "global_avg" in s
    assert "total_records" in s
