"""Tests for lib.config module."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.config import VAULT_ROOT, MAX_TOKENS, PRIORITY_ORDER, IGNORED_PAGES


def test_vault_root_exists():
    assert VAULT_ROOT.exists()
    assert (VAULT_ROOT / "_scripts").exists()


def test_max_tokens():
    assert MAX_TOKENS == 128000


def test_priority_order():
    assert "wiki/entities/" in PRIORITY_ORDER
    assert len(PRIORITY_ORDER) == 5


def test_ignored_pages():
    assert "index" in IGNORED_PAGES
    assert "log" in IGNORED_PAGES
