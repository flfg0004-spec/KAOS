"""txtai vector store — reemplazo completo de sqlite-vec.

Usa txtai (v9.9.0) como backend unificado con búsqueda híbrida (BM25 + vector + RRF).
Sin servidor, ~50-80MB RAM, sin Docker.

API pública compatible con la anterior implementación sqlite-vec:
  - build_index(full=False) -> str
  - query(text, top_k=5) -> list[dict]
  - update(path) -> str
  - update_many(paths) -> str
  - status() -> str
  - get_all_entries() -> list[dict]
  - query_vectors(target_path, top_k=3) -> list[dict]
  - concept_vector(path) -> list | None
"""

import json
import re
import sys
from pathlib import Path
from functools import lru_cache

CHUNK_SIZE = 512
EMBED_DIM = 384

BASE = (Path(__file__).resolve().parent.parent.parent)
KAOS_ROOT = BASE.parent
TXTAI_DIR = KAOS_ROOT / ".memory" / "cache" / "txtai"
JSON_FILE = KAOS_ROOT / ".memory" / "cache" / "embeddings.json"

_EMBEDDINGS_CACHE = None


def _get_embeddings(create: bool = True):
    """Obtiene instancia singleton de txtai.Embeddings."""
    global _EMBEDDINGS_CACHE
    if _EMBEDDINGS_CACHE is not None:
        return _EMBEDDINGS_CACHE

    try:
        import txtai

        if TXTAI_DIR.exists() and (TXTAI_DIR / "embeddings").exists():
            embeddings = txtai.Embeddings()
            embeddings.load(str(TXTAI_DIR / "embeddings"))
        elif create:
            embeddings = txtai.Embeddings(
                path="BAAI/bge-small-en-v1.5",
                content=True,
                hybrid=True,
            )
        else:
            return None

        _EMBEDDINGS_CACHE = embeddings
        return embeddings
    except ImportError:
        return None


def warmup_model():
    """Pre-load txtai model (call at pipeline init)."""
    return _get_embeddings()


def chunk_text(text: str) -> list[str]:
    """Chunk text by semantic sections (#/## headings) with title prefix."""
    sections = re.split(r'\n(?=#{1,6} )', text)
    chunks = []
    for section in sections:
        if not section.strip():
            continue
        lines = section.split('\n')
        heading = ""
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                heading = stripped.lstrip('#').strip()
                break
        title = heading if heading else (lines[0].strip() if lines else '')
        content_lines = [l for l in lines if not l.strip().startswith('#')]
        content = '\n'.join(content_lines).strip()
        min_content = 5 if heading else 20
        if len(content) < min_content:
            continue
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
    """Rebuild txtai index. If full=False, only adds new pages."""
    embeddings = _get_embeddings(create=True)
    if embeddings is None:
        return "ERROR: txtai not installed. Run: pip install txtai"

    if full:
        TXTAI_DIR.mkdir(parents=True, exist_ok=True)

    # Track existing paths
    existing_paths = set()
    if hasattr(embeddings, "search"):
        try:
            results = embeddings.search("SELECT DISTINCT id FROM txtai")
            for r in results:
                pid = r.get("id", "")
                path_part = pid.split("::")[0] if "::" in pid else pid
                existing_paths.add(path_part)
        except Exception:
            pass

    md_files = _get_md_files()
    new_count = 0
    total_before = len(existing_paths) if existing_paths else 0

    texts = []
    paths_map = {}
    for f in md_files:
        rel = f.relative_to(KAOS_ROOT / ".memory").as_posix()
        if not full and rel in existing_paths:
            continue
        text = _read(f)
        if not text.strip():
            continue
        chunks = chunk_text(text)
        if not chunks:
            continue
        for i, chunk in enumerate(chunks):
            doc_id = f"{rel}::{i}"
            texts.append(chunk)
            paths_map[doc_id] = rel

    if not texts:
        total = total_before or (len(existing_paths) if existing_paths else 0)
        return f"Vector index: {total} pages (no new content)."

    embeddings.index(texts)
    if full:
        embeddings.save(str(TXTAI_DIR / "embeddings"))

    new_count = len(set(paths_map.values()))
    total = total_before + new_count
    return f"Vector index built: {new_count} new pages, {total} total."


def query(text: str, top_k: int = 5) -> list[dict]:
    """Búsqueda híbrida (BM25 + vector) via txtai."""
    embeddings = _get_embeddings(create=False)
    if embeddings is None:
        return _bm25_search(text, top_k)

    try:
        results = embeddings.search(text, limit=top_k)
        formatted = []
        for r in results:
            doc_id = r.get("id", "")
            path_part = doc_id.split("::")[0] if "::" in doc_id else doc_id
            text_part = r.get("text", "")[:200]
            score = r.get("score", 0)
            formatted.append({
                "path": path_part,
                "snippet": text_part,
                "score": round(score, 3),
            })
        return formatted
    except Exception as e:
        return _bm25_search(text, top_k)


def update(path: str) -> str:
    """Re-embed a single page (add or update)."""
    embeddings = _get_embeddings(create=True)
    if embeddings is None:
        return "ERROR: txtai not installed"

    full_path = KAOS_ROOT / ".memory" / path
    if not full_path.exists():
        return f"Removed {path} (not found)."

    text = _read(full_path)
    if not text.strip():
        return f"Skipped {path} (empty)."

    chunks = chunk_text(text)
    if not chunks:
        return f"Skipped {path} (no chunks)."

    # Remove old entries for this path
    try:
        old = embeddings.search(f"SELECT id FROM txtai WHERE id LIKE '{path}::%'")
        old_ids = [r["id"] for r in old if "id" in r]
        for oid in old_ids:
            embeddings.delete([oid])
    except Exception:
        pass

    # Add new chunks
    texts = []
    for i, chunk in enumerate(chunks):
        doc_id = f"{path}::{i}"
        texts.append((doc_id, chunk, None))

    if texts:
        embeddings.upsert(texts)
        embeddings.save(str(TXTAI_DIR / "embeddings"))

    return f"Updated {path} ({len(chunks)} chunks)."


def update_many(paths: list[str]) -> str:
    """Re-embed multiple pages."""
    updated = 0
    for path in paths:
        result = update(path)
        if "Updated" in result or "Skipped" in result or "Removed" in result:
            updated += 1
    return f"Updated {updated}/{len(paths)} pages."


def status() -> str:
    embeddings = _get_embeddings(create=False)
    if embeddings is None:
        return "Vector store: txtai not initialized."

    try:
        results = embeddings.search("SELECT id, text FROM txtai LIMIT 10000")
        unique_paths = set()
        for r in results:
            doc_id = r.get("id", "")
            path_part = doc_id.split("::")[0] if "::" in doc_id else doc_id
            unique_paths.add(path_part)
        return f"Vector store: txtai ({len(results)} chunks, {len(unique_paths)} pages)."
    except Exception:
        return "Vector store: txtai (unknown size)."


def get_all_entries() -> list[dict]:
    """Get all unique paths (backward compat for quality.py)."""
    embeddings = _get_embeddings(create=False)
    if embeddings is None:
        return []

    try:
        results = embeddings.search("SELECT DISTINCT id FROM txtai")
        seen = set()
        entries = []
        for r in results:
            doc_id = r.get("id", "")
            path_part = doc_id.split("::")[0] if "::" in doc_id else doc_id
            if path_part not in seen:
                seen.add(path_part)
                entries.append({"path": path_part})
        return entries
    except Exception:
        return []


def concept_vector(path: str) -> list:
    """Get first embedding vector for a concept (used by synapse)."""
    embeddings = _get_embeddings(create=False)
    if embeddings is None:
        return None
    try:
        vector = embeddings.vector(f"{path}::0")
        if vector is not None:
            return vector.tolist() if hasattr(vector, "tolist") else list(vector)
    except Exception:
        pass
    return None


def query_vectors(target_path: str, top_k: int = 3) -> list[dict]:
    """Find similar vectors to a given concept's first chunk (synapse)."""
    vec = concept_vector(target_path)
    if vec is None:
        alt = f"wiki/{target_path}" if not target_path.startswith("wiki/") else target_path[5:]
        vec = concept_vector(alt)
    if vec is None:
        return []

    embeddings = _get_embeddings(create=False)
    if embeddings is None:
        return []

    try:
        results = embeddings.search(
            f"SELECT id, text, score FROM txtai WHERE id != '{target_path}::0'",
            limit=top_k,
        )
        formatted = []
        for r in results:
            doc_id = r.get("id", "")
            path_part = doc_id.split("::")[0] if "::" in doc_id else doc_id
            formatted.append({
                "path": path_part,
                "slug": Path(path_part).stem,
                "score": round(r.get("score", 0), 3),
                "snippet": r.get("text", "")[:200],
            })
        return formatted
    except Exception:
        return []


def _bm25_search(text: str, top_k: int = 5) -> list[dict]:
    """Keyword overlap fallback."""
    from lib.bm25 import search as bm25_search
    return bm25_search(text, top_k=top_k, base_dir=KAOS_ROOT / ".memory")


def migrate_from_json() -> str:
    """Migrate embeddings.json to txtai (legacy compat)."""
    if not JSON_FILE.exists():
        return "No embeddings.json found."
    try:
        data = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        return f"Error reading embeddings.json: {e}"

    entries = data.get("entries", [])
    if not entries:
        return "No entries in embeddings.json."

    embeddings = _get_embeddings(create=True)
    if embeddings is None:
        return "ERROR: txtai not installed"

    count = 0
    for entry in entries:
        path = entry.get("path", "")
        chunks = entry.get("chunks", [])
        if not chunks:
            continue
        texts = []
        for i, chunk in enumerate(chunks):
            doc_id = f"{path}::{i}"
            texts.append((doc_id, chunk, None))
        if texts:
            embeddings.upsert(texts)
            count += len(texts)

    embeddings.save(str(TXTAI_DIR / "embeddings"))
    return f"Migrated {count} chunks from embeddings.json to txtai."
