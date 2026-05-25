"""Tests for semantic contradiction detection (F6)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_contradictions_cosine_sim():
    from lib.contradictions import _cosine_sim
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    c = [0.0, 1.0, 0.0]
    assert abs(_cosine_sim(a, b) - 1.0) < 1e-6
    assert abs(_cosine_sim(a, c)) < 1e-6


def test_contradictions_load_state():
    from lib.contradictions import _load_state
    state = _load_state()
    assert isinstance(state, list)


def test_contradictions_report_format():
    from lib.contradictions import report
    r = report()
    assert "Contradictions" in r or "Semantic" in r or "complementary" in r.lower()


def test_contradictions_detect_empty():
    from lib.contradictions import detect
    result = detect()
    assert isinstance(result, list)


def test_contradictions_classify_robust():
    from lib.contradictions import classify
    pair = {"file_a": "test_nonexistent_a", "file_b": "test_nonexistent_b", "similarity": 0.9}
    result = classify(pair)
    assert "verdict" in result
    assert result["verdict"] in ("contradiction", "complement", "independent")


def test_contradictions_run_detection_dry():
    from lib.contradictions import run_detection
    result = run_detection(dry_run=True)
    assert isinstance(result, list)
