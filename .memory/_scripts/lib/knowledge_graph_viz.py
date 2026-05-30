"""Cytoscape.js Knowledge Graph generator.

Converts VaultGraph (NetworkX) to Cytoscape.js JSON format and
injects it into an interactive HTML template for browser exploration.

Usage:
    from lib.knowledge_graph_viz import generate
    path = generate()
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent.parent
KAOS_ROOT = BASE.parent
DASHBOARD_DIR = KAOS_ROOT / ".memory" / "dashboard"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

COMMUNITY_COLORS = [
    "#38bdf8",
    "#a78bfa",
    "#f59e0b",
    "#22c55e",
    "#ef4444",
    "#ec4899",
    "#14b8a6",
    "#f97316",
    "#6366f1",
    "#84cc16",
    "#06b6d4",
    "#d946ef",
    "#10b981",
    "#eab308",
    "#64748b",
]


def _build_vault_graph():
    try:
        from lib.wikilinks import VaultGraph

        vg = VaultGraph()
        return vg
    except Exception as e:
        logger.warning("Could not build VaultGraph: %s", e)
        return None


def export_to_cytoscape(graph=None) -> dict:
    if graph is None:
        vg = _build_vault_graph()
        if vg is None:
            return {"elements": {"nodes": [], "edges": []}}
        graph = vg.graph
        page_map = vg.page_map
    else:
        page_map = {}

    if graph.number_of_nodes() == 0:
        return {"elements": {"nodes": [], "edges": []}}

    import networkx as nx

    try:
        pr = nx.pagerank(graph, alpha=0.85)
    except Exception:
        pr = {n: 1.0 / graph.number_of_nodes() for n in graph.nodes()}

    try:
        undirected = graph.to_undirected()
        from networkx.algorithms.community import louvain_communities

        communities = louvain_communities(undirected, seed=42)
        node_to_community = {}
        for i, comm in enumerate(communities):
            for node in comm:
                node_to_community[node] = i
    except Exception:
        node_to_community = {}

    weight_max = max(pr.values()) if pr else 1

    nodes = []
    for node in graph.nodes():
        score = pr.get(node, 0)
        community = node_to_community.get(node, 0)
        nodes.append(
            {
                "data": {
                    "id": str(node),
                    "label": str(node)[:40],
                    "weight": round(score / weight_max, 4) if weight_max > 0 else 0,
                    "community": community,
                    "color": COMMUNITY_COLORS[community % len(COMMUNITY_COLORS)],
                    "path": page_map.get(node, {}).get("path", ""),
                }
            }
        )

    edges = []
    for i, (source, target) in enumerate(graph.edges()):
        edges.append(
            {
                "data": {
                    "id": f"e{i}",
                    "source": str(source),
                    "target": str(target),
                    "weight": 1,
                }
            }
        )

    return {"elements": {"nodes": nodes, "edges": edges}}


def generate(output_path: str | Path | None = None, graph=None) -> str:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = DASHBOARD_DIR / "knowledge-graph.html"

    data = export_to_cytoscape(graph=graph)

    template_file = TEMPLATE_DIR / "knowledge-graph.html"
    template = template_file.read_text(encoding="utf-8") if template_file.exists() else _embedded_template()

    json_str = json.dumps(data, ensure_ascii=False)
    html = template.replace("const ELEMENTS = null;", f"const ELEMENTS = {json_str};")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")

    logger.info(
        "Knowledge graph generated: %s (nodes=%d, edges=%d)",
        output.resolve(),
        len(data["elements"]["nodes"]),
        len(data["elements"]["edges"]),
    )
    return str(output.resolve())


def _embedded_template() -> str:
    """Fallback template when file is missing."""
    return """<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>KAOS Knowledge Graph</title>
<script src="https://unpkg.com/cytoscape/dist/cytoscape.min.js"></script>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:system-ui,-apple-system,sans-serif; background:#0f172a; color:#e2e8f0; }
  #cy { width:100%; height:100vh; }
  .loading { display:flex; align-items:center; justify-content:center; height:100vh; color:#64748b; }
</style>
</head>
<body>
<div id="cy"><div class="loading">Cargando grafo…</div></div>
<script>
const ELEMENTS = %s;
function init() {
  if (!ELEMENTS || !ELEMENTS.elements || !ELEMENTS.elements.nodes || ELEMENTS.elements.nodes.length === 0) {
    document.getElementById("cy").innerHTML = '<div class="loading">Grafo vacío</div>'; return;
  }
  cytoscape({ container: document.getElementById("cy"), elements: ELEMENTS.elements,
    style: [
      { selector: "node", css: { "background-color": "#38bdf8", label: "data(label)", color: "#e2e8f0", "font-size": "10px" } },
      { selector: "edge", css: { "line-color": "#334155", "target-arrow-shape": "triangle", "curve-style": "bezier" } },
    ],
    layout: { name: "cose" },
  });
}
document.addEventListener("DOMContentLoaded", init);
</script>
</body>
</html>"""
