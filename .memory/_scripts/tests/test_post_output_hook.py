"""Tests for post_output_hook.py — the Metis post-output verification hook."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / ".tools"))
from post_output_hook import parse_okrs, check_okrs, check_foda, check_roadmap, check_risks


SAMPLE_OKRS = """
## O1: Expandir市场份额

**Objective**: Incrementar market share de 15% a 25% en 12 meses

- KR1: Alcanzar 25% de market share (baseline: 15%)
- KR2: Reducir churn de 8% a 4%
- KR3: Aumentar NPS de 40 a 60
"""

SAMPLE_FODA = """
## Strengths
- Equipo técnico sólido con experiencia en cloud (rating: 8/10)
- Producto maduro con 99.9% uptime (rating: 9/10)
- Base de clientes leales en segmento enterprise (rating: 7/10)

## Weaknesses
- Falta de presencia en mercado LATAM (rating: 4/10)
- Proceso de onboarding lento (rating: 3/10)
- Dependencia de un solo proveedor cloud (rating: 5/10)

## Opportunities
- Crecimiento de mercado GPU cloud 40% anual (rating: 8/10)
- Nuevos segmentos en IA/ML (rating: 7/10)
- Expansión a industria financiera (rating: 6/10)

## Threats
- Competidores con pricing agresivo (rating: 7/10)
- Regulaciones de datos en Europa (rating: 6/10)
- Guerra de talento técnico (rating: 8/10)
"""

SAMPLE_ROADMAP = """
## H1 (0-3 meses)
- Lanzar versión 2.0 del producto core
- Contratar 3 ingenieros senior
- Migrar infraestructura a multi-cloud

## H2 (3-6 meses)
- Expandir a mercado LATAM con equipo local
- Integrar pagos encriptados
- Lanzar programa de partners

## H3 (6-12 meses)
- Plataforma IA adaptativa con routing inteligente
- Expansión a industria financiera (licencias)
- IPO preparation
"""

SAMPLE_RISKS = """
## Risk Matrix

- Riesgo: Competidor lanza producto similar (prob: alta, impacto: alto)
  Mitigación: Diferenciación vía IA y precio
- Riesgo: Fuga de talento clave (prob: media, impacto: alto)
  Mitigación: Plan de retención con equity
- Riesgo: Regulación cambiante en Europa (prob: media, impacto: medio)
  Mitigación: Equipo legal dedicado
"""


class TestParseOkrs:
    def test_parse_okrs_finds_objectives(self):
        okrs = parse_okrs(SAMPLE_OKRS)
        assert len(okrs) == 1
        assert "market share" in okrs[0]["objective"]

    def test_parse_okrs_finds_key_results(self):
        okrs = parse_okrs(SAMPLE_OKRS)
        assert len(okrs[0]["key_results"]) >= 2

    def test_parse_okrs_empty_text(self):
        assert parse_okrs("") == []

    def test_parse_okrs_no_okrs(self):
        assert parse_okrs("# Just a header\nSome text") == []


class TestCheckOkrs:
    def test_okrs_pass_with_targets(self):
        result = check_okrs(SAMPLE_OKRS)
        assert result["count"] >= 1
        assert result["kr_targets"] >= 1
        assert result["passed"] is True

    def test_okrs_fail_no_targets(self):
        text = "## O1: Test\n**Objective**: Do stuff\n- KR1: Just a description without numbers"
        result = check_okrs(text)
        assert result["passed"] is False

    def test_okrs_empty(self):
        result = check_okrs("")
        assert result["count"] == 0
        assert result["passed"] is False


class TestCheckFoda:
    def test_foda_passes_with_3_per_quadrant(self):
        result = check_foda(SAMPLE_FODA)
        assert result["passed"] is True
        for q in ["strengths", "weaknesses", "opportunities", "threats"]:
            assert result["counts"][q] >= 3

    def test_foda_fails_with_empty(self):
        result = check_foda("")
        assert result["passed"] is False

    def test_foda_fails_with_few_items(self):
        text = "## Strengths\n- One item"
        result = check_foda(text)
        assert result["passed"] is False


class TestCheckRoadmap:
    def test_roadmap_passes_with_3_horizons(self):
        result = check_roadmap(SAMPLE_ROADMAP)
        assert result["passed"] is True
        assert result["horizons"]["h1"] > 0
        assert result["horizons"]["h2"] > 0
        assert result["horizons"]["h3"] > 0

    def test_roadmap_fails_with_empty(self):
        result = check_roadmap("")
        assert result["passed"] is False

    def test_roadmap_fails_with_one_horizon(self):
        text = "## H1\n- Milestone A"
        result = check_roadmap(text)
        assert result["passed"] is False


class TestCheckRisks:
    def test_risks_passes_with_mitigation(self):
        result = check_risks(SAMPLE_RISKS)
        assert result["total"] >= 2
        assert result["with_mitigation"] >= 1
        assert result["passed"] is True

    def test_risks_fails_with_empty(self):
        result = check_risks("")
        assert result["passed"] is False

    def test_risks_fails_no_mitigation(self):
        text = "- Risk without mitigation plan"
        result = check_risks(text)
        assert result["passed"] is False
