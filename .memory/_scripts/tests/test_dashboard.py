"""Tests for dashboard generation and metrics structure."""
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))


def test_dashboard_json_exists():
    """Verifica que el archivo dashboard.json existe."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "..", "dashboard", "dashboard.json")
    assert os.path.exists(dashboard_path), "dashboard.json not found"


def test_dashboard_metrics_structure():
    """Verifica que dashboard.json tiene las metricas esperadas."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "..", "dashboard", "dashboard.json")
    with open(dashboard_path, encoding="utf-8") as f:
        data = json.load(f)
    assert "timestamp" in data
    assert "vault" in data
    assert "health" in data
    assert "pipeline" in data
    assert "ingest" in data
    assert "synapse" in data
    assert "quality" in data


def test_dashboard_deepseek():
    """Verifica que deepseek metrics existen en dashboard."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "..", "dashboard", "dashboard.json")
    with open(dashboard_path, encoding="utf-8") as f:
        data = json.load(f)
    ds = data.get("deepseek", {})
    assert "total_calls" in ds
    assert "total_cost_usd" in ds
    assert isinstance(ds["total_calls"], (int, float))
