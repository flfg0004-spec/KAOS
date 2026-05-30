"""RateLimiter — token bucket rate limiter per-agent."""

import logging
import time

_LOG = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter — per-agent LLM call throttling."""

    def __init__(self, max_calls: int = 60, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.tokens = max_calls
        self.last_refill = time.time()

    def acquire(self, agent: str = "") -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_calls, self.tokens + elapsed * (self.max_calls / self.window_seconds))
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    def reset(self):
        self.tokens = self.max_calls
        self.last_refill = time.time()


_RATE_LIMITERS: dict[str, RateLimiter] = {}
_AGENT_RATE_LIMITS: dict[str, int] = {
    "aletheia": 100,
    "kratos": 60,
    "kosmos": 30,
    "mnemosyne": 20,
    "metis": 10,
    "kronos": 30,
    "critic": 20,
    "planner": 20,
}


def check_rate_limit(agent: str) -> bool:
    if agent not in _RATE_LIMITERS:
        max_calls = _AGENT_RATE_LIMITS.get(agent, 60)
        _RATE_LIMITERS[agent] = RateLimiter(max_calls=max_calls)
    return _RATE_LIMITERS[agent].acquire(agent)


def reset():
    for limiter in _RATE_LIMITERS.values():
        limiter.reset()
