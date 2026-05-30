"""Tests for mcp_ether — MCP server tools integration."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_ether_mcp_resolve_model():
    import json

    from mcp_ether import ether_resolve_model

    result = json.loads(ether_resolve_model(task_type="research"))
    assert result["model"] == "go-pro"


def test_ether_mcp_judge_empty():
    import json

    from mcp_ether import ether_judge

    result = json.loads(ether_judge(prompt="", response=""))
    assert "error" in result


def test_ether_mcp_judge_validation():
    import json

    from mcp_ether import ether_judge

    result = json.loads(ether_judge(prompt="test", response=""))
    assert "error" in result


def test_ether_mcp_resolve_model_default():
    import json

    from mcp_ether import ether_resolve_model

    result = json.loads(ether_resolve_model())
    assert result["model"] == "go-flash"


def test_ether_mcp_token_tracker_structure():
    import json

    from mcp_ether import ether_token_tracker

    result = json.loads(ether_token_tracker())
    assert "total_calls" in result
    assert "total_cost_usd" in result
