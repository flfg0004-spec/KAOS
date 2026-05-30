"""Tests for lib.knowledge_tour — topological sort and markdown generation."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def _make_test_graph():
    import networkx as nx

    G = nx.DiGraph()
    G.add_edge("A", "B")
    G.add_edge("B", "C")
    G.add_edge("A", "D")
    return G


def test_topological_layers_linear():
    import networkx as nx
    from lib.knowledge_tour import topological_layers

    G = nx.DiGraph()
    G.add_edge("A", "B")
    G.add_edge("B", "C")
    layers = topological_layers(G)
    assert len(layers) == 3
    assert layers[0] == ["A"]
    assert layers[1] == ["B"]
    assert layers[2] == ["C"]


def test_topological_layers_diamond():
    from lib.knowledge_tour import topological_layers

    G = _make_test_graph()
    layers = topological_layers(G)
    assert len(layers) == 3
    assert layers[0] == ["A"]
    assert set(layers[1]) == {"B", "D"}
    assert layers[2] == ["C"]


def test_topological_layers_empty():
    import networkx as nx
    from lib.knowledge_tour import topological_layers

    G = nx.DiGraph()
    layers = topological_layers(G)
    assert layers == []


def test_detect_cycles_no_cycles():
    from lib.knowledge_tour import detect_cycles

    G = _make_test_graph()
    cycles = detect_cycles(G)
    assert cycles == []


def test_detect_cycles_with_cycle():
    import networkx as nx
    from lib.knowledge_tour import detect_cycles

    G = nx.DiGraph()
    G.add_edge("A", "B")
    G.add_edge("B", "C")
    G.add_edge("C", "A")
    cycles = detect_cycles(G)
    assert len(cycles) > 0


def test_assign_learning_levels():
    from lib.knowledge_tour import assign_learning_levels

    G = _make_test_graph()
    page_map = {"A": {}, "B": {}, "C": {}, "D": {}}
    levels = assign_learning_levels(page_map, G)
    assert levels["A"] == 0
    assert levels["B"] == 1
    assert levels["C"] == 2
    assert levels["D"] == 1


def test_generate_tour_contains_sections():
    from lib.knowledge_tour import generate_tour

    G = _make_test_graph()
    page_map = {"A": {}, "B": {}, "C": {}, "D": {}}
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "test-tour.md"
        md = generate_tour(page_map, G, output_path=output, title="Test Tour")
        assert "Start Here" in md
        assert "Core Concepts" in md
        assert "Advanced Topics" in md
        assert "```mermaid" in md
        assert "Test Tour" in md


def test_generate_tour_empty_graph():
    import networkx as nx
    from lib.knowledge_tour import generate_tour

    G = nx.DiGraph()
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "empty-tour.md"
        md = generate_tour({}, G, output_path=output, title="Empty Tour")
        assert "Empty Tour" in md


def test_generate_tour_frontmatter():
    import yaml
    from lib.knowledge_tour import generate_tour

    G = _make_test_graph()
    page_map = {"A": {}, "B": {}, "C": {}, "D": {}}
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "fm-tour.md"
        md = generate_tour(page_map, G, output_path=output)
        front = md.split("---")[1]
        parsed = yaml.safe_load(front)
        assert parsed["nodes"] == 4
        assert parsed["levels"] == 3
        assert parsed["cycles"] == 0
