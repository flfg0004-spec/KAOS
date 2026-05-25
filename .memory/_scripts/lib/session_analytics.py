"""Session Analytics — read opencode.db, correlate with pipelines, track user feedback.

Data sources:
  - opencode.db (SQLite): session, message, part tables with JSON token/agent data
  - _pipeline/context.json: cross-agent memory
  - _pipeline/pipeline-durations.json: pipeline completion records
  - cache/feedback.json: user ratings per session
"""
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

from lib.config import VAULT_ROOT

CACHE_DIR = VAULT_ROOT / "cache"
FEEDBACK_PATH = CACHE_DIR / "feedback.json"
ANALYTICS_PATH = CACHE_DIR / "session-analytics.json"


# ── opencode.db location (platform-aware) ─────────────────────────

def find_opencode_db() -> Path | None:
    candidates = []
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", ""))
        if base.exists():
            candidates.append(base / "opencode" / "opencode.db")
        candidates.append(Path.home() / ".local/share/opencode/opencode.db")
    elif sys.platform == "darwin":
        candidates.append(Path.home() / "Library/Application Support/opencode/opencode.db")
    else:
        candidates.append(Path.home() / ".local/share/opencode/opencode.db")
    for p in candidates:
        if p.exists():
            return p.resolve()
    return None


# ── opencode.db queries ───────────────────────────────────────────

def open_connection(db_path: Path | None = None) -> sqlite3.Connection | None:
    path = db_path or find_opencode_db()
    if not path:
        return None
    try:
        conn = sqlite3.connect(str(path), timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def get_recent_sessions(days: int = 7, limit: int = 20) -> list[dict]:
    """Get recent sessions with message counts from opencode.db."""
    conn = open_connection()
    if not conn:
        return []
    cutoff = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    try:
        cur = conn.execute("""
            SELECT s.id, s.title, s.project_id,
                   s.time_created / 1000 as created_ts,
                   s.time_updated / 1000 as updated_ts,
                   (SELECT COUNT(*) FROM message m WHERE m.session_id = s.id) as msg_count
            FROM session s
            WHERE s.time_created > ?
            ORDER BY s.time_updated DESC
            LIMIT ?
        """, (cutoff, limit))
        rows = cur.fetchall()
        sessions = []
        for r in rows:
            sessions.append({
                "id": r["id"],
                "title": r["title"],
                "project_id": r["project_id"],
                "created": datetime.fromtimestamp(r["created_ts"]).isoformat() if r["created_ts"] else None,
                "updated": datetime.fromtimestamp(r["updated_ts"]).isoformat() if r["updated_ts"] else None,
                "message_count": r["msg_count"],
                "duration_min": None,
            })
        # Compute duration for sessions that have both timestamps
        for s in sessions:
            if s["created"] and s["updated"]:
                try:
                    c = datetime.fromisoformat(s["created"])
                    u = datetime.fromisoformat(s["updated"])
                    s["duration_min"] = round((u - c).total_seconds() / 60, 1)
                except Exception:
                    pass
        return sessions
    except Exception:
        return []
    finally:
        conn.close()


def get_tokens_per_agent(days: int = 7) -> list[dict]:
    """Get token usage per agent from step-finish parts."""
    conn = open_connection()
    if not conn:
        return []
    cutoff = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    try:
        cur = conn.execute("""
            SELECT
                json_extract(m.data, '$.agent') as agent,
                json_extract(m.data, '$.modelID') as model,
                COUNT(*) as llm_calls,
                COALESCE(SUM(json_extract(p.data, '$.tokens.input')), 0) as input_tokens,
                COALESCE(SUM(json_extract(p.data, '$.tokens.output')), 0) as output_tokens,
                COALESCE(SUM(json_extract(p.data, '$.tokens.total')), 0) as total_tokens,
                COALESCE(SUM(json_extract(p.data, '$.cost')), 0) as total_cost
            FROM message m
            JOIN part p ON p.message_id = m.id
            JOIN session s ON m.session_id = s.id
            WHERE s.time_created > ?
              AND json_extract(p.data, '$.type') = 'step-finish'
              AND json_extract(m.data, '$.agent') IS NOT NULL
            GROUP BY json_extract(m.data, '$.agent')
            ORDER BY total_tokens DESC
        """, (cutoff,))
        return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


# ── User feedback ─────────────────────────────────────────────────

def save_feedback(agent: str, session_id: str, rating: int, comment: str = "") -> bool:
    """Save user feedback for an agent session.
    
    Args:
        agent: Agent name (aletheia, kosmos, etc.)
        session_id: Session identifier
        rating: 1-5 rating
        comment: Optional text feedback
    
    Returns:
        True if saved successfully
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data = {"entries": []}
    if FEEDBACK_PATH.exists():
        try:
            data = json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    data["entries"].append({
        "timestamp": datetime.now().isoformat(),
        "agent": agent,
        "session_id": session_id,
        "rating": rating,
        "comment": comment,
    })
    data["entries"] = data["entries"][-500:]
    FEEDBACK_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def get_feedback_summary() -> dict:
    """Get aggregated feedback stats."""
    if not FEEDBACK_PATH.exists():
        return {"total": 0, "avg_rating": 0, "per_agent": {}}
    try:
        data = json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
        entries = data.get("entries", [])
        if not entries:
            return {"total": 0, "avg_rating": 0, "per_agent": {}}
        per_agent = {}
        total_rating = 0
        for e in entries:
            agent = e.get("agent", "unknown")
            rating = e.get("rating", 0)
            if agent not in per_agent:
                per_agent[agent] = {"count": 0, "total_rating": 0}
            per_agent[agent]["count"] += 1
            per_agent[agent]["total_rating"] += rating
            total_rating += rating
        for a in per_agent:
            per_agent[a]["avg"] = round(per_agent[a]["total_rating"] / per_agent[a]["count"], 1)
        return {
            "total": len(entries),
            "avg_rating": round(total_rating / len(entries), 1),
            "per_agent": per_agent,
        }
    except Exception:
        return {"total": 0, "avg_rating": 0, "per_agent": {}}


# ── Correlation: sessions ↔ pipelines ─────────────────────────────

def correlate_pipelines(sessions: list[dict]) -> list[dict]:
    """Cross-reference sessions with pipeline records by timestamp proximity."""
    pipes_path = VAULT_ROOT / "_pipeline" / "pipeline-durations.json"
    pipelines = []
    if pipes_path.exists():
        try:
            pipelines = json.loads(pipes_path.read_text(encoding="utf-8")).get("entries", [])
        except Exception:
            pass
    for s in sessions:
        s["matched_pipelines"] = []
        if not s.get("created"):
            continue
        try:
            s_time = datetime.fromisoformat(s["created"]).timestamp()
        except Exception:
            continue
        for p in pipelines:
            p_time = datetime.fromisoformat(p.get("timestamp", "")).timestamp() if p.get("timestamp") else 0
            if abs(s_time - p_time) < 3600:
                s["matched_pipelines"].append({
                    "pipeline_id": p.get("timestamp", ""),
                    "duration_s": p.get("duration_s", 0),
                    "profile": p.get("profile", ""),
                })
    return sessions


# ── Build analytics store ─────────────────────────────────────────

def build_analytics() -> dict:
    """Build full session analytics snapshot."""
    sessions = get_recent_sessions(days=7)
    sessions = correlate_pipelines(sessions)
    agent_tokens = get_tokens_per_agent(days=7)
    feedback = get_feedback_summary()
    total_messages = sum(s.get("message_count", 0) for s in sessions)
    avg_duration = None
    durations = [s["duration_min"] for s in sessions if s.get("duration_min")]
    if durations:
        avg_duration = round(sum(durations) / len(durations), 1)
    analytics = {
        "generated_at": datetime.now().isoformat(),
        "period_days": 7,
        "total_sessions": len(sessions),
        "total_messages": total_messages,
        "avg_duration_min": avg_duration,
        "recent_sessions": sessions[:10],
        "agent_token_usage": agent_tokens,
        "feedback": feedback,
    }
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ANALYTICS_PATH.write_text(json.dumps(analytics, indent=2, ensure_ascii=False), encoding="utf-8")
    return analytics


# ── CLI entry point ───────────────────────────────────────────────

def report() -> str:
    analytics = build_analytics()
    lines = [f"# Session Analytics (last {analytics['period_days']} days)"]
    lines.append(f"*Generated: {analytics['generated_at']}*\n")
    lines.append(f"- **Sessions**: {analytics['total_sessions']}")
    lines.append(f"- **Messages**: {analytics['total_messages']}")
    if analytics.get("avg_duration_min"):
        lines.append(f"- **Avg duration**: {analytics['avg_duration_min']} min")
    fb = analytics.get("feedback", {})
    if fb.get("total", 0) > 0:
        lines.append(f"- **User ratings**: {fb['total']} ratings, avg {fb['avg_rating']}/5")
    if analytics.get("agent_token_usage"):
        lines.append("\n## Tokens per Agent")
        for row in analytics["agent_token_usage"]:
            lines.append(f"- **{row.get('agent', '?')}**: {row.get('total_tokens', 0):,} tokens, "
                         f"${row.get('total_cost', 0):.4f}, {row.get('llm_calls', 0)} calls")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())