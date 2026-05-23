"""Tests for lib.lint module."""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_broken_links_empty():
    from lib.lint import broken_links
    result, combined = broken_links([])
    assert result == []
    assert isinstance(combined, str)


def test_orphan_pages_empty():
    from lib.lint import orphan_pages
    result = orphan_pages([], "")
    assert result == []
