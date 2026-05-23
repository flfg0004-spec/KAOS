"""Tests for lib.pressure module."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.pressure import estimate_tokens, get_level


def test_estimate_tokens_empty():
    assert estimate_tokens("") == 0


def test_estimate_tokens_short():
    t = estimate_tokens("hello world")
    assert t > 0
    assert isinstance(t, int)


def test_level_normal():
    r = get_level(1000, 128000)
    assert r["level"] == "normal"
    assert r["action"] == "none"


def test_level_warning():
    r = get_level(90000, 128000)
    assert r["level"] == "warning"
    assert r["action"] == "trim"


def test_level_high():
    r = get_level(110000, 128000)
    assert r["level"] == "high"
    assert r["action"] == "compress"


def test_level_critical():
    r = get_level(122000, 128000)
    assert r["level"] == "critical"
    assert r["action"] == "archive"


def test_pressure_output_format():
    r = get_level(5000, 128000)
    assert "pressure" in r
    assert "level" in r
    assert "action" in r
    assert "recommendation" in r
