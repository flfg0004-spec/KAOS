"""Semantic Cache — cache de respuestas LLM basado en similitud semantica.

Arquitectura:
  - Embeddings: usa txtai (BAAI/bge-small-en-v1.5, 384d)
  - Storage: SQLite local en .memory/cache/semantic_cache.db
  - Threshold: 0.92 (configurable) para determinar cache HIT

Flujo:
  LLM call → SemanticCache.get(query) → HIT → respuesta cacheada (0ms, $0)
                                       → MISS → LLM call → guardar en cache

Metricas:
  - Cache hit rate: objetivo >20%
  - Reduccion de tokens: 25-40%
  - Latencia de cache: <5ms
"""

import json
import logging
import sqlite3
import struct
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("semantic_cache")

CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".memory" / "cache"
CACHE_DB = CACHE_DIR / "semantic_cache.db"
SIMILARITY_THRESHOLD = 0.92
MAX_ENTRIES = 10000


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    n1 = sum(a * a for a in v1) ** 0.5
    n2 = sum(b * b for b in v2) ** 0.5
    return dot / (n1 * n2) if n1 * n2 > 0 else 0.0


def _serialize(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _deserialize(data: bytes) -> list[float]:
    return list(struct.unpack(f"{len(data) // 4}f", data))


class SemanticCache:
    def __init__(self, db_path: str = str(CACHE_DB), threshold: float = SIMILARITY_THRESHOLD):
        self.path = db_path
        self.threshold = threshold
        self._embed_model = None
        self._db_init()

    def _db_init(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS semantic_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT UNIQUE,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                embedding BLOB,
                created_at TEXT DEFAULT (datetime('now')),
                hit_count INTEGER DEFAULT 0,
                last_hit TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON semantic_cache(query_hash)")
        conn.commit()
        conn.close()

    def _get_embedding(self, text: str) -> list[float]:
        """Obtiene embedding usando fastembed (compatible con vectorstore.py)."""
        if self._embed_model is None:
            try:
                from fastembed import TextEmbedding
                self._embed_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            except ImportError:
                try:
                    from sentence_transformers import SentenceTransformer
                    self._embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
                except ImportError:
                    return []
        vec = list(self._embed_model.embed([text]))[0]
        if hasattr(vec, 'tolist'):
            return vec.tolist()
        return list(vec)

    def get(self, query: str) -> Optional[str]:
        """Busca en cache una respuesta semanticamente similar.
        
        Primero intenta match exacto (hash), luego semantic si hay modelo.
        """
        query_hash = str(hash(query))
        conn = sqlite3.connect(self.path)

        # Intentar match exacto primero
        exact = conn.execute(
            "SELECT response FROM semantic_cache WHERE query_hash = ?",
            (query_hash,)
        ).fetchone()
        if exact:
            conn.execute(
                "UPDATE semantic_cache SET hit_count = hit_count + 1, last_hit = datetime('now') "
                "WHERE query_hash = ?", (query_hash,))
            conn.commit()
            conn.close()
            logger.debug(f"Exact cache HIT: {query[:50]}...")
            return exact[0]

        # Busqueda semantica si hay modelo disponible
        q_vec = self._get_embedding(query)
        if not q_vec:
            conn.close()
            return None

        rows = conn.execute(
            "SELECT query, response, embedding FROM semantic_cache WHERE embedding IS NOT NULL"
        ).fetchall()
        conn.close()

        best_match = None
        best_score = 0

        for stored_query, stored_response, stored_embedding in rows:
            if not stored_embedding:
                continue
            stored_vec = _deserialize(stored_embedding)
            score = _cosine_similarity(q_vec, stored_vec)
            if score > best_score:
                best_score = score
                best_match = stored_response

        if best_score >= self.threshold and best_match is not None:
            conn = sqlite3.connect(self.path)
            conn.execute(
                "UPDATE semantic_cache SET hit_count = hit_count + 1, last_hit = datetime('now') "
                "WHERE query_hash = ?", (str(hash(query)),))
            conn.commit()
            conn.close()
            logger.debug(f"Semantic cache HIT (score={best_score:.3f}): {query[:50]}...")
            return best_match

        logger.debug(f"Cache MISS (best_score={best_score:.3f}): {query[:50]}...")
        return None

    def set(self, query: str, response: str):
        """Guarda una respuesta en cache."""
        if not response or not query:
            return

        q_hash = str(hash(query))
        q_vec = self._get_embedding(query) if self._embed_model else []

        conn = sqlite3.connect(self.path)
        conn.execute(
            "INSERT OR REPLACE INTO semantic_cache "
            "(query_hash, query, response, embedding, created_at, hit_count) "
            "VALUES (?, ?, ?, ?, datetime('now'), 0)",
            (q_hash, query[:500], response, _serialize(q_vec) if q_vec else b"")
        )
        conn.commit()

        # Purge si excede max_entries
        count = conn.execute("SELECT COUNT(*) FROM semantic_cache").fetchone()[0]
        if count > MAX_ENTRIES:
            conn.execute(
                "DELETE FROM semantic_cache WHERE id IN ("
                "  SELECT id FROM semantic_cache ORDER BY hit_count ASC, last_hit ASC LIMIT ?"
                ")", (count - MAX_ENTRIES,))
            conn.commit()

        conn.close()
        logger.debug(f"Cache SET: {query[:50]}...")

    def stats(self) -> dict:
        """Estadisticas del cache."""
        conn = sqlite3.connect(self.path)
        total = conn.execute("SELECT COUNT(*) FROM semantic_cache").fetchone()[0]
        with_hits = conn.execute(
            "SELECT COUNT(*) FROM semantic_cache WHERE hit_count > 0"
        ).fetchone()[0]
        total_hits = conn.execute(
            "SELECT COALESCE(SUM(hit_count), 0) FROM semantic_cache"
        ).fetchone()[0]
        conn.close()

        return {
            "total_entries": total,
            "entries_with_hits": with_hits,
            "total_hits": total_hits,
            "hit_rate": round(total_hits / (total + total_hits) * 100, 1)
                if (total + total_hits) > 0 else 0,
            "threshold": self.threshold,
            "max_entries": MAX_ENTRIES,
        }

    def clear(self):
        """Limpia todo el cache."""
        conn = sqlite3.connect(self.path)
        conn.execute("DELETE FROM semantic_cache")
        conn.commit()
        conn.close()
        logger.info("Semantic cache cleared")


cache = SemanticCache()
