"""Score store — SQLite persistence for validation scores."""
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "cache" / "aletheia_scores.db"
_LOCK = threading.Lock()


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
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
    with _LOCK:
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
    with _LOCK:
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
    with _LOCK:
        conn = _conn()
        row = conn.execute(
            "SELECT AVG(score) FROM scores WHERE timestamp >= datetime('now', ? || ' days')",
            (f"-{days}",),
        ).fetchone()
        conn.close()
    return round(row[0], 3) if row and row[0] else 0.0


def trend(days: int = 30) -> list[dict]:
    """Returns daily average scores for trend analysis."""
    with _LOCK:
        conn = _conn()
        rows = conn.execute(
            "SELECT DATE(timestamp) as day, AVG(score) as avg_score, COUNT(*) as count "
            "FROM scores WHERE timestamp >= datetime('now', ? || ' days') "
            "GROUP BY day ORDER BY day",
            (f"-{days}",),
        ).fetchall()
        conn.close()
    return [{"day": r[0], "avg_score": round(r[1], 3), "count": r[2]} for r in rows]


def latest_scores(limit: int = 10) -> list[dict]:
    """Get the most recent score records."""
    return history(limit=limit)


def get_model_score(model_name: str = "", task_type: str = "", min_samples: int = 3) -> float:
    """Returns average quality score for a model from recent samples.
    
    Args:
        model_name: Filter by model (from metadata JSON).
        task_type: Filter by task type (from metadata JSON).
        min_samples: Minimum samples required. Returns 1.0 (default trust) if insufficient.
    
    Returns:
        float: Average score 0.0-1.0, or 1.0 if insufficient data.
    """
    with _LOCK:
        conn = _conn()
        rows = conn.execute(
            "SELECT score, metadata FROM scores ORDER BY id DESC LIMIT 100"
        ).fetchall()
        conn.close()
    relevant = []
    for score, meta_json in rows:
        try:
            meta = json.loads(meta_json) if meta_json else {}
        except Exception:
            meta = {}
        if model_name and meta.get("model") != model_name:
            continue
        if task_type and meta.get("task_type") != task_type:
            continue
        relevant.append(score)
    if len(relevant) < min_samples:
        return 1.0
    return round(sum(relevant) / len(relevant), 3)
