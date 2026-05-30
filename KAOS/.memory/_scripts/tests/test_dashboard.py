"""Tests for dashboard generation and metrics structure — v2 with lifecycle + contradictions."""
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))


def test_dashboard_json_exists():
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "..", "dashboard", "dashboard.json")
    assert os.path.exists(dashboard_path), "dashboard.json not found"


def test_dashboard_metrics_structure():
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


def test_dashboard_lifecycle_metrics():
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "..", "dashboard", "dashboard.json")
    with open(dashboard_path, encoding="utf-8") as f:
        data = json.load(f)
    lc = data.get("lifecycle", {})
    assert "tiers" in lc
    assert "total" in lc
    assert "avg_confidence" in lc
    assert "flagged" in lc


def test_dashboard_contradictions_metrics():
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "..", "dashboard", "dashboard.json")
    with open(dashboard_path, encoding="utf-8") as f:
        data = json.load(f)
    ct = data.get("contradictions", {})
    assert "total" in ct
    assert "contradictions" in ct
    assert "complements" in ct


def test_dashboard_quality_sparklines():
    from lib.dashboard import _sparklines
    spark = _sparklines()
    assert isinstance(spark, str)


def test_dashboard_ring_gauge():
    from lib.dashboard import _ring_gauge
    html = _ring_gauge(50, 100, "Test", "#38bdf8")
    assert '<svg' in html
    assert '50' in html or 'Test' in html


def test_dashboard_deepseek():
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "..", "dashboard", "dashboard.json")
    with open(dashboard_path, encoding="utf-8") as f:
        data = json.load(f)
    ds = data.get("deepseek", {})
    assert "total_calls" in ds
    assert "total_cost_usd" in ds
    assert isinstance(ds["total_calls"], (int, float))
