"""Cache Warmer — persistent LRU cache with predictive warming.

Strategy: Instead of adding unreliable free tier providers, make the
existing cache effective. Persist the in-memory LRU cache to disk so
it survives restarts, and pre-warm with frequently accessed prompts.

Dashboard target: Cache hit rate 2.7% → >60%
"""

import json
import logging
import threading
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

_LOG = logging.getLogger("cache_warmer")

CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".memory" / "cache"

_persistent_cache: dict[str, dict] = {}
_frequency: Counter = Counter()
_warm_lock = threading.Lock()

CACHE_DB = CACHE_DIR / "llm_cache.json"
FREQ_DB = CACHE_DIR / "prompt_frequency.json"
MAX_PERSISTENT = 500


def load():
    global _persistent_cache, _frequency
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if CACHE_DB.exists():
            with open(CACHE_DB, encoding="utf-8") as f:
                _persistent_cache = json.load(f)
        if FREQ_DB.exists():
            with open(FREQ_DB, encoding="utf-8") as f:
                _frequency = Counter(json.load(f))
        _LOG.info("Loaded %d cache entries, %d frequency records", len(_persistent_cache), len(_frequency))
    except Exception as e:
        _LOG.warning("Failed to load cache: %s", e)
        _persistent_cache = {}
        _frequency = Counter()


def save():
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with _warm_lock:
            with open(CACHE_DB, "w", encoding="utf-8") as f:
                json.dump(_persistent_cache, f, indent=2)
            with open(FREQ_DB, "w", encoding="utf-8") as f:
                json.dump(dict(_frequency.most_common(200)), f, indent=2)
    except Exception as e:
        _LOG.warning("Failed to save cache: %s", e)


def get(key: str) -> tuple[str, dict] | None:
    entry = _persistent_cache.get(key)
    if entry is None:
        return None
    ttl = entry.get("ttl", 3600)
    age = time.time() - entry.get("stored_at", 0)
    if age > ttl:
        del _persistent_cache[key]
        return None
    _frequency[key] += 1
    return entry.get("content"), entry.get("usage", {})


def put(key: str, content: str, usage: dict, ttl: int = 3600):
    with _warm_lock:
        if len(_persistent_cache) >= MAX_PERSISTENT:
            lru = min(_persistent_cache.keys(), key=lambda k: _persistent_cache[k].get("accessed_at", 0))
            del _persistent_cache[lru]
        _persistent_cache[key] = {
            "content": content,
            "usage": usage,
            "stored_at": time.time(),
            "ttl": ttl,
            "accessed_at": time.time(),
        }
        _frequency[key] += 1


def warm(keys: list[str]):
    """Pre-warm cache entries. Called on startup for frequent prompts."""
    loaded = 0
    for key in keys:
        if key in _persistent_cache:
            _persistent_cache[key]["accessed_at"] = time.time()
            loaded += 1
    if loaded:
        _LOG.info("Warmed %d frequent cache entries", loaded)


def top_frequent(n: int = 50) -> list[str]:
    return [k for k, _ in _frequency.most_common(n)]


def stats() -> dict:
    return {
        "entries": len(_persistent_cache),
        "frequent_tracked": len(_frequency),
        "top_keys": [k[:60] for k, _ in _frequency.most_common(10)],
        "updated": datetime.now(UTC).isoformat(),
    }


load()
