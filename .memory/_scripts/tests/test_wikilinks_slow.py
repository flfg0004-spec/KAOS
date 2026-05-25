"""Slow tests for lib.wikilinks (requires real embeddings + optional Gemini Flash)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _slow(func):
    func._slow = True
    return func


@_slow
def test_wikilinks_real_suggest():
    from lib.wikilinks import suggest
    suggestions = suggest(min_confidence=0.75, mode="embedding", top_k=5)
    assert isinstance(suggestions, list)
    for s in suggestions:
        assert "from" in s
        assert "to" in s
        assert "score" in s


@_slow
def test_wikilinks_real_suggest_hybrid():
    from lib.wikilinks import suggest
    suggestions = suggest(min_confidence=0.85, mode="hybrid", top_k=5)
    assert isinstance(suggestions, list)


@_slow
def test_wikilinks_real_report():
    from lib.wikilinks import report
    r = report()
    assert "Wikilink Analysis" in r
    assert "Valid wikilinks" in r
