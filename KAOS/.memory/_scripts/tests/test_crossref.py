"""Tests for lib.crossref — Phase 11 bidirectional wikilink verification."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_crossref_import():
    from lib import crossref
    assert hasattr(crossref, "verify_bidirectional")
    assert hasattr(crossref, "suggest_backlinks")
    assert hasattr(crossref, "report")


def test_verify_bidirectional_structure():
    from lib.crossref import verify_bidirectional
    results = verify_bidirectional()
    assert isinstance(results, list)
    if results:
        r = results[0]
        assert "from" in r
        assert "to" in r
        assert "from_path" in r
        assert "to_path" in r
        assert "fix" in r


def test_suggest_backlinks_structure():
    from lib.crossref import suggest_backlinks
    results = suggest_backlinks(top_k=5)
    assert isinstance(results, list)


def test_report_structure():
    from lib.crossref import report
    text = report()
    assert isinstance(text, str)
    assert text.startswith("# Cross-Reference Report")
    assert "Unidirectional Wikilinks" in text
    assert "Suggested Backlinks" in text
