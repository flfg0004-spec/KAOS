"""Tests for lib.synapse — concept indexing and wikilink extraction."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_synapse_module_loads():
    import lib.synapse
    assert hasattr(lib.synapse, "status") or hasattr(lib.synapse, "index")


def test_synapse_build_graph():
    from lib.wikilinks import build_graph
    graph = build_graph()
    assert isinstance(graph, dict)
    assert len(graph) > 0


def test_synapse_page_names():
    from lib.wikilinks import build_graph
    graph = build_graph()
    for name, data in graph.items():
        assert "path" in data
        assert "links" in data
        assert "backlinks" in data
        assert isinstance(data["links"], list)
        assert isinstance(data["backlinks"], list)
