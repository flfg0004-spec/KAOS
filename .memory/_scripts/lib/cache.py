"""Persistent cross-session cache with LRU eviction, mtime invalidation, and semantic cache."""
import json, time, hashlib
from pathlib import Path
from datetime import datetime

from lib.config import VAULT_ROOT, CACHE_CACHE_MAX_ENTRIES, CACHE_CACHE_DEFAULT_TTL

METADATA_FILE = VAULT_ROOT / "cache" / "metadata.json"
PAGES_DIR = VAULT_ROOT / "cache" / "pages"
SEMANTIC_CACHE_FILE = VAULT_ROOT / "cache" / "semantic_cache.json"

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

_SENTENCE_MODEL = None

def _get_sentence_model():
    global _SENTENCE_MODEL
    if _SENTENCE_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _SENTENCE_MODEL = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        except Exception:
            return None
    return _SENTENCE_MODEL


class SemanticCache:
    """LRU cache con similitud coseno para queries semánticamente cercanas."""
    
    def __init__(self, maxsize: int = 100, threshold: float = 0.92):
        self.maxsize = maxsize
        self.threshold = threshold
        self._cache = self._load()
    
    def _load(self) -> list:
        if SEMANTIC_CACHE_FILE.exists():
            try:
                return json.loads(SEMANTIC_CACHE_FILE.read_text())
            except Exception:
                pass
        return []
    
    def _save(self):
        SEMANTIC_CACHE_FILE.write_text(json.dumps(self._cache[-self.maxsize:], indent=2))
    
    def _get_vec(self, text: str):
        if not HAS_NUMPY:
            return None
        model = _get_sentence_model()
        if model is None:
            return None
        try:
            return model.encode([text])[0]
        except Exception:
            return None
    
    def get(self, query: str):
        query_vec = self._get_vec(query)
        if query_vec is None:
            return None
        for entry in self._cache:
            cached_vec = np.array(entry.get("vector", []))
            if len(cached_vec) == 0:
                continue
            sim = np.dot(query_vec, cached_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(cached_vec))
            if sim > self.threshold:
                entry["hits"] = entry.get("hits", 0) + 1
                self._save()
                return entry["result"]
        return None
    
    def put(self, query: str, result: list):
        query_vec = self._get_vec(query)
        if query_vec is None:
            return
        entry = {
            "query": query,
            "vector": query_vec.tolist(),
            "result": result,
            "hits": 0,
            "timestamp": datetime.now().isoformat()
        }
        self._cache.append(entry)
        if len(self._cache) > self.maxsize:
            self._cache = self._cache[-self.maxsize:]
        self._save()
    
    def stats(self) -> str:
        total = len(self._cache)
        hits = sum(e.get("hits", 0) for e in self._cache)
        return f"Semantic cache: {total} entries, {hits} total hits"


_semantic_cache = None

def get_semantic_cache() -> SemanticCache:
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    return _semantic_cache


def _default_meta() -> dict:
    return {
        "version": 2,
        "lastBuild": datetime.now().isoformat(),
        "maxEntries": CACHE_MAX_ENTRIES,
        "entries": [],
    }


def _load() -> dict:
    if METADATA_FILE.exists():
        try:
            return json.loads(METADATA_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ⚠️ cache: metadata load error: {e}")
    return _default_meta()


def _save(meta: dict) -> None:
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    METADATA_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def get(path: str) -> str | None:
    meta = _load()
    entry = next((e for e in meta["entries"] if e["path"] == path), None)
    if not entry:
        return None

    full = VAULT_ROOT / path
    current_mtime = datetime.fromtimestamp(full.stat().st_mtime).isoformat() if full.exists() else None

    if entry.get("mtime") != current_mtime:
        return None

    age = time.time() - datetime.fromisoformat(entry["lastAccess"]).timestamp()
    if age > entry.get("ttl", CACHE_DEFAULT_TTL):
        return None

    cached = PAGES_DIR / f"{path.replace('/', '_')}.txt"
    if cached.exists():
        entry["hits"] = entry.get("hits", 0) + 1
        entry["lastAccess"] = datetime.now().isoformat()
        _save(meta)
        return cached.read_text(encoding="utf-8")
    return None


def put(path: str, content: str, ttl: int = CACHE_DEFAULT_TTL) -> None:
    meta = _load()
    meta["entries"] = [e for e in meta["entries"] if e["path"] != path]

    full = VAULT_ROOT / path
    mtime = datetime.fromtimestamp(full.stat().st_mtime).isoformat() if full.exists() else datetime.now().isoformat()

    meta["entries"].insert(0, {
        "path": path,
        "mtime": mtime,
        "lastAccess": datetime.now().isoformat(),
        "hits": 0,
        "ttl": ttl,
    })

    if len(meta["entries"]) > CACHE_MAX_ENTRIES:
        meta["entries"] = sorted(meta["entries"], key=lambda e: (e.get("hits", 0), e["lastAccess"]))
        meta["entries"] = meta["entries"][:CACHE_MAX_ENTRIES]

    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = PAGES_DIR / f"{path.replace('/', '_')}.txt"
    cache_file.write_text(content, encoding="utf-8")

    _save(meta)


def evict(path: str | None = None) -> str:
    meta = _load()
    if path:
        meta["entries"] = [e for e in meta["entries"] if e["path"] != path]
        cache_file = PAGES_DIR / f"{path.replace('/', '_')}.txt"
        if cache_file.exists():
            cache_file.unlink()
        msg = f"Evicted {path}"
    else:
        meta["entries"] = []
        for f in PAGES_DIR.glob("*.txt"):
            f.unlink()
        msg = "Evicted all entries"
    _save(meta)
    return msg


def stats() -> str:
    meta = _load()
    entries = meta.get("entries", [])
    total_hits = sum(e.get("hits", 0) for e in entries)
    lines = [
        f"Cache entries: {len(entries)}/{meta.get('maxEntries', CACHE_MAX_ENTRIES)}",
        f"Total hits: {total_hits}",
    ]
    for e in entries[:10]:
        lines.append(f"  {e['path']} — hits={e.get('hits',0)} ttl={e.get('ttl', CACHE_DEFAULT_TTL)}s")
    if len(entries) > 10:
        lines.append(f"  ... and {len(entries) - 10} more")
    return "\n".join(lines)
