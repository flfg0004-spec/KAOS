"""Tests for Sleep Cycle — 5-phase memory consolidation."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"
os.environ["LLM_DIRECT_ENABLED"] = "false"

import sqlite3
from pathlib import Path


def _clean_db():
    from lib.sleep_cycle import DB, SLEEP_MARKER
    result = True
    if DB.exists():
        try:
            DB.unlink()
            result = True
        except PermissionError:
            result = False
    if SLEEP_MARKER.exists():
        try:
            SLEEP_MARKER.unlink()
        except Exception:
            pass
    return result


def _populate_test_db(count: int = 60):
    """Populate a test DB with entries."""
    from lib.code_memory import init, store
    from lib.sleep_cycle import DB
    init()
    for i in range(count):
        store(
            error_message=f"TestError {i}: test error pattern",
            language="python",
            code_snippet=f"x = {i}",
        )


def test_status_empty():
    from lib.sleep_cycle import status
    _clean_db()
    s = status()
    assert "total" in s
    assert "active" in s
    assert "last_sleep" in s


def test_status_with_entries():
    from lib.sleep_cycle import status
    _clean_db()
    _populate_test_db(5)
    s = status()
    assert s["total"] >= 5
    assert s["active"] >= 5


def test_score_importance():
    from lib.sleep_cycle import score_importance
    _clean_db()
    _populate_test_db(5)
    result = score_importance()
    assert result["entries_scored"] >= 5
    for entry in result["scores"]:
        assert 0 <= entry["importance"] <= 1


def test_prune_dry_run():
    from lib.sleep_cycle import prune_and_consolidate
    _clean_db()
    _populate_test_db(60)
    result = prune_and_consolidate(dry_run=True)
    assert result["status"] == "dry_run"
    assert "phases" in result
    assert "1_score" in result["phases"]
    assert "2_triage" in result["phases"]
    assert "3_revision" in result["phases"]
    assert "4_graph" in result["phases"]
    assert "5_reflection" in result["phases"]


def test_prune_execute():
    from lib.sleep_cycle import prune_and_consolidate
    _clean_db()
    _populate_test_db(60)
    result = prune_and_consolidate(dry_run=False)
    assert result["status"] == "completed"
    assert result["phases"]["1_score"]["entries_scored"] >= 50


def test_prune_skipped_if_few_entries():
    from lib.sleep_cycle import prune_and_consolidate
    was_cleaned = _clean_db()
    _populate_test_db(5)
    result = prune_and_consolidate(dry_run=False)
    if was_cleaned:
        assert result["status"] == "skipped", f"Expected skipped, got {result['status']}"
    else:
        assert result["status"] in ("skipped", "completed")


def test_importance_recency():
    from lib.sleep_cycle import _compute_importance
    import datetime
    now = datetime.datetime.now()
    
    # Recent entry with high retrievals
    rec = (1, 0.9, 10, 0.8, now.isoformat(), now.isoformat())
    new_score = _compute_importance(rec)
    
    # Old entry with low retrievals
    old = (2, 0.3, 1, 0.2, (now - datetime.timedelta(days=200)).isoformat(), "")
    old_score = _compute_importance(old)
    
    assert new_score > old_score, "Recent/frequent entries should score higher"


def test_sleep_marker_created():
    from lib.sleep_cycle import prune_and_consolidate, SLEEP_MARKER
    _clean_db()
    _populate_test_db(60)
    prune_and_consolidate(dry_run=False)
    assert SLEEP_MARKER.exists()


def test_sleep_marker_skips_if_recent():
    from lib.sleep_cycle import prune_and_consolidate, SLEEP_MARKER
    _clean_db()
    _populate_test_db(60)
    # First run: should execute
    prune_and_consolidate(dry_run=False)
    # Second run: should skip (less than 7 days)
    result = prune_and_consolidate(dry_run=False)
    assert result["status"] == "skipped"


def test_phases_structure():
    from lib.sleep_cycle import prune_and_consolidate
    _clean_db()
    _populate_test_db(60)
    result = prune_and_consolidate(dry_run=True)
    expected_phases = {"1_score", "2_triage", "3_revision", "4_graph", "5_reflection"}
    assert expected_phases.issubset(result["phases"].keys())
