"""Tests for lib.viz — Mermaid visualization generation."""
import sys, os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_viz_module_loads():
    import lib.viz
    assert hasattr(lib.viz, "generate_all") or hasattr(lib.viz, "generate_graph")


def test_viz_generate_graph():
    from lib.viz import generate_graph
    dot = generate_graph()
    assert dot is not None
    assert isinstance(dot, str)
    assert "graph" in dot.lower() or "flowchart" in dot.lower() or "```" in dot


def test_viz_generate_quality():
    from lib.viz import generate_quality
    dot = generate_quality()
    assert dot is not None
    assert isinstance(dot, str)
