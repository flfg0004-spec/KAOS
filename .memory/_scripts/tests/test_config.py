"""Tests for lib.config — constants, thresholds, env vars."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_config_vault_root():
    from lib.config import VAULT_ROOT
    assert VAULT_ROOT.exists()
    assert (VAULT_ROOT / "wiki").exists()


def test_config_thresholds():
    from lib.config import PRESSURE_THRESHOLDS
    assert "critical" in PRESSURE_THRESHOLDS
    assert PRESSURE_THRESHOLDS["critical"] > PRESSURE_THRESHOLDS["high"]
    assert PRESSURE_THRESHOLDS["high"] > PRESSURE_THRESHOLDS["warning"]


def test_config_priority_order():
    from lib.config import PRIORITY_ORDER
    assert isinstance(PRIORITY_ORDER, list)
    assert len(PRIORITY_ORDER) > 0
    assert all(isinstance(p, str) for p in PRIORITY_ORDER)


def test_config_ignored_pages():
    from lib.config import IGNORED_PAGES
    assert "index" in IGNORED_PAGES
    assert "log" in IGNORED_PAGES


def test_config_environ():
    from lib.config import MAX_TOKENS, CACHE_MAX_ENTRIES
    assert MAX_TOKENS > 0
    assert CACHE_MAX_ENTRIES > 0
    assert MAX_TOKENS == 128000
    assert CACHE_MAX_ENTRIES == 30
