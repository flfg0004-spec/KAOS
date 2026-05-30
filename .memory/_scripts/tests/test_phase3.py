"""Quick integration tests for Phase 3 modules."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_opa_bridge_evaluate():
    from lib.opa_bridge import check_agent, status

    s = status()
    assert "opa_available" in s
    assert "policy_files" in s

    # Test agent policy — output must be >= 50 chars with wikilinks
    r = check_agent("aletheia", "research content with [[wikilinks]] and sources referenced correctly in this analysis")
    assert r["allowed"] is True

    # Test short output denial
    r = check_agent("test", "hi")
    assert r["allowed"] is False


def test_opa_bridge_architecture():
    from lib.opa_bridge import check_architecture

    r = check_architecture(
        adr={"title": "Test", "context": "ctx", "decision": "dec", "consequences": ["+ good"], "status": "draft"},
        code="code with required pattern",
    )
    assert "allowed" in r
    assert "denials" in r


def test_arch_graph_add_node():
    from lib.arch_graph import add_node, query, status

    s = status()
    assert "total_nodes" in s

    r = add_node("test-adr", "adr", {"title": "Test ADR"})
    assert r["status"] in ("created", "updated")

    r = query("node", {"id": "test-adr"})
    assert r["count"] >= 1


def test_arch_graph_query_types():
    from lib.arch_graph import query

    r = query("nodes_by_type", {"type": "adr"})
    assert "results" in r
    assert "count" in r

    r = query("recent", {"limit": 5})
    assert "results" in r


def test_pr_gate_no_violations():
    from lib.pr_gate import analyze_diff

    clean = "def test():\n    pass\n"
    r = analyze_diff(clean)
    assert r["violation_count"] == 0
    assert r["score"] == 100


def test_pr_gate_violations():
    from lib.pr_gate import analyze_diff, generate_pr_comment

    bad = "except:\n    pass\nfrom controllers import models\nhost = '127.0.0.1'\n"
    r = analyze_diff(bad)
    assert r["violation_count"] > 0

    comment = generate_pr_comment(r, "Test PR")
    assert "Architecture Review" in comment


def test_pr_gate_blocked():
    from lib.pr_gate import gate

    bad = "except:\n    pass\n"
    r = gate(bad, "test.py", "Bad PR", threshold=80)
    assert "passed" in r
    assert "comment" in r


def test_forecasting_no_data():
    from lib.forecasting import forecast_by_agent, status

    s = status()
    assert "available" in s
    assert "data_points" in s

    forecast_by_agent(days=1, forecast_horizon=7)
    # May be insufficient data or success depending on existing scores


def test_forecasting_summary():
    from lib.forecasting import summary

    s = summary(days=90)
    assert "status" in s


def test_policy_files_exist():
    import os

    root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    arch = os.path.join(root, "policy", "architecture.rego")
    agents = os.path.join(root, "policy", "agents.rego")
    assert os.path.exists(arch), f"Missing: {arch}"
    assert os.path.exists(agents), f"Missing: {agents}"


# ── Negative / Edge Case Tests ─────────────────────────


def test_opa_bridge_denial_short_output():
    from lib.opa_bridge import check_agent

    r = check_agent("kratos", "short")
    assert r["allowed"] is False


def test_opa_bridge_missing_fields():
    from lib.opa_bridge import check_architecture

    r = check_architecture(adr={"title": "incomplete"}, code="")
    assert r["allowed"] is False


def test_opa_bridge_node_exists():
    """Verify arch_graph node ID uniqueness."""
    from lib.arch_graph import add_node

    r1 = add_node("dedup-test", "adr", {"title": "first"})
    r2 = add_node("dedup-test", "adr", {"title": "second"})
    assert r1["status"] in ("created", "updated")
    assert r2["status"] == "updated"


def test_arch_graph_graph_empty():
    from lib.arch_graph import query

    r = query("path", {"source": "nonexistent", "target": "nowhere"})
    assert r["count"] == 0


def test_pr_gate_empty_diff():
    from lib.pr_gate import analyze_diff

    r = analyze_diff("")
    assert r["violation_count"] == 0
    assert r["score"] == 100


def test_pr_gate_binary_diff():
    from lib.pr_gate import analyze_diff

    r = analyze_diff("Binary files a/image.png and b/image.png differ")
    assert r["violation_count"] == 0


def test_pr_gate_threshold():
    from lib.pr_gate import gate

    r = gate("eval() and except: pass", "test.py", "Bad PR", threshold=0)
    assert r["passed"] is True
    r2 = gate("eval() and except: pass", "test.py", "Bad PR", threshold=100)
    assert r2["passed"] is False


def test_forecasting_moving_average():
    from lib.forecasting import moving_average

    r = moving_average([10, 20, 30, 40, 50], window=2)
    assert len(r) == 5
    assert r[-1] == 45.0  # (40+50)/2


def test_policy_files_content():
    """Verify policy files have valid Rego syntax (basic check)."""
    import os

    root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    for fname in ["architecture.rego", "agents.rego"]:
        path = os.path.join(root, "policy", fname)
        with open(path) as f:
            content = f.read()
        assert "package kaos" in content, f"{fname} missing package declaration"
        assert "deny[" in content, f"{fname} missing deny rule"
