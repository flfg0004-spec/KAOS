"""Tests for lib.validator — cross-validation with Gemini Flash."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_validator_module_loads():
    import lib.validator
    assert hasattr(lib.validator, "run") or hasattr(lib.validator, "validate")


def test_validator_basic():
    from lib.cross_validator import run
    result = run(path="", profile="desarrollo")
    assert result is not None
    assert isinstance(result, str)
