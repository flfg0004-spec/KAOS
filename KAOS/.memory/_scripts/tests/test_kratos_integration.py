"""Integration tests for Kratos — code generation, PRGII methodology, OPA governance."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["LLM_DIRECT_ENABLED"] = "false"
os.environ["KAOS_TESTING"] = "1"


def test_kratos_node_returns_dict():
    from lib.agent_executor import kratos_node

    state = {"topic": "implement API in Python", "profile": "desarrollo"}
    result = kratos_node(state)
    assert "kratos_output" in result
    assert "kratos_prompt" in result


def test_kratos_prompt_includes_prgii():
    from lib.agent_executor import kratos_node

    result = kratos_node({"topic": "write function", "profile": "desarrollo"})
    prompt = result.get("kratos_prompt", "")
    assert "PRGII" in prompt or "PLAN" in prompt


def test_kratos_governance_field():
    from lib.agent_executor import kratos_node

    result = kratos_node({"topic": "test", "profile": "desarrollo"})
    assert "governance_allowed" in result


def test_kratos_empty_topic():
    from lib.agent_executor import kratos_node

    result = kratos_node({"topic": "", "profile": "desarrollo"})
    assert "kratos_output" in result


def test_kratos_code_experience_retrieval():
    from lib.agent_executor import kratos_node

    result = kratos_node({"topic": "fix TypeError", "profile": "desarrollo"})
    prompt = result.get("kratos_prompt", "")
    assert "CodeExperience" in prompt or "experiencias" in prompt.lower()
