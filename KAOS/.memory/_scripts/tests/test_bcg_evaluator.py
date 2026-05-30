"""Tests for lib.bcg_evaluator — BCG 8-dimension evaluation + OKR checklist."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_evaluate_strategy_basic():
    from lib.bcg_evaluator import evaluate_strategy
    r = evaluate_strategy("")
    assert isinstance(r, dict)
    assert "total_score_10" in r
    assert "dimensions" in r
    assert "passed" in r


def test_evaluate_strategy_structure():
    from lib.bcg_evaluator import evaluate_strategy
    text = (
        "# Resumen Ejecutivo\n\n"
        "## Análisis Situacional\n"
        "Según fuentes, el mercado crece 20% anual.\n\n"
        "## Estrategia Propuesta\n"
        "Objetivo: Reducir incidentes en 50%.\n\n"
        "## Riesgos\n"
        "Riesgo de dependencia tecnológica.\n\n"
        "## Próximos Pasos\n"
        "Implementar en Q1 2026."
    )
    r = evaluate_strategy(text)
    assert r["total_score_10"] > 0
    assert len(r["dimensions"]) == 8
    assert "structure" in r["dimensions"]
    assert "synthesis" in r["dimensions"]


def test_evaluate_strategy_dimension_keys():
    from lib.bcg_evaluator import evaluate_strategy
    r = evaluate_strategy("test")
    for dim_id, dim_data in r["dimensions"].items():
        assert "score" in dim_data
        assert "max" in dim_data
        assert "weight" in dim_data
        assert "weighted" in dim_data
        assert dim_data["max"] == 5


def test_evaluate_strategy_detects_structure():
    from lib.bcg_evaluator import evaluate_strategy
    structured = (
        "# Title\n\n## Section 1\ncontent\n\n## Section 2\ncontent\n"
        "## Section 3\ncontent\n## Section 4\ncontent\n## Section 5\ncontent\n"
    )
    r = evaluate_strategy(structured)
    assert r["dimensions"]["structure"]["score"] >= 3


def test_evaluate_strategy_synthesis():
    from lib.bcg_evaluator import evaluate_strategy
    text = (
        "## Recomendaciones\n"
        "1. Implementar feature X en Q1\n"
        "2. Reducir deuda técnica en 30%\n\n"
        "## Conclusión\n"
        "Se recomienda priorizar según RICE score."
    )
    r = evaluate_strategy(text)
    assert r["dimensions"]["synthesis"]["score"] >= 2


def test_evaluate_okrs_basic():
    from lib.bcg_evaluator import evaluate_okrs
    r = evaluate_okrs([])
    assert r["total_okrs"] == 0
    assert r["passed"] is False


def test_evaluate_okrs_valid():
    from lib.bcg_evaluator import evaluate_okrs
    okrs = [
        {"objective": "Mejorar calidad del sistema", "key_results": ["Reducir bugs en 50%", "Aumentar cobertura de tests a 80%"]}
    ]
    r = evaluate_okrs(okrs)
    assert r["total_okrs"] == 1
    assert len(r["checks"]) == 1
    assert r["checks"][0]["scores"]["measurability"] == 1


def test_evaluate_okrs_multiple():
    from lib.bcg_evaluator import evaluate_okrs
    okrs = [
        {"objective": "Objective 1", "key_results": ["Reduce X by 50% without affecting Y"]},
        {"objective": "Objective 2", "key_results": ["Increase Z"]},
    ]
    r = evaluate_okrs(okrs)
    assert r["total_okrs"] == 2
    assert r["checks"][0]["scores"]["counter_metric"] == 1


def test_evaluate_strategy_llm_fallback():
    """When use_llm=False, falls back to heuristic (same as evaluate_strategy)."""
    from lib.bcg_evaluator import evaluate_strategy_llm
    r = evaluate_strategy_llm("test", use_llm=False)
    assert "total_score_10" in r
    assert "framework" in r
    assert "BCG" in r["framework"]


def test_bcg_evaluator_node():
    from lib.agent_executor import bcg_evaluator_node
    state = {"metis_output": "## Strategy\nReduce X by 50%.\n## Recommendations\nImplement in Q1."}
    result = bcg_evaluator_node(state)
    assert "bcg_score" in result
    assert "bcg_passed" in result
    assert "bcg_details" in result
