"""kosmos_memory.py — Sistema de Memoria Arquitectónica para KosmosV2.

Niveles de memoria:
- L0: SQLite FTS5 para búsqueda textual de ADRs y documentación
- L1: txtai embeddings (Fase 2) — búsqueda semántica vectorial
- L2: Architecture Knowledge Graph (futuro, Fase 3)

Dependencias L0: solo sqlite3 (stdlib), pathlib, json, datetime, re
Dependencias L1: txtai (v9.9.0+), vectorstore.py (existente)
"""

import json
import logging
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "cache" / "kosmos" / "fts5.db"
DEFAULT_ADRS_DIR = Path(__file__).resolve().parent.parent.parent / "schema"

# ── Helpers for simple YAML-like frontmatter parsing (no pyyaml dependency) ──

_RE_FM_SEPARATOR = re.compile(r'^---\s*$', re.MULTILINE)
_RE_TAG_LIST = re.compile(r'^\s*-\s*(.+)$', re.MULTILINE)
_RE_TAG_INLINE = re.compile(r'\[([^\]]+)\]')
_RE_STATUS_LINE = re.compile(r'\*\*Estado?\*\*\s*:?\s*(\w[\w\s]*)', re.UNICODE)
_RE_TITLE_H1 = re.compile(r'^#\s+(.+)$', re.MULTILINE)
_RE_DATE = re.compile(r'\*\*Fecha\*\*\s*:?\s*(\d{4}-\d{2}-\d{2})', re.UNICODE)
_RE_TAGS_INLINE = re.compile(r'(?:tags|Tags|Tags):\s*(.+)$', re.MULTILINE)


def _parse_frontmatter(text: str) -> Dict[str, Any]:
    """Extract YAML-like frontmatter from ADR text without pyyaml.

    Handles both:
      ---
      key: value
      tags: [tag1, tag2]
      ---
      ...content...

    and inline metadata like:
      **Estado**: Aceptado
      **Fecha**: 2026-05-29

    Returns:
        dict with keys: title, content, status, tags (list), date, id
    """
    result: Dict[str, Any] = {
        "title": "",
        "content": text,
        "status": "proposed",
        "tags": [],
        "date": "",
        "id": "",
    }

    # Try YAML frontmatter between --- markers
    parts = _RE_FM_SEPARATOR.split(text, maxsplit=2)
    if len(parts) >= 3:
        fm_text = parts[1].strip()
        body = parts[2].strip()
        result["content"] = body

        for line in fm_text.split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip().lower()
            value = value.strip()

            if key == "title":
                result["title"] = value.strip('"').strip("'")
            elif key == "status":
                result["status"] = value.strip('"').strip("'").lower()
            elif key == "date":
                result["date"] = value.strip('"').strip("'")
            elif key == "tags":
                # Support both [tag1, tag2] and YAML list - tag1
                tag_match = _RE_TAG_INLINE.search(value)
                if tag_match:
                    raw = tag_match.group(1)
                    result["tags"] = [t.strip().strip('"').strip("'") for t in raw.split(",") if t.strip()]
                else:
                    # Multi-line YAML list — already consumed in splitted parts
                    # Fallback: parse inline list items
                    list_items = _RE_TAG_LIST.findall(fm_text)
                    if list_items:
                        result["tags"] = [t.strip() for t in list_items]
            elif key == "id":
                result["id"] = value.strip('"').strip("'")
            elif key == "related_adrs":
                tag_match = _RE_TAG_INLINE.search(value)
                if tag_match:
                    raw = tag_match.group(1)
                    result["related_adrs"] = [t.strip() for t in raw.split(",") if t.strip()]
    else:
        body = text

    # If no title from frontmatter, extract from first # heading
    if not result["title"]:
        h1_match = _RE_TITLE_H1.search(body or text)
        if h1_match:
            result["title"] = h1_match.group(1).strip()

    # If no status from frontmatter, look for **Estado** pattern
    if result["status"] == "proposed":
        status_match = _RE_STATUS_LINE.search(text)
        if status_match:
            result["status"] = status_match.group(1).strip().lower()

    # If no date from frontmatter, look for **Fecha** pattern
    if not result["date"]:
        date_match = _RE_DATE.search(text)
        if date_match:
            result["date"] = date_match.group(1).strip()

    # If no tags from frontmatter, look for inline tags
    if not result["tags"]:
        tags_match = _RE_TAGS_INLINE.search(text)
        if tags_match:
            raw = tags_match.group(1)
            # Could be [tag1, tag2] or just comma-separated
            tag_match = _RE_TAG_INLINE.search(raw)
            if tag_match:
                raw_inner = tag_match.group(1)
                result["tags"] = [t.strip() for t in raw_inner.split(",") if t.strip()]

    # Extract ADR id from title if missing
    if not result["id"]:
        id_match = re.search(r'(ADR-\d+)', result["title"] or "")
        if id_match:
            result["id"] = id_match.group(1)

    return result


class ArchitectureMemoryL0:
    """Sistema de Memoria Arquitectónica Nivel 0 basado en SQLite FTS5.

    Proporciona indexación y búsqueda full-text de ADRs (Architecture Decision Records)
    y documentación arquitectónica almacenada en formato Markdown.

    Características:
    - Indexación automática de ADRs desde directorios
    - Búsqueda full-text con ranking por relevancia
    - Filtrado por tags y estado
    - Estadísticas de la base de conocimiento
    - Prevención de duplicados por título
    """

    def __init__(self, db_path: str = "") -> None:
        """Initialize ArchitectureMemoryL0.

        Args:
            db_path: Path to the SQLite database file. If empty, defaults to
                     ``{vault}/cache/kosmos/fts5.db``.
        """
        if not db_path:
            db_path = str(DEFAULT_DB_PATH)
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._initialized = False
        self.initialize_schema()
        logger.info("ArchitectureMemoryL0 initialized at %s", self._db_path)

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create the SQLite connection (lazy init)."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        return self._conn

    def initialize_schema(self) -> None:
        """Create the ADR tables and FTS5 index if they don't exist.

        Schema:
        - ``adrs``: main table with id, title, content, filepath, created,
          modified, tags (JSON), status
        - ``adrs_fts``: FTS5 virtual table indexing title + content + tags
          with content-sync to ``adrs``
        """
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS adrs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                content     TEXT,
                filepath    TEXT UNIQUE,
                created     TEXT,
                modified    TEXT,
                tags        TEXT DEFAULT '[]',
                status      TEXT DEFAULT 'proposed'
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS adrs_fts USING fts5(
                title,
                content,
                tags,
                content='adrs',
                content_rowid='id',
                tokenize='porter unicode61'
            );

            -- Triggers to keep FTS in sync with main table
            CREATE TRIGGER IF NOT EXISTS adrs_ai AFTER INSERT ON adrs BEGIN
                INSERT INTO adrs_fts(rowid, title, content, tags)
                VALUES (new.id, new.title, new.content, new.tags);
            END;

            CREATE TRIGGER IF NOT EXISTS adrs_ad AFTER DELETE ON adrs BEGIN
                INSERT INTO adrs_fts(adrs_fts, rowid, title, content, tags)
                VALUES ('delete', old.id, old.title, old.content, old.tags);
            END;

            CREATE TRIGGER IF NOT EXISTS adrs_au AFTER UPDATE ON adrs BEGIN
                INSERT INTO adrs_fts(adrs_fts, rowid, title, content, tags)
                VALUES ('delete', old.id, old.title, old.content, old.tags);
                INSERT INTO adrs_fts(rowid, title, content, tags)
                VALUES (new.id, new.title, new.content, new.tags);
            END;
        """)
        conn.commit()
        self._initialized = True
        logger.debug("Schema initialized with FTS5 on adrs table")

    def index_adr(self, adr_path: str) -> Dict[str, Any]:
        """Read an ADR markdown file, parse it, and index it in FTS5.

        Args:
            adr_path: Path to the ADR markdown file.

        Returns:
            Dict with metadata: id, title, filepath, status, tags, date.
        """
        path = Path(adr_path)
        if not path.exists():
            logger.warning("ADR file not found: %s", adr_path)
            return {"error": f"File not found: {adr_path}"}

        raw_text = path.read_text(encoding="utf-8", errors="replace")
        parsed = _parse_frontmatter(raw_text)

        title = parsed.get("title", path.stem)
        content = parsed.get("content", raw_text)
        status = parsed.get("status", "proposed")
        tags = parsed.get("tags", [])
        date = parsed.get("date", "")
        tags_json = json.dumps(tags)

        # Get file modification time
        mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        ctime = date or datetime.fromtimestamp(path.stat().st_ctime).strftime("%Y-%m-%d")

        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO adrs (title, content, filepath, created, modified, tags, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (title, content, str(path), ctime, mtime, tags_json, status),
            )
            conn.commit()
            cursor = conn.execute("SELECT id FROM adrs WHERE filepath = ?", (str(path),))
            row = cursor.fetchone()
            adr_id = row["id"] if row else -1
            logger.info("Indexed ADR: %s (id=%d, status=%s)", title, adr_id, status)
            return {
                "id": adr_id,
                "title": title,
                "filepath": str(path),
                "status": status,
                "tags": tags,
                "date": date,
            }
        except sqlite3.IntegrityError as exc:
            logger.warning("Integrity error indexing %s: %s", adr_path, exc)
            return {"error": str(exc), "filepath": adr_path}

    def index_all_adrs(self, adrs_dir: str = "") -> int:
        """Scan a directory for ADR markdown files and index all of them.

        Looks for ``*.md`` files in the given directory and its ``ADRs/``
        subdirectory.

        Args:
            adrs_dir: Directory containing ADR files. If empty, defaults to
                      ``{vault}/schema``.

        Returns:
            Number of ADRs indexed.
        """
        if not adrs_dir:
            adrs_dir = str(DEFAULT_ADRS_DIR)
        base = Path(adrs_dir)
        if not base.exists():
            logger.warning("ADRs directory not found: %s", base)
            return 0

        md_files: List[Path] = []
        md_files.extend(base.glob("*.md"))
        adr_subdir = base / "ADRs"
        if adr_subdir.exists():
            md_files.extend(adr_subdir.glob("*.md"))

        count = 0
        for md_path in sorted(md_files):
            try:
                result = self.index_adr(str(md_path))
                if "error" not in result:
                    count += 1
                else:
                    logger.warning("Skipped %s: %s", md_path, result["error"])
            except Exception as exc:
                logger.error("Failed to index %s: %s", md_path, exc)

        logger.info("Indexed %d/%d ADRs from %s", count, len(md_files), base)
        return count

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search over ADRs using FTS5.

        Supports FTS5 query syntax:
        - Simple terms: ``microservicio``
        - Prefix: ``arquitec*``
        - Phrase: ``\"sistema memoria\"``
        - Boolean: ``adr AND memoria``

        Args:
            query: The search query string.
            limit: Maximum number of results to return (default 10).

        Returns:
            List of dicts with keys: id, title, snippet, score, tags, status.
        """
        if not query or not query.strip():
            return []

        conn = self._get_conn()
        # Sanitize query for FTS5 — escape special characters where needed
        safe_query = query.strip()
        if not safe_query:
            return []

        try:
            # FTS5 with bm25 ranking (lower = better, so negate for intuitive score)
            rows = conn.execute(
                """SELECT a.id, a.title, a.tags, a.status,
                          snippet(adrs_fts, 1, '<mark>', '</mark>', '...', 40) AS snippet,
                          -bm25(adrs_fts) AS score
                   FROM adrs_fts
                   JOIN adrs a ON a.id = adrs_fts.rowid
                   WHERE adrs_fts MATCH ?
                   ORDER BY score DESC
                   LIMIT ?""",
                (safe_query, limit),
            ).fetchall()
        except sqlite3.OperationalError as exc:
            logger.warning("FTS5 query error for '%s': %s", safe_query, exc)
            # Fallback: LIKE search
            like_pattern = f"%{safe_query}%"
            rows = conn.execute(
                """SELECT id, title, tags, status, content AS snippet, 0.0 AS score
                   FROM adrs
                   WHERE title LIKE ? OR content LIKE ?
                   LIMIT ?""",
                (like_pattern, like_pattern, limit),
            ).fetchall()

        results = []
        for row in rows:
            tags_raw = row["tags"] or "[]"
            try:
                tags_list = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
            except (json.JSONDecodeError, TypeError):
                tags_list = []

            results.append({
                "id": row["id"],
                "title": row["title"],
                "snippet": row["snippet"] if row["snippet"] else "",
                "search_score": round(float(row["score"]), 2) if row["score"] else 0.0,
                "tags": tags_list,
                "status": row["status"],
            })

        return results

    def search_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Filter ADRs by tag (case-insensitive substring match).

        Args:
            tag: Tag to search for (e.g. ``memoria``, ``refactor``).

        Returns:
            List of matching ADR dicts.
        """
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT id, title, tags, status, created, modified
               FROM adrs
               WHERE tags LIKE ?""",
            (f"%{tag}%",),
        ).fetchall()

        results = []
        for row in rows:
            tags_raw = row["tags"] or "[]"
            try:
                tags_list = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
            except (json.JSONDecodeError, TypeError):
                tags_list = []

            if any(tag.lower() in t.lower() for t in tags_list):
                results.append({
                    "id": row["id"],
                    "title": row["title"],
                    "tags": tags_list,
                    "status": row["status"],
                    "created": row["created"],
                    "modified": row["modified"],
                })

        return results

    def search_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Filter ADRs by status.

        Args:
            status: Status filter (``proposed``, ``accepted``, ``deprecated``,
                    ``implementado``, etc.). Case-insensitive.

        Returns:
            List of matching ADR dicts.
        """
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT id, title, tags, status, created, modified
               FROM adrs
               WHERE LOWER(status) = LOWER(?)""",
            (status.strip(),),
        ).fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "tags": json.loads(row["tags"]) if isinstance(row["tags"], str) else row["tags"],
                "status": row["status"],
                "created": row["created"],
                "modified": row["modified"],
            }
            for row in rows
        ]

    def get_adr(self, adr_id: int) -> Dict[str, Any]:
        """Get a full ADR record by its database ID.

        Args:
            adr_id: The database ID of the ADR.

        Returns:
            Dict with all ADR fields, or empty dict if not found.
        """
        conn = self._get_conn()
        row = conn.execute(
            """SELECT id, title, content, filepath, created, modified, tags, status
               FROM adrs WHERE id = ?""",
            (adr_id,),
        ).fetchone()

        if row is None:
            return {}

        tags_raw = row["tags"] or "[]"
        try:
            tags_list = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
        except (json.JSONDecodeError, TypeError):
            tags_list = []

        return {
            "id": row["id"],
            "title": row["title"],
            "content": row["content"],
            "filepath": row["filepath"],
            "created": row["created"],
            "modified": row["modified"],
            "tags": tags_list,
            "status": row["status"],
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about the ADR knowledge base.

        Returns:
            Dict with keys: total_adrs, por_status, por_tag, last_updated,
            last_adrs.
        """
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) AS cnt FROM adrs").fetchone()["cnt"]

        # Per-status counts
        status_rows = conn.execute(
            "SELECT LOWER(status) AS st, COUNT(*) AS cnt FROM adrs GROUP BY st"
        ).fetchall()
        por_status: Dict[str, int] = {r["st"]: r["cnt"] for r in status_rows}

        # Per-tag counts (parse JSON tags)
        all_tags_rows = conn.execute("SELECT tags FROM adrs").fetchall()
        por_tag: Dict[str, int] = {}
        for row in all_tags_rows:
            try:
                tags = json.loads(row["tags"]) if isinstance(row["tags"], str) else row["tags"]
                for tag in tags:
                    tag = tag.strip().lower()
                    por_tag[tag] = por_tag.get(tag, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass

        # Last 5 ADRs
        last_rows = conn.execute(
            "SELECT id, title, status, modified FROM adrs ORDER BY modified DESC LIMIT 5"
        ).fetchall()
        last_adrs = [
            {
                "id": r["id"],
                "title": r["title"],
                "status": r["status"],
                "modified": r["modified"],
            }
            for r in last_rows
        ]

        return {
            "total_adrs": total,
            "por_status": por_status,
            "por_tag": dict(sorted(por_tag.items(), key=lambda x: -x[1])),
            "last_adrs": last_adrs,
            "db_path": str(self._db_path),
        }

    def adr_exists(self, title: str) -> bool:
        """Check if an ADR with the given title already exists.

        Performs a case-insensitive comparison.

        Args:
            title: The ADR title to check.

        Returns:
            True if an ADR with this title exists.
        """
        conn = self._get_conn()
        row = conn.execute(
            "SELECT 1 FROM adrs WHERE LOWER(title) = LOWER(?) LIMIT 1",
            (title.strip(),),
        ).fetchone()
        return row is not None

    def get_related_adrs(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find semantically related ADRs using FTS5 rank-based search.

        This is a simple relevance search using FTS5's BM25 ranking. For proper
        semantic search, use L1 (txtai embeddings, coming in Fase 2).

        Args:
            query: Search query describing the topic.
            limit: Maximum results (default 5).

        Returns:
            List of related ADR dicts with title, snippet, score, tags, status.
        """
        return self.search(query, limit=limit)

    def close(self) -> None:
        """Close the database connection explicitly."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.debug("Database connection closed")

    def __enter__(self) -> "ArchitectureMemoryL0":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


# ═══════════════════════════════════════════════════════════════
# L1: txtai Vector Store (Fase 2)
# ═══════════════════════════════════════════════════════════════


class ArchitectureMemoryL1:
    """Sistema de Memoria Arquitectónica Nivel 1 basado en txtai embeddings.

    Proporciona búsqueda semántica vectorial sobre ADRs usando el modelo
    BAAI/bge-small-en-v1.5 (384-dim). Integra con el módulo ``vectorstore.py``
    existente para reutilizar su índice híbrido (BM25 + vector + RRF).

    Características:
    - Búsqueda semántica por similitud de embeddings
    - Indexación automática de ADRs desde L0
    - Encontrar ADRs relacionados semánticamente
    - Re-indexación consolidada bajo demanda

    Uso:
        memory_l0 = ArchitectureMemoryL0()
        memory_l1 = ArchitectureMemoryL1(memory_l0=memory_l0)
        memory_l1.warmup()
        count = memory_l1.index_adrs_to_txtai()
        results = memory_l1.semantic_search("memoria vectorial", top_k=5)
    """

    def __init__(self, memory_l0: Any = None) -> None:
        """Initialize ArchitectureMemoryL1.

        Args:
            memory_l0: Optional ArchitectureMemoryL0 instance to use as data
                       source for indexing. If not provided, creates a new one.
        """
        self._memory_l0 = memory_l0
        self._warmed_up = False
        self._last_index_count = 0
        self._index_timestamp = ""

        logger.info("ArchitectureMemoryL1 initialized (memory_l0=%s)",
                     "provided" if memory_l0 is not None else "None")

    def warmup(self) -> bool:
        """Pre-load the txtai embedding model.

        Calls ``vectorstore.warmup_model()`` to ensure the model is loaded
        into memory before first query.

        Returns:
            True if model was warmed up successfully, False otherwise.
        """
        try:
            from lib.vectorstore import warmup_model as _warmup

            result = _warmup()
            self._warmed_up = result is not None
            if self._warmed_up:
                logger.info("txtai model warmed up successfully")
            else:
                logger.warning("txtai model warmup returned None")
            return self._warmed_up
        except ImportError as exc:
            logger.warning("txtai not available for warmup: %s", exc)
            self._warmed_up = False
            return False
        except Exception as exc:
            logger.warning("txtai warmup failed: %s", exc)
            self._warmed_up = False
            return False

    def index_adrs_to_txtai(self) -> int:
        """Index all ADRs from L0 into the txtai vector store.

        Reads all ADRs from the L0 SQLite database, chunks them, and indexes
        them into txtai using ``vectorstore.update()`` for incremental updates
        or ``vectorstore.build_index()`` for a full rebuild.

        Returns:
            Number of ADR pages indexed.
        """
        try:
            # Ensure L0 is available
            if self._memory_l0 is None:
                from lib.kosmos_memory import ArchitectureMemoryL0
                self._memory_l0 = ArchitectureMemoryL0()

            # Get all ADR filepaths from L0
            stats = self._memory_l0.get_stats()
            total_adrs = stats.get("total_adrs", 0)

            # Use vectorstore.build_index to index all markdown files
            from lib.vectorstore import build_index, status as vs_status

            # Build index incrementally (full=False adds only new content)
            result = build_index(full=False)

            # Get updated count from status
            status_str = vs_status()
            self._last_index_count = total_adrs
            self._index_timestamp = datetime.now().isoformat()

            logger.info("Indexed ADRs to txtai: %s", result)
            return total_adrs

        except ImportError as exc:
            logger.warning("txtai not available for indexing: %s", exc)
            return 0
        except Exception as exc:
            logger.error("Failed to index ADRs to txtai: %s", exc)
            return 0

    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search over indexed ADRs.

        Uses txtai's hybrid search (BM25 + vector + RRF) via the existing
        ``vectorstore.query()`` function.

        Args:
            query: Natural language query string.
            top_k: Number of results to return (default 5).

        Returns:
            List of dicts with keys: path, snippet, score, title (inferred).
        """
        try:
            from lib.vectorstore import query as _vs_query

            if not query or not query.strip():
                return []

            raw_results = _vs_query(query, top_k=top_k)

            results = []
            for r in raw_results:
                # Try to infer title from path
                path_str = r.get("path", "")
                title = Path(path_str).stem.replace("-", " ").replace("_", " ").title() if path_str else ""

                results.append({
                    "path": path_str,
                    "title": title,
                    "snippet": r.get("snippet", ""),
                    "score": r.get("score", 0.0),
                })

            logger.debug("Semantic search for '%s': %d results", query[:40], len(results))
            return results

        except ImportError as exc:
            logger.warning("txtai not available for search: %s", exc)
            return []
        except Exception as exc:
            logger.error("Semantic search failed: %s", exc)
            return []

    def find_related_adrs(self, adr_id: int, top_k: int = 3) -> List[Dict[str, Any]]:
        """Find ADRs semantically similar to a given ADR.

        Uses the ADR's content from L0 to search the txtai vector store
        for semantically similar documents.

        Args:
            adr_id: Database ID of the ADR in L0.
            top_k: Number of related ADRs to return (default 3).

        Returns:
            List of dicts with keys: path, title, snippet, score.
        """
        try:
            if self._memory_l0 is None:
                from lib.kosmos_memory import ArchitectureMemoryL0
                self._memory_l0 = ArchitectureMemoryL0()

            # Get the source ADR content from L0
            adr = self._memory_l0.get_adr(adr_id)
            if not adr:
                logger.warning("ADR #%d not found in L0", adr_id)
                return []

            # Use the ADR title + a snippet as the query
            query = f"{adr.get('title', '')} {adr.get('content', '')[:300]}"
            return self.semantic_search(query, top_k=top_k)

        except Exception as exc:
            logger.error("find_related_adrs failed for ADR #%d: %s", adr_id, exc)
            return []

    def consolidate(self) -> str:
        """Force a full re-index of all ADRs into txtai.

        Calls ``vectorstore.build_index(full=True)`` to rebuild the entire
        vector index from scratch.

        Returns:
            Status string from the build operation.
        """
        try:
            from lib.vectorstore import build_index

            result = build_index(full=True)

            # Update L0 index if needed
            if self._memory_l0 is not None:
                try:
                    self._memory_l0.index_all_adrs()
                except Exception as exc:
                    logger.warning("L0 re-index during consolidation failed: %s", exc)

            self._index_timestamp = datetime.now().isoformat()
            logger.info("Consolidated txtai index: %s", result)
            return result

        except ImportError as exc:
            logger.warning("txtai not available for consolidation: %s", exc)
            return "ERROR: txtai not available"
        except Exception as exc:
            logger.error("Consolidation failed: %s", exc)
            return f"ERROR: {exc}"

    def status(self) -> Dict[str, Any]:
        """Get the current status of the L1 memory index.

        Returns:
            Dict con keys: available (bool), chunks (int), pages (int),
            model (str), dimension (int), last_index (str), warmed_up (bool).
        """
        status: Dict[str, Any] = {
            "available": False,
            "chunks": 0,
            "pages": 0,
            "model": "BAAI/bge-small-en-v1.5",
            "dimension": 384,
            "last_index": self._index_timestamp,
            "warmed_up": self._warmed_up,
        }

        try:
            from lib.vectorstore import status as vs_status

            status_str = vs_status()
            # Parse status string like "Vector store: txtai (142 chunks, 38 pages)."
            parse_match = re.search(r'(\d+)\s+chunks', status_str)
            if parse_match:
                status["chunks"] = int(parse_match.group(1))
            pages_match = re.search(r'(\d+)\s+pages', status_str)
            if pages_match:
                status["pages"] = int(pages_match.group(1))

            status["available"] = "txtai" in status_str and "not initialized" not in status_str
            status["raw_status"] = status_str

        except ImportError:
            status["raw_status"] = "txtai not installed"
        except Exception as exc:
            status["raw_status"] = f"Error: {exc}"

        return status

    def close(self) -> None:
        """Clean up resources. Currently a no-op for L1."""
        logger.debug("ArchitectureMemoryL1 closed")


# ── Standalone helpers ──

def index_adrs_sync(adrs_dir: str = "", db_path: str = "") -> int:
    """Convenience function: initialize memory, scan and index all ADRs.

    Args:
        adrs_dir: Directory containing ADR files.
        db_path: SQLite database path.

    Returns:
        Number of ADRs indexed.
    """
    memory = ArchitectureMemoryL0(db_path=db_path)
    try:
        return memory.index_all_adrs(adrs_dir=adrs_dir)
    finally:
        memory.close()


# ── Quick test ──
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    memory = ArchitectureMemoryL0()
    count = memory.index_all_adrs()
    print(f"Indexed {count} ADRs")

    stats = memory.get_stats()
    print(f"Total ADRs: {stats['total_adrs']}")
    print(f"Por status: {stats['por_status']}")
    print(f"Top tags: {dict(list(stats['por_tag'].items())[:5])}")

    # Test search
    results = memory.search("memoria arquitectura")
    print(f"\nSearch 'memoria arquitectura': {len(results)} results")
    for r in results[:3]:
        print(f"  - {r['title']} (score={r['search_score']}, status={r['status']})")

    # Test get_adr
    if results:
        adr = memory.get_adr(results[0]["id"])
        print(f"\nFull ADR #{adr['id']}: {adr['title'][:60]}...")

    memory.close()
    print("\nArchitectureMemoryL0: OK")
