"""Tests for Ether Router integration (resolve_model + CircuitBreaker + chat)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_resolve_model_comprehensive():
    from lib.aether.import resolve_model

    cases = [
        ("task_type=research", {"task_type": "research"}, "go-pro", "high"),
        ("task_type=strategy", {"task_type": "strategy"}, "go-kimi-latest", None),
        ("task_type=lint", {"task_type": "lint"}, "go-flash", None),
        ("agent=aletheia", {"agent": "aletheia"}, "go-pro", "high"),
        ("agent=metis", {"agent": "metis"}, "go-kimi-latest", None),
        ("agent=kratos", {"agent": "kratos"}, "go-flash", None),
        ("agent=mnemosyne", {"agent": "mnemosyne"}, "go-flash", None),
        ("override=kimi", {"task_type": "lint", "model_override": "go-kimi-latest"}, "go-kimi-latest", None),
        ("agent=unknown", {"agent": "unknown"}, "go-flash", None),
        ("empty", {}, "go-flash", None),
    ]

    for name, kwargs, expected_model, expected_thinking in cases:
        result = resolve_model(**kwargs)
        assert result["model"] == expected_model, f"{name}: expected model={expected_model}, got {result['model']}"
        assert result["thinking"] == expected_thinking, (
            f"{name}: expected thinking={expected_thinking}, got {result['thinking']}"
        )


def test_circuit_breaker_integration():
    from lib.aether.circuit import CircuitBreaker

    cb = CircuitBreaker(failure_threshold=3, reset_timeout=600, half_open_max=1)

    cb.record_success("go-flash")
    assert cb.is_available("go-flash")

    for _ in range(3):
        cb.record_failure("go-pro")

    assert not cb.is_available("go-pro")
    assert cb.get_status()["go-pro"]["state"] == "open"

    cb.record_success("go-pro")
    assert cb.is_available("go-pro")
    assert cb.get_status()["go-pro"]["state"] == "closed"


def test_resolve_model_circuit_breaker_fallback():
    from lib.aether.import resolve_model
    from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER

    _ETHER_CIRCUIT_BREAKER.reset()

    _ETHER_CIRCUIT_BREAKER.record_success("go-pro")
    _ETHER_CIRCUIT_BREAKER.record_success("go-flash")

    result = resolve_model(task_type="research")
    assert result["model"] == "go-pro"

    for _ in range(3):
        _ETHER_CIRCUIT_BREAKER.record_failure("go-pro")

    result2 = resolve_model(task_type="research")
    assert result2["model"] in ("go-mimo", "go-flash")
    assert "fallback" in result2["resolved_by"]

    _ETHER_CIRCUIT_BREAKER.record_success("go-pro")


def test_routing_report():
    from lib.aether.import EtherTracker

    tracker = EtherTracker()
    report = tracker.get_routing_report()
    assert isinstance(report, str)
    assert "Multi-Model Routing Report" in report


def test_resolve_model_all_task_types():
    from lib.aether.import resolve_model
    from lib.aether.config import TASK_MODEL_MAP

    for task in TASK_MODEL_MAP:
        result = resolve_model(task_type=task)
        assert isinstance(result["model"], str)
        assert result["model"].startswith("go-") or result["model"] == "mimo-direct"


# ── New Tests (expanded coverage) ──────────────────────────


def test_aether_facade_backward_compat():
    """Verify lib.ether facade still works."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from lib.aether.import CircuitBreaker, chat, resolve_model
        from lib.aether.tracker import EtherTracker as TokenTracker

        assert resolve_model is not None
        assert TokenTracker is not None
        assert CircuitBreaker is not None
        assert chat is not None


def test_aether_circuit_persistence_save_load():

    from lib.aether.circuit import CircuitBreaker

    cb = CircuitBreaker(failure_threshold=2, reset_timeout=30, half_open_max=1)

    cb.record_failure("test-save-model")
    cb.record_failure("test-save-model")
    assert not cb.is_available("test-save-model")

    saved = cb.get_status()
    assert saved["test-save-model"]["state"] == "open"


def test_aether_tracker_thread_safety():
    """Verify EtherTracker doesn't crash with concurrent calls."""
    import threading

    from lib.aether.tracker import EtherTracker

    tracker = EtherTracker()
    errors = []

    def track_call():
        try:
            tracker.track(prompt_tokens=100, completion_tokens=50, model="go-flash")
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=track_call) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Thread safety errors: {errors}"
    assert tracker.get_stats()["total_calls"] >= 20


def test_aether_rate_limiter():
    from lib.aether.limiter import RateLimiter

    rl = RateLimiter(max_calls=5, window_seconds=60)
    for _ in range(5):
        assert rl.acquire("test")
    assert not rl.acquire("test")


def test_aether_config_env_vars():
    """Verify ETHER_* config env vars are properly exported."""
    from lib.aether.config import (
        ETHER_CIRCUIT_RESET_TIMEOUT,
        ETHER_DEFAULT_MODEL,
        ETHER_FAILURE_THRESHOLD,
        ETHER_HALF_OPEN_MAX,
    )

    assert isinstance(ETHER_DEFAULT_MODEL, str)
    assert ETHER_DEFAULT_MODEL.startswith("go-")
    assert isinstance(ETHER_CIRCUIT_RESET_TIMEOUT, int)
    assert isinstance(ETHER_FAILURE_THRESHOLD, int)
    assert isinstance(ETHER_HALF_OPEN_MAX, int)


def test_circuit_breaker_reset():
    from lib.aether.circuit import CircuitBreaker

    cb = CircuitBreaker(failure_threshold=2, reset_timeout=600, half_open_max=1)
    cb.record_failure("test-reset-model")
    cb.record_failure("test-reset-model")
    assert not cb.is_available("test-reset-model")
    cb.reset()
    assert cb.get_status() == {}, f"Expected empty state after reset, got {cb.get_status()}"
    assert cb.is_available("test-reset-model")


def test_tracker_get_recent_sessions():
    from lib.aether.tracker import EtherTracker

    t = EtherTracker()
    t.track(prompt_tokens=100, completion_tokens=50, model="go-flash")
    sessions = t.get_recent_sessions(5)
    assert len(sessions) >= 1
    assert sessions[0]["model"] == "go-flash"


