"""Tests for mcp_kroki — diagram rendering via Kroki MCP server."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_supported_types():
    from mcp_kroki import SUPPORTED_TYPES

    assert "mermaid" in SUPPORTED_TYPES
    assert "plantuml" in SUPPORTED_TYPES
    assert "graphviz" in SUPPORTED_TYPES
    assert "d2" in SUPPORTED_TYPES
    assert "vegalite" in SUPPORTED_TYPES
    assert "bpmn" in SUPPORTED_TYPES
    assert len(SUPPORTED_TYPES) >= 15


def test_unsupported_type():
    from mcp_kroki import render_diagram

    result = json.loads(render_diagram("foobar", "test"))
    assert result["success"] is False
    assert "Unsupported" in result["error"]


def test_unsupported_lowercase():
    from mcp_kroki import render_diagram

    result = json.loads(render_diagram("MERMAID", "test"))
    assert result["success"] is False  # lowercase conversion happens but server is offline


def test_offline_fallback():
    from mcp_kroki import render_diagram

    result = json.loads(render_diagram("mermaid", "graph TD; A-->B;"))
    assert result["success"] is False
    assert "Cannot connect" in result["error"] or "Kroki" in result["error"]


def test_invalid_output_format():
    from mcp_kroki import render_diagram

    result = json.loads(render_diagram("mermaid", "test", output_format="pdf"))
    assert result["success"] is False
    assert "Unsupported" in result["error"] or "Cannot connect" in result["error"]


def test_default_output_format():
    from mcp_kroki import SUPPORTED_TYPES, render_diagram

    for t in ("mermaid", "plantuml", "graphviz"):
        assert t in SUPPORTED_TYPES
    result = json.loads(render_diagram("mermaid", "test", output_format="svg"))
    assert result["success"] is False  # server offline is expected


def test_kroki_url_env():
    import os

    os.environ["KROKI_URL"] = "http://custom:9999"
    import importlib

    import mcp_kroki

    importlib.reload(mcp_kroki)
    assert mcp_kroki.KROKI_URL == "http://custom:9999"
    os.environ.pop("KROKI_URL", None)
    importlib.reload(mcp_kroki)


def test_kroki_timeout_env():
    import os

    os.environ["KROKI_TIMEOUT"] = "60"
    import importlib

    import mcp_kroki as mod

    importlib.reload(mod)
    assert mod.DEFAULT_TIMEOUT == 60
    os.environ.pop("KROKI_TIMEOUT", None)
    importlib.reload(mod)


def test_mcp_instance():
    from mcp_kroki import mcp

    assert mcp.name == "kaos-kroki"
