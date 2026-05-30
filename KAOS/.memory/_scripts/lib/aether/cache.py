"""AetherCache — unified persistent storage for Aether components.

Single base path, atomic writes, size limits, periodic cleanup.
Replaces individual cache logic in: tracker.py, quality_store.py,
circuit.py, observability.py, eval.py
"""

import json
import logging
import os
import threading
from datetime import date, timedelta
from pathlib import Path
from typing import Any

_LOG = logging.getLogger(__name__)

CACHE_BASE = Path(__file__).resolve().parent.parent.parent.parent.parent / ".memory" / "cache"
_KAOS_TESTING = os.environ.get("KAOS_TESTING", "").lower() in ("1", "true")


class AetherCache:
    """Thread-safe persistent cache with atomic writes and size management."""

    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

    def __init__(self, name: str, max_entries: int = None, max_file_size: int = None):
        self.name = name
        self.path = CACHE_BASE / name
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.max_entries = max_entries
        self.max_file_size = max_file_size or self.MAX_FILE_SIZE_BYTES
        self._collections = {}

    def load(self, default: Any = None) -> Any:
        if _KAOS_TESTING:
            return default or {}
        if not self.path.exists():
            return default or {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception as e:
            _LOG.warning("AetherCache[%s]: load failed: %s", self.name, e)
            return default or {}

    def save(self, data: Any):
        if _KAOS_TESTING:
            return
        with self._lock:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(data, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            tmp.replace(self.path)
            self._check_size()

    def append_entry(self, collection: str, entry: dict):
        self._collections.setdefault(collection, []).append(entry)
        coll_path = self.path.with_name(f"{self.name}_{collection}.jsonl")
        with open(coll_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    def load_collection(self, collection: str) -> list:
        coll_path = self.path.with_name(f"{self.name}_{collection}.jsonl")
        if not coll_path.exists():
            return []
        try:
            lines = coll_path.read_text(encoding="utf-8").strip().split("\n")
            return [json.loads(l) for l in lines if l]
        except Exception:
            return []

    def append_jsonl(self, entry: dict, max_lines: int = None):
        with self._lock:
            if max_lines and self.path.exists():
                lines = self.path.read_text(encoding="utf-8").strip().split("\n")
                if len([l for l in lines if l]) >= max_lines:
                    bak = self.path.with_suffix(".jsonl.bak")
                    self.path.replace(bak)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
            self._check_size()

    @staticmethod
    def trim_entries(data: list, max_entries: int, keep_last: int = None) -> list:
        keep = keep_last or max_entries // 2
        if len(data) > max_entries:
            return data[-keep:]
        return data

    def purge_old(self, days: int = 30):
        cutoff = date.today() - timedelta(days=days)
        for f in CACHE_BASE.glob("*"):
            if f.is_file():
                mtime = date.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    f.unlink()
                    _LOG.info("AetherCache: purged old file %s", f.name)

    def _check_size(self):
        if self.path.exists() and self.path.stat().st_size > self.max_file_size:
            _LOG.warning("AetherCache[%s]: %d bytes exceeds limit %d",
                         self.name, self.path.stat().st_size, self.max_file_size)
            self._compress()

    def _compress(self):
        data = self.load()
        if data is not None:
            compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            self.path.write_text(compact, encoding="utf-8")
