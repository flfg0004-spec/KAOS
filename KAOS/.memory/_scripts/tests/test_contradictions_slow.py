"""Slow tests for lib.contradictions (requires real Gemini Flash API)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _slow(func):
    func._slow = True
    return func


@_slow
def test_contradictions_real_classify():
    from lib.contradictions import classify
    pair = {"file_a": "machine-learning", "file_b": "deep-learning", "similarity": 0.92}
    from lib.wikilinks import build_graph
    page_map = build_graph()
    if "machine-learning" in page_map and "deep-learning" in page_map:
        result = classify(pair)
        assert "verdict" in result
        assert result["verdict"] in ("contradiction", "complement", "independent")


@_slow
def test_contradictions_real_report():
    from lib.contradictions import report
    r = report()
    assert isinstance(r, str)
    assert len(r) > 0
