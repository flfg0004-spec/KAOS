"""Tests for tools.simulate — Monte Carlo simulation engine for strategic OKRs."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".tools"))

os.environ["KAOS_TESTING"] = "1"


def test_beta_distribution_mean():
    from simulate import SimulationEngine
    engine = SimulationEngine(iterations=50000)
    samples = engine.beta_distribution(5, 2, 50000)
    mean = sum(samples) / len(samples)
    assert abs(mean - 5 / 7) < 0.02, f"Expected mean ~0.714, got {mean}"


def test_evaluate_key_result_high_prob():
    from simulate import SimulationEngine
    engine = SimulationEngine(iterations=10000)
    kr = {
        "name": "Easy KR",
        "target_value": 0.3,
        "variables": [{"name": "HighCapability", "alpha": 5, "beta": 2}],
        "formula": "v0",
    }
    result = engine.evaluate_key_result(kr)
    assert result["probability_success"] > 0.8, f"P={result['probability_success']}"


def test_evaluate_key_result_low_prob():
    from simulate import SimulationEngine
    engine = SimulationEngine(iterations=10000)
    kr = {
        "name": "Hard KR",
        "target_value": 0.95,
        "variables": [{"name": "LowCapability", "alpha": 2, "beta": 5}],
        "formula": "v0",
    }
    result = engine.evaluate_key_result(kr)
    assert result["probability_success"] < 0.2, f"P={result['probability_success']}"


def test_okr_combined_probability():
    from simulate import SimulationEngine
    engine = SimulationEngine(iterations=10000)
    okr = {
        "objective": "Test OKR",
        "key_results": [
            {
                "name": "KR1",
                "target_value": 0.3,
                "variables": [{"name": "V1", "alpha": 5, "beta": 2}],
                "formula": "v0",
            },
            {
                "name": "KR2",
                "target_value": 0.3,
                "variables": [{"name": "V2", "alpha": 5, "beta": 2}],
                "formula": "v0",
            },
        ],
    }
    result = engine.evaluate_okr(okr)
    assert result["combined_probability"] > 0
    for kr_res in result["key_results"]:
        assert kr_res["probability_success"] > result["combined_probability"]


def test_sensitivity_detects_impact():
    from simulate import SimulationEngine
    engine = SimulationEngine(iterations=5000)
    okr = {
        "objective": "Sensitivity Test",
        "key_results": [
            {
                "name": "KR1",
                "target_value": 0.5,
                "variables": [
                    {"name": "Stable", "alpha": 10, "beta": 1},
                    {"name": "Unstable", "alpha": 1, "beta": 10},
                ],
                "formula": "v0 * v1",
            },
        ],
    }
    analysis = engine.sensitivity_analysis(okr)
    kr_analysis = analysis["key_results"][0]
    impacts = [v["impact"] for v in kr_analysis["variables"]]
    assert len(impacts) == 2
    for imp in impacts:
        assert imp > 0, f"Expected positive impact, got {imp}"


def test_cli_help():
    import subprocess
    tools_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".tools")
    script = os.path.join(tools_dir, "simulate.py")
    result = subprocess.run(
        [sys.executable, script, "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "Monte Carlo" in result.stdout
