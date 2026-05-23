"""Tests for quality score calculator."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_quality_status():
    """Verifica que quality.status() retorna el formato esperado."""
    from lib.quality import status
    s = status()
    assert "Quality Score" in s
    assert "Confidence matrix" in s
    assert "Embeddings" in s
    assert "Tests" in s
    assert "Lint" in s
    assert "Wikilinks" in s


def test_quality_score_parsing():
    """Verifica que el score es un numero valido."""
    from lib.quality import status
    import re
    s = status()
    m = re.search(r"Quality Score:\s*([\d.]+)", s)
    assert m is not None
    score = float(m.group(1))
    assert 0 <= score <= 100


def test_quality_confidence_matrix():
    """Verifica que la matriz de confianza se reporta correctamente."""
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
    """Verifica que _embedded_pages retorna tupla de enteros."""
    from lib.quality import _embedded_pages
    embedded, total = _embedded_pages()
    assert isinstance(embedded, int)
    assert isinstance(total, int)
    assert embedded >= 0
    assert total > 0
