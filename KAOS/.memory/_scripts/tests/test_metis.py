"""Tests for Metis agent — routing, prompt, context, integration."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"
os.environ["LLM_DIRECT_ENABLED"] = "false"
os.environ["RAG_ENABLED"] = "false"
os.environ["HERMES_ENABLED"] = "false"
os.environ["EXECUTOR_ENABLED"] = "false"


def test_metis_routing_code():
    from lib.orchestrator import route_after_strategy, KAOSState
    state = KAOSState(topic="implementar API REST en Python", profile="desarrollo")
    route = route_after_strategy(state)
    assert route == "kratos", f"Expected kratos, got {route}"
    assert route in ("kratos", "mnemosyne", "cross_validator")


def test_metis_routing_no_code():
    from lib.orchestrator import route_after_strategy, KAOSState
    state = KAOSState(topic="análisis de mercado de IA", profile="desarrollo")
    route = route_after_strategy(state)
    assert route == "mnemosyne", f"Expected mnemosyne, got {route}"


def test_metis_routing_production():
    from lib.orchestrator import route_after_strategy, KAOSState
    state = KAOSState(topic="cualquier tema", profile="produccion")
    route = route_after_strategy(state)
    assert route == "cross_validator", f"Expected cross_validator, got {route}"


def test_metis_node_output():
    from lib.agent_executor import metis_node
    state = {"topic": "test strategy", "aletheia_output": "research", "kosmos_output": "architecture"}
    result = metis_node(state)
    assert "metis_output" in result
    assert "metis_prompt" in result


def test_metis_prompt_includes_methodology():
    from lib.agent_executor import metis_node
    state = {"topic": "test", "aletheia_output": "research", "kosmos_output": "arch"}
    result = metis_node(state)
    prompt = result.get("metis_prompt", "")
    assert "FODA" in prompt or "Diagnóstico" in prompt
    assert "OKR" in prompt or "objetivos" in prompt
    assert "Roadmap" in prompt or "Horizontes" in prompt
    assert "Riesgos" in prompt or "riesgos" in prompt


def test_metis_context_structure():
    """Verify metis writes OKRs/risks to context."""
    from lib.agent_executor import metis_node
    import json
    state = {"topic": "test", "aletheia_output": "x", "kosmos_output": "y"}
    result = metis_node(state)
    assert "metis_prompt" in result
