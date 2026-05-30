"""Slow tests for lib.memory_lifecycle (requires real file system)."""
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _slow(func):
    func._slow = True
    return func


@_slow
def test_lifecycle_real_evaluate():
    from lib.memory_lifecycle import evaluate
    test_path = Path(os.path.dirname(__file__)) / ".." / "wiki" / "index.md"
    if test_path.exists():
        result = evaluate(test_path)
        assert "tier" in result
        assert "confidence" in result
        assert result["tier"] in ("new", "active", "frozen", "archive", "stale")
        assert 0 <= result["confidence"] <= 1


@_slow
def test_lifecycle_real_status():
    from lib.memory_lifecycle import status
    s = status()
    assert "Tier Distribution" in s or "Memory Lifecycle" in s


@_slow
def test_lifecycle_real_evaluate_all():
    from lib.memory_lifecycle import run_evaluate_all
    results = run_evaluate_all(dry_run=True)
    assert isinstance(results, list)
    if results:
        assert "confidence" in results[0]
