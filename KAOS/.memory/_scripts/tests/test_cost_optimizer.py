"""Tests for Cost & Reliability Optimization Engine."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_track_call_updates_costs():
    from lib.cost_optimizer import _state, track_call

    dict(_state["costs"])
    track_call("deepseek", "deepseek-v4-flash", 1000, 200)
    assert len(_state["costs"]) >= 1
    key = "deepseek/deepseek-v4-flash"
    assert key in _state["costs"]
    assert _state["costs"][key]["calls"] > 0


def test_budget_tracking():
    from lib.cost_optimizer import status, track_call

    track_call("deepseek", "deepseek-chat", 100000, 20000)
    s = status()
    assert "weekly_spent" in s
    assert "weekly_budget" in s
    assert s["weekly_budget"] == "$5.00"


def test_circuit_breaker_closed():
    from lib.cost_optimizer import get_breaker, provider_available

    b = get_breaker("deepseek")
    b.record_success()
    assert provider_available("deepseek")


def test_circuit_breaker_opens():
    from lib.cost_optimizer import get_breaker, provider_available

    b = get_breaker("test-provider")
    for _ in range(3):
        b.record_failure()
    assert not provider_available("test-provider")


def test_circuit_breaker_records_result():
    from lib.cost_optimizer import provider_available, record_provider_result

    record_provider_result("test-provider-2", True)
    assert provider_available("test-provider-2")


def test_backoff_delay():
    from lib.cost_optimizer import backoff_delay

    assert backoff_delay(0) == 1.0
    assert backoff_delay(1) == 2.0
    assert backoff_delay(2) == 4.0
    assert backoff_delay(3) == 8.0
    assert backoff_delay(10) == 30.0


def test_cache_hit_rate():
    from lib.cost_optimizer import cache_hit_rate, record_cache_hit, record_cache_miss

    record_cache_hit()
    record_cache_hit()
    record_cache_miss()
    rate = cache_hit_rate()
    assert rate > 0
    assert rate <= 100


def test_status_structure():
    from lib.cost_optimizer import status

    s = status()
    assert "cache_hit_rate" in s
    assert "circuit_breakers" in s
    assert "costs_by_model" in s
    assert "weekly_spent" in s
    assert "budget_used_pct" in s


def test_status_type():
    from lib.cost_optimizer import status

    s = status()
    assert isinstance(s["cache_hit_rate"], (int, float))
    assert isinstance(s["circuit_breakers"], dict)
    assert isinstance(s["costs_by_model"], dict)
