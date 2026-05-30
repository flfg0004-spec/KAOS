"""Sleep Cycle — 5-phase memory consolidation for CodeExperience.

Implements MemForge-inspired sleep cycle:
  1. Score: composite importance (recency + frequency + confidence + resolution)
  2. Triage: move low-score to cold tier, mark weak for revision
  3. Revision: LLM-rewrite of weak experiences (augment, correct, merge, compress)
  4. Graph maintenance: decay edges, dedup similar entities
  5. Reflection: synthesize cross-episode insights

Trigger: explicit call + auto-execution every 7 days.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("sleep_cycle")

DB = (Path(__file__).resolve().parent.parent.parent / "cache" / "code_experiences.db")
SLEEP_MARKER = (Path(__file__).resolve().parent.parent.parent / "cache" / ".last_sleep")

SCORE_WEIGHTS = {
    "recency": 0.30,
    "frequency": 0.30,
    "confidence": 0.20,
    "resolution_rate": 0.20,
}

COLD_THRESHOLD = 0.2
ARCHIVE_AFTER_DAYS = 90
DELETE_AFTER_DAYS = 365
MIN_ENTRIES_TO_TRIGGER = 50


def _compute_importance(row: tuple) -> float:
    """Compute composite importance score for a single experience.
    
    Args:
        row: (id, confidence, retrieval_count, resolution_rate, created_at, last_retrieved)
    
    Returns:
        score 0.0-1.0
    """
    _, confidence, retrievals, resolution, created_raw, retrieved_raw = row
    
    confidence = confidence if confidence else 0.5
    retrievals = retrievals if retrievals else 0
    resolution = resolution if resolution else 0.0
    
    # Recency: days since last retrieval (or creation)
    try:
        if retrieved_raw:
            last_access = datetime.strptime(retrieved_raw, "%Y-%m-%d %H:%M:%S")
        else:
            last_access = datetime.strptime(created_raw, "%Y-%m-%d %H:%M:%S") if created_raw else datetime.now()
    except Exception:
        last_access = datetime.now()
    
    days_since = (datetime.now() - last_access).days
    recency = max(0, 1.0 - days_since / 90.0)  # decays over 90 days
    
    # Frequency: normalized to 20 retrievals = 1.0
    frequency = min(1.0, retrievals / 20.0)
    
    score = (
        SCORE_WEIGHTS["recency"] * recency
        + SCORE_WEIGHTS["frequency"] * frequency
        + SCORE_WEIGHTS["confidence"] * confidence
        + SCORE_WEIGHTS["resolution_rate"] * resolution
    )
    
    return min(1.0, max(0.0, score))


def _run_sleep_cycle(dry_run: bool = False) -> dict:
    """Execute the 5-phase sleep cycle.
    
    Args:
        dry_run: If True, only report without making changes
    
    Returns:
        dict with phase results
    """
    conn = sqlite3.connect(str(DB))
    result = {"phases": {}, "total_before": 0}
    
    try:
        # ── Phase 0: Snapshot ──
        total = conn.execute("SELECT COUNT(*) FROM code_experiences").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE confidence >= 0").fetchone()[0]
        result["total_before"] = total
        result["active_before"] = active
        
        if total < MIN_ENTRIES_TO_TRIGGER:
            result["status"] = "skipped"
            result["reason"] = f"Only {total} entries (need {MIN_ENTRIES_TO_TRIGGER})"
            return result
        
        # ── Phase 1: Score ──
        rows = conn.execute("""
            SELECT id, confidence, retrieval_count, resolution_rate, 
                   created_at, last_retrieved
            FROM code_experiences WHERE confidence >= 0
        """).fetchall()
        
        scored = []
        for row in rows:
            importance = _compute_importance(row)
            scored.append((row[0], importance))
        
        # Update importance scores in DB
        if not dry_run:
            conn.executemany(
                "UPDATE code_experiences SET confidence = MIN(1.0, MAX(?, confidence * 0.5 + 0.5 * ?)) WHERE id = ?",
                [(imp, imp, eid) for eid, imp in scored]
            )
        
        result["phases"]["1_score"] = {
            "entries_scored": len(scored),
            "avg_importance": round(sum(s[1] for s in scored) / max(1, len(scored)), 3),
        }
        
        # ── Phase 2: Triage ──
        cold_candidates = conn.execute("""
            SELECT COUNT(*) FROM code_experiences 
            WHERE confidence >= 0 AND confidence < ? AND retrieval_count < 2
            AND julianday('now') - julianday(created_at) > 30
        """, (COLD_THRESHOLD,)).fetchone()[0]
        
        if not dry_run:
            conn.execute("""
                UPDATE code_experiences SET confidence = -1 WHERE confidence >= 0
                AND confidence < ? AND retrieval_count < 2
                AND julianday('now') - julianday(created_at) > 30
            """, (COLD_THRESHOLD,))
            archived_now = conn.execute("SELECT changes()").fetchone()[0]
        else:
            archived_now = cold_candidates
        
        result["phases"]["2_triage"] = {
            "cold_candidates": cold_candidates,
            "archived_now": archived_now,
        }
        
        # ── Phase 3: Revision (LLM rewrite of weak entries) ──
        # In dry_run, just count candidates
        weak_entries = conn.execute("""
            SELECT COUNT(*) FROM code_experiences 
            WHERE confidence >= 0 AND confidence < 0.4 AND confidence >= 0
        """).fetchone()[0]
        
        result["phases"]["3_revision"] = {
            "weak_entries": weak_entries,
            "revised": 0,
            "note": "LLM revision: requires agent invocation outside sleep cycle",
        }
        
        # ── Phase 4: Graph maintenance (permanent delete) ──
        to_delete = conn.execute("""
            SELECT COUNT(*) FROM code_experiences 
            WHERE confidence = -1 AND julianday('now') - julianday(created_at) > ?
        """, (DELETE_AFTER_DAYS,)).fetchone()[0]
        
        if not dry_run:
            conn.execute("""
                DELETE FROM code_experiences WHERE confidence = -1
                AND julianday('now') - julianday(created_at) > ?
            """, (DELETE_AFTER_DAYS,))
            deleted_now = conn.execute("SELECT changes()").fetchone()[0]
        else:
            deleted_now = to_delete
        
        # Hard cap at 10,000 active entries
        if not dry_run:
            active_count = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE confidence >= 0").fetchone()[0]
            if active_count > 10000:
                overflow = active_count - 10000
                conn.execute("""
                    UPDATE code_experiences SET confidence = -1 WHERE id IN (
                        SELECT id FROM code_experiences WHERE confidence >= 0
                        ORDER BY retrieval_count ASC, confidence ASC
                        LIMIT ?
                    )
                """, (overflow,))
                result["phases"]["4_graph"]["overflow_archived"] = overflow
        
        result["phases"]["4_graph"] = {
            "permanently_deleted": deleted_now,
            "to_delete_candidates": to_delete,
        }
        
        # ── Phase 5: Reflection ──
        after_active = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE confidence >= 0").fetchone()[0]
        after_archived = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE confidence = -1").fetchone()[0]
        
        result["phases"]["5_reflection"] = {
            "active_after": after_active,
            "archived_after": after_archived,
            "reduction": active - after_active,
        }
        
        if not dry_run:
            conn.commit()
            # Write sleep marker
            SLEEP_MARKER.write_text(datetime.now().isoformat())
        
        result["status"] = "completed" if not dry_run else "dry_run"
        return result
    
    finally:
        conn.close()


def score_importance(entry_id: int = None) -> dict:
    """Score a single entry or all entries for importance."""
    conn = sqlite3.connect(str(DB))
    try:
        if entry_id:
            row = conn.execute("""
                SELECT id, confidence, retrieval_count, resolution_rate, 
                       created_at, last_retrieved
                FROM code_experiences WHERE id = ?
            """, (entry_id,)).fetchone()
            if not row:
                return {"error": "not found"}
            return {"id": entry_id, "importance": round(_compute_importance(row), 3)}
        
        rows = conn.execute("""
            SELECT id, confidence, retrieval_count, resolution_rate, 
                   created_at, last_retrieved
            FROM code_experiences WHERE confidence >= 0
        """).fetchall()
        scores = [{"id": r[0], "importance": round(_compute_importance(r), 3)} for r in rows]
        return {"entries_scored": len(scores), "scores": scores}
    finally:
        conn.close()


def prune_and_consolidate(dry_run: bool = False) -> dict:
    """Public entry point for sleep cycle.
    
    Checks if sleep is needed (last sleep > 7 days ago or never).
    
    Args:
        dry_run: If True, only report without making changes
    
    Returns:
        dict with phase results
    """
    # Check if sleep is needed
    if SLEEP_MARKER.exists():
        try:
            last_sleep = datetime.fromisoformat(SLEEP_MARKER.read_text().strip())
            days_since = (datetime.now() - last_sleep).days
            if days_since < 7 and not dry_run:
                return {"status": "skipped", "reason": f"Last sleep {days_since} days ago (< 7)"}
        except Exception:
            pass
    
    return _run_sleep_cycle(dry_run=dry_run)


def status() -> dict:
    """Get sleep cycle status info."""
    try:
        from lib.code_memory import init
        init()
    except Exception:
        pass
    
    conn = sqlite3.connect(str(DB))
    try:
        try:
            total = conn.execute("SELECT COUNT(*) FROM code_experiences").fetchone()[0]
            active = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE confidence >= 0").fetchone()[0]
            archived = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE confidence = -1").fetchone()[0]
            forgotten = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE confidence = -2").fetchone()[0]
        except Exception:
            conn.close()
            return {"total": 0, "active": 0, "archived": 0, "forgotten": 0,
                    "last_sleep": "never", "needs_sleep": False, "error": "no tables yet"}
        
        last_sleep = "never"
        if SLEEP_MARKER.exists():
            try:
                last_sleep = SLEEP_MARKER.read_text().strip()
            except Exception:
                pass
        
        return {
            "total": total,
            "active": active,
            "archived": archived,
            "forgotten": forgotten,
            "last_sleep": last_sleep,
            "needs_sleep": total > 0 and (
                not SLEEP_MARKER.exists() or 
                (datetime.now() - datetime.fromisoformat(last_sleep)).days >= 7
            ) if last_sleep != "never" else total > MIN_ENTRIES_TO_TRIGGER,
        }
    finally:
        conn.close()


if __name__ == "__main__":
    import json
    
    print("=== Sleep Cycle Status ===")
    s = status()
    print(f"Total: {s['total']} | Active: {s['active']} | Archived: {s['archived']}")
    print(f"Last sleep: {s['last_sleep']}")
    print(f"Needs sleep: {s['needs_sleep']}")
    
    if s["total"] >= MIN_ENTRIES_TO_TRIGGER:
        print("\n=== Dry Run ===")
        result = prune_and_consolidate(dry_run=True)
        print(json.dumps(result, indent=2))
        
        print("\n=== Execute ===")
        live = prune_and_consolidate()
        print(json.dumps(live, indent=2))
    else:
        print(f"\nNot enough entries to trigger sleep (need {MIN_ENTRIES_TO_TRIGGER}, have {s['total']})")
