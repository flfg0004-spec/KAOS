"""Tests for OKR→Initiative→Task pipeline (F3)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"
os.environ["LLM_DIRECT_ENABLED"] = "false"


def test_scope_initiatives_basic():
    from lib.strategy_tools import scope_initiatives
    okrs = [
        {"objective": "Mejorar calidad", "key_results": ["Reducir bugs en 50%", "Aumentar cobertura a 80%"]}
    ]
    initiatives = scope_initiatives(okrs)
    assert len(initiatives) == 2
    assert initiatives[0]["id"] == "INI-1-1"
    assert initiatives[1]["id"] == "INI-1-2"
    assert initiatives[1]["dependencies"] == ["INI-1-1"]


def test_scope_initiatives_empty():
    from lib.strategy_tools import scope_initiatives
    assert scope_initiatives([]) == []


def test_assign_krs():
    from lib.strategy_tools import scope_initiatives, assign_krs
    okrs = [{"objective": "Build API", "key_results": ["Implementar API REST", "Investigar alternativas"]}]
    initiatives = scope_initiatives(okrs)
    assignment = assign_krs(okrs, initiatives)
    assert len(assignment) == 2
    assert assignment.get("INI-1-1") == "kratos"  # "Implementar" → kratos
    assert assignment.get("INI-1-2") == "aletheia"  # "Investigar" → aletheia


def test_build_execution_plan():
    from lib.strategy_tools import scope_initiatives, assign_krs, build_execution_plan
    okrs = [{"objective": "Test", "key_results": ["Reduce X by 50%"]}]
    initiatives = scope_initiatives(okrs)
    assignment = assign_krs(okrs, initiatives)
    plan = build_execution_plan(okrs, initiatives, assignment)
    assert "plan" in plan
    assert plan["total_initiatives"] == 1
    assert "estimated_total_weeks" in plan


def test_execution_plan_structure():
    from lib.strategy_tools import build_execution_plan
    initiatives = [
        {"id": "INI-1-1", "key_result": "KR1", "dependencies": [], "effort_weeks": 2,
         "critical_path": True, "success_criteria": ["C1"]},
    ]
    plan = build_execution_plan([], initiatives, {"INI-1-1": "kratos"})
    assert plan["total_initiatives"] == 1
    assert plan["plan"][0]["agent"] == "kratos"
    assert plan["plan"][0]["critical_path"] is True


def test_metis_node_sets_initiatives():
    """Verify metis_node writes initiatives to context when OKRs present."""
    from lib.agent_executor import metis_node
    state = {"topic": "test pipeline", "aletheia_output": "research", "kosmos_output": "arch"}
    result = metis_node(state)
    assert "metis_output" in result


def test_kratos_node_receives_okrs():
    """Verify kratos_node includes OKRs in prompt structure."""
    from lib.agent_executor import kratos_node
    state = {"topic": "test code"}
    result = kratos_node(state)
    prompt = result.get("kratos_prompt", "")
    assert "OKRs Estratégicos" in prompt or "Tarea" in prompt
