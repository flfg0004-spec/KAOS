"""E2E tests for the full pipeline lifecycle (mcp_pipeline)."""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_pipeline import (
    pipeline_run, pipeline_status, pipeline_cancel, pipeline_list,
    pipeline_execute, PIPELINE_DIR,
)

_cleanup = []


def _remove(pids):
    for pid in pids:
        p = PIPELINE_DIR / f"{pid}.json"
        if p.exists():
            p.unlink()


def test_pipeline_full_cycle():
    r = pipeline_run("e2e test", ["aletheia", "kratos"])
    pid = r["pipeline_id"]
    _cleanup.append(pid)
    assert "error" not in r, f"Run failed: {r}"

    result = pipeline_execute(pid, mock_delay=0.01)
    assert "error" not in result, f"Execute failed: {result}"
    assert result["state"] == "completed", f"Expected completed, got {result['state']}"

    s = pipeline_status(pid)
    assert s["state"] == "completed"
    assert s["completed_nodes"] == 2


def test_pipeline_priority_sorting():
    pids = []
    for pri in ["low", "critical", "normal"]:
        r = pipeline_run(f"pri-{pri}", ["kratos"], priority=pri)
        pids.append(r["pipeline_id"])
        _cleanup.append(r["pipeline_id"])

    lst = pipeline_list(limit=20, sort_by_priority=True)
    prios = [p.get("priority", "normal") for p in lst["pipelines"]]
    critical_idx = prios.index("critical")
    normal_idx = prios.index("normal")
    low_idx = prios.index("low")
    assert critical_idx < normal_idx < low_idx, f"Wrong priority order: {prios}"


def test_pipeline_cancel():
    r = pipeline_run("cancel test", ["kratos"])
    pid = r["pipeline_id"]
    _cleanup.append(pid)

    c = pipeline_cancel(pid)
    assert c["state"] == "cancelled"

    s = pipeline_status(pid)
    assert s["state"] == "cancelled"

    c2 = pipeline_cancel(pid)
    assert "error" not in c2


def test_pipeline_list_filter():
    r1 = pipeline_run("active1", ["kratos"])
    r2 = pipeline_run("active2", ["kratos"])
    _cleanup.extend([r1["pipeline_id"], r2["pipeline_id"]])

    lst_all = pipeline_list(limit=10)
    assert len(lst_all["pipelines"]) >= 2

    pipeline_cancel(r1["pipeline_id"])
    lst_cancelled = pipeline_list(limit=10, state="cancelled")
    cancelled_ids = [p["pipeline_id"] for p in lst_cancelled["pipelines"]]
    assert r1["pipeline_id"] in cancelled_ids


def test_invalid_priority():
    r = pipeline_run("bad prio", ["kratos"], priority="invalid")
    assert "error" in r
    assert "Invalid priority" in r["error"]


def teardown_module(module):
    _remove(_cleanup)
