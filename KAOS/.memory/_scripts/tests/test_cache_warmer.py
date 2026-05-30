"""Tests for Cache Warmer — persistent LRU with frequency tracking."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_put_and_get():
    from lib.cache_warmer import _persistent_cache, get, put

    _persistent_cache.clear()
    put("test-key", "hello", {"tokens": 10})
    result = get("test-key")
    assert result is not None
    content, usage = result
    assert content == "hello"
    assert usage["tokens"] == 10


def test_get_missing():
    from lib.cache_warmer import get

    result = get("nonexistent-key-xyz")
    assert result is None


def test_ttl_expiry():
    from lib.cache_warmer import _persistent_cache, get, put

    _persistent_cache.clear()
    put("ttl-key", "data", {}, ttl=0)
    result = get("ttl-key")
    assert result is None


def test_lru_eviction():
    from lib.cache_warmer import _persistent_cache, put

    _persistent_cache.clear()
    from lib.cache_warmer import MAX_PERSISTENT

    for i in range(MAX_PERSISTENT + 5):
        put(f"evict-key-{i}", f"data-{i}", {})
    assert len(_persistent_cache) <= MAX_PERSISTENT


def test_top_frequent():
    from lib.cache_warmer import _frequency, put, top_frequent

    _frequency.clear()
    for i in range(10):
        put(f"freq-key-{i}", f"data-{i}", {})
    for _ in range(5):
        from lib.cache_warmer import get

        get("freq-key-0")
        get("freq-key-1")
    top = top_frequent(3)
    assert "freq-key-0" in top or "freq-key-1" in top


def test_stats():
    from lib.cache_warmer import stats

    s = stats()
    assert "entries" in s
    assert "frequent_tracked" in s
    assert "top_keys" in s
    assert "updated" in s
