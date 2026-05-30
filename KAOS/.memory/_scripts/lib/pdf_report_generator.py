"""PDF Report Generator — Main engine for generating polished PDF reports."""

import logging
import re
from datetime import datetime
from pathlib import Path

from lib.pdf_branding import AGENT_COLORS, BRAND_COLORS, FONTS
from lib.pdf_chart_engine import generate_chart

logger = logging.getLogger(__name__)

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent.parent / ".vault"
REPORTS_DIR = VAULT_ROOT / "reports"
TEMPLATES_DIR = Path(__file__).resolve().parent / "pdf_templates"


def _ensure_dirs():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


def generate_report(agent_type: str, data: dict, output_path: str | Path | None = None) -> str:
    """Generate a PDF report for an agent.

    Args:
        agent_type: Agent name (aletheia, kosmos, metis, kratos, mnemosyne, kronos)
        data: Report data including title, sections, charts config
        output_path: Optional custom output path

    Returns:
        Path to generated PDF file
    """
    _ensure_dirs()

    from jinja2 import Environment, FileSystemLoader
    from playwright.sync_api import sync_playwright

    # Setup Jinja2
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)

    # Custom filter: safely convert newlines to <br> without using | safe on user content
    def nl2br(value):
        """Convert newlines to <br> tags. Input is already escaped by Jinja2 autoescape."""
        from markupsafe import Markup

        return Markup(str(value).replace("\n", "<br>"))

    env.filters["nl2br"] = nl2br

    # Load agent-specific template or fallback to base
    template_name = f"{agent_type}.html"
    if not (TEMPLATES_DIR / template_name).exists():
        template_name = "base.html"

    template = env.get_template(template_name)

    # Generate charts
    charts = {}
    for chart_config in data.get("charts", []):
        chart_id = chart_config["id"]
        chart_type = chart_config["type"]
        chart_data = chart_config["data"]
        chart_title = chart_config.get("title", "")
        try:
            charts[chart_id] = generate_chart(chart_type, chart_data, chart_title)
        except Exception as e:
            logger.warning("Chart generation failed for %s (%s): %s", chart_id, chart_type, e)

    # Render HTML
    html_content = template.render(
        title=data.get("title", f"KAOS {agent_type.title()} Report"),
        subtitle=data.get("subtitle", ""),
        agent_type=agent_type,
        agent_color=AGENT_COLORS.get(agent_type, BRAND_COLORS["accent"]),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        sections=data.get("sections", []),
        charts=charts,
        brand_colors=BRAND_COLORS,
        fonts=FONTS,
        **data.get("extra", {}),
    )

    # Determine output path
    if output_path is None:
        slug = data.get("title", agent_type).lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)  # Remove invalid chars
        slug = re.sub(r"[\s]+", "-", slug).strip("-")[:50]  # Replace spaces with hyphens
        output_path = REPORTS_DIR / f"{agent_type}-{slug}-{datetime.now().strftime('%Y%m%d')}.pdf"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate PDF with Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = browser.new_page()
        page.set_default_timeout(30000)  # 30s timeout for all operations
        page.set_content(html_content, wait_until="domcontentloaded")
        page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"},
        )
        browser.close()

    logger.info("PDF report generated: %s", output_path)
    return str(output_path.resolve())


# ── Agent-specific report generators ──


def generate_aletheia_report(topic: str, findings: list[dict], sources: list[dict], **kwargs) -> str:
    """Generate Aletheia research report."""
    # Build source type distribution for pie chart
    source_types: dict[str, int] = {}
    for s in sources:
        t = s.get("type", "unknown")
        source_types[t] = source_types.get(t, 0) + 1

    return generate_report(
        "aletheia",
        {
            "title": f"Research Report: {topic}",
            "subtitle": "Aletheia Research Agent",
            "sections": [
                {"title": "Executive Summary", "content": kwargs.get("summary", "")},
                {
                    "title": "Key Findings",
                    "content": "\n".join(
                        f"- **{f.get('title', 'Finding')}**: {f.get('description', '')}" for f in findings
                    ),
                },
            ],
            "charts": [
                {
                    "id": "sources_by_type",
                    "type": "pie",
                    "title": "Sources by Type",
                    "data": {"labels": list(source_types.keys()), "values": list(source_types.values())},
                },
            ],
            "extra": {"findings": findings, "sources": sources},
        },
        kwargs.get("output_path"),
    )


def generate_kosmos_report(topic: str, adr_content: str, metrics: dict, **kwargs) -> str:
    """Generate Kosmos architecture report."""
    return generate_report(
        "kosmos",
        {
            "title": f"Architecture Review: {topic}",
            "subtitle": "Kosmos Architecture Agent",
            "sections": [
                {"title": "Architecture Decision Record", "content": adr_content},
            ],
            "charts": [
                {
                    "id": "quality_radar",
                    "type": "radar",
                    "title": "Architecture Quality",
                    "data": {"labels": list(metrics.keys()), "values": list(metrics.values())},
                },
            ],
            "extra": {"adr_content": adr_content},
        },
        kwargs.get("output_path"),
    )


def generate_metis_report(topic: str, strategy: dict, okrs: list[dict], risks: list[dict], **kwargs) -> str:
    """Generate Metis strategy report."""
    risk_levels: dict[str, int] = {}
    for r in risks:
        level = r.get("level", "unknown")
        risk_levels[level] = risk_levels.get(level, 0) + 1

    return generate_report(
        "metis",
        {
            "title": f"Strategic Analysis: {topic}",
            "subtitle": "Metis Strategy Agent",
            "sections": [
                {"title": "Strategy Overview", "content": strategy.get("overview", "")},
                {
                    "title": "Risks",
                    "content": "\n".join(f"- **{r.get('name', 'Risk')}**: {r.get('impact', '')}" for r in risks),
                },
            ],
            "charts": [
                {
                    "id": "okr_progress",
                    "type": "bar",
                    "title": "OKR Progress",
                    "data": {"x": [o.get("name", "") for o in okrs], "y": [o.get("progress", 0) for o in okrs]},
                },
                {
                    "id": "risk_matrix",
                    "type": "pie",
                    "title": "Risk Distribution",
                    "data": {"labels": list(risk_levels.keys()), "values": list(risk_levels.values())},
                },
            ],
            "extra": {"okrs": okrs, "risks": risks},
        },
        kwargs.get("output_path"),
    )


def generate_kratos_report(topic: str, code_metrics: dict, **kwargs) -> str:
    """Generate Kratos code quality report."""
    return generate_report(
        "kratos",
        {
            "title": f"Code Quality Report: {topic}",
            "subtitle": "Kratos Code Agent",
            "sections": [
                {"title": "Code Metrics", "content": "\n".join(f"- **{k}**: {v}" for k, v in code_metrics.items())},
            ],
            "charts": [
                {
                    "id": "code_metrics",
                    "type": "bar",
                    "title": "Code Metrics",
                    "data": {"x": list(code_metrics.keys()), "y": list(code_metrics.values())},
                },
            ],
        },
        kwargs.get("output_path"),
    )


def generate_mnemosyne_report(topic: str, curation_data: dict, quality_score: float, **kwargs) -> str:
    """Generate Mnemosyne curation report."""
    return generate_report(
        "mnemosyne",
        {
            "title": f"Curation Report: {topic}",
            "subtitle": "Mnemosyne Memory Guardian",
            "sections": [
                {"title": "Curation Summary", "content": f"Quality Score: **{quality_score}/100**"},
            ],
            "charts": [
                {"id": "quality_gauge", "type": "gauge", "title": "Quality Score", "data": {"value": quality_score}},
                {
                    "id": "phases_bar",
                    "type": "bar",
                    "title": "Curation Phases",
                    "data": {"x": list(curation_data.keys()), "y": list(curation_data.values())},
                },
            ],
        },
        kwargs.get("output_path"),
    )


def generate_kronos_report(pipeline_metrics: dict, costs: dict, **kwargs) -> str:
    """Generate Kronos pipeline report."""
    return generate_report(
        "kronos",
        {
            "title": "Pipeline Performance Report",
            "subtitle": "Kronos Orchestrator",
            "sections": [
                {
                    "title": "Pipeline Metrics",
                    "content": "\n".join(f"- **{k}**: {v}" for k, v in pipeline_metrics.items()),
                },
            ],
            "charts": [
                {
                    "id": "costs_bar",
                    "type": "bar",
                    "title": "Cost Breakdown",
                    "data": {"x": list(costs.keys()), "y": list(costs.values())},
                },
            ],
            "extra": {"pipeline_metrics": pipeline_metrics, "costs": costs},
        },
        kwargs.get("output_path"),
    )


def generate_pipeline_report(state: dict, **kwargs) -> str:
    """Generate a combined pipeline report from the full KAOS state."""
    sections = []

    aletheia_out = state.get("aletheia_output", "")
    if aletheia_out:
        sections.append({"title": "Research (Aletheia)", "content": aletheia_out[:1000]})

    kosmos_out = state.get("kosmos_output", "")
    if kosmos_out:
        sections.append({"title": "Architecture (Kosmos)", "content": kosmos_out[:1000]})

    metis_out = state.get("metis_output", "")
    if metis_out:
        sections.append({"title": "Strategy (Metis)", "content": metis_out[:1000]})

    kratos_out = state.get("kratos_output", "")
    if kratos_out:
        sections.append({"title": "Code (Kratos)", "content": kratos_out[:1000]})

    mnemosyne_out = state.get("mnemosyne_output", "")
    if mnemosyne_out:
        sections.append({"title": "Curation (Mnemosyne)", "content": mnemosyne_out[:1000]})

    if not sections:
        sections.append({"title": "Status", "content": "No agent outputs available for this pipeline run."})

    return generate_report(
        "kronos",
        {
            "title": f"Pipeline Report: {state.get('topic', 'Unknown Topic')}",
            "subtitle": "KAOS Full Pipeline Execution",
            "sections": sections,
            "charts": [],
        },
        kwargs.get("output_path"),
    )
