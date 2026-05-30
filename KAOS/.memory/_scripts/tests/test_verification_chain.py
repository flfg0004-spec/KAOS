"""Tests for the real verification_chain implementation (Fase 3)."""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / ".tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["KAOS_TESTING"] = "1"

from verification_chain import (
    fase1_aletheia,
    fase2_kosmos,
    fase3_metis,
    generate_report,
    compute_composite_score,
    run_all_fases,
    generate_claim_id,
    verify_output,
    _extract_urls,
    _extract_citations,
    _extract_arch_terms,
    VERIFICATION_DIR,
)

SAMPLE_REPORT = """# Strategic Analysis Report

## Objective
Improve system performance and scalability.

## Key Findings
The current architecture uses a monolithic deployment with high latency.
We need to migrate to microservices with event-driven communication.

**Architecture**: The system has high coupling between modules.
**API Gateway**: Single point of failure detected.
**Cache Layer**: Redis implementation inconsistent across services.

## References
- Source: Market analysis 2026 [https://example.com/report]
- Research data from Q1 2026
- Technical documentation: https://docs.example.com/architecture

## Risk Assessment
1. High latency in payment processing (see reference [PAY-001])
2. Database connection pool exhaustion
"""


def test_fase1_aletheia_detects_references():
    result = fase1_aletheia(SAMPLE_REPORT)
    assert result["phase"] == 1
    assert result["agent"] == "aletheia"
    assert "veracidad" in result["scores"]
    assert "coherencia" in result["scores"]
    assert result["details"]["urls_found"] >= 2
    assert result["details"]["citations_found"] >= 1


def test_fase1_aletheia_no_content():
    result = fase1_aletheia("")
    assert result["scores"]["veracidad"] == 20
    assert result["details"]["urls_found"] == 0


def test_fase2_kosmos_detects_arch_terms():
    result = fase2_kosmos(SAMPLE_REPORT)
    assert result["phase"] == 2
    assert result["agent"] == "kosmos"
    assert "completitud" in result["scores"]
    assert "reproducibilidad" in result["scores"]
    assert result["details"]["unique_arch_terms"] >= 4


def test_fase2_kosmos_no_content():
    result = fase2_kosmos("")
    assert result["scores"]["completitud"] == 10


def test_fase3_metis_no_file():
    result = fase3_metis(Path("/tmp/nonexistent_report_xyz.md"))
    assert result["phase"] == 3
    assert result["agent"] == "metis"
    assert "veracidad" in result["scores"]


def test_generate_report_contains_all_fases():
    f1 = fase1_aletheia(SAMPLE_REPORT)
    f2 = fase2_kosmos(SAMPLE_REPORT)
    f3 = {"agent": "metis", "phase": 3, "label": "Estratégica", "scores": {"veracidad": 60, "utilidad": 70}, "details": {}}
    composite = compute_composite_score([f1, f2, f3], "desarrollo")
    report = generate_report([f1, f2, f3], composite, "desarrollo")
    assert "Fase 1" in report
    assert "Fase 2" in report
    assert "Fase 3" in report
    assert "Score Composite" in report
    assert "aletheia" in report.lower() or "Aletheia" in report
    assert "kosmos" in report.lower() or "Kosmos" in report
    assert "metis" in report.lower() or "Metis" in report


def test_generate_claim_id_format():
    cid = generate_claim_id("Kosmos", "architecture-check")
    assert cid.startswith("kosmos")
    assert "architecture-check" in cid
    assert " " not in cid


def test_verify_output_structure():
    v, path = verify_output("test-claim", "aletheia", "kosmos", {"veracidad": 80, "coherencia": 75})
    assert v["agent_origin"] == "aletheia"
    assert v["agent_verifier"] == "kosmos"
    assert v["scores"]["veracidad"] == 80
    assert "evidence_hash" in v
    assert path.exists()
    assert path.suffix == ".json"
    path.unlink()


def test_extract_urls():
    text = "Visit https://example.com and http://test.org for more."
    urls = _extract_urls(text)
    assert len(urls) == 2
    assert "https://example.com" in urls


def test_extract_citations():
    text = "fuentes: reporte anual 2026, y ref: análisis de mercado"
    citations = _extract_citations(text)
    assert len(citations) >= 1


def test_extract_arch_terms():
    text = "La arquitectura de microservicios usa API gateway y eventos"
    terms = _extract_arch_terms(text)
    assert "arquitectura" in terms
    assert "microservicio" in terms
    assert "api" in terms
    assert "evento" in terms


def test_no_arch_terms():
    terms = _extract_arch_terms("this is plain text without any architectural references whatsoever")
    assert len(terms) == 0


def test_run_all_fases_file_not_found():
    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp) / "nonexistent.md"
        try:
            run_all_fases(fake, "desarrollo")
            assert False, "Should have raised SystemExit"
        except SystemExit:
            pass


def test_compute_composite_empty():
    score = compute_composite_score([], "desarrollo")
    assert score == 0.0


def test_compute_composite():
    fases = [
        {"agent": "aletheia", "phase": 1, "scores": {"veracidad": 80, "coherencia": 70}},
        {"agent": "kosmos", "phase": 2, "scores": {"completitud": 75, "reproducibilidad": 65}},
        {"agent": "metis", "phase": 3, "scores": {"veracidad": 60, "utilidad": 70}},
    ]
    score = compute_composite_score(fases, "desarrollo")
    assert score > 0
    assert score <= 100


def test_run_all_fases_with_synthetic():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_REPORT)
        tmp_path = f.name
    try:
        fases = run_all_fases(Path(tmp_path), "desarrollo")
        assert len(fases) == 3
        assert fases[0]["phase"] == 1
        assert fases[1]["phase"] == 2
        assert fases[2]["phase"] == 3
    finally:
        os.unlink(tmp_path)


def test_report_contains_scores():
    f1 = fase1_aletheia(SAMPLE_REPORT)
    f2 = fase2_kosmos(SAMPLE_REPORT)
    f3 = {"agent": "metis", "phase": 3, "label": "Estratégica", "scores": {"veracidad": 80, "utilidad": 85}, "details": {}}
    composite = compute_composite_score([f1, f2, f3], "desarrollo")
    report = generate_report([f1, f2, f3], composite, "desarrollo")
    assert "/100" in report
    assert "Composite" in report


def test_verify_output_includes_evaluations():
    v, path = verify_output("eval-claim", "agent_a", "agent_b", {"veracidad": 85, "coherencia": 90})
    assert "evaluations" in v
    assert "veracidad" in v["evaluations"]
    assert "coherencia" in v["evaluations"]
    path.unlink()
