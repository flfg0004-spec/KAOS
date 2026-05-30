"""Tests for lib.pdf_report_generator — agent-specific report generators."""

from pathlib import Path

import pytest
from lib.pdf_report_generator import (
    generate_aletheia_report,
    generate_kosmos_report,
    generate_kratos_report,
    generate_kronos_report,
    generate_metis_report,
    generate_mnemosyne_report,
    generate_pipeline_report,
)

from tests.pdf.fixtures.sample_data import (
    SAMPLE_PIPELINE_STATE,
)


@pytest.mark.usefixtures("mock_playwright")
class TestAletheiaReport:
    def test_generates_pdf(self, tmp_path):
        path = generate_aletheia_report(
            "AI Trends",
            [{"title": "Agentic AI", "description": "Autonomous agents are becoming mainstream."}],
            [{"type": "arxiv"}, {"type": "blog"}],
            summary="Research summary",
            output_path=tmp_path / "test.pdf",
        )
        assert path.endswith(".pdf")
        assert (tmp_path / "test.pdf").exists()


@pytest.mark.usefixtures("mock_playwright")
class TestKosmosReport:
    def test_generates_pdf(self, tmp_path):
        path = generate_kosmos_report(
            "Microservices",
            "ADR: Event-driven architecture",
            {"scalability": 85, "maintainability": 72},
            output_path=tmp_path / "test.pdf",
        )
        assert path.endswith(".pdf")
        assert (tmp_path / "test.pdf").exists()


@pytest.mark.usefixtures("mock_playwright")
class TestMetisReport:
    def test_generates_pdf(self, tmp_path):
        path = generate_metis_report(
            "Market Expansion",
            {"overview": "Expand into APAC markets"},
            [{"name": "Market Entry", "progress": 65}],
            [{"name": "Regulatory", "level": "high", "impact": "High"}],
            output_path=tmp_path / "test.pdf",
        )
        assert path.endswith(".pdf")
        assert (tmp_path / "test.pdf").exists()


@pytest.mark.usefixtures("mock_playwright")
class TestKratosReport:
    def test_generates_pdf(self, tmp_path):
        path = generate_kratos_report(
            "Payment Module",
            {"Lines of Code": 4500, "Test Coverage": 87, "Complexity": 42},
            output_path=tmp_path / "test.pdf",
        )
        assert path.endswith(".pdf")
        assert (tmp_path / "test.pdf").exists()


@pytest.mark.usefixtures("mock_playwright")
class TestMnemosyneReport:
    def test_generates_pdf(self, tmp_path):
        path = generate_mnemosyne_report(
            "Knowledge Base",
            {"Deduplication": 120, "Wikilink": 85, "Archival": 45},
            85.0,
            output_path=tmp_path / "test.pdf",
        )
        assert path.endswith(".pdf")
        assert (tmp_path / "test.pdf").exists()


@pytest.mark.usefixtures("mock_playwright")
class TestKronosReport:
    def test_generates_pdf(self, tmp_path):
        path = generate_kronos_report(
            {"Total Runs": 245, "Avg Duration": "12.4s", "Success Rate": "94%"},
            {"OpenAI": 124.50, "Playwright": 32.00, "Storage": 8.75},
            output_path=tmp_path / "test.pdf",
        )
        assert path.endswith(".pdf")
        assert (tmp_path / "test.pdf").exists()


@pytest.mark.usefixtures("mock_playwright")
class TestPipelineReport:
    def test_generates_pdf(self, tmp_path):
        path = generate_pipeline_report(
            SAMPLE_PIPELINE_STATE,
            output_path=tmp_path / "pipeline.pdf",
        )
        assert path.endswith(".pdf")
        assert (tmp_path / "pipeline.pdf").exists()

    def test_empty_state_fallback(self, tmp_path):
        path = generate_pipeline_report(
            {},
            output_path=tmp_path / "empty.pdf",
        )
        assert path.endswith(".pdf")
        assert (tmp_path / "empty.pdf").exists()


@pytest.mark.usefixtures("mock_playwright")
class TestEdgeCases:
    def test_chart_failure_does_not_crash(self, tmp_path):
        """Chart generation failure is caught and report still generates."""
        path = generate_kronos_report(
            {"Total Runs": 245},
            {"Cost": 100},
            output_path=tmp_path / "chart_fail.pdf",
        )
        assert path.endswith(".pdf")
        assert (tmp_path / "chart_fail.pdf").exists()

    def test_auto_slug_path_generation(self):
        """When no output_path is given, a slug is auto-generated."""
        path = generate_metis_report(
            "Auto Slug Test",
            {"overview": "Test"},
            [{"name": "OKR", "progress": 50}],
            [{"name": "Risk", "level": "low", "impact": "Low"}],
        )
        assert path.endswith(".pdf")
        assert Path(path).exists()
        assert "auto-slug-test" in path.lower()

    def test_chart_failure_logged(self, monkeypatch, tmp_path):
        """Chart failure is caught and doesn't crash the report."""
        import lib.pdf_report_generator as rp


        def failing_chart(*a, **kw):
            raise ValueError("Simulated chart failure")

        monkeypatch.setattr(rp, "generate_chart", failing_chart)
        path = generate_kronos_report(
            {"Total Runs": 245},
            {"Cost": 100},
            output_path=tmp_path / "fail.pdf",
        )
        assert path.endswith(".pdf")
        assert (tmp_path / "fail.pdf").exists()
