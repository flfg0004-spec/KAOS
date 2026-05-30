"""Tests for lib.atdi — Architecture Technical Debt Index."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_calculate_empty():
    from lib.atdi import calculate

    r = calculate({})
    assert r["atdi_score"] == 0
    assert r["estimated_hours"] == 0
    assert r["severity"] == "none"


def test_calculate_single_critical():
    from lib.atdi import calculate

    r = calculate({"critical": 1})
    assert r["total_smells"] == 1
    assert r["atdi_score"] > 0
    assert r["severity"] in ("low", "medium")


def test_calculate_multiple():
    from lib.atdi import calculate

    r = calculate({"critical": 1, "high": 2, "medium": 3})
    assert r["total_smells"] == 6
    assert r["estimated_hours"] > 10
    assert r["severity"] in ("medium", "high", "critical")


def test_calculate_with_component_impact():
    from lib.atdi import calculate

    r = calculate({"high": 1}, total_components=5, affected_components=3)
    assert r["component_impact"] == 60.0


def test_calculate_all_components_affected():
    from lib.atdi import calculate

    r = calculate({"high": 1}, total_components=5, affected_components=5)
    assert r["component_impact"] == 100.0


def test_from_smell_pipeline():
    from lib.atdi import from_smell_pipeline

    smell_result = {
        "severity_breakdown": {"critical": 1, "high": 1, "medium": 0, "low": 1},
        "static_count": 3,
    }
    r = from_smell_pipeline(smell_result)
    assert "atdi_score" in r
    assert r["total_smells"] == 3


def test_severity_classification():
    from lib.atdi import calculate

    r = calculate({"critical": 5, "high": 5})
    assert r["severity"] in ("high", "critical")


def test_avg_severity():
    from lib.atdi import calculate

    r = calculate({"critical": 1, "low": 1})
    avg = r["avg_severity"]
    assert 2.5 <= avg <= 4.0, f"Expected ~3.0, got {avg}"
