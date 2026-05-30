"""Tests for lib.knowledge_graph_viz — Cytoscape.js Knowledge Graph."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["KAOS_TESTING"] = "1"


def _small_graph():
    import networkx as nx

    G = nx.DiGraph()
    G.add_node("page_a", path="wiki/page_a.md")
    G.add_node("page_b", path="wiki/page_b.md")
    G.add_node("page_c", path="wiki/page_c.md")
    G.add_edge("page_a", "page_b")
    G.add_edge("page_b", "page_c")
    G.add_edge("page_a", "page_c")
    return G


def _empty_graph():
    import networkx as nx

    return nx.DiGraph()


def test_export_empty_graph():
    from lib.knowledge_graph_viz import export_to_cytoscape

    result = export_to_cytoscape(graph=_empty_graph())
    assert result["elements"]["nodes"] == []
    assert result["elements"]["edges"] == []


def test_export_small_graph():
    from lib.knowledge_graph_viz import export_to_cytoscape

    result = export_to_cytoscape(graph=_small_graph())
    nodes = result["elements"]["nodes"]
    edges = result["elements"]["edges"]
    assert len(nodes) == 3
    assert len(edges) == 3
    node_ids = {n["data"]["id"] for n in nodes}
    assert node_ids == {"page_a", "page_b", "page_c"}


def test_node_has_required_fields():
    from lib.knowledge_graph_viz import export_to_cytoscape

    result = export_to_cytoscape(graph=_small_graph())
    for node in result["elements"]["nodes"]:
        d = node["data"]
        assert "id" in d
        assert "label" in d
        assert "weight" in d
        assert "community" in d
        assert "color" in d


def test_edge_has_required_fields():
    from lib.knowledge_graph_viz import export_to_cytoscape

    result = export_to_cytoscape(graph=_small_graph())
    for edge in result["elements"]["edges"]:
        d = edge["data"]
        assert "id" in d
        assert "source" in d
        assert "target" in d
        assert "weight" in d


def test_node_weights_normalized():
    from lib.knowledge_graph_viz import export_to_cytoscape

    result = export_to_cytoscape(graph=_small_graph())
    weights = [n["data"]["weight"] for n in result["elements"]["nodes"]]
    assert max(weights) <= 1.0
    assert min(weights) >= 0


def test_community_colors():
    from lib.knowledge_graph_viz import COMMUNITY_COLORS, export_to_cytoscape

    result = export_to_cytoscape(graph=_small_graph())
    for node in result["elements"]["nodes"]:
        color = node["data"]["color"]
        assert color in COMMUNITY_COLORS


def test_generate_creates_html():
    from lib.knowledge_graph_viz import generate

    output = Path(os.path.dirname(__file__)) / "_test_kg.html"
    generate(str(output))
    assert output.exists()
    html = output.read_text(encoding="utf-8")
    assert "cytoscape" in html.lower()
    assert "ELEMENTS" in html
    output.unlink(missing_ok=True)


def test_generate_with_small_graph():
    from lib.knowledge_graph_viz import export_to_cytoscape, generate

    data = export_to_cytoscape(graph=_small_graph())
    assert data["elements"]["nodes"]
    output = Path(os.path.dirname(__file__)) / "_test_kg_data.html"
    generate(str(output), graph=_small_graph())
    html = output.read_text(encoding="utf-8")
    assert "page_a" in html
    assert "page_b" in html
    assert "page_c" in html
    output.unlink(missing_ok=True)


def test_default_output_path():
    from lib.knowledge_graph_viz import generate

    result = generate()
    assert result
    output = Path(result)
    assert output.exists()
    assert output.name == "knowledge-graph.html"
    output.unlink(missing_ok=True)


def test_generate_with_real_vault():
    from lib.knowledge_graph_viz import generate

    output = Path(os.path.dirname(__file__)) / "_test_kg_real.html"
    generate(str(output))
    assert output.exists()
    html = output.read_text(encoding="utf-8")
    assert "cytoscape" in html.lower()
    output.unlink(missing_ok=True)


def test_html_contains_cytoscape_script():
    from lib.knowledge_graph_viz import generate

    output = Path(os.path.dirname(__file__)) / "_test_kg_script.html"
    generate(str(output), graph=_small_graph())
    html = output.read_text(encoding="utf-8")
    assert "cytoscape.min.js" in html
    assert "cose" in html  # layout algorithm
    output.unlink(missing_ok=True)


def test_graph_with_isolated_nodes():
    import networkx as nx
    from lib.knowledge_graph_viz import export_to_cytoscape

    G = nx.DiGraph()
    G.add_nodes_from(["a", "b", "c"])
    result = export_to_cytoscape(graph=G)
    assert len(result["elements"]["nodes"]) == 3
    assert len(result["elements"]["edges"]) == 0


def test_graph_with_self_loops():
    import networkx as nx
    from lib.knowledge_graph_viz import export_to_cytoscape

    G = nx.DiGraph()
    G.add_edge("a", "a")
    G.add_edge("a", "b")
    result = export_to_cytoscape(graph=G)
    assert len(result["elements"]["nodes"]) == 2
    assert len(result["elements"]["edges"]) == 2


def test_output_path_creates_dirs():
    from lib.knowledge_graph_viz import generate

    output = Path(os.path.dirname(__file__)) / "_nested_kg_test" / "_kg.html"
    generate(str(output), graph=_small_graph())
    assert output.exists()
    assert output.stat().st_size > 0
    output.unlink(missing_ok=True)
    output.parent.rmdir()
