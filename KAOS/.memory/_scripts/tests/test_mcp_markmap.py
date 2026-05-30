"""Tests for mcp_markmap — mindmap generation via Markmap MCP server."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_empty_markdown():
    from mcp_markmap import render_mindmap

    result = json.loads(render_mindmap(""))
    assert result["success"] is False
    assert "empty" in result["error"].lower()


def test_whitespace_markdown():
    from mcp_markmap import render_mindmap

    result = json.loads(render_mindmap("   \n  \n  "))
    assert result["success"] is False
    assert "empty" in result["error"].lower()


def test_markmap_available():
    import subprocess

    try:
        result = subprocess.run(["npx", "markmap", "--version"], capture_output=True, text=True, timeout=15)
        available = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        available = False
    from mcp_markmap import render_mindmap

    result = json.loads(render_mindmap("# Hello\n\n## World\n\nSome content"))
    if available:
        assert result["success"] is True
        assert "path" in result
        output_path = Path(result["path"])
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "markmap" in content.lower() or "svg" in content.lower() or "html" in content.lower()
        output_path.unlink(missing_ok=True)
    else:
        assert result["success"] is False


def test_mindmap_output_file_exists():
    import subprocess

    try:
        result = subprocess.run(["npx", "markmap", "--version"], capture_output=True, text=True, timeout=15)
        available = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        available = False
    if not available:
        return

    from mcp_markmap import render_mindmap

    output = Path(os.path.dirname(__file__)) / "_test_mindmap.html"
    result = json.loads(
        render_mindmap("# Root\n\n## Child 1\n\n## Child 2\n\n### Grandchild\n\nSome text", output_path=str(output))
    )
    assert result["success"] is True
    assert output.exists()
    assert output.stat().st_size > 0
    output.unlink(missing_ok=True)


def test_mcp_instance():
    from mcp_markmap import mcp

    assert mcp.name == "kaos-markmap"
