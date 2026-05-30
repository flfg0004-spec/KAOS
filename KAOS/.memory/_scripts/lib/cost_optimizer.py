"""Cost & Reliability Optimization Engine.

Strategy: instead of chasing unreliable free tiers, optimize the existing
DeepSeek + OpenCode Go providers through:
1. Cost tracking per-model with weekly budget management
2. Exponential backoff retry for transient errors
3. Circuit breaker for provider-level failures
4. Semantic cache warming for common prompt patterns

Dashboard targets:
  - Cache hit rate: 2.7% → >60%
  - Weekly cost: $30 → <$5
  - Provider reliability: 99%+
"""

import json
import logging
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".memory" / "cache"
_LOG = logging.getLogger("cost_optimizer")

COST_PER_MODEL = {
    "deepseek-v4-flash": {"input": 0.14, "output": 0.28},
    "deepseek-v4-pro": {"input": 0.50, "output": 1.00},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
}
FLAT_COST = {"opencode-go": {"input": 0.08, "output": 0.16}}
WEEKLY_BUDGET_CENTS = 500
ALERT_THRESHOLD = 0.8

_state: dict[str, Any] = {
    "costs": {},
    "breaker_states": {},
    "cache_stats": {"hits": 0, "misses": 0},
    "weekly_spent_cents": 0,
    "last_reset": datetime.now(UTC).isoformat(),
    "alert_sent": False,
}
_state_lock = threading.Lock()


def _load_state():
    path = CACHE_DIR / "cost_optimizer.json"
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                with _state_lock:
                    _state.update(data)
        except Exception as e:
            _LOG.warning("Failed to load cost state: %s", e)


def _save_state():
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = CACHE_DIR / "cost_optimizer.json"
        with _state_lock, open(path, "w", encoding="utf-8") as f:
            json.dump(_state, f, indent=2, default=str)
    except Exception as e:
        _LOG.warning("Failed to save cost state: %s", e)


def _reset_weekly_if_needed():
    last = datetime.fromisoformat(_state["last_reset"])
    if datetime.now(UTC) - last > timedelta(days=7):
        _state["weekly_spent_cents"] = 0
        _state["alert_sent"] = False
        _state["last_reset"] = datetime.now(UTC).isoformat()


def track_call(provider: str, model: str, prompt_tokens: int, completion_tokens: int):
    _reset_weekly_if_needed()
    cost_table = COST_PER_MODEL if provider == "deepseek" else FLAT_COST
    rates = cost_table.get(model, cost_table.get("deepseek-chat", {"input": 0.14, "output": 0.28}))
    cost_cents = (prompt_tokens * rates["input"] + completion_tokens * rates["output"]) / 10_000
    with _state_lock:
        key = f"{provider}/{model}"
        _state["costs"].setdefault(key, {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_cents": 0})
        _state["costs"][key]["calls"] += 1
        _state["costs"][key]["prompt_tokens"] += prompt_tokens
        _state["costs"][key]["completion_tokens"] += completion_tokens
        _state["costs"][key]["cost_cents"] = round(_state["costs"][key]["cost_cents"] + cost_cents, 4)
        _state["weekly_spent_cents"] = round(_state["weekly_spent_cents"] + cost_cents, 4)
    _check_budget()
    _save_state()


def _check_budget():
    spent = _state["weekly_spent_cents"]
    budget = WEEKLY_BUDGET_CENTS
    if spent >= budget * ALERT_THRESHOLD and not _state["alert_sent"]:
        _state["alert_sent"] = True
        pct = round(spent / budget * 100, 1)
        _LOG.warning("Budget alert: %.1f%% of weekly budget used ($%.2f/$%.2f)", pct, spent / 100, budget / 100)
    if spent >= budget:
        _LOG.warning("Weekly budget EXCEEDED: $%.2f / $%.2f", spent / 100, budget / 100)


_breaker = None


def _get_breaker():
    global _breaker
    if _breaker is None:
        from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER

        _breaker = _ETHER_CIRCUIT_BREAKER
    return _breaker


def record_provider_result(provider: str, success: bool):
    cb = _get_breaker()
    if success:
        cb.record_success(provider)
    else:
        cb.record_failure(provider)
    with _state_lock:
        _state["breaker_states"][provider] = "closed" if success else "open"


def provider_available(provider: str) -> bool:
    cb = _get_breaker()
    return not cb.is_open(provider)


def backoff_delay(attempt: int, base: float = 1.0, max_delay: float = 30.0) -> float:
    return min(base * 2**attempt, max_delay)


def record_cache_hit():
    with _state_lock:
        _state["cache_stats"]["hits"] += 1


def record_cache_miss():
    with _state_lock:
        _state["cache_stats"]["misses"] += 1


def cache_hit_rate() -> float:
    with _state_lock:
        hits = _state["cache_stats"]["hits"]
        misses = _state["cache_stats"]["misses"]
        total = hits + misses
        return round(hits / total * 100, 1) if total > 0 else 0.0


def status() -> dict:
    _reset_weekly_if_needed()
    with _state_lock:
        return {
            "weekly_spent": f"${_state['weekly_spent_cents'] / 100:.2f}",
            "weekly_budget": f"${WEEKLY_BUDGET_CENTS / 100:.2f}",
            "budget_used_pct": round(_state["weekly_spent_cents"] / WEEKLY_BUDGET_CENTS * 100, 1)
            if WEEKLY_BUDGET_CENTS > 0
            else 0,
            "cache_hit_rate": cache_hit_rate(),
            "circuit_breakers": dict(_state["breaker_states"]),
            "costs_by_model": dict(_state["costs"]),
            "alert_sent": _state["alert_sent"],
            "last_reset": _state["last_reset"],
        }


_load_state()

