"""Pytest conftest — CircuitBreaker isolation + env setup."""

import os

import pytest

os.environ.setdefault("KAOS_TESTING", "1")

# Clear persistent CircuitBreaker state
cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".memory", "cache")
cb_file = os.path.join(cache_dir, "circuit_breaker_aether.json")
if os.path.exists(cb_file):
    os.remove(cb_file)


@pytest.fixture(autouse=True)
def reset_circuit_breaker():
    from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER

    _ETHER_CIRCUIT_BREAKER.reset()
    yield
    _ETHER_CIRCUIT_BREAKER.reset()
