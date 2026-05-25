"""Tests for Multi-Model Router integration (resolve_model + CircuitBreaker + chat)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_resolve_model_comprehensive():
    from lib.dsol import resolve_model

    cases = [
        ("task_type=research",   {"task_type": "research"},         "go-pro",   "high"),
        ("task_type=strategy",   {"task_type": "strategy"},         "go-kimi-latest", None),
        ("task_type=lint",       {"task_type": "lint"},             "go-flash", None),
        ("agent=aletheia",       {"agent": "aletheia"},             "go-pro",   "high"),
        ("agent=metis",          {"agent": "metis"},                "go-kimi-latest", None),
        ("agent=kratos",         {"agent": "kratos"},               "go-flash", None),
        ("agent=mnemosyne",      {"agent": "mnemosyne"},            "go-flash", None),
        ("override=kimi",        {"task_type": "lint", "model_override": "go-kimi-latest"}, "go-kimi-latest", None),
        ("agent=unknown",        {"agent": "unknown"},              "go-flash", None),
        ("empty",                {},                                "go-flash", None),
    ]

    for name, kwargs, expected_model, expected_thinking in cases:
        result = resolve_model(**kwargs)
        assert result["model"] == expected_model, f"{name}: expected model={expected_model}, got {result['model']}"
        assert result["thinking"] == expected_thinking, f"{name}: expected thinking={expected_thinking}, got {result['thinking']}"


def test_circuit_breaker_integration():
    from lib.dsol import CircuitBreaker

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
    from lib.dsol import resolve_model, _CIRCUIT_BREAKER

    _CIRCUIT_BREAKER.record_success("go-pro")
    _CIRCUIT_BREAKER.record_success("go-flash")

    result = resolve_model(task_type="research")
    assert result["model"] == "go-pro"

    for _ in range(3):
        _CIRCUIT_BREAKER.record_failure("go-pro")

    result2 = resolve_model(task_type="research")
    assert result2["model"] == "go-flash"
    assert "fallback" in result2["resolved_by"]

    _CIRCUIT_BREAKER.record_success("go-pro")


def test_routing_report():
    from lib.dsol import TokenTracker
    tracker = TokenTracker()
    report = tracker.get_routing_report()
    assert isinstance(report, str)
    assert "Multi-Model Routing Report" in report


def test_resolve_model_all_task_types():
    from lib.dsol import resolve_model, TASK_MODEL_MAP
    for task in TASK_MODEL_MAP:
        result = resolve_model(task_type=task)
        assert isinstance(result["model"], str)
        assert result["model"].startswith("go-")
