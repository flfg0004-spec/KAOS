"""sqlite-vec vector store — persistent, queryable, zero-dependency vector DB."""

import json
import sqlite3
import re
import sys
import warnings
from pathlib import Path
from functools import lru_cache
from contextlib import contextmanager

CHUNK_SIZE = 512
CHUNK_OVERLAP = 128
EMBED_DIM = 384

BASE = (Path(__file__).resolve().parent.parent.parent)
KAOS_ROOT = BASE.parent
DB_FILE = KAOS_ROOT / ".memory" / "cache" / "vectors.db"
JSON_FILE = KAOS_ROOT / ".memory" / "cache" / "embeddings.json"


_MODEL_CACHE = None
def _import_model():
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    try:
        from fastembed import TextEmbedding
        _MODEL_CACHE = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        return _MODEL_CACHE
    except ImportError:
        try:
            from sentence_transformers import SentenceTransformer
            _MODEL_CACHE = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            return _MODEL_CACHE
        except ImportError:
            return None

def warmup_model():
    """Pre-load model singleton into cache (call at pipeline init)."""
    return _import_model()


def chunk_text(text: str) -> list[str]:
    """Chunk text by semantic sections (#/## headings) with title prefix."""
    import re
    sections = re.split(r'\n(?=#{1,6} )', text)
    chunks = []
    for section in sections:
        if not section.strip():
            continue
        lines = section.split('\n')
        # Find the actual heading line (first line starting with #)
        heading = ""
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                heading = stripped.lstrip('#').strip()
                break
        # Extract section title from heading
        title = heading if heading else (lines[0].strip() if lines else '')
        # Content = all non-heading lines
        content_lines = [l for l in lines if not l.strip().startswith('#')]
        content = '\n'.join(content_lines).strip()
        
        # Lower threshold for sub-sections; include everything for main headings
        min_content = 5 if heading else 20
        if len(content) < min_content:
            continue
        
        # Prefix each chunk with section title for semantic context
        while len(content) > 0:
            chunk_end = min(CHUNK_SIZE, len(content))
            if chunk_end < len(content):
                last_space = content.rfind(' ', 0, chunk_end)
                if last_space > CHUNK_SIZE // 2:
                    chunk_end = last_space
            chunk = content[:chunk_end].strip()
            if chunk:
                chunks.append(f"[{title}] {chunk}")
            content = content[chunk_end:].strip() if chunk_end < len(content) else ''
    
    return chunks or [text[:CHUNK_SIZE]]


@contextmanager
def _db():
    conn = sqlite3.connect(str(DB_FILE))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.enable_load_extension(True)
    try:
        import sqlite_vec
        sqlite_vec.load(conn)
    except ImportError:
        pass
    finally:
        conn.enable_load_extension(False)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _db() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS vault_chunks ("
                     "  rowid INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "  path TEXT NOT NULL,"
                     "  chunk_text TEXT NOT NULL,"
                     "  chunk_index INTEGER NOT NULL"
                     ")")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_path ON vault_chunks(path)")
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS vault_vectors USING vec0("
            f"  embedding float[{EMBED_DIM}]"
            ")"
        )


def _serialize(vector):
    """Serialize a float32 vector for sqlite-vec."""
    import struct
    return struct.pack(f"{len(vector)}f", *vector)


def _get_md_files():
    md_files = list((KAOS_ROOT / ".memory").rglob("*.md"))
    exclude_dirs = {"cache", "_pending", ".git", "_scripts", "dashboard"}
    return [f for f in md_files if not any(p in exclude_dirs for p in f.parts)]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def build_index(full: bool = False) -> str:
    """Rebuild vector index. If full=False, only adds new pages."""
    model = _import_model()
    if not model:
        return "ERROR: embedding model not installed. Run: pip install fastembed sentence-transformers"
    init_db()

    with _db() as conn:
        if full:
            conn.execute("DELETE FROM vault_vectors")
            conn.execute("DELETE FROM vault_chunks")

        existing = set()
        for row in conn.execute("SELECT DISTINCT path FROM vault_chunks"):
            existing.add(row[0])

        md_files = _get_md_files()
        new_count = 0
        for f in md_files:
            rel = f.relative_to(KAOS_ROOT / ".memory").as_posix()
            if not full and rel in existing:
                continue
            text = _read(f)
            if not text.strip():
                continue
            chunks = chunk_text(text)
            if not chunks:
                continue
            import numpy as np
            vecs = list(model.embed(chunks))
            vecs = [np.array(v) if not isinstance(v, np.ndarray) else v for v in vecs]
            for i, (chunk, vec) in enumerate(zip(chunks, vecs)):
                cur = conn.execute("INSERT INTO vault_chunks(path, chunk_text, chunk_index) VALUES (?, ?, ?)",
                                   (rel, chunk, i))
                rowid = cur.lastrowid
                conn.execute("INSERT INTO vault_vectors(rowid, embedding) VALUES (?, ?)",
                             (rowid, _serialize(vec)))
            new_count += 1

        total = conn.execute("SELECT COUNT(DISTINCT path) FROM vault_chunks").fetchone()[0]
        return f"Vector index built: {new_count} new pages, {total} total."


def query(text: str, top_k: int = 5) -> list[dict]:
    """Semantic search via sqlite-vec KNN."""
    model = _import_model()
    if not model:
        return _bm25_search(text, top_k)

    init_db()
    import numpy as np
    q_vec = list(model.embed([text]))[0]
    if not isinstance(q_vec, np.ndarray):
        q_vec = np.array(q_vec)

    with _db() as conn:
        try:
            results = conn.execute(
                "SELECT c.path, c.chunk_text, v.distance "
                "FROM vault_vectors v "
                "JOIN vault_chunks c ON v.rowid = c.rowid "
                "WHERE v.embedding MATCH ? AND k = ? "
                "ORDER BY v.distance",
                [_serialize(q_vec), top_k]
            ).fetchall()
        except Exception as e:
            print(f"  ⚠️ vectorstore: query failed: {e}")
            return _bm25_search(text, top_k)

    return [
        {"path": r[0], "snippet": r[1][:200], "score": round(1.0 / (1.0 + r[2]), 3)}
        for r in results
    ]


def update(path: str) -> str:
    """Re-embed a single page."""
    model = _import_model()
    if not model:
        return "ERROR: embedding model not installed"
    init_db()

    full_path = KAOS_ROOT / ".memory" / path
    with _db() as conn:
        conn.execute("DELETE FROM vault_vectors WHERE rowid IN ("
                     "  SELECT rowid FROM vault_chunks WHERE path = ?"
                     ")", (path,))
        conn.execute("DELETE FROM vault_chunks WHERE path = ?", (path,))

        if not full_path.exists():
            return f"Removed {path} from index."

        text = _read(full_path)
        if not text.strip():
            return f"Removed {path} (empty)."

        chunks = chunk_text(text)
        if not chunks:
            return f"Skipped {path} (no chunks)."

        import numpy as np
        vecs = list(model.embed(chunks))
        vecs = [np.array(v) if not isinstance(v, np.ndarray) else v for v in vecs]
        for i, (chunk, vec) in enumerate(zip(chunks, vecs)):
            cur = conn.execute("INSERT INTO vault_chunks(path, chunk_text, chunk_index) VALUES (?, ?, ?)",
                               (path, chunk, i))
            rowid = cur.lastrowid
            conn.execute("INSERT INTO vault_vectors(rowid, embedding) VALUES (?, ?)",
                         (rowid, _serialize(vec)))

    return f"Updated {path} ({len(chunks)} chunks)."


def update_many(paths: list[str]) -> str:
    """Re-embed multiple pages."""
    updated = 0
    for path in paths:
        result = update(path)
        if "Updated" in result or "Removed" in result:
            updated += 1
    return f"Updated {updated}/{len(paths)} pages."


def status() -> str:
    init_db()
    with _db() as conn:
        pages = conn.execute("SELECT COUNT(DISTINCT path) FROM vault_chunks").fetchone()[0]
        chunks = conn.execute("SELECT COUNT(*) FROM vault_chunks").fetchone()[0]
        return f"Vector store: {pages} pages, {chunks} chunks."


def get_entries_by_path(pattern: str) -> list[dict]:
    """Get entries matching a path pattern (e.g. wiki/concepts/%)."""
    init_db()
    with _db() as conn:
        rows = conn.execute(
            "SELECT path, chunk_text, chunk_index FROM vault_chunks "
            "WHERE path LIKE ? ORDER BY path, chunk_index",
            (pattern,)
        ).fetchall()
    entries = {}
    for path, chunk_text, chunk_index in rows:
        if path not in entries:
            entries[path] = {"path": path, "chunks": [], "vectors": []}
        entries[path]["chunks"].append(chunk_text)
    return list(entries.values())


def get_all_entries() -> list[dict]:
    """Get all entries (backward compat for quality.py)."""
    init_db()
    with _db() as conn:
        rows = conn.execute("SELECT DISTINCT path FROM vault_chunks").fetchall()
    return [{"path": r[0]} for r in rows]


def concept_vector(path: str) -> list:
    """Get the first embedding vector for a concept (used by synapse)."""
    init_db()
    alternatives = [path]
    if path.startswith("wiki/"):
        alternatives.append(path[5:])
    with _db() as conn:
        for p in alternatives:
            row = conn.execute(
                "SELECT v.embedding FROM vault_vectors v "
                "JOIN vault_chunks c ON v.rowid = c.rowid "
                "WHERE c.path = ? AND c.chunk_index = 0",
                (p,)
            ).fetchone()
            if row:
                import struct
                vec = struct.unpack(f"{EMBED_DIM}f", row[0])
                return list(vec)
    return None


def query_vectors(target_path: str, top_k: int = 3) -> list[dict]:
    """Find similar vectors to a given concept's first chunk (synapse cosine)."""
    candidates = [target_path]
    if target_path.startswith("wiki/"):
        candidates.append(target_path[5:])
    else:
        candidates.append("wiki/" + target_path)

    vec = None
    actual_path = None
    for p in candidates:
        v = concept_vector(p)
        if v is not None:
            vec = v
            actual_path = p
            break
    if vec is None:
        return []

    init_db()
    with _db() as conn:
        try:
            results = conn.execute(
                "SELECT c.path, c.chunk_text, v.distance "
                "FROM vault_vectors v "
                "JOIN vault_chunks c ON v.rowid = c.rowid "
                "WHERE v.embedding MATCH ? AND c.path != ? AND c.chunk_index = 0 AND k = ? "
                "ORDER BY v.distance",
                [_serialize(vec), actual_path, top_k]
            ).fetchall()
        except Exception:
            return []

    return [
        {"path": r[0], "slug": Path(r[0]).stem, "score": round(1.0 / (1.0 + r[2]), 3),
         "snippet": r[1][:200]}
        for r in results
    ]


def _bm25_search(text: str, top_k: int = 5) -> list[dict]:
    """Keyword overlap fallback when sentence-transformers is unavailable."""
    query_tokens = set(text.lower().split())
    if not query_tokens:
        return []
    md_files = _get_md_files()
    scores = []
    for f in md_files:
        content = _read(f)
        tokens = set(content.lower().split())
        overlap = len(query_tokens & tokens)
        if overlap > 0:
            scores.append({
                "path": f.relative_to(KAOS_ROOT / ".memory").as_posix(),
                "snippet": content[:200],
                "score": overlap / len(query_tokens),
            })
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:top_k]


def migrate_from_json() -> str:
    """Migrate existing embeddings.json to sqlite-vec."""
    if not JSON_FILE.exists():
        return "No embeddings.json found to migrate."
    try:
        data = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        return f"Error reading embeddings.json: {e}"

    entries = data.get("entries", [])
    if not entries:
        return "No entries in embeddings.json."

    init_db()
    with _db() as conn:
        count = 0
        for entry in entries:
            path = entry.get("path", "")
            chunks = entry.get("chunks", [])
            vectors = entry.get("vectors", [])
            if not chunks:
                continue
            for i, chunk in enumerate(chunks):
                vec = vectors[i] if i < len(vectors) else None
                cur = conn.execute("INSERT INTO vault_chunks(path, chunk_text, chunk_index) VALUES (?, ?, ?)",
                                   (path, chunk, i))
                rowid = cur.lastrowid
                if vec:
                    conn.execute("INSERT INTO vault_vectors(rowid, embedding) VALUES (?, ?)",
                                 (rowid, _serialize(vec)))
                count += 1

    return f"Migrated {count} chunks from embeddings.json to sqlite-vec."
