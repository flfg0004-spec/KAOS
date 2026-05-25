"""Tests for embedding-based txtai (F0: real embeddings replacing TF-IDF)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_txtai_tools_list():
    from mcp_txtai import TOOLS
    names = {t["name"] for t in TOOLS}
    assert "semantic_search" in names
    assert "deduplicate" in names
    assert "similarity_matrix" in names


def test_txtai_initialize_response():
    from mcp_txtai import _respond
    import io, sys as _sys
    captured = io.StringIO()
    old = _sys.stdout
    _sys.stdout = captured
    try:
        _respond(1, {"protocolVersion": "2026-03-26", "capabilities": {"tools": {}}})
        output = captured.getvalue()
        parsed = json.loads(output.strip())
        assert parsed["id"] == 1
        assert "result" in parsed
        assert parsed["result"]["protocolVersion"] == "2026-03-26"
    finally:
        _sys.stdout = old


def test_txtai_dedup_default_threshold():
    from mcp_txtai import TOOLS
    dedup = [t for t in TOOLS if t["name"] == "deduplicate"][0]
    threshold = dedup["inputSchema"]["properties"]["threshold"]["default"]
    assert threshold == 0.85, f"Expected 0.85, got {threshold}"


def test_txtai_empty_search():
    from mcp_txtai import _semantic_search
    result = _semantic_search("test", "/nonexistent/path", 5)
    assert result == []


def test_txtai_empty_dedup():
    from mcp_txtai import _deduplicate
    result = _deduplicate("/nonexistent/path", 0.85)
    assert result == []


def test_obsidian_module_imports():
    from lib.obsidian import ObsidianClient
    client = ObsidianClient()
    assert client is not None
    assert hasattr(client, "search")
    assert hasattr(client, "read")
    assert hasattr(client, "tags")
    assert hasattr(client, "write")
    assert hasattr(client, "append")
    assert hasattr(client, "get_backlinks")
    assert hasattr(client, "find_orphan_notes")
    assert hasattr(client, "find_unresolved_links")
    assert hasattr(client, "suggest_links")


def test_obsidian_status_format():
    from lib.obsidian import ObsidianClient
    client = ObsidianClient()
    status = client.status()
    assert isinstance(status, str)
    assert "Obsidian CLI MCP:" in status
