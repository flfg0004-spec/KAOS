"""Tests for memory lifecycle management (F6)."""
import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_lifecycle_evaluate():
    from lib.memory_lifecycle import evaluate
    mf = os.path.join(os.path.dirname(__file__), "..", "wiki", "index.md")
    if not os.path.exists(mf):
        mf = os.path.join(os.path.dirname(__file__), "..", "..", "wiki", "index.md")
    if os.path.exists(mf):
        r = evaluate(Path(mf))
        assert "tier" in r
        assert "confidence" in r
        assert r["tier"] in ("new", "active", "frozen", "archive", "stale")
        assert 0 <= r["confidence"] <= 1


def test_lifecycle_status_output():
    from lib.memory_lifecycle import status
    s = status()
    assert "Memory Lifecycle" in s or "Tier Distribution" in s or "Average confidence" in s or "Flagged" in s


def test_lifecycle_evaluate_all():
    from lib.memory_lifecycle import run_evaluate_all
    results = run_evaluate_all(dry_run=True)
    assert isinstance(results, list)
    if results:
        assert "path" in results[0]
        assert "tier" in results[0]


def test_lifecycle_confidence():
    from lib.memory_lifecycle import _confidence_score
    assert _confidence_score(0) == 1.0
    assert _confidence_score(365) < 1.0
    assert _confidence_score(10000) >= 0.0


def test_lifecycle_tier_thresholds():
    from lib.memory_lifecycle import _get_tier
    assert _get_tier(3) == "new"
    assert _get_tier(10) == "active"
    assert _get_tier(20) == "frozen"
    assert _get_tier(60) == "archive"
    assert _get_tier(200) == "stale"


def test_lifecycle_recommendations():
    from lib.memory_lifecycle import _recommendation
    assert "ARCHIVE" in _recommendation("stale", 0.2, True, 3)
    assert "REVIEW" in _recommendation("archive", 0.5, True, 3)
    assert "OK" in _recommendation("frozen", 0.7, True, 3)
    assert "LINK" in _recommendation("active", 0.9, True, 0)
    assert "FM" in _recommendation("active", 0.9, False, 5)
    assert "GROW" in _recommendation("new", 1.0, True, 3)
