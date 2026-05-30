"""Tests for lib.viz_orchestrator — visualization orchestrator."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_orchestrate_unknown_agent():
    from lib.viz_orchestrator import orchestrate

    result = orchestrate("nonexistent")
    assert result.success is False
    assert result.paths == []


def test_orchestrate_mnemosyne_default():
    from lib.viz_orchestrator import orchestrate

    result = orchestrate("mnemosyne")
    assert result.success is True
    assert result.agent == "mnemosyne"


def test_orchestrate_kosmos_default():
    from lib.viz_orchestrator import orchestrate

    result = orchestrate("kosmos")
    assert result.success is True


def test_orchestrate_metis_default():
    from lib.viz_orchestrator import orchestrate

    result = orchestrate("metis")
    assert result.success is True


def test_orchestrate_aletheia_default():
    from lib.viz_orchestrator import orchestrate

    result = orchestrate("aletheia")
    assert result.success is True


def test_orchestrate_kratos_default():
    from lib.viz_orchestrator import orchestrate

    result = orchestrate("kratos")
    assert result.success is True


def test_viz_output_dataclass():
    from lib.viz_orchestrator import VizOutput

    v = VizOutput(success=True, paths=["/a.html"], format="html", agent="test", diagram_type="mindmap")
    assert v.success is True
    assert v.paths == ["/a.html"]
    assert v.format == "html"
    assert v.agent == "test"


def test_viz_output_empty():
    from lib.viz_orchestrator import VizOutput

    v = VizOutput()
    assert v.success is False
    assert v.paths == []
    assert v.format == ""


def test_render_kroki_offline():
    from lib.viz_orchestrator import _render_kroki

    result = _render_kroki("mermaid", "graph TD; A-->B;")
    assert result.success is False
    assert result.diagram_type == "mermaid"


def test_render_markmap_offline():
    from lib.viz_orchestrator import _render_markmap

    result = _render_markmap("# Hello")
    assert result.diagram_type == "mindmap"
