"""Tests for quality score calculator — v2 with 7 metrics."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_quality_status():
    from lib.quality import status
    s = status()
    assert "Quality Score" in s
    assert "Confidence matrix" in s
    assert "Embeddings" in s
    assert "Tests" in s
    assert "Lint" in s
    assert "Wikilinks" in s
    assert "Connectivity" in s
    assert "Freshness" in s


def test_quality_score_parsing():
    from lib.quality import status
    import re
    s = status()
    m = re.search(r"Quality Score:\s*([\d.]+)", s)
    assert m is not None
    score = float(m.group(1))
    assert 0 <= score <= 100


def test_quality_connectivity():
    from lib.quality import _connectivity_score
    score = _connectivity_score()
    assert 0 <= score <= 1


def test_quality_freshness():
    from lib.quality import _freshness_score
    score = _freshness_score()
    assert 0 <= score <= 1


def test_quality_detail_keys():
    from lib.quality import calculate
    q = calculate()
    assert "details" in q
    d = q["details"]
    assert "connectivity" in d
    assert "freshness" in d
    assert d["connectivity"]["score"] >= 0
    assert d["freshness"]["score"] >= 0


def test_quality_confidence_matrix():
    from lib.quality import status
    import re
    s = status()
    m = re.search(r"Confidence matrix:\s*(\d+)/(\d+)", s)
    assert m is not None
    count = int(m.group(1))
    total = int(m.group(2))
    assert count >= 0
    assert total > 0
    assert count <= total


def test_quality_embedded_pages():
    from lib.quality import _embedded_pages
    embedded, total = _embedded_pages()
    assert isinstance(embedded, int)
    assert isinstance(total, int)
    assert embedded >= 0
    assert total > 0


def test_quality_trend():
    from lib.quality import trend
    t = trend(days=7)
    assert isinstance(t, dict)
