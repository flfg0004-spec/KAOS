"""Tests for ingest module — text, dedup, validation, wikipedia."""
import sys
import os

# Add paths for ingest.py dependencies
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.join(_TEST_DIR, "..")
_KAOS_ROOT = os.path.join(_SCRIPTS_DIR, "..", "..")
_TOOLS_DIR = os.path.join(_KAOS_ROOT, ".tools")
for p in [_SCRIPTS_DIR, _KAOS_ROOT, _TOOLS_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)


def test_ingest_text():
    """Verifica ingesta de texto plano."""
    from ingest import ingest_text
    result = ingest_text("Contenido de prueba para test global con mas de 50 caracteres.", "test-ingest")
    assert result["status"] in ("ingested", "deduped")
    assert result.get("sha256", "") != ""


def test_ingest_dedup():
    """Verifica deduplicacion SHA-256."""
    from ingest import ingest_text
    text = "Texto unico para dedup test con mas de 50 caracteres para validar."
    r1 = ingest_text(text, "test-dedup")
    r2 = ingest_text(text, "test-dedup")
    assert r1["status"] in ("ingested", "deduped")
    assert r2["status"] == "deduped"


def test_ingest_content_validation():
    """Verifica que contenido corto es rechazado."""
    from ingest import ingest_text
    result = ingest_text("corto", "test-corto")
    assert result["status"] == "error"
    assert "too short" in result["message"]


def test_ingest_slug_clean():
    """Verifica que los slugs se limpian correctamente."""
    from ingest import _clean_slug
    assert _clean_slug("  Test Title With Spaces!  ") == "test-title-with-spaces"
    assert _clean_slug("") == "untitled"


def test_ingest_sha256():
    """Verifica que SHA-256 es consistente."""
    from ingest import _sha256
    h1 = _sha256("mismo contenido")
    h2 = _sha256("mismo contenido")
    h3 = _sha256("otro contenido")
    assert h1 == h2
    assert h1 != h3
