"""Integration tests for Metis — strategy generation, OKR validation, BCG evaluation."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["LLM_DIRECT_ENABLED"] = "false"
os.environ["KAOS_TESTING"] = "1"


def test_metis_node_returns_dict():
    from lib.agent_executor import metis_node

    state = {"topic": "test strategy", "aletheia_output": "research", "kosmos_output": "arch"}
    result = metis_node(state)
    assert "metis_output" in result
    assert "metis_prompt" in result


def test_metis_prompt_includes_framework():
    from lib.agent_executor import metis_node

    result = metis_node({"topic": "test", "aletheia_output": "x", "kosmos_output": "y"})
    prompt = result.get("metis_prompt", "")
    assert "FODA" in prompt or "SWOT" in prompt or "OKR" in prompt


def test_metis_accepts_gaps():
    from lib.agent_executor import metis_node

    result = metis_node(
        {"topic": "test", "aletheia_output": "x", "kosmos_output": "y", "aletheia_pending_gaps": ["gap1"]}
    )
    assert "metis_output" in result


def test_metis_empty_topic():
    from lib.agent_executor import metis_node

    result = metis_node({"topic": "", "aletheia_output": "", "kosmos_output": ""})
    assert "metis_output" in result
