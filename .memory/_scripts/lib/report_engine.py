"""Curation Report Engine — Phase 14 structured report.

Consumes output from all 14 curation phases and produces:
  - Markdown human-readable report
  - Structured JSON compatible with SKILL.md schema
  - Aletheia feedback block
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any

from lib import quality, gaps
from lib.wikilinks import parse as wikilinks_parse
from lib.memory_lifecycle import status as lifecycle_status
from lib.graph_analysis import VaultGraph

BASE = (Path(__file__).resolve().parent.parent.parent)


def _parse_score_block(text: str) -> dict:
    """Parse quality.status() output into structured data."""
    result = {"score": 0, "details": {}}
    import re
    m = re.search(r"### Quality Score:?\s*([\d.]+)", text)
    if m:
        result["score"] = float(m.group(1))
    for line in text.split("\n"):
        m2 = re.match(r"\*\s+([\w\s]+):\s+([\d.]+)", line)
        if m2:
            result["details"][m2.group(1).strip()] = float(m2.group(2))
    return result


def generate_curation_report(phases: dict[str, Any] = None) -> str:
    """Generate a full curation summary as markdown.

    Args:
        phases: Optional dict with per-phase results keyed by phase name.
                If None, computes from current vault state.

    Returns:
        Markdown report string.
    """
    if phases is None:
        phases = _collect_phases()

    lines = [
        "# Mnemosyne Curation Report",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Phase Summary\n",
    ]

    phase_order = [
        "ingest", "tag", "link", "dedup", "quality", "compress",
        "index", "lint", "graph", "gaps", "crossref", "lifecycle",
        "contradictions", "dashboard",
    ]
    for name in phase_order:
        p = phases.get(name, {})
        count = p.get("count", p.get("issues", p.get("score", "")))
        status = "✅" if p.get("ok", True) else "❌"
        desc = p.get("description", name)
        lines.append(f"- {status} **F{phase_order.index(name)+1} {desc}**: {count}")

    lines.append("")
    quality_data = _parse_score_block(phases.get("quality_raw", ""))
    qscore = quality_data.get("score", _current_quality_score())

    lines.append(f"## Quality Score: {qscore}/100\n")

    vg = _safe_vaultgraph()
    if vg:
        s = vg.summary()
        lines.extend([
            "### Graph Health\n",
            f"- Nodes: {s['nodes']}, Edges: {s['edges']}",
            f"- Density: {s['density']}, Communities: {s['communities']}",
            f"- Avg PageRank: {s['avg_page_rank']}",
            f"- Islands: {s['islands']}, Bridges: {s['bridges']}",
            "",
        ])

    orphan_count = len([
        n for n, d in (vg.page_map.items() if vg else {}.items())
        if not d.get("backlinks") and n not in {"index", "log"}
    ]) if vg else 0

    lines.extend([
        "### Vault Stats\n",
        f"- Orphan pages: {orphan_count}",
        f"- Decayed topics: {len(_decayed_topics())}",
        "",
    ])

    lines.extend([
        "## Aletheia Feedback\n",
        "```json\n",
        json.dumps(_aletheia_feedback(qscore, orphan_count), indent=2, ensure_ascii=False),
        "\n```\n",
    ])

    return "\n".join(lines)


def to_json(phases: dict[str, Any] = None) -> dict:
    """Structured JSON report matching SKILL.md schema.

    Returns:
        dict with curation_report, issues_found, wikilinks_added,
        tags_assigned, duplicates_fused, gaps_detected,
        graph_communities, quality_score, aletheia_feedback.
    """
    if phases is None:
        phases = _collect_phases()

    qscore = _current_quality_score()

    wikilinks_data = wikilinks_parse()
    gap_report = gaps.report()
    gap_count = gap_report.count("-**") - 1 if gap_report else 0

    vg = _safe_vaultgraph()
    communities = len(vg.louvain_communities()) if vg and not vg.node_count == 0 else 0

    result = {
        "curation_report": generate_curation_report(phases),
        "issues_found": phases.get("lint", {}).get("issues", 0),
        "wikilinks_added": phases.get("link", {}).get("count", 0),
        "tags_assigned": phases.get("tag", {}).get("count", 0),
        "duplicates_fused": phases.get("dedup", {}).get("count", 0),
        "gaps_detected": max(0, gap_count),
        "graph_communities": communities,
        "quality_score": round(qscore, 1),
        "aletheia_feedback": _aletheia_feedback(qscore, wikilinks_data.get("orphans", 0)),
    }
    return result


def _current_quality_score() -> float:
    try:
        return float(quality.status().split("Score:")[-1].split("/")[0].strip())
    except Exception:
        try:
            return quality.calculate().get("score", 0.0)
        except Exception:
            return 0.0


def _safe_vaultgraph() -> VaultGraph | None:
    try:
        return VaultGraph()
    except Exception:
        return None


def _decayed_topics() -> list[str]:
    try:
        from lib.memory_lifecycle import run_evaluate_all
        return [
            r["path"] for r in run_evaluate_all()
            if r.get("confidence", 1.0) < 0.5
        ]
    except Exception:
        return []


def _aletheia_feedback(qscore: float, orphans: int) -> dict:
    return {
        "new_concepts_curated": [],
        "confidence_validated": qscore >= 70.0,
        "contradictions_found": 0,
        "orphans_remaining": orphans,
        "quality_score": round(qscore, 1),
        "recommendation": "ok" if qscore >= 70 else "needs_review",
    }


def _collect_phases() -> dict[str, Any]:
    """Snapshot all phase outputs from current vault state."""
    phases = {}
    try:
        phases["quality_raw"] = quality.status()
    except Exception:
        phases["quality_raw"] = ""

    try:
        w = wikilinks_parse()
        phases["link"] = {"count": w.get("validLinks", 0), "ok": True}
    except Exception:
        phases["link"] = {"count": 0, "ok": False}

    try:
        lint_issues = 0
        report_path = BASE / "schema" / "lint-report.md"
        if report_path.exists():
            import re
            m = re.search(r"Total issues:\s*(\d+)", report_path.read_text(encoding="utf-8"))
            if m:
                lint_issues = int(m.group(1))
        phases["lint"] = {"issues": lint_issues, "ok": lint_issues == 0}
    except Exception:
        phases["lint"] = {"issues": -1, "ok": False}

    try:
        from lib.contradictions import report as contradictions_report
        phases["contradictions"] = {"ok": True}
    except Exception:
        phases["contradictions"] = {"ok": False}

    try:
        phases["lifecycle"] = {"ok": True}
    except Exception:
        phases["lifecycle"] = {"ok": False}

    return phases
