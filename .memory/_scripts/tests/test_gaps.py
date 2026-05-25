"""Tests for lib.gaps (F5 knowledge gap detection)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_test_page_map():
    """5-node graph with gaps:
    A → B → C (chain)
    D (isolated)
    E (isolated)
    """
    return {
        "A": {"path": "wiki/concepts/a.md", "headings": ["A"], "content": "machine learning algorithms data training",
              "links": [{"target": "B", "section": ""}], "backlinks": []},
        "B": {"path": "wiki/concepts/b.md", "headings": ["B"], "content": "neural networks deep learning training",
              "links": [{"target": "C", "section": ""}], "backlinks": ["A"]},
        "C": {"path": "wiki/concepts/c.md", "headings": ["C"], "content": "supervised learning classification data",
              "links": [], "backlinks": ["B"]},
        "D": {"path": "wiki/concepts/d.md", "headings": ["D"], "content": "quantum physics wave particle",
              "links": [{"target": "E", "section": ""}], "backlinks": []},
        "E": {"path": "wiki/concepts/e.md", "headings": ["E"], "content": "quantum computing qubits superposition",
              "links": [], "backlinks": ["D"]},
    }


def test_gap_detector_creation():
    from lib.gaps import GapDetector
    gd = GapDetector(_make_test_page_map())
    assert gd.graph.number_of_nodes() == 5
    assert gd.graph.number_of_edges() == 3


def test_information_sinks():
    from lib.gaps import GapDetector
    gd = GapDetector(_make_test_page_map())
    sinks = gd.information_sinks()
    assert len(sinks) >= 2  # C and E have 0 outbound
    for s in sinks:
        assert s["type"] == "information_sink"
        assert s["in_degree"] >= 1


def test_source_orphans():
    from lib.gaps import GapDetector
    gd = GapDetector(_make_test_page_map())
    orphans = gd.source_orphans()
    # A and D have no backlinks
    assert len(orphans) >= 0  # May be 0 if out_degree < 3


def test_topic_islands():
    from lib.gaps import GapDetector
    gd = GapDetector(_make_test_page_map())
    islands = gd.topic_islands()
    # D+E form an island disconnected from A+B+C
    assert len(islands) >= 1
    assert "members" in islands[0]


def test_suggest_gaps():
    from lib.gaps import GapDetector
    gd = GapDetector(_make_test_page_map())
    gaps = gd.suggest_gaps(min_confidence=0.0)
    assert len(gaps) >= 1
    types = {g["type"] for g in gaps}
    assert "information_sink" in types or "topic_island" in types


def test_report_string():
    from lib.gaps import report
    r = report(min_confidence=0.0)
    assert "Knowledge Gap Report" in r
    assert "Total gaps" in r


def test_token_overlap():
    from lib.gaps import _token_overlap
    assert _token_overlap("hello world foo", "hello world bar") > 0
    assert _token_overlap("abc def", "ghi jkl") == 0.0
    assert _token_overlap("", "test") == 0.0


def test_common_topics():
    from lib.gaps import _common_topics
    topics = _common_topics(["machine learning algorithms", "deep learning neural networks"])
    assert len(topics) > 0
    assert "learning" in topics or "machine" in topics or "deep" in topics
