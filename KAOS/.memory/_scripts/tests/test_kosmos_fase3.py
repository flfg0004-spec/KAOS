"""Tests for KosmosV2 Fase 3 — Autonomy: monitoring, dashboard, KG, Kronos."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
os.environ["LLM_DIRECT_ENABLED"] = "false"

def test_monitor_quick_scan():
    from kosmos_monitor import ArchitectureMonitor
    mon = ArchitectureMonitor()
    report = mon.quick_scan()
    assert hasattr(report, 'health_score')
    assert hasattr(report, 'atdi_score')
    assert hasattr(report, 'smell_count')
    assert 0 <= report.health_score <= 100
    assert 0 <= report.atdi_score <= 100

def test_monitor_alerts():
    from kosmos_monitor import ArchitectureMonitor
    mon = ArchitectureMonitor()
    alerts = mon.get_alerts()
    assert isinstance(alerts, list)

def test_monitor_trend():
    from kosmos_monitor import ArchitectureMonitor
    mon = ArchitectureMonitor()
    trend = mon.get_trend(days=7)
    assert isinstance(trend, dict)
    assert "health_scores" in trend or "scores" in trend or "averages" in trend

def test_monitor_full_scan():
    from kosmos_monitor import ArchitectureMonitor
    mon = ArchitectureMonitor()
    report = mon.full_scan()
    assert hasattr(report, 'timestamp')
    assert hasattr(report, 'health_score')
    assert hasattr(report, 'component_count')

def test_debt_tracker():
    from kosmos_monitor import DebtTracker
    tracker = DebtTracker()
    result = tracker.estimate_resolution_cost(25.0)
    assert "hours" in result or "estimated_hours" in result or "cost" in result

def test_dashboard_collect():
    from kosmos_dashboard import KosmosDashboard
    dash = KosmosDashboard()
    metrics = dash.collect_metrics()
    assert isinstance(metrics, dict)

def test_dashboard_render():
    from kosmos_dashboard import KosmosDashboard
    dash = KosmosDashboard()
    html = dash.render_html({"health_score": 75, "atdi_score": 15, "smell_count": 5,
                              "smell_breakdown": {"high": 1, "medium": 3, "low": 1},
                              "alerts": [], "adrs": [], "routing": {}, "contracts": {},
                              "pipeline_last": {}, "history": []})
    assert "<html" in html or "<!DOCTYPE" in html
    assert "75" in html or "health" in html.lower()

def test_kronos_feedback():
    from kosmos_kronos_feedback import KosmosKronosLoop
    loop = KosmosKronosLoop()
    result = loop.report_pipeline_health({"pipeline": "KosmosV2", "topic": "test",
                                           "nodes_executed": 8, "nodes_with_errors": 0,
                                           "errors": {}, "elapsed_seconds": 0.5,
                                           "node_results": {}})
    assert isinstance(result, dict)

def test_kronos_bottleneck():
    from kosmos_kronos_feedback import KosmosKronosLoop
    loop = KosmosKronosLoop()
    analysis = loop.get_bottleneck_analysis()
    assert isinstance(analysis, dict)

def test_f3_imports():
    from kosmos_monitor import ArchitectureMonitor, DebtTracker
    from kosmos_dashboard import KosmosDashboard
    from kosmos_kronos_feedback import KosmosKronosLoop, PipelineHealthReport
    assert ArchitectureMonitor is not None
    assert KosmosDashboard is not None
    assert KosmosKronosLoop is not None

def test_arch_graph_class():
    from lib.arch_graph import ArchKnowledgeGraph
    kg = ArchKnowledgeGraph()
    result = kg.add_node("TEST-001", "adr", {"title": "Test"})
    assert result is not None

def test_arch_graph_add_edge():
    from lib.arch_graph import ArchKnowledgeGraph
    kg = ArchKnowledgeGraph()
    kg.add_node("TEST-A", "adr", {"title": "A"})
    kg.add_node("TEST-B", "adr", {"title": "B"})
    result = kg.add_edge("TEST-A", "TEST-B", "references")
    assert result is not None
    assert result.get("status") in ("created", "updated")
