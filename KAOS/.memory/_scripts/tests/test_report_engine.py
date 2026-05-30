"""Tests for lib.report_engine — Phase 14 structured curation report."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_report_engine_import():
    from lib import report_engine
    assert hasattr(report_engine, "generate_curation_report")
    assert hasattr(report_engine, "to_json")


def test_generate_curation_report_with_phases():
    """Lightweight: pass explicit phases dict, no vault computation."""
    from lib.report_engine import generate_curation_report
    phases = {
        "ingest": {"count": 5, "ok": True, "description": "Ingest"},
        "tag": {"count": 12, "ok": True, "description": "Tag"},
        "link": {"count": 8, "ok": True, "description": "Link"},
        "lint": {"issues": 0, "ok": True},
    }
    text = generate_curation_report(phases)
    assert isinstance(text, str)
    assert "F1" in text
    assert "F2" in text


test_generate_curation_report_with_phases._slow = False


def test_aletheia_feedback():
    from lib.report_engine import _aletheia_feedback
    fb = _aletheia_feedback(85.0, 3)
    assert fb["quality_score"] == 85.0
    assert fb["confidence_validated"] is True
    assert fb["orphans_remaining"] == 3
    assert fb["recommendation"] == "ok"

    fb2 = _aletheia_feedback(50.0, 10)
    assert fb2["confidence_validated"] is False
    assert fb2["recommendation"] == "needs_review"


def test_report_from_scratch():
    """Heavy: builds full vault graph and quality score."""
    from lib.report_engine import generate_curation_report
    text = generate_curation_report()
    assert isinstance(text, str)
    assert text.startswith("# Mnemosyne Curation Report")


test_report_from_scratch._slow = True


def test_to_json_structure():
    """Heavy: computes full quality + gap + graph analysis."""
    from lib.report_engine import to_json
    r = to_json()
    assert isinstance(r, dict)
    assert "curation_report" in r
    assert "issues_found" in r
    assert "wikilinks_added" in r
    assert "tags_assigned" in r
    assert "duplicates_fused" in r
    assert "gaps_detected" in r
    assert "graph_communities" in r
    assert "quality_score" in r
    assert "aletheia_feedback" in r
    assert isinstance(r["aletheia_feedback"], dict)
    assert "new_concepts_curated" in r["aletheia_feedback"]
    assert "confidence_validated" in r["aletheia_feedback"]


test_to_json_structure._slow = True
