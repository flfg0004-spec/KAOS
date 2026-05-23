"""Tests for lib.pipeline module."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_pipeline_cycle():
    """Test init → check → step-done → complete cycle (Aletheia→Kosmos→Metis→Mnemosyne)."""
    from lib import pipeline
    result = pipeline.init("research analysis")
    assert "initialized" in result
    assert "aletheia-ready" in result

    check_a = pipeline.check("Aletheia")
    assert "task available" in check_a

    step_a = pipeline.step_done("Aletheia")
    assert "Kosmos ready" in step_a

    check_k = pipeline.check("Kosmos")
    assert "task available" in check_k

    step_k = pipeline.step_done("Kosmos")
    assert "Metis ready" in step_k

    step_m = pipeline.step_done("Metis")
    assert "Mnemosyne ready" in step_m

    step_mn = pipeline.step_done("Mnemosyne")
    assert "pipeline complete" in step_mn

    final = pipeline.check()
    assert "idle" in final or "complete" in final
