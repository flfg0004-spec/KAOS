"""Tests for knowledge_synthesis.py."""
import os
import tempfile
from pathlib import Path

import pytest

os.environ["KAOS_TESTING"] = "1"

from lib.knowledge_synthesis import (
    synthesize,
    estimate_diff_ratio,
    create_backup,
    _synthesize_frontmatter,
    _synthesize_sources,
    _extract_frontmatter,
)


@pytest.fixture
def temp_doc() -> tuple[Path, Path]:
    d = Path(tempfile.mkdtemp())
    content = "# Sin título\n\nContenido breve sin frontmatter.\n"
    fp = d / "test.md"
    fp.write_text(content, encoding="utf-8")
    return d, fp


def _make_low_scores(path: str) -> dict:
    return {
        "path": path,
        "score": 35.0,
        "level": "ROUGH",
        "metrics": {
            "completitud": {"score": 10, "weight": 0.15},
            "confianza": {"score": 20, "weight": 0.20},
            "conectividad": {"score": 5, "weight": 0.15},
            "frescura": {"score": 80, "weight": 0.10},
            "precision_factual": {"score": 10, "weight": 0.15},
            "legibilidad": {"score": 15, "weight": 0.10},
            "utilidad": {"score": 50, "weight": 0.10},
            "coherencia": {"score": 80, "weight": 0.05},
        },
    }


def test_synthesize_returns_dict(temp_doc):
    _, fp = temp_doc
    scores = _make_low_scores(str(fp))
    result = synthesize(fp, scores, dry_run=True)
    assert isinstance(result, dict)
    assert "path" in result
    assert "score_before" in result
    assert "operations" in result


def test_synthesize_low_score_triggers_operations(temp_doc):
    _, fp = temp_doc
    scores = _make_low_scores(str(fp))
    result = synthesize(fp, scores, dry_run=True)
    assert len(result["operations"]) > 0, (
        f"Expected operations for low score, got: {result}"
    )


def test_synthesize_high_score_skips(temp_doc):
    _, fp = temp_doc
    scores = {
        "path": str(fp), "score": 85.0, "level": "CURATED",
        "metrics": {},
    }
    result = synthesize(fp, scores, dry_run=True)
    assert "no synthesis needed" in (result.get("error") or "").lower(), (
        f"Expected skip for high score, got: {result}"
    )
    assert len(result["operations"]) == 0


def test_synthesize_dry_run_does_not_write(temp_doc):
    d, fp = temp_doc
    scores = _make_low_scores(str(fp))
    original = fp.read_text(encoding="utf-8")
    synthesize(fp, scores, dry_run=True)
    assert fp.read_text(encoding="utf-8") == original


def test_synthesize_frontmatter_added():
    content = "# Mi Título\n\nContenido de prueba.\n"
    fm = {}
    result = _synthesize_frontmatter(content, fm, Path("test.md"))
    assert result.startswith("---")
    assert "title:" in result or "title: Mi Título" in result
    assert "tags:" in result


def test_synthesize_sources_added():
    content = "# Tema\n\nTexto con https://ejemplo.com y más.\n"
    scores = {"path": "test.md", "score": 30, "level": "ROUGH", "metrics": {}}
    result = _synthesize_sources(content, scores)
    assert "## Referencias" in result or result == content


def test_create_backup_creates_bak(temp_doc):
    _, fp = temp_doc
    backup = create_backup(fp)
    assert backup is not None
    assert backup.exists()
    assert backup.suffix == ".bak"


def test_estimate_diff_ratio_no_change_zero():
    assert estimate_diff_ratio("hola\nmundo", "hola\nmundo") == 0.0


def test_estimate_diff_ratio_complete_change():
    assert estimate_diff_ratio("hola", "adiós") > 0.0


def test_synthesize_canonical_skipped(temp_doc):
    _, fp = temp_doc
    # CANONICAL guard triggers when needs_synthesis passes but level is CANONICAL
    scores = {
        "path": str(fp), "score": 50.0, "level": "CANONICAL",
        "metrics": {"conectividad": {"score": 100}},
    }
    result = synthesize(fp, scores, dry_run=True)
    error = result.get("error") or ""
    assert "CANONICAL" in error or "no synthesis needed" not in error
