"""Tests for lib.strategy — SWOT, OKR, RiskMatrix, StrategyReport."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_swot_analyze():
    from lib.strategy import SWOTMatrix
    swot = SWOTMatrix("El sistema tiene una fortaleza en escalabilidad y oportunidad de crecimiento.",
                       "La arquitectura actual tiene deuda técnica.")
    result = swot.analyze()
    assert isinstance(result, dict)
    assert "strengths" in result
    assert "weaknesses" in result
    assert "opportunities" in result
    assert "threats" in result


def test_swot_render():
    from lib.strategy import SWOTMatrix
    swot = SWOTMatrix("test research", "test arch")
    text = swot.render()
    assert "FODA" in text
    assert "Fortalezas" in text


def test_okr_generate():
    from lib.strategy import OKREngine
    engine = OKREngine()
    okrs = engine.generate(["Mejorar la calidad del sistema", "Reducir incidentes"])
    assert len(okrs) == 2
    assert okrs[0]["objective"] == "Mejorar la calidad del sistema"
    assert len(okrs[0]["key_results"]) >= 1


def test_okr_validate_missing_target():
    from lib.strategy import OKREngine
    engine = OKREngine()
    errors = engine.validate([
        {"objective": "Test objective", "key_results": ["Mejorar sin numero"]}
    ])
    assert len(errors) >= 1
    assert "numeric target" in errors[0] or "missing" in errors[0]


def test_okr_validate_valid():
    from lib.strategy import OKREngine
    engine = OKREngine()
    errors = engine.validate([
        {"objective": "Valid OKR", "key_results": ["Reducir incidentes en 50%"]}
    ])
    assert len(errors) == 0


def test_risk_matrix_identify():
    from lib.strategy import RiskMatrix
    rm = RiskMatrix()
    risks = rm.identify(["Dependencia de API externa", "Competencia en el mercado"])
    assert len(risks) == 2
    assert "risk" in risks[0]
    assert "probability" in risks[0]
    assert "impact" in risks[0]
    assert "mitigation" in risks[0]


def test_risk_matrix_render():
    from lib.strategy import RiskMatrix
    rm = RiskMatrix()
    risks = rm.identify(["Riesgo técnico"])
    text = rm.render()
    assert "Matriz de Riesgos" in text
    assert "Probabilidad" in text


def test_strategy_report_generate():
    from lib.strategy import StrategyReport
    report = StrategyReport("Test Topic", "research data", "architecture data")
    result = report.generate(["Objective 1"])
    assert isinstance(result, dict)
    assert "topic" in result
    assert "swot" in result
    assert "okrs" in result
    assert "risks" in result
    assert "strategy" in result
    assert "confidence" in result


def test_strategy_report_render():
    from lib.strategy import StrategyReport
    report = StrategyReport("Test", "test", "test")
    text = report.render()
    assert "Estrategia:" in text
    assert "Confianza:" in text


def test_strategy_report_to_json():
    from lib.strategy import StrategyReport
    report = StrategyReport("Test", "test", "test")
    js = report.to_json()
    assert isinstance(js, str)
    assert '"topic"' in js
    assert '"okrs"' in js
