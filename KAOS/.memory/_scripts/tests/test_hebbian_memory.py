"""Tests for Hebbian Memory — co-retrieval graph, associations, decay."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def _clean_db():
    from lib.hebbian_memory import HEBBIAN_DB
    if HEBBIAN_DB.exists():
        try:
            HEBBIAN_DB.unlink()
        except PermissionError:
            pass


def test_init_creates_tables():
    from lib.hebbian_memory import _init_hebbian_db, get_graph_stats
    _clean_db()
    _init_hebbian_db()
    stats = get_graph_stats()
    assert "total_edges" in stats
    assert "nodes_with_edges" in stats


def test_record_co_retrieval_single():
    from lib.hebbian_memory import record_co_retrieval
    _clean_db()
    result = record_co_retrieval([1])
    assert result["edges_affected"] == 0


def test_record_co_retrieval_pair():
    from lib.hebbian_memory import record_co_retrieval
    _clean_db()
    result = record_co_retrieval([1, 2])
    assert result["edges_affected"] == 1


def test_record_co_retrieval_triple():
    from lib.hebbian_memory import record_co_retrieval
    _clean_db()
    result = record_co_retrieval([1, 2, 3])
    assert result["edges_affected"] == 3  # (1,2), (1,3), (2,3)


def test_strength_increases():
    from lib.hebbian_memory import record_co_retrieval, get_graph_stats
    _clean_db()
    record_co_retrieval([1, 2])  # first: strength=0.3
    record_co_retrieval([1, 2])  # second: strength=0.45
    record_co_retrieval([1, 2])  # third: strength=0.6

    conn = __import__('sqlite3').connect(str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent / "cache" / "hebbian_edges.db"))
    row = conn.execute("SELECT strength, co_retrievals FROM hebbian_edges WHERE source_id=1 AND target_id=2").fetchone()
    conn.close()
    assert row[0] >= 0.5
    assert row[1] >= 3


def test_get_associated():
    from lib.hebbian_memory import record_co_retrieval, get_associated
    _clean_db()
    record_co_retrieval([1, 2])
    record_co_retrieval([1, 3])
    assoc = get_associated(1, min_strength=0.1)
    assert len(assoc) > 0


def test_decay_edges():
    from lib.hebbian_memory import record_co_retrieval, decay_edges
    _clean_db()
    record_co_retrieval([1, 2])
    result = decay_edges(dry_run=True)
    assert result["status"] == "dry_run"
    assert result["total_before"] >= 1


def test_get_graph_stats():
    from lib.hebbian_memory import get_graph_stats
    _clean_db()
    stats = get_graph_stats()
    assert isinstance(stats["total_edges"], int)
    assert 0 <= stats["avg_strength"] <= 1
