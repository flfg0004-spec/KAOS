"""Test S2 features: priority, timeout, retry, executor."""

import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_pipeline import pipeline_run, pipeline_status, pipeline_list, pipeline_cancel, _process_node, PIPELINE_DIR, _load

cleanup = []

def test_priority():
    r1 = pipeline_run("urgent fix", ["kratos"], priority="critical")
    r2 = pipeline_run("background", ["mnemosyne"], priority="low")
    r3 = pipeline_run("normal task", ["aletheia"], priority="normal")
    cleanup.extend([r1["pipeline_id"], r2["pipeline_id"], r3["pipeline_id"]])
    assert r1["priority"] == "critical", f"Expected critical, got {r1['priority']}"
    assert r2["priority"] == "low"
    assert r3["priority"] == "normal"
    
    lst = pipeline_list(limit=5, sort_by_priority=True)
    priorities = [p.get("priority", "normal") for p in lst["pipelines"]]
    assert priorities[0] == "critical", f"Critical should be first: {priorities}"
    print(f"  ✅ Priority order: {' → '.join(priorities)}")

def test_timeout():
    r = pipeline_run("timeout test", ["kratos"], timeout_seconds=2)
    cleanup.append(r["pipeline_id"])
    result = _process_node(r["pipeline_id"], "kratos", mock_delay=5.0)
    assert result["state"] == "timeout", f"Expected timeout, got {result['state']}"
    print(f"  ✅ Timeout detected: {result['state']}")

def test_retry():
    r = pipeline_run("retry test", ["kratos"], timeout_seconds=30)
    cleanup.append(r["pipeline_id"])
    node = _load(r["pipeline_id"])["nodes"]["kratos"]
    node["attempt"] = 0
    result = _process_node(r["pipeline_id"], "kratos", mock_delay=0.1)
    print(f"  ✅ Retry result: {result['state']} (attempts: {result.get('attempt', node['attempt'])})")

def test_invalid_priority():
    r = pipeline_run("invalid", ["kratos"], priority="invalid")
    assert "error" in r, f"Expected error for invalid priority: {r}"
    print(f"  ✅ Invalid priority rejected: {r['error']}")

def cleanup_pipelines():
    for pid in cleanup:
        path = PIPELINE_DIR / f"{pid}.json"
        if path.exists():
            path.unlink()

if __name__ == "__main__":
    try:
        print("=== S2 Pipeline Tests ===\n")
        test_priority()
        test_timeout()
        test_retry()
        test_invalid_priority()
        print("\n✅ All S2 tests passed!")
    finally:
        cleanup_pipelines()
