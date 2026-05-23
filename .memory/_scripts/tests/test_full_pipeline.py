"""Tests: Full pipeline end-to-end (profile init, steps, content validation)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_pipeline_init_with_profile():
    """Verifica inicialización de pipeline con perfil deep."""
    from lib import pipeline
    result = pipeline.init("Test full pipeline E2E", profile="deep")
    assert "initialized" in result
    assert "deep" in result


def test_pipeline_check_after_init():
    """Verifica que check detecta pipeline activo."""
    from lib import pipeline
    result = pipeline.check()
    assert "active" in result or "ready" in result


def test_pipeline_full_cycle():
    """Verifica ciclo completo Aletheia → Kosmos → Metis → Mnemosyne → complete."""
    from lib import pipeline
    r1 = pipeline.step_done("Aletheia")
    assert "done" in r1
    r2 = pipeline.step_done("Kosmos")
    assert "done" in r2
    r3 = pipeline.step_done("Metis")
    assert "done" in r3
    r4 = pipeline.step_done("Mnemosyne")
    assert "complete" in r4


def test_pipeline_idle_after_complete():
    """Verifica que después del ciclo completo, pipeline está idle/complete."""
    from lib import pipeline
    result = pipeline.check()
    assert "idle" in result or "complete" in result or "active" not in result


def test_pipeline_init_standard():
    """Verifica inicialización con perfil standard (default)."""
    from lib import pipeline
    result = pipeline.init("Test standard profile", profile="standard")
    assert "initialized" in result
    assert "standard" in result
