"""Tests for lib.wikilinks (F3 semantic wikilinks) — fast tests only."""
import sys, os
os.environ["KAOS_TESTING"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_build_graph():
    from lib.wikilinks import build_graph
    g = build_graph()
    assert isinstance(g, dict)
    assert len(g) > 0
    name, data = next(iter(g.items()))
    assert "path" in data
    assert "links" in data
    assert "backlinks" in data


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
    assert r["pages"] > 0


def test_suggest_returns_list():
    """suggest() with extreme threshold returns empty list quickly (no embedding call needed)."""
    from lib.wikilinks import suggest
    result = suggest(min_confidence=0.999, mode="embedding", top_k=5)
    assert isinstance(result, list)


def test_report_no_suggestions():
    from lib.wikilinks import report
    r = report(suggestions_enabled=False)
    assert "Wikilink Analysis" in r
    assert "Pages analyzed" in r
    assert "Valid wikilinks" in r


def test_report_with_suggestions():
    from lib.wikilinks import report
    r = report(suggestions_enabled=True)
    assert "Wikilink Analysis" in r


def test_graph_dot():
    from lib.wikilinks import graph_dot
    dot = graph_dot()
    assert dot.startswith("digraph")
    assert "}" in dot


def test_cosine_sim():
    from lib.wikilinks import _cosine_sim
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert abs(_cosine_sim(a, b) - 1.0) < 1e-6
    assert abs(_cosine_sim(a, [0.0, 1.0, 0.0]) - 0.0) < 1e-6
    assert abs(_cosine_sim([], []) - 0.0) < 1e-6


def test_parse_broken_links():
    from lib.wikilinks import parse
    r = parse()
    assert "broken" in r
    assert isinstance(r["broken"], list)


def test_parse_orphans():
    from lib.wikilinks import parse
    r = parse()
    assert "orphan_list" in r
    assert isinstance(r["orphan_list"], list)


def test_apply_suggestion_dry_run():
    from lib.wikilinks import apply_suggestion, build_graph
    g = build_graph()
    names = list(g.keys())
    if len(names) < 2:
        return
    suggestion = {"from": names[0], "to": names[1], "score": 0.9, "method": "embedding"}
    result = apply_suggestion(suggestion, page_map=g, dry_run=True)
    assert "status" in result
    assert result["status"] in ("would_add", "already_exists", "error")


def test_apply_suggestion_nonexistent():
    from lib.wikilinks import apply_suggestion, build_graph
    g = build_graph()
    suggestion = {"from": "NONEXISTENT_NOTE_12345", "to": "test", "score": 0.5}
    result = apply_suggestion(suggestion, page_map=g, dry_run=True)
    assert "error" in result or result.get("status") == "error"
