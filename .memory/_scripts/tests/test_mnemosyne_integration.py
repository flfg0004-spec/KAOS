"""Integration tests for Mnemosyne — curation pipeline, gap feedback, file locking, governance."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["LLM_DIRECT_ENABLED"] = "false"
os.environ["KAOS_TESTING"] = "1"


def test_mnemosyne_node_returns_dict():
    from lib.agent_executor import mnemosyne_node

    state = {"topic": "test integration"}
    result = mnemosyne_node(state)
    assert "mnemosyne_output" in result
    assert "curation_metrics" in result


def test_mnemosyne_curation_report_structure():
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "architecture analysis"})
    report = result.get("mnemosyne_output", "")
    assert "# Mnemosyne Curation Report" in report
    assert "## Results" in report
    assert "## Phases" in report


def test_mnemosyne_phases_executed():
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "test phases"})
    metrics = result.get("curation_metrics", {})
    phases = metrics.get("phases", [])
    assert len(phases) >= 1
    assert any("A:" in p for p in phases)
    assert any("B:" in p for p in phases)


def test_mnemosyne_metrics_contain_kpis():
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "test kpis"})
    metrics = result.get("curation_metrics", {})
    for key in ("tags_added", "wikilinks_added", "lint_issues", "duration_s", "errors"):
        assert key in metrics, f"Missing key: {key}"


def test_mnemosyne_sets_aletheia_gaps():
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "knowledge gaps"})
    assert "aletheia_pending_gaps" in result


def test_mnemosyne_file_locked_write():
    """Verify mnemosyne_node uses file locking for curation report."""
    import inspect

    from lib.agent_executor import mnemosyne_node

    source = inspect.getsource(mnemosyne_node)
    assert "acquire_lock" in source, "mnemosyne_node must use file locking"


def test_mnemosyne_quality_recording():
    """Verify mnemosyne records quality metrics."""
    import inspect

    from lib.agent_executor import mnemosyne_node

    source = inspect.getsource(mnemosyne_node)
    assert "kosmos_quality" in source or "kq_record" in source, "mnemosyne_node must record quality"


def test_mnemosyne_opa_governance():
    """Verify mnemosyne_node checks OPA governance."""
    import inspect

    from lib.agent_executor import mnemosyne_node

    source = inspect.getsource(mnemosyne_node)
    assert "opa_bridge" in source or "check_agent" in source, "mnemosyne_node must check OPA"


def test_mnemosyne_cross_agent_context():
    """Verify mnemosyne_node updates cross-agent context."""
    from lib import pipeline
    from lib.agent_executor import mnemosyne_node

    # Clear context first
    ctx_path = os.path.join(os.path.dirname(__file__), "..", "..", "_pipeline", "context.json")
    if os.path.exists(ctx_path):
        os.remove(ctx_path)
    mnemosyne_node({"topic": "cross agent test"})
    ctx = pipeline.load_context()
    agents = ctx.get("agents", [])
    assert "mnemosyne" in agents, "mnemosyne should be added to context agents"


def test_mnemosyne_empty_topic():
    """Verify mnemosyne handles empty topic gracefully."""
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": ""})
    assert "mnemosyne_output" in result
    assert "curation_metrics" in result


def test_mnemosyne_gap_check_function():
    """Verify _gap_check_node returns structured gaps."""
    from lib.orchestrator import _gap_check_node

    result = _gap_check_node({"topic": "test gaps"})
    assert "mnemosyne_gaps" in result
    assert "needs_gap_check" in result


def test_mnemosyne_gap_check_empty_topic():
    """Verify _gap_check_node handles empty topic."""
    from lib.orchestrator import _gap_check_node

    result = _gap_check_node({"topic": ""})
    assert "mnemosyne_gaps" in result
    assert result["needs_gap_check"] is False


# ── Phase-Specific Metrics Tests ──────────────────────────


def test_mnemosyne_quality_score_range():
    """Verify quality_score is a valid number."""
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "quality check"})
    qs = result["curation_metrics"].get("quality_score", -1)
    assert isinstance(qs, (int, float))
    assert 0 <= qs <= 100


def test_mnemosyne_gapdetector_instantiated():
    """Verify GapDetector is instantiated in source."""
    import inspect

    from lib.agent_executor import mnemosyne_node

    source = inspect.getsource(mnemosyne_node)
    assert "GapDetector()" in source, "GapDetector must be instantiated"


def test_mnemosyne_gaps_in_metrics():
    """Verify gaps_detected metric is present."""
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "gap detection test"})
    assert "gaps_detected" in result["curation_metrics"]


def test_mnemosyne_graph_nodes_metric():
    """Verify graph_nodes metric is present."""
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "graph test"})
    assert "graph_nodes" in result["curation_metrics"]


def test_mnemosyne_crossref_metric():
    """Verify crossref_unidirectional metric is present."""
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "crossref test"})
    assert "crossref_unidirectional" in result["curation_metrics"]


def test_mnemosyne_lifecycle_metrics():
    """Verify lifecycle metrics are present."""
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "lifecycle test"})
    m = result["curation_metrics"]
    assert "lifecycle_total" in m
    assert "lifecycle_avg_confidence" in m


def test_mnemosyne_compress_metric():
    """Verify compress_entries metric is present."""
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "compress test"})
    assert "compress_entries" in result["curation_metrics"]


def test_mnemosyne_new_kpis_in_report():
    """Verify new KPIs appear in the curation report text."""
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "kpi report test"})
    report = result.get("mnemosyne_output", "")
    assert "Quality score" in report
    assert "Graph nodes" in report
    assert "Lifecycle entries" in report


def test_mnemosyne_phase_markers_complete():
    """Verify all 10 phase markers (A-J) exist in source."""
    import inspect

    from lib.agent_executor import mnemosyne_node

    source = inspect.getsource(mnemosyne_node)
    for phase in (
        "A:lint",
        "A:tagger",
        "B:",
        "C:gaps",
        "D:quality",
        "E:compress",
        "F:index",
        "G:graph",
        "H:crossref",
        "I:lifecycle",
        "J:dashboard",
    ):
        assert phase in source, f"Missing phase marker: {phase}"


def test_mnemosyne_incremental_metrics():
    """Verify incremental analysis metrics are present."""
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "incremental test"})
    m = result["curation_metrics"]
    assert "incremental" in m
    assert "files_skipped" in m
    assert "files_processed" in m


def test_mnemosyne_incremental_disabled_by_default():
    """Verify incremental is False when feature flag is off."""
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "default test"})
    m = result["curation_metrics"]
    assert m["incremental"] is False


def test_mnemosyne_opa_returns_denials():
    """Verify OPA governance returns denials list."""
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "opa test"})
    metrics = result["curation_metrics"]
    assert "governance_denials" in metrics


def test_mnemosyne_dashboard_metric():
    """Verify dashboard_path is present."""
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "dashboard test"})
    assert "dashboard_path" in result["curation_metrics"]


def test_mnemosyne_all_results_structure():
    """Verify ALL expected keys in curation_metrics."""
    from lib.agent_executor import mnemosyne_node

    result = mnemosyne_node({"topic": "complete test"})
    m = result["curation_metrics"]
    expected_keys = {
        "tags_added",
        "wikilinks_added",
        "duplicates_merged",
        "gaps_detected",
        "quality_score",
        "lint_issues",
        "graph_nodes",
        "graph_edges",
        "crossref_unidirectional",
        "lifecycle_total",
        "lifecycle_avg_confidence",
        "compress_entries",
        "phases",
        "errors",
        "duration_s",
        "governance_allowed",
        "governance_denials",
    }
    missing = expected_keys - set(m.keys())
    assert not missing, f"Missing keys: {missing}"


def test_mnemosyne_knowledge_scorer_integration():
    from lib.feature_flags import enable, disable

    enable("use_knowledge_scorer")
    try:
        from lib.agent_executor import mnemosyne_node

        result = mnemosyne_node({"topic": "test scorer integration"})
        m = result["curation_metrics"]
        assert "knowledge_score_avg" in m
        assert isinstance(m["knowledge_scores"], list)
        phases = " ".join(m.get("phases", []))
        assert "D2:" in phases or "D2:knowledge_scorer(skip)" in phases
    finally:
        disable("use_knowledge_scorer")


def test_mnemosyne_knowledge_tier_distribution():
    from pathlib import Path
    from lib.knowledge_scorer import score_directory

    import tempfile
    d = Path(tempfile.mkdtemp())
    (d / "a.md").write_text("---\ntitle: A\ntags: [a]\ncreated: 2026-01-01\n---\n\n# A\n\nContenido.\n", encoding="utf-8")
    (d / "b.md").write_text("# B\n\nOtro contenido.\n", encoding="utf-8")
    results = score_directory(d, recursive=False)
    dist = {}
    for r in results:
        lvl = r.get("level", "RAW")
        dist[lvl] = dist.get(lvl, 0) + 1
    assert isinstance(dist, dict)
    assert len(dist) > 0


def test_mnemosyne_synthesis_guardrails():
    from pathlib import Path
    from lib.knowledge_synthesis import synthesize

    import tempfile
    fp = Path(tempfile.mkdtemp()) / "guard-test.md"
    fp.write_text("# Test\n\nContenido.\n", encoding="utf-8")
    scores = {"path": str(fp), "score": 50.0, "level": "CANONICAL", "metrics": {}}
    result = synthesize(fp, scores, dry_run=True)
    error = result.get("error") or ""
    assert "CANONICAL" in error
