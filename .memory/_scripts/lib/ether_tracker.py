"""EtherTracker — token usage and cost tracking for LLM calls."""
import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("ether_tracker")

_LOCK = threading.Lock()
_DB_PATH = Path(__file__).resolve().parent.parent.parent / "cache" / "ether_tracker.db"

_MODEL_COST_MAP = {
    "go-flash": {"input": 0.00014, "output": 0.00028},
    "go-pro": {"input": 0.00174, "output": 0.00348},
    "go-kimi-latest": {"input": 0.00095, "output": 0.00400},
    "deepseek-v4-flash": {"input": 0.00014, "output": 0.00028},
    "deepseek-v4-pro": {"input": 0.00174, "output": 0.00348},
}


def _conn():
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            agent TEXT NOT NULL,
            model TEXT NOT NULL,
            task_type TEXT,
            tokens_in INTEGER DEFAULT 0,
            tokens_out INTEGER DEFAULT 0,
            duration_ms REAL DEFAULT 0,
            success INTEGER DEFAULT 1,
            metadata TEXT
        )
    """)
    conn.commit()
    return conn


def track_call(agent: str, model: str = "", tokens_in: int = 0, tokens_out: int = 0,
               task_type: str = "", duration_ms: float = 0, success: bool = True, metadata: dict = None):
    with _LOCK:
        conn = _conn()
        conn.execute(
            "INSERT INTO calls (timestamp, agent, model, task_type, tokens_in, tokens_out, duration_ms, success, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), agent, model or "unknown", task_type,
             tokens_in, tokens_out, duration_ms, 1 if success else 0,
             json.dumps(metadata or {})),
        )
        conn.commit()
        conn.close()


def _cost_per_1k(model: str) -> tuple:
    rates = _MODEL_COST_MAP.get(model, {"input": 0.0, "output": 0.0})
    return rates["input"], rates["output"]


def report(days: int = 7) -> dict:
    with _LOCK:
        conn = _conn()
        if days > 0:
            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            rows = conn.execute(
                "SELECT agent, model, tokens_in, tokens_out, success FROM calls WHERE timestamp >= ? ORDER BY id",
                (cutoff,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT agent, model, tokens_in, tokens_out, success FROM calls ORDER BY id"
            ).fetchall()
        conn.close()
    total_calls = len(rows)
    total_tokens_in = sum(r[2] for r in rows)
    total_tokens_out = sum(r[3] for r in rows)
    total_cost = 0.0
    per_agent = {}
    for agent, model, tin, tout, success in rows:
        rate_in, rate_out = _cost_per_1k(model)
        cost = (tin / 1000) * rate_in + (tout / 1000) * rate_out
        total_cost += cost
        if agent not in per_agent:
            per_agent[agent] = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0}
        per_agent[agent]["calls"] += 1
        per_agent[agent]["tokens_in"] += tin
        per_agent[agent]["tokens_out"] += tout
        per_agent[agent]["cost_usd"] += cost
    for a in per_agent:
        per_agent[a]["cost_usd"] = round(per_agent[a]["cost_usd"], 6)
    return {
        "total_calls": total_calls,
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "total_cost_usd": round(total_cost, 6),
        "per_agent": per_agent,
    }


def top_models(limit: int = 10) -> list:
    with _LOCK:
        conn = _conn()
        rows = conn.execute(
            "SELECT model, COUNT(*) as calls, SUM(tokens_in) as tin, SUM(tokens_out) as tout "
            "FROM calls GROUP BY model ORDER BY calls DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
    return [{"model": r[0], "calls": r[1], "tokens_in": r[2], "tokens_out": r[3]} for r in rows]


def agent_summary(agent: str, days: int = 7) -> dict:
    with _LOCK:
        conn = _conn()
        if days > 0:
            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            row = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(tokens_in),0), COALESCE(SUM(tokens_out),0), "
                "COALESCE(AVG(duration_ms),0), COALESCE(SUM(CASE WHEN success=0 THEN 1 ELSE 0 END),0) "
                "FROM calls WHERE agent=? AND timestamp>=?", (agent, cutoff)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(tokens_in),0), COALESCE(SUM(tokens_out),0), "
                "COALESCE(AVG(duration_ms),0), COALESCE(SUM(CASE WHEN success=0 THEN 1 ELSE 0 END),0) "
                "FROM calls WHERE agent=?", (agent,)
            ).fetchone()
        conn.close()
    if not row or row[0] == 0:
        return {"calls": 0, "tokens_in": 0, "tokens_out": 0, "avg_duration_ms": 0, "errors": 0}
    return {
        "calls": row[0], "tokens_in": row[1], "tokens_out": row[2],
        "avg_duration_ms": round(row[3], 1), "errors": row[4],
    }
