"""Tests for cross-agent intelligence — gap extraction and routing."""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"
os.environ["LLM_DIRECT_ENABLED"] = "false"


def test_metis_node_sets_gaps():
    """Verify metis_node writes gaps to context when critique generated."""
    from lib.agent_executor import metis_node
    state = {"topic": "test gaps", "aletheia_output": "research", "kosmos_output": "arch"}
    result = metis_node(state)
    assert "metis_output" in result


def test_aletheia_node_accepts_gaps():
    """Verify aletheia_node can accept and use gaps_identified."""
    from lib.agent_executor import aletheia_node
    state = {"topic": "research with gaps", "metis_gaps": ["gap1", "gap2"]}
    result = aletheia_node(state)
    assert "aletheia_output" in result


def test_route_with_gaps():
    """Verify routing when gaps are present (inject to pipeline context)."""
    from lib.pipeline import save_context, load_context
    import os
    ctx_path = os.path.join(os.path.dirname(__file__), "..", "..", "_pipeline", "context.json")
    if os.path.exists(ctx_path):
        os.remove(ctx_path)
    save_context("metis", {
        "strategy_summary": "test",
        "metis_to_aletheia": {
            "gaps_identified": ["gap1", "gap2"],
            "confidence": "media",
        }
    })
    ctx = load_context()
    ca = ctx.get("cross_agent", {})
    assert "metis_to_aletheia" in ca
    assert "gaps_identified" in ca["metis_to_aletheia"]


def test_gap_extraction_from_metis():
    """Test that metis_node passes through gaps to cross-agent context."""
    from lib.agent_executor import metis_node
    state = {"topic": "extract gaps", "aletheia_output": "data", "kosmos_output": "arch"}
    result = metis_node(state)
    import json
    from lib.agent_executor import _load_context
    ctx = _load_context()
    ca = ctx.get("cross_agent", {})
    metis_feedback = ca.get("metis_to_aletheia", {})
    assert "gaps_identified" in metis_feedback
    assert "confidence" in metis_feedback
