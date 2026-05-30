"""Tests for knowledge_scorer.py and knowledge_levels.py."""

import os
import tempfile
from pathlib import Path

import pytest

os.environ["KAOS_TESTING"] = "1"

from lib.knowledge_scorer import score_document, score_directory, format_report, PESOS
from lib.knowledge_levels import (
    assign_level,
    needs_synthesis,
    get_tier_info,
    can_promote,
    get_promotion_path,
    TIERS,
)


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def temp_wiki(tmp_path: Path) -> Path:
    d = tmp_path / "wiki" / "concepts"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def well_formed_doc(temp_wiki: Path) -> Path:
    """Documento completo con frontmatter, secciones, wikilinks."""
    content = (
        "---\n"
        "title: Test Concept\n"
        "tags: [test, concept]\n"
        "created: 2026-05-01\n"
        "---\n"
        "\n"
        "# Test Concept\n"
        "\n"
        "## Introducción\n"
        "\n"
        "Este es un documento de prueba con contenido significativo "
        "para verificar el funcionamiento del knowledge scorer.\n"
        "\n"
        "## Confianza\n"
        "\n"
        "- ✅ Fuente verificada\n"
        "- ⚡ Pendiente de validación\n"
        "\n"
        "## Relaciones\n"
        "\n"
        "Esto se relaciona con [[OtroConcepto]] y [[FuentePrincipal]].\n"
        "También ver https://ejemplo.com para más información.\n"
        "\n"
        "## Detalles\n"
        "\n"
        "- Primer elemento de lista\n"
        "- Segundo elemento\n"
        "- Tercer elemento con [[WikiLink]] adicional\n"
        "\n"
        "```python\n"
        "print('hello')\n"
        "```\n"
    )
    fp = temp_wiki / "test-concept.md"
    fp.write_text(content, encoding="utf-8")
    return fp


@pytest.fixture
def empty_doc(temp_wiki: Path) -> Path:
    """Documento vacío sin frontmatter."""
    fp = temp_wiki / "empty.md"
    fp.write_text("", encoding="utf-8")
    return fp


@pytest.fixture
def minimal_doc(temp_wiki: Path) -> Path:
    """Documento mínimo sin estructura."""
    fp = temp_wiki / "minimal.md"
    fp.write_text("# Solo título\n\nSin mucho contenido real.", encoding="utf-8")
    return fp


# ── Test knowledge_scorer ──────────────────────────────────────────────


def test_score_document_returns_dict(well_formed_doc: Path):
    result = score_document(well_formed_doc)
    assert isinstance(result, dict)


def test_score_document_has_all_8_metrics(well_formed_doc: Path):
    result = score_document(well_formed_doc)
    metrics = result.get("metrics", {})
    expected = {"completitud", "confianza", "conectividad", "frescura",
                "precision_factual", "legibilidad", "utilidad", "coherencia"}
    assert expected == set(metrics.keys()), f"Missing: {expected - set(metrics.keys())}"


def test_score_document_score_range_0_100(well_formed_doc: Path):
    result = score_document(well_formed_doc)
    score = result["score"]
    assert 0 <= score <= 100, f"Score {score} fuera de rango"


def test_score_document_level_assigned(well_formed_doc: Path):
    result = score_document(well_formed_doc)
    assert result["level"] in TIERS, f"Nivel inválido: {result['level']}"


def test_score_document_empty_file_returns_low_score(empty_doc: Path):
    result = score_document(empty_doc)
    assert result["score"] < 60, f"Documento vacío debería tener score bajo, obtuvo {result['score']}"


def test_score_document_with_frontmatter_scores_higher(temp_wiki: Path):
    with_fm = temp_wiki / "with-fm.md"
    with_fm.write_text(
        "---\ntitle: With FM\ntags: [a]\ncreated: 2026-01-01\n---\n\n# Title\n\nContenido.\n",
        encoding="utf-8",
    )
    without_fm = temp_wiki / "without-fm.md"
    without_fm.write_text("# Title\n\nContenido.\n", encoding="utf-8")

    r1 = score_document(with_fm)
    r2 = score_document(without_fm)
    c1 = r1["metrics"]["completitud"]["score"]
    c2 = r2["metrics"]["completitud"]["score"]
    assert c1 > c2, f"Con frontmatter ({c1}) debería > sin ({c2})"


def test_score_document_with_wikilinks_scores_higher(temp_wiki: Path):
    with_links = temp_wiki / "with-links.md"
    with_links.write_text(
        "# Links\n\n[[ConceptoA]] y [[ConceptoB]] y [[ConceptoC]].\n",
        encoding="utf-8",
    )
    without_links = temp_wiki / "without-links.md"
    without_links.write_text("# No Links\n\nSin enlaces.\n", encoding="utf-8")

    r1 = score_document(with_links)
    r2 = score_document(without_links)
    c1 = r1["metrics"]["conectividad"]["score"]
    c2 = r2["metrics"]["conectividad"]["score"]
    assert c1 >= c2, f"Con links ({c1}) debería >= sin ({c2})"


def test_score_document_nonexistent_path():
    result = score_document("/tmp/nonexistent-file-12345.md")
    assert "error" in result
    assert result["score"] == 0


def test_score_directory_returns_list(temp_wiki: Path):
    (temp_wiki / "a.md").write_text("# A\n\nContenido.\n", encoding="utf-8")
    (temp_wiki / "b.md").write_text("# B\n\nContenido.\n", encoding="utf-8")
    results = score_directory(temp_wiki, recursive=False)
    assert isinstance(results, list)
    assert len(results) == 2


# ── Test knowledge_levels ──────────────────────────────────────────────


def test_assign_level_raw_to_low():
    assert assign_level(0) == "RAW"
    assert assign_level(10) == "RAW"
    assert assign_level(20) == "RAW"


def test_assign_level_canonical_to_high():
    assert assign_level(91) == "CANONICAL"
    assert assign_level(95) == "CANONICAL"
    assert assign_level(100) == "CANONICAL"


def test_needs_synthesis_below_60():
    assert needs_synthesis(0) is True
    assert needs_synthesis(30) is True
    assert needs_synthesis(59) is True
    assert needs_synthesis(60) is False
    assert needs_synthesis(80) is False


def test_format_report_contains_scores(well_formed_doc: Path):
    results = [score_document(well_formed_doc)]
    report = format_report(results)
    assert "Knowledge Scoring Report" in report
    assert str(well_formed_doc.stem) in report or "test-concept" in report


# ── Additional level tests ─────────────────────────────────────────────


def test_assign_level_all_tiers():
    assert assign_level(5) == "RAW"
    assert assign_level(30) == "ROUGH"
    assert assign_level(50) == "DRAFT"
    assert assign_level(70) == "REVIEW"
    assert assign_level(85) == "CURATED"
    assert assign_level(95) == "CANONICAL"


def test_get_tier_info_valid():
    info = get_tier_info("DRAFT")
    assert info["name"] == "DRAFT"
    assert info["min_score"] == 41
    assert info["max_score"] == 60
    assert isinstance(info["requires_synthesis"], bool)
    assert isinstance(info["requires_hitl"], bool)


def test_get_tier_info_invalid():
    with pytest.raises(ValueError):
        get_tier_info("NONEXISTENT")


def test_can_promote_without_previous():
    result = can_promote(95)
    assert result["can_promote"] is False
    assert result["target_tier"] == "CANONICAL"
    # Score 80 is CURATED (76-90), needs 91+ for CANONICAL
    result = can_promote(80)
    assert result["can_promote"] is False
    assert result["current_tier"] == "CURATED"


def test_can_promote_already_max():
    result = can_promote(95)
    assert result["can_promote"] is False
    assert result["target_tier"] == "CANONICAL"


def test_can_promote_blocked_drop():
    result = can_promote(50, previous_score=80)
    assert result["can_promote"] is False
    assert result["blocked_by"] is not None


def test_get_promotion_path_from_raw():
    path = get_promotion_path("RAW")
    assert path == ["ROUGH", "DRAFT", "REVIEW", "CURATED", "CANONICAL"]


def test_get_promotion_path_from_curated():
    path = get_promotion_path("CURATED")
    assert path == ["CANONICAL"]


def test_get_promotion_path_at_canonical():
    path = get_promotion_path("CANONICAL")
    assert path == []


# ── Weight sum sanity ──────────────────────────────────────────────────


def test_weights_sum_to_one():
    total = sum(PESOS.values())
    assert abs(total - 1.0) < 0.01, f"Pesos suman {total}, debería ser 1.0"
