"""Tests for lib.dsol — token tracker, cache optimization, LLM config."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_dsol_budgets():
    from lib.dsol import BUDGETS
    assert "flash" in BUDGETS
    assert "pro" in BUDGETS
    assert BUDGETS["flash"]["min"] <= BUDGETS["flash"]["optimal"]


def test_dsol_thinking_config():
    from lib.dsol import THINKING_CONFIG, configure_thinking
    assert None in THINKING_CONFIG
    assert "high" in THINKING_CONFIG
    config = configure_thinking(None)
    assert config == {}


def test_dsol_allocate():
    from lib.dsol import allocate
    tokens = allocate("general", 1000, "flash")
    assert tokens >= 1024
    heavy = allocate("synthesize", 1000, "flash")
    assert heavy >= tokens


def test_dsol_build_optimized_context():
    """Test with aletheia (uses directory-only prefixes, avoids file-based glob edge case)."""
    from lib.dsol import build_optimized_context
    ctx = build_optimized_context("aletheia", "test task")
    assert "# Context for aletheia" in ctx
    assert "test task" in ctx


def test_dsol_token_tracker():
    from lib.dsol import TokenTracker
    tracker = TokenTracker()
    stats = tracker.get_stats()
    assert "total_calls" in stats
    assert "total_cost_usd" in stats
    assert isinstance(stats["total_calls"], int)


def test_dsol_get_output_config():
    from lib.dsol import get_output_config
    cfg = get_output_config(use_json=True, thinking=None)
    assert "response_format" in cfg
    cfg2 = get_output_config(use_json=False, thinking="high")
    assert cfg2 == {}


def test_dsol_estimate_cache_ratio():
    from lib.dsol import estimate_cache_ratio
    prompt = [{"role": "system", "content": "Hello"}, {"role": "user", "content": "World"}]
    result = estimate_cache_ratio(prompt)
    assert "cacheable_ratio" in result
    assert result["cacheable_ratio"] > 0
