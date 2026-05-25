"""Tests for lib.wikilinks (F3 semantic wikilinks)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_build_graph():
    from lib.wikilinks import build_graph
    g = build_graph()
    assert isinstance(g, dict)
    assert len(g) > 0


def test_parse():
    from lib.wikilinks import parse
    r = parse()
    assert "pages" in r
    assert "validLinks" in r
    assert "brokenLinks" in r
    assert "orphans" in r


def test_parse_structure():
    from lib.wikilinks import parse
    r = parse()
    assert r["pages"] > 0, "Should find at least some pages"
    assert r["validLinks"] >= 0
    assert r["brokenLinks"] >= 0


def test_suggest_minimal():
    from lib.wikilinks import suggest
    result = suggest(min_confidence=0.99, mode="embedding")
    assert isinstance(result, list)


def test_suggest_returns_list():
    from lib.wikilinks import suggest
    result = suggest(min_confidence=0.75, mode="embedding", top_k=5)
    assert isinstance(result, list)
    if result:
        assert "from" in result[0]
        assert "to" in result[0]
        assert "score" in result[0]


def test_apply_suggestion_dry_run():
    from lib.wikilinks import apply_suggestion, build_graph
    g = build_graph()
    if not g:
        return
    names = list(g.keys())
    if len(names) < 2:
        return
    suggestion = {"from": names[0], "to": names[1], "score": 0.9, "method": "embedding"}
    result = apply_suggestion(suggestion, page_map=g, dry_run=True)
    assert "status" in result
    assert result["status"] in ("would_add", "already_exists")


def test_report_no_suggestions():
    from lib.wikilinks import report
    r = report(suggestions_enabled=False)
    assert "Wikilink Analysis" in r
    assert "Pages analyzed" in r


def test_graph_dot():
    from lib.wikilinks import graph_dot
    dot = graph_dot()
    assert dot.startswith("digraph")
    assert "}" in dot


def test_get_embedding():
    from lib.wikilinks import _get_embedding
    result = _get_embedding("test query for embedding")
    if result is not None:
        assert len(result) == 384  # bge-small-en-v1.5 dims


def test_cosine_sim():
    from lib.wikilinks import _cosine_sim
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert _cosine_sim(a, b) == 1.0
    assert _cosine_sim(a, [0.0, 1.0, 0.0]) == 0.0
