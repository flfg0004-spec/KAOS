"""Visualization orchestrator — central routing for all visual tools.

Each agent calls orchestrate() after completing its node, and the
orchestrator checks feature flags, routes to the correct renderer,
and returns paths to generated files.

Usage:
    from lib.viz_orchestrator import orchestrate
    result = orchestrate("mnemosyne", {"topic": "foo", "curation_metrics": {...}})
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from lib.feature_flags import is_enabled

logger = logging.getLogger(__name__)

DASHBOARD_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".memory" / "dashboard"


@dataclass
class VizOutput:
    success: bool = False
    paths: list[str] = field(default_factory=list)
    format: str = ""
    agent: str = ""
    diagram_type: str = ""


@dataclass
class KosmosData:
    adr_content: str = ""


@dataclass
class MetisData:
    domain_clusters: str = ""


@dataclass
class MnemosyneData:
    curation_phases: str = ""
    topic: str = ""


@dataclass
class AletheiaData:
    research_tree: str = ""


@dataclass
class KratosData:
    code_flow: str = ""


def _parse_agent_data(agent: str, data: dict | None):
    if data is None:
        return None
    if agent == "kosmos":
        return KosmosData(adr_content=data.get("adr_content", ""))
    elif agent == "metis":
        return MetisData(domain_clusters=data.get("domain_clusters", ""))
    elif agent == "mnemosyne":
        return MnemosyneData(
            curation_phases=data.get("curation_phases", ""),
            topic=data.get("topic", ""),
        )
    elif agent == "aletheia":
        return AletheiaData(research_tree=data.get("research_tree", ""))
    elif agent == "kratos":
        return KratosData(code_flow=data.get("code_flow", ""))
    return None


def _render_kroki(diagram_type: str, source: str, output_format: str = "svg") -> VizOutput:
    try:
        import json

        from mcp_kroki import render_diagram

        result = json.loads(render_diagram(diagram_type, source, output_format))
        out = VizOutput(
            success=result.get("success", False),
            format=output_format,
            diagram_type=diagram_type,
        )
        if result.get("success"):
            out.paths = [result.get("content", "")]
        return out
    except Exception as e:
        logger.warning("Kroki render failed: %s", e)
        return VizOutput(success=False, format=output_format, diagram_type=diagram_type)


def _render_markmap(markdown_text: str, output_path: str | None = None) -> VizOutput:
    try:
        import json

        from mcp_markmap import render_mindmap

        result = json.loads(render_mindmap(markdown_text, output_path))
        if result.get("success"):
            return VizOutput(
                success=True,
                paths=[result["path"]],
                format="html",
                diagram_type="mindmap",
            )
        return VizOutput(
            success=False, format="html", diagram_type="mindmap", paths=[result.get("error", "unknown error")]
        )
    except Exception as e:
        logger.warning("Markmap render failed: %s", e)
        return VizOutput(success=False, format="html", diagram_type="mindmap")


def _render_quality_dashboard(output_path: str | Path | None = None) -> VizOutput:
    try:
        from lib.visual_dashboard import generate_quality_dashboard

        path = generate_quality_dashboard(output_path=output_path)
        return VizOutput(success=True, paths=[path], format="html", diagram_type="quality-dashboard")
    except Exception as e:
        logger.warning("Quality dashboard generation failed: %s", e)
        return VizOutput(success=False, format="html", diagram_type="quality-dashboard")


def _render_knowledge_graph(graph=None, output_path: str | Path | None = None) -> VizOutput:
    try:
        from lib.knowledge_graph_viz import generate as kg_generate

        path = kg_generate(output_path=output_path, graph=graph)
        return VizOutput(success=True, paths=[path], format="html", diagram_type="knowledge-graph")
    except Exception as e:
        logger.warning("Knowledge graph generation failed: %s", e)
        return VizOutput(success=False, format="html", diagram_type="knowledge-graph")


def orchestrate_pdf(agent: str, data: dict, output_path: str | None = None) -> VizOutput:
    """Generate PDF report for agent.

    Args:
        agent: Agent name (aletheia, kosmos, metis, kratos, mnemosyne, kronos)
        data: Report data dict (title, sections, charts, etc.)
        output_path: Optional custom output path

    Returns:
        VizOutput with PDF path
    """
    if not is_enabled("use_pdf_reports"):
        return VizOutput(success=False, agent=agent, format="pdf")

    try:
        from lib.pdf_report_generator import generate_report

        path = generate_report(agent, data, output_path)
        return VizOutput(success=True, paths=[path], format="pdf", agent=agent)
    except Exception as e:
        logger.warning("PDF report generation failed: %s", e)
        return VizOutput(success=False, agent=agent, format="pdf")


def orchestrate(
    agent: str,
    data: dict | None = None,
    output_path: str | Path | None = None,
) -> VizOutput:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = DASHBOARD_DIR

    agent = agent.lower().strip()
    typed_data = _parse_agent_data(agent, data)

    if agent == "kosmos":
        return _orchestrate_kosmos(typed_data, output_path)
    elif agent == "metis":
        return _orchestrate_metis(typed_data, output_path)
    elif agent == "mnemosyne":
        return _orchestrate_mnemosyne(typed_data, output_path)
    elif agent == "aletheia":
        return _orchestrate_aletheia(typed_data, output_path)
    elif agent == "kratos":
        return _orchestrate_kratos(typed_data, output_path)
    else:
        logger.warning("Unknown agent: %s", agent)
        return VizOutput(success=False, agent=agent)


def _orchestrate_kosmos(data: KosmosData | None, output_path: str | Path) -> VizOutput:
    result = VizOutput(success=True, agent="kosmos", format="html")

    if is_enabled("use_kroki_diagrams") and data and data.adr_content:
        out = _render_kroki("structurizr", data.adr_content)
        if out.success:
            result.paths.extend(out.paths)

    return result


def _orchestrate_metis(data: MetisData | None, output_path: str | Path) -> VizOutput:
    result = VizOutput(success=True, agent="metis", format="html")

    if is_enabled("use_kroki_diagrams") and data and data.domain_clusters:
        out = _render_kroki("graphviz", data.domain_clusters)
        if out.success:
            result.paths.extend(out.paths)

    return result


def _orchestrate_mnemosyne(data: MnemosyneData | None, output_path: str | Path) -> VizOutput:
    result = VizOutput(success=True, agent="mnemosyne", format="html")

    if is_enabled("use_plotly_dashboard"):
        out = _render_quality_dashboard(output_path=output_path / "quality-dashboard.html")
        if out.success:
            result.paths.extend(out.paths)

    if is_enabled("use_cytoscape_graph"):
        out = _render_knowledge_graph(output_path=output_path / "knowledge-graph.html")
        if out.success:
            result.paths.extend(out.paths)

    if is_enabled("use_markmap_mindmaps") and data and data.curation_phases:
        out = _render_markmap(data.curation_phases)
        if out.success:
            result.paths.extend(out.paths)

    return result


def _orchestrate_aletheia(data: AletheiaData | None, output_path: str | Path) -> VizOutput:
    result = VizOutput(success=True, agent="aletheia", format="html")

    if is_enabled("use_markmap_mindmaps") and data and data.research_tree:
        out = _render_markmap(data.research_tree)
        if out.success:
            result.paths.extend(out.paths)

    return result


def _orchestrate_kratos(data: KratosData | None, output_path: str | Path) -> VizOutput:
    result = VizOutput(success=True, agent="kratos", format="html")

    if is_enabled("use_kroki_diagrams") and data and data.code_flow:
        out = _render_kroki("blockdiag", data.code_flow)
        if out.success:
            result.paths.extend(out.paths)

    return result
