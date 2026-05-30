"""Aletheia Score Store — persistencia de scores de validación.

Guarda resultados de validate_aletheia_output en SQLite para tracking histórico.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "cache" / "aletheia_scores.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            topic TEXT,
            score REAL NOT NULL,
            valid INTEGER NOT NULL,
            sections_found TEXT,
            warnings TEXT,
            metadata TEXT
        )
    """)
    conn.commit()
    return conn


def save(topic: str, score: float, valid: bool, sections_found: list[str], warnings: list[str], metadata: dict = None):
    conn = _conn()
    conn.execute(
        "INSERT INTO scores (timestamp, topic, score, valid, sections_found, warnings, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            datetime.now().isoformat(),
            topic[:200],
            score,
            1 if valid else 0,
            json.dumps(sections_found),
            json.dumps(warnings),
            json.dumps(metadata or {}),
        ),
    )
    conn.commit()
    conn.close()


def history(limit: int = 20) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        "SELECT timestamp, topic, score, valid, warnings FROM scores ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [
        {
            "timestamp": r[0],
            "topic": r[1],
            "score": r[2],
            "valid": bool(r[3]),
            "warnings": json.loads(r[4]) if r[4] else [],
        }
        for r in rows
    ]


def average(days: int = 7) -> float:
    conn = _conn()
    cutoff = datetime.now().isoformat()
    row = conn.execute(
        "SELECT AVG(score) FROM scores WHERE timestamp >= datetime('now', ? || ' days')",
        (f"-{days}",),
    ).fetchone()
    conn.close()
    return round(row[0], 3) if row and row[0] else 0.0


def trend(days: int = 30) -> list[dict]:
    """Returns daily average scores for trend analysis."""
    conn = _conn()
    rows = conn.execute(
        "SELECT DATE(timestamp) as day, AVG(score) as avg_score, COUNT(*) as count "
        "FROM scores WHERE timestamp >= datetime('now', ? || ' days') "
        "GROUP BY day ORDER BY day",
        (f"-{days}",),
    ).fetchall()
    conn.close()
    return [{"day": r[0], "avg_score": round(r[1], 3), "count": r[2]} for r in rows]
