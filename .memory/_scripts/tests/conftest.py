"""Pytest conftest — clears CircuitBreaker persistence between runs."""

import os

os.environ.setdefault("KAOS_TESTING", "1")

# Clear persistent CircuitBreaker state
cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".memory", "cache")
cb_file = os.path.join(cache_dir, "circuit_breaker_aether.json")
if os.path.exists(cb_file):
    os.remove(cb_file)
