"""Tests for Synapse cross-linking engine."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_synapse_status():
    """Verifica que status report incluye métricas clave."""
    from lib.synapse import status
    s = status()
    assert "Concepts indexed" in s
    assert "Total [[wikilinks]]" in s


def test_synapse_index():
    """Verifica que index_all() reconstruye el índice sin errores."""
    from lib.synapse import index_all
    result = index_all()
    assert "indexed" in result


def test_synapse_find_similar():
    """Verifica que _find_similar retorna lista con scores."""
    from lib.synapse import _find_similar
    results = _find_similar("deep learning", top_k=3)
    assert isinstance(results, list)
    assert len(results) <= 3
    if results:
        assert "score" in results[0]
        assert "slug" in results[0]


def test_synapse_cross_link_pipeline_maid():
    """Verifica cross-link de concepto existente."""
    from lib.synapse import cross_link
    result = cross_link("pipeline-maid")
    assert "linked" in result or "not found" in result or "no similar" in result


def test_synapse_inject_wikilink():
    """Verifica inyección de [[wikilinks]] en contenido."""
    from lib.synapse import _inject_wikilink
    content = "Texto de prueba sin enlaces"
    modified, changed = _inject_wikilink(content, "concepto-ejemplo")
    assert changed is True
    assert "[[concepto-ejemplo]]" in modified
    modified2, changed2 = _inject_wikilink(modified, "concepto-ejemplo")
    assert changed2 is False
