"""Pytest conftest — CircuitBreaker isolation + vectorstore mock + env setup."""

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


class FakeVectorStore:
    """Fake vector store that returns empty results — no txtai dependency."""

    def hybrid_search(self, text, top_k=5):
        return []

    def embed_strategy(self, sid, ctx, content):
        return f"strategy::{sid}"


@pytest.fixture
def mock_vectorstore(monkeypatch):
    """Mock _get_vectorstore to return a working fake — isolates tests from txtai."""

    def _fake_get_vectorstore():
        return {
            "hybrid_search": FakeVectorStore().hybrid_search,
            "embed_strategy": FakeVectorStore().embed_strategy,
        }

    import strategy_memory

    monkeypatch.setattr(strategy_memory, "_get_vectorstore", _fake_get_vectorstore)
    return FakeVectorStore()
