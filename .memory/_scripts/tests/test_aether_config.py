"""Tests for lib.ether — token tracker, cache optimization, LLM config."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_aether_budgets():
    from lib.aether.config import BUDGETS

    assert "flash" in BUDGETS
    assert "pro" in BUDGETS
    assert BUDGETS["flash"]["min"] <= BUDGETS["flash"]["optimal"]


def test_aether_thinking_config():
    from lib.aether.client import configure_thinking
    from lib.aether.config import THINKING_CONFIG

    assert None in THINKING_CONFIG
    assert "high" in THINKING_CONFIG
    config = configure_thinking(None)
    assert config == {}


def test_aether_allocate():
    from lib.aether.client import allocate

    tokens = allocate("general", 1000, "flash")
    assert tokens >= 1024
    heavy = allocate("synthesize", 1000, "flash")
    assert heavy >= tokens


def test_aether_build_optimized_context():
    """Test with aletheia."""
    from lib.aether.client import build_optimized_context

    ctx = build_optimized_context("aletheia", "test task")
    assert "# Context for aletheia" in ctx
    assert "test task" in ctx


def test_aether_tracker():
    from lib.aether.tracker import EtherTracker

    tracker = EtherTracker()
    stats = tracker.get_stats()
    assert "total_calls" in stats
    assert "total_cost_usd" in stats
    assert isinstance(stats["total_calls"], int)


def test_aether_output_config():
    from lib.aether.client import get_output_config

    cfg = get_output_config(use_json=True, thinking=None)
    assert "response_format" in cfg
    cfg2 = get_output_config(use_json=False, thinking="high")
    assert cfg2 == {}


def test_aether_estimate_cache_ratio():
    from lib.aether.client import estimate_cache_ratio

    prompt = [{"role": "system", "content": "Hello"}, {"role": "user", "content": "World"}]
    result = estimate_cache_ratio(prompt)
    assert "cacheable_ratio" in result
    assert result["cacheable_ratio"] > 0


# ── Multi-Model Router Tests ────────────────────────────────


def test_router_constants():
    from lib.aether.config import AGENT_DEFAULT_TASK, MODEL_FALLBACK_CHAIN, MODEL_TIERS, TASK_MODEL_MAP

    assert "research" in TASK_MODEL_MAP
    assert "strategy" in TASK_MODEL_MAP
    assert "lint" in TASK_MODEL_MAP
    assert "verify" in TASK_MODEL_MAP
    assert MODEL_TIERS["flash"]["target_pct"] == 80
    assert MODEL_TIERS["pro"]["target_pct"] == 5
    assert MODEL_TIERS["kimi"]["target_pct"] == 15
    assert AGENT_DEFAULT_TASK["aletheia"] == "research"
    assert AGENT_DEFAULT_TASK["metis"] == "strategy"
    assert AGENT_DEFAULT_TASK["kratos"] == "code_gen"
    assert "go-flash" in MODEL_FALLBACK_CHAIN
    assert "go-pro" in MODEL_FALLBACK_CHAIN
    assert "go-kimi-latest" in MODEL_FALLBACK_CHAIN


def test_router_resolve_model_by_task_type():
    from lib.aether.import resolve_model

    result = resolve_model(task_type="research")
    assert result["model"] == "go-pro"
    assert result["thinking"] == "high"
    assert result["tier"] == "pro"

    result2 = resolve_model(task_type="lint")
    assert result2["model"] == "go-flash"

    result3 = resolve_model(task_type="strategy")
    assert result3["model"] == "go-kimi-latest"

    result4 = resolve_model(task_type="synthesize")
    assert result4["model"] == "go-kimi-latest"


def test_router_resolve_model_by_agent_fallback():
    from lib.aether.import resolve_model

    result = resolve_model(agent="aletheia")
    assert result["model"] == "go-pro"

    result2 = resolve_model(agent="metis")
    assert result2["model"] == "go-kimi-latest"

    result3 = resolve_model(agent="kratos")
    assert result3["model"] == "go-flash"


def test_router_resolve_model_explicit_override():
    from lib.aether.import resolve_model

    result = resolve_model(task_type="general", model_override="go-kimi-latest")
    assert result["model"] == "go-kimi-latest"


def test_router_circuit_breaker_states():
    from lib.aether.circuit import CircuitBreaker

    cb = CircuitBreaker(failure_threshold=2, reset_timeout=600, half_open_max=1)
    assert cb.is_available("test-model")

    cb.record_success("test-model")
    assert cb.is_available("test-model")

    cb.record_failure("test-model")
    assert cb.is_available("test-model")

    cb.record_failure("test-model")
    assert not cb.is_available("test-model")
    assert cb.get_status()["test-model"]["state"] == "open"


def test_router_budgets_includes_kimi():
    from lib.aether.config import BUDGETS

    assert "kimi" in BUDGETS
    assert BUDGETS["kimi"]["min"] <= BUDGETS["kimi"]["optimal"]


def test_router_all_task_types_have_valid_model():
    from lib.aether.config import TASK_MODEL_MAP

    valid_models = {"go-flash", "go-pro", "go-kimi-latest"}
    for task, rule in TASK_MODEL_MAP.items():
        assert rule["model"] in valid_models, f"{task}: invalid model {rule['model']}"
        assert rule["tier"] in {"flash", "pro", "kimi"}, f"{task}: invalid tier"


def test_router_token_tracker_model_breakdown():
    from lib.aether.import EtherTracker

    tracker = EtherTracker()
    breakdown = tracker.get_model_breakdown()
    assert isinstance(breakdown, dict)


# ── CircuitBreaker Persistence Tests ────────────────────────


def test_circuit_persistence():

    from lib.aether.circuit import CircuitBreaker

    cb = CircuitBreaker(failure_threshold=2, reset_timeout=600, half_open_max=1)
    cb.record_failure("persist-model")
    cb.record_failure("persist-model")
    assert not cb.is_available("persist-model")
    state = cb.get_status()
    assert "persist-model" in state


# ── Chain Import Test ───────────────────────────────────────


def test_aether_import_chain():
    """Verify all levels of ether import work."""
    from lib.aether.import CircuitBreaker, EtherTracker, resolve_model

    assert resolve_model is not None
    assert CircuitBreaker is not None
    assert EtherTracker is not None


# ── Config Env Var Fallback Test ────────────────────────────


def test_aether_env_fallback():
    """Verify ETHER_* config falls back to ROUTER_* by setting ROUTER_* in test env."""
    import os

    os.environ.setdefault("ROUTER_CIRCUIT_BREAKER_ENABLED", "true")
    import importlib

    from lib.aether.import config as ether_config

    importlib.reload(ether_config)
    from lib.aether.config import ETHER_CIRCUIT_BREAKER_ENABLED

    assert isinstance(ETHER_CIRCUIT_BREAKER_ENABLED, bool)


