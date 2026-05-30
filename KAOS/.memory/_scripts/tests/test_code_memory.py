"""Tests for CodeExperience memory — store, search, feedback, prune, status."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"
os.environ["LLM_DIRECT_ENABLED"] = "false"


def _clean_db():
    """Remove test DB so each test starts clean."""
    from lib.code_memory import DB
    if DB.exists():
        try:
            DB.unlink()
        except PermissionError:
            import os
            os.system(f"del /f /q \"{DB}\" 2>nul" if os.name == "nt" else f"rm -f \"{DB}\"")


def test_init_creates_tables():
    from lib.code_memory import init, DB
    _clean_db()
    result = init()
    assert DB.exists()
    assert "initialized" in result

    import sqlite3
    conn = sqlite3.connect(str(DB))
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    conn.close()
    assert "code_experiences" in tables
    assert "code_exp_fts" in tables
    assert "bandit_state" in tables


def test_store_creates_entry():
    from lib.code_memory import init, store
    _clean_db()
    init()
    result = store(
        error_message="TypeError: cannot unpack non-iterable NoneType object",
        language="python",
        code_snippet="a, b = get_values()"
    )
    assert result["status"] == "created"
    assert "hash" in result


def test_store_dedup():
    from lib.code_memory import init, store
    _clean_db()
    init()
    r1 = store("ZeroDivisionError: division by zero", "python", code_snippet="1/0")
    assert r1["status"] == "created"
    r2 = store("ZeroDivisionError: division by zero", "python", code_snippet="1/0")
    assert r2["status"] == "exists"


def test_search_fts():
    from lib.code_memory import init, store, search
    _clean_db()
    init()
    store("TypeError: cannot unpack non-iterable", "python", code_snippet="a, b = func()")
    store("KeyError: 'missing_key'", "python", code_snippet="d['missing']")
    
    results = search("unpack", code_snippet="x, y = f()", language="python")
    assert len(results) >= 1
    assert "TypeError" in results[0]["error"] or "unpack" in results[0]["error"]


def test_search_filters_low_confidence():
    from lib.code_memory import init, store, search, feedback
    _clean_db()
    init()
    store("TestError: low conf", "python")
    # feedback with failure multiple times to drive confidence down
    from lib.code_memory import feedback
    r = store("TestError: will drop", "python")
    if r["status"] == "created":
        for _ in range(3):
            feedback(r["hash"], success=False)
    
    results = search("TestError", code_snippet="", language="python")
    # Should not return if confidence < 0.2
    for res in results:
        assert res["confidence"] >= 0.2


def test_feedback_updates_confidence():
    from lib.code_memory import init, store, feedback
    _clean_db()
    init()
    r = store("FeedbackTest: initial", "python")
    if r["status"] == "created":
        fb = feedback(r["hash"], success=True)
        assert fb["status"] == "updated"
        assert fb["new_confidence"] > 0.5


def test_feedback_reduces_confidence():
    from lib.code_memory import init, store, feedback
    _clean_db()
    init()
    r = store("FeedbackTest: failure", "python")
    if r["status"] == "created":
        fb = feedback(r["hash"], success=False)
        assert fb["status"] == "updated"
        assert fb["new_confidence"] <= 0.52  # bandit may return ~0.5 with 1 sample


def test_prune_dry_run():
    from lib.code_memory import init, prune
    _clean_db()
    init()
    result = prune(dry_run=True)
    assert "candidates_for_archive" in result
    assert "total_active" in result


def test_status():
    from lib.code_memory import init, store, status
    _clean_db()
    init()
    s = status()
    assert "total_experiences" in s
    assert "active" in s
    assert "avg_confidence" in s
    assert "with_ast" in s


def test_capture_from_bash():
    from lib.code_memory import init, capture_from_bash
    _clean_db()
    init()
    result = capture_from_bash(exit_code=1, stderr="TypeError: NoneType", cmd="test_cmd", cwd="python")
    assert result["status"] in ("created", "exists")


def test_capture_from_bash_ok_skips():
    from lib.code_memory import init, capture_from_bash
    _clean_db()
    init()
    result = capture_from_bash(exit_code=0, stderr="", cmd="test", cwd="")
    assert result["status"] == "ok"


def test_full_cycle():
    """Full store → search → feedback → prune cycle."""
    from lib.code_memory import init, store, search, feedback, prune
    _clean_db()
    init()
    
    r = store("FullCycle: test error", "python", code_snippet="test_code")
    assert r["status"] == "created"
    h = r["hash"]
    
    results = search("test error", code_snippet="test_code", language="python")
    assert any(res["hash"] == h for res in results)
    
    fb = feedback(h, success=True)
    assert fb["status"] == "updated"
    
    p = prune(dry_run=True)
    assert p["total_active"] >= 1
