"""Tests for MCP CodeExperience server — tool handlers, JSON-RPC protocol."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_process_request_list_tools():
    from lib.mcp_kratos_memory import process_request
    request = {"id": 1, "method": "list_tools", "params": {}}
    response = process_request(request)
    assert "result" in response
    assert "tools" in response["result"]
    tool_names = [t["name"] for t in response["result"]["tools"]]
    assert "ce_search" in tool_names
    assert "ce_store" in tool_names
    assert "ce_status" in tool_names
    assert "ce_feedback" in tool_names
    assert "ce_skill_search" in tool_names


def test_process_request_unknown_method():
    from lib.mcp_kratos_memory import process_request
    request = {"id": 1, "method": "unknown_method", "params": {}}
    response = process_request(request)
    assert "error" in response
    assert response["error"]["code"] == -32601


def test_ce_search_no_query():
    from lib.mcp_kratos_memory import _handle_ce_search
    result = _handle_ce_search({"query": ""})
    assert "error" in result


def test_ce_search_returns_results():
    from lib.mcp_kratos_memory import _handle_ce_search
    result = _handle_ce_search({"query": "error", "top_k": 3})
    assert "results" in result
    assert "count" in result


def test_ce_store_no_message():
    from lib.mcp_kratos_memory import _handle_ce_store
    result = _handle_ce_store({})
    assert "error" in result


def test_ce_store_creates():
    from lib.code_memory import init
    init()
    from lib.mcp_kratos_memory import _handle_ce_store
    result = _handle_ce_store({"error_message": "MCP test error", "language": "python"})
    assert result["status"] in ("created", "exists")


def test_ce_status():
    from lib.mcp_kratos_memory import _handle_ce_status
    result = _handle_ce_status({})
    assert "total_experiences" in result or "active" in result


def test_ce_feedback_no_hash():
    from lib.mcp_kratos_memory import _handle_ce_feedback
    result = _handle_ce_feedback({"hash": ""})
    assert "error" in result


def test_ce_skill_search_no_query():
    from lib.mcp_kratos_memory import _handle_ce_skill_search
    result = _handle_ce_skill_search({"query": ""})
    assert "error" in result


def test_ce_skill_search_returns():
    from lib.mcp_kratos_memory import _handle_ce_skill_search
    result = _handle_ce_skill_search({"query": "error", "top_k": 3})
    assert "skills" in result
    assert "count" in result


def test_process_request_malformed_json():
    from lib.mcp_kratos_memory import process_request
    request = {"method": "ce_status", "params": {}}
    response = process_request(request)
    assert "result" in response
