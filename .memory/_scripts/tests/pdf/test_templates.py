"""Tests for Jinja2 PDF templates — base.html and metis.html."""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "lib" / "pdf_templates"
BRAND_COLORS = {
    "primary": "#1e293b",
    "secondary": "#334155",
    "accent": "#38bdf8",
    "success": "#22c55e",
    "warning": "#eab308",
    "danger": "#ef4444",
    "text": "#e2e8f0",
    "muted": "#94a3b8",
    "background": "#0f172a",
}
AGENT_COLORS = {
    "aletheia": "#4A90D9",
    "kosmos": "#7B68EE",
    "metis": "#E8A87C",
    "kratos": "#DC143C",
    "mnemosyne": "#C0C0C0",
    "kronos": "#FFD700",
}
FONTS = {
    "heading": "Inter, system-ui, sans-serif",
    "body": "Inter, system-ui, sans-serif",
    "mono": "JetBrains Mono, monospace",
}

SAMPLE_SECTIONS = [
    {"title": "Executive Summary", "content": "This is a test report."},
    {"title": "Findings", "content": "- Finding 1\n- Finding 2"},
]

SAMPLE_CHARTS = {
    "chart1": "c3R1Yi1wbGFjZWhvbGRlcg==",
}


@pytest.fixture
def env():
    """Create a Jinja2 environment with the nl2br filter."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)

    def nl2br(value):
        from markupsafe import Markup

        return Markup(str(value).replace("\n", "<br>"))

    env.filters["nl2br"] = nl2br
    return env


class TestBaseTemplate:
    def test_renders_with_minimal_data(self, env):
        """Base template renders without errors with minimal data."""
        template = env.get_template("base.html")
        html = template.render(
            title="Test Report",
            subtitle="Test",
            agent_type="aletheia",
            agent_color=AGENT_COLORS["aletheia"],
            generated_at="2026-01-01 00:00",
            sections=[],
            charts={},
            brand_colors=BRAND_COLORS,
            fonts=FONTS,
        )
        assert "<html" in html
        assert "Test Report" in html
        assert "aletheia" in html

    def test_renders_sections_and_charts(self, env):
        """Base template renders sections and charts correctly."""
        template = env.get_template("base.html")
        html = template.render(
            title="Full Report",
            subtitle="With data",
            agent_type="metis",
            agent_color=AGENT_COLORS["metis"],
            generated_at="2026-01-01 00:00",
            sections=SAMPLE_SECTIONS,
            charts=SAMPLE_CHARTS,
            brand_colors=BRAND_COLORS,
            fonts=FONTS,
        )
        assert "Executive Summary" in html
        assert "Findings" in html
        assert '<img src="data:image/png;base64,' in html
        assert "c3R1Yi1wbGFjZWhvbGRlcg==" in html

    def test_xss_escaping(self, env):
        """XSS in section.content is escaped, not rendered as HTML."""
        template = env.get_template("base.html")
        xss_content = '<script>alert("xss")</script>'
        html = template.render(
            title="XSS Test",
            subtitle="",
            agent_type="test",
            agent_color="#fff",
            generated_at="2026-01-01 00:00",
            sections=[{"title": "Test", "content": xss_content}],
            charts={},
            brand_colors=BRAND_COLORS,
            fonts=FONTS,
        )
        assert "<script>" not in html or "&lt;script&gt;" in html
        assert "alert" not in html or "&lt;script&gt;" in html

    def test_has_required_blocks(self):
        """Base template defines the required Jinja2 blocks."""
        source = Path(TEMPLATES_DIR / "base.html").read_text(encoding="utf-8")
        assert "{% block extra_css %}" in source
        assert "{% block content %}" in source
        assert "{% endblock %}" in source


class TestMetisTemplate:
    def test_renders_with_okrs_and_risks(self, env):
        """Metis template renders OKR bars and risk items."""
        template = env.get_template("metis.html")
        html = template.render(
            title="Strategy Report",
            subtitle="Metis Strategy",
            agent_type="metis",
            agent_color=AGENT_COLORS["metis"],
            generated_at="2026-01-01 00:00",
            sections=SAMPLE_SECTIONS,
            charts=SAMPLE_CHARTS,
            brand_colors=BRAND_COLORS,
            fonts=FONTS,
            okrs=[{"name": "Market Entry", "progress": 65}],
            risks=[{"name": "Regulatory", "level": "high", "impact": "High"}],
        )
        assert "Strategy Report" in html
        assert "Market Entry" in html
        assert "65%" in html
        assert "Regulatory" in html
        assert "risk-high" in html

    def test_extends_base(self):
        """Metis template extends base.html."""
        source = (TEMPLATES_DIR / "metis.html").read_text(encoding="utf-8")
        assert '{% extends "base.html" %}' in source
