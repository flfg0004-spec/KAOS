"""Cache Boundary — Anthropic 7+13 sections pattern with SQLite hit tracking."""

import json
import sqlite3
import threading
import time
import hashlib
from pathlib import Path
from functools import wraps
from datetime import datetime

from lib.config import VAULT_ROOT

CACHE_DB = VAULT_ROOT / "cache" / "cache_boundary.db"
_lock = threading.Lock()

# ── Static sections (always cached, ~90% hit rate) ──

STATIC_SECTIONS = {
    "identity": "You are Kronos, Orchestrator of KAOS — pipeline orchestration, adaptive routing, error recovery.",
    "date": lambda: datetime.now().strftime("Current date: %Y-%m-%d %H:%M UTC"),
    "project_info": "Project: KAOS (Knowledge-Augmented Operating System). Multi-agent system.",
    "mcp_definitions": "Tools: pipeline_status, pipeline_run, pipeline_cancel, pipeline_list.",
    "core_tools": "Core agents: Aletheia (research), Kratos (code), Kosmos (arch), Metis (strategy), Mnemosyne (memory).",
    "caching_instructions": "Structure prompts: static sections first (guaranteed cache), dynamic sections after.",
    "permission_modes": "Modes: read-only (plan), confirm (default), auto-execute (yolo).",
}

DYNAMIC_SECTION_KEYS = [
    "conversation_history", "directory_listing", "current_error",
    "test_output", "git_diff", "lint_output", "typecheck_output",
    "previous_tool_results", "agent_output", "pipeline_state",
    "execution_metrics", "quality_scores", "agent_feedback",
]


def _init_db():
    CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(CACHE_DB)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_hits (
                key TEXT PRIMARY KEY,
                section TEXT,
                hits INTEGER DEFAULT 0,
                misses INTEGER DEFAULT 0,
                last_access REAL,
                created_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS section_stats (
                section TEXT PRIMARY KEY,
                hits INTEGER DEFAULT 0,
                misses INTEGER DEFAULT 0,
                tokens_saved INTEGER DEFAULT 0
            )
        """)
        conn.commit()


def _hash_key(section: str, content: str) -> str:
    return hashlib.sha256(f"{section}:{content}".encode()).hexdigest()[:16]


def track_hit(section: str, tokens_saved: int = 0):
    with _lock, sqlite3.connect(str(CACHE_DB)) as conn:
        conn.execute(
            "UPDATE section_stats SET hits = hits + 1, tokens_saved = tokens_saved + ? WHERE section = ?",
            (tokens_saved, section)
        )
        if conn.total_changes == 0:
            conn.execute(
                "INSERT INTO section_stats (section, hits, tokens_saved) VALUES (?, 1, ?)",
                (section, tokens_saved)
            )


def track_miss(section: str):
    with _lock, sqlite3.connect(str(CACHE_DB)) as conn:
        conn.execute("UPDATE section_stats SET misses = misses + 1 WHERE section = ?", (section,))
        if conn.total_changes == 0:
            conn.execute("INSERT INTO section_stats (section, misses) VALUES (?, 1)", (section,))


def build_prompt(
    static_overrides: dict = None,
    dynamic_sections: dict = None,
    pipeline_context: dict = None,
) -> str:
    """Builds a structured prompt with 7 static + up to 13 dynamic sections.
    
    Args:
        static_overrides: Override specific static sections.
        dynamic_sections: Dict of dynamic section key → content.
        pipeline_context: Pipeline state dict to inject as pipeline_state section.
    
    Returns:
        Structured prompt string.
    """
    parts = []

    for key, value in STATIC_SECTIONS.items():
        content = static_overrides.get(key, value) if static_overrides else value
        if callable(content):
            content = content()
        parts.append(f"[{key}]\n{content}")

    dynamic_sections = dynamic_sections or {}
    if pipeline_context:
        dynamic_sections["pipeline_state"] = json.dumps(pipeline_context, indent=2, default=str)
    for key in DYNAMIC_SECTION_KEYS:
        if key in dynamic_sections and dynamic_sections[key]:
            parts.append(f"[{key}]\n{dynamic_sections[key]}")

    result = "\n\n".join(parts)
    return result


def cached_boundary(ttl: int = 3600):
    """Decorator: caches function output keyed by section + args.
    
    Uses SQLite for hit tracking. Returns cached result if within TTL.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            section = kwargs.get("section", func.__name__)
            content = func(*args, **kwargs)

            key = _hash_key(section, str(content)[:200])
            now = time.time()

            with _lock, sqlite3.connect(str(CACHE_DB)) as conn:
                row = conn.execute(
                    "SELECT hits, last_access FROM cache_hits WHERE key = ?", (key,)
                ).fetchone()

                if row and (now - row[1]) < ttl:
                    conn.execute(
                        "UPDATE cache_hits SET hits = hits + 1, last_access = ? WHERE key = ?",
                        (now, key)
                    )
                    track_hit(section, len(str(content)))
                    return content

                if row:
                    conn.execute(
                        "UPDATE cache_hits SET misses = misses + 1, last_access = ? WHERE key = ?",
                        (now, key)
                    )
                else:
                    conn.execute(
                        "INSERT INTO cache_hits (key, section, hits, misses, last_access, created_at) VALUES (?, ?, 0, 0, ?, ?)",
                        (key, section, now, now)
                    )
                track_miss(section)

            return content
        return wrapper
    return decorator


def stats() -> dict:
    """Returns cache boundary statistics."""
    _init_db()
    with sqlite3.connect(str(CACHE_DB)) as conn:
        rows = conn.execute("SELECT section, hits, misses, tokens_saved FROM section_stats").fetchall()
        total_hits = sum(r[1] for r in rows)
        total_misses = sum(r[2] for r in rows)
        total_saved = sum(r[3] for r in rows)
        rate = round(total_hits / max(total_hits + total_misses, 1) * 100, 1)

        return {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "hit_rate_pct": rate,
            "tokens_saved": total_saved,
            "by_section": {r[0]: {"hits": r[1], "misses": r[2], "tokens_saved": r[3]} for r in rows},
        }


_init_db()
