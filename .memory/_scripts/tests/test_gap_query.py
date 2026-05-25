"""Tests for lib.gap_query — Phase 0 Gap Query API."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_query_gaps_import():
    from lib import gap_query
    assert hasattr(gap_query, "query_gaps")
    assert callable(gap_query.query_gaps)


def test_query_gaps_structure():
    from lib.gap_query import query_gaps
    r = query_gaps("quantum computing")
    assert isinstance(r, dict)
    assert "topic" in r
    assert "existing_concepts" in r
    assert "gaps_detected" in r
    assert "orphan_pages" in r
    assert "decayed_topics" in r
    assert "confidence_gaps" in r
    assert "total_existing" in r
    assert "total_gaps" in r
    assert "generated_at" in r
    assert r["topic"] == "quantum computing"


def test_query_gaps_empty_topic():
    from lib.gap_query import query_gaps
    r = query_gaps("")
    assert isinstance(r, dict)
    assert r["total_existing"] == 0


def test_query_gaps_existing_concepts():
    from lib.gap_query import _semantic_search
    results = _semantic_search("test")
    assert isinstance(results, list)


def test_confidence_gaps():
    from lib.gap_query import _confidence_gaps
    results = _confidence_gaps()
    assert isinstance(results, list)


def test_decayed_topics():
    from lib.gap_query import _decayed_topics
    results = _decayed_topics(min_confidence=0.01)
    assert isinstance(results, list)
