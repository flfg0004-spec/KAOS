"""E2E: Aletheia Router → validate_aletheia_output → Score Store persistence."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


@pytest.fixture(autouse=True)
def _patch_db_path():
    from lib import aletheia_score_store as store

    tmpdir = tempfile.mkdtemp()
    old_path = store.DB_PATH
    store.DB_PATH = type(old_path)(tmpdir) / "test.db"
    yield
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


GOOD_OUTPUT = """## Resumen Ejecutivo
Este es un resumen ejecutivo del tema investigado.

## Hallazgos clave
Se encontraron múltiples fuentes relevantes. Fuente: https://example.com

## Análisis detallado
El análisis muestra una matriz de confianza con alta certeza.

## Conclusiones
Se concluye que el tema tiene alta prioridad estratégica.

## Recomendaciones
Se recomienda monitoreo continuo.
"""

BAD_OUTPUT = """## Resumen Ejecutivo
Sin hallazgos claros.

Sin fuentes ni análisis.
"""


def test_validate_good_output():
    from lib.agent_tools import validate_aletheia_output

    result = validate_aletheia_output(GOOD_OUTPUT, "Test topic")
    assert result["valid"] is True
    assert result["score"] >= 0.8


def test_validate_bad_output():
    from lib.agent_tools import validate_aletheia_output

    result = validate_aletheia_output(BAD_OUTPUT, "Test topic")
    assert result["valid"] is False
    assert result["score"] < 0.5


def test_score_store_save_and_retrieve():
    from lib.agent_tools import validate_aletheia_output
    from lib import aletheia_score_store as store

    result = validate_aletheia_output(GOOD_OUTPUT, "E2E test")
    store.save(
        topic="E2E test",
        score=result["score"],
        valid=result["valid"],
        sections_found=result.get("sections_found", []),
        warnings=result.get("warnings", []),
        metadata={"profile": "standard"},
    )

    hist = store.history(limit=5)
    assert len(hist) >= 1
    entry = hist[0]
    assert entry["topic"] == "E2E test"
    assert entry["valid"] is True
    assert entry["score"] >= 0.8


def test_e2e_full_flow():
    from lib.agent_tools import validate_aletheia_output
    from lib import aletheia_score_store as store

    topic = "E2E full integration test"
    result = validate_aletheia_output(GOOD_OUTPUT, topic)

    store.save(
        topic=topic,
        score=result["score"],
        valid=result["valid"],
        sections_found=result.get("sections_found", []),
        warnings=result.get("warnings", []),
        metadata={"profile": "standard", "test": True},
    )

    hist = store.history(limit=10)
    matches = [h for h in hist if h["topic"] == topic]
    assert len(matches) >= 1
    entry = matches[-1]
    assert entry["valid"] is True
    assert entry["score"] >= 0.5

    avg = store.average(days=30)
    assert avg > 0.0
