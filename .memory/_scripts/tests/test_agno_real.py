"""Test: Agno real MCP Gateway — verify library import and tool exposure."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_agno_import():
    from mcp.server.fastmcp import FastMCP
    assert FastMCP is not None


def test_gateway_non_mock():
    from lib.agno_gateway import create_gateway, MCP_AVAILABLE

    gw = create_gateway(host="127.0.0.1", port=8011)
    status = gw.status()

    assert status["available"] is True, "MCP SDK should be available"
    assert len(status["tools_registered"]) == 5
    assert "kaos_research" in status["tools_registered"]
    assert "vault_read" in status["tools_registered"]


def test_gateway_tools_real():
    from lib.agno_gateway import _vault_read, _vault_search

    result = _vault_read(".memory/wiki/index.md")
    assert isinstance(result, str)
    assert len(result) > 0

    search = _vault_search("aletheia")
    data = __import__("json").loads(search)
    assert isinstance(data, list)
