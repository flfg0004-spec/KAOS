"""kosmos/cache.py — Pipeline cache LRU+TTL thread-safe (KosmosV3 A1+A3)."""

import json
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional


class PipelineCache:
    """Thread-safe LRU cache with TTL and optional persistence (KosmosV3 A3).

    Unifica las funciones de _PIPELINE_CACHE y SemanticCache en una sola clase.
    - LRU eviction via OrderedDict
    - TTL configurable por entrada (default 1800s = 30 min)
    - Persistencia opcional a disco (JSON)
    - Thread-safe con Lock

    maxsize: max entries (default 500)
    ttl_seconds: time-to-live per entry (default 1800 = 30 min)
    persist_path: path JSON file for persistence (default None = no persist)
    """

    def __init__(self, maxsize: int = 500, ttl_seconds: int = 1800, persist_path: str = ""):
        self._maxsize = maxsize
        self._ttl = ttl_seconds
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._persist_path = Path(persist_path) if persist_path else None
        self._hits = 0
        self._misses = 0
        self._load()

    def _load(self) -> None:
        """Load cache from disk if persist_path configured."""
        if not self._persist_path or not self._persist_path.exists():
            return
        try:
            data = json.loads(self._persist_path.read_text(encoding="utf-8"))
            for entry in data.get("entries", []):
                self._cache[entry["key"]] = entry["value"]
                self._timestamps[entry["key"]] = entry.get("timestamp", time.time())
            self._hits = data.get("hits", 0)
            self._misses = data.get("misses", 0)
        except Exception:
            pass

    def _save(self) -> None:
        """Save cache to disk if persist_path configured."""
        if not self._persist_path:
            return
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            now = time.time()
            entries = [
                {"key": k, "value": v, "timestamp": self._timestamps.get(k, now)}
                for k, v in self._cache.items()
            ]
            data = {"entries": entries, "hits": self._hits, "misses": self._misses}
            self._persist_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except Exception:
            pass

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            if time.time() - self._timestamps.get(key, 0) > self._ttl:
                del self._cache[key]
                del self._timestamps[key]
                self._misses += 1
                return None
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            self._timestamps[key] = time.time()
            while len(self._cache) > self._maxsize:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
                del self._timestamps[oldest]
        self._save()

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._hits = 0
            self._misses = 0
        self._save()

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "maxsize": self._maxsize,
                "ttl_seconds": self._ttl,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / max(total, 1) * 100, 1),
                "persist_path": str(self._persist_path) if self._persist_path else None,
            }
