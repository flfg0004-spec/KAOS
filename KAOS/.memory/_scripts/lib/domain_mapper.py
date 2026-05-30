"""Domain Mapper — clusters technical architecture components into business domain contexts.

Uses txtai embeddings for semantic clustering of arch_graph nodes,
with rule-based fallback when txtai is unavailable.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "wiki" / "reports"


def _ensure_reports_dir():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _load_graph() -> dict:
    graph_file = Path(__file__).resolve().parent.parent.parent / "cache" / "arch-graph" / "graph.json"
    if graph_file.exists():
        try:
            return json.loads(graph_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to load arch graph: %s", e)
    return {"nodes": [], "edges": []}


def extract_node_features(graph_data: dict = None) -> list[dict]:
    """Extract feature vectors from arch_graph nodes for clustering."""
    if graph_data is None:
        graph_data = _load_graph()

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    edge_count_map: dict[str, int] = {}
    connected_to_map: dict[str, list[str]] = {}
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        edge_count_map[src] = edge_count_map.get(src, 0) + 1
        connected_to_map.setdefault(src, []).append(tgt)

    features = []
    for n in nodes:
        nid = n.get("id", "")
        props = n.get("properties", {}) or {}
        prop_text = " ".join(str(v) for v in props.values() if isinstance(v, str)) if isinstance(props, dict) else ""
        features.append(
            {
                "node_id": nid,
                "node_type": n.get("type", "unknown"),
                "properties": props,
                "edge_count": edge_count_map.get(nid, 0),
                "connected_to": connected_to_map.get(nid, []),
                "property_text": prop_text,
            }
        )

    return features


def _fallback_cluster(features: list[dict], n_clusters: int = 4) -> list[int]:
    """Rule-based clustering fallback when txtai is unavailable — group by node_type."""
    type_order = sorted({f["node_type"] for f in features})
    type_to_cluster = {t: i % max(n_clusters, 1) for i, t in enumerate(type_order)}
    return [type_to_cluster[f["node_type"]] for f in features]


def compute_embeddings(features: list[dict]) -> list[list[float]]:
    """Compute embeddings via txtai MCP subprocess."""
    import os

    if os.environ.get("KAOS_TESTING") == "1":
        return []
    import subprocess
    import sys

    texts = [(f["node_id"] + " " + f["property_text"]).strip() or f["node_id"] for f in features]
    if not texts:
        return []
    mcp_embed = Path(__file__).resolve().parent / ".." / "mcp_embed.py"
    req = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "embed", "arguments": {"texts": texts}}}
    )
    try:
        r = subprocess.run([sys.executable, str(mcp_embed)], input=req, capture_output=True, text=True, timeout=30)
        if r.returncode == 0 and r.stdout.strip():
            resp = json.loads(r.stdout.strip())
            content = resp.get("result", {}).get("content", [])
            if content:
                return json.loads(content[0]["text"])
    except Exception as e:
        logger.warning("txtai embedding failed: %s", e)
    return []


def cluster_nodes(features: list[dict], n_clusters: int = 4, embeddings: list[list[float]] | None = None) -> list[int]:
    """Cluster feature vectors into n_clusters groups using K-Means."""
    [f["property_text"] for f in features]

    if embeddings is None:
        embeddings = compute_embeddings(features)

    if embeddings and len(embeddings) == len(features):
        try:
            import numpy as np
            from sklearn.cluster import KMeans

            n = min(n_clusters, len(set(tuple(e) for e in embeddings)))
            n = max(n, 1)
            kmeans = KMeans(n_clusters=n, random_state=42, n_init="auto")
            labels = kmeans.fit_predict(np.array(embeddings))
            return labels.tolist()
        except Exception as e:
            logger.warning("K-Means failed: %s — falling back to rule-based", e)

    return _fallback_cluster(features, n_clusters)


def name_clusters(features: list[dict], labels: list[int]) -> dict[int, str]:
    """Assign descriptive names to each cluster based on dominant node types."""
    cluster_data: dict[int, list[str]] = {}
    for f, l in zip(features, labels, strict=False):
        cluster_data.setdefault(l, []).append(f["node_type"])

    names: dict[int, str] = {}
    for cid, types in cluster_data.items():
        from collections import Counter

        counter = Counter(types)
        dominant = counter.most_common(1)[0][0]
        total = len(types)
        names[cid] = f"{dominant.capitalize()} ({total} nodes)"

    return names


def generate_report(
    features: list[dict],
    labels: list[int],
    cluster_names: dict[int, str],
    output_path: str | Path | None = None,
    title: str = "Architecture Domain Map",
) -> str:
    """Generate a markdown report with bounded contexts, dependency matrix, and glossary."""
    n_clusters = len(set(labels))
    slug = title.lower().replace(" ", "-")[:40]
    output_path = REPORTS_DIR / f"domain-map-{slug}.md" if output_path is None else Path(output_path)

    dep_matrix: dict[int, dict[int, int]] = {i: {j: 0 for j in range(n_clusters)} for i in range(n_clusters)}
    for f, l in zip(features, labels, strict=False):
        for conn in f["connected_to"]:
            for other_f, other_l in zip(features, labels, strict=False):
                if other_f["node_id"] == conn and other_l != l:
                    dep_matrix[l][other_l] = dep_matrix.get(l, {}).get(other_l, 0) + 1

    cluster_members: dict[int, list[dict]] = {}
    for f, l in zip(features, labels, strict=False):
        cluster_members.setdefault(l, []).append(f)

    lines = []
    lines.append("---")
    lines.append("type: report")
    lines.append(f"title: {title}")
    lines.append(f"generated: '{datetime.now().strftime('%Y-%m-%d %H:%M')}'")
    lines.append(f"clusters: {n_clusters}")
    lines.append(f"total_nodes: {len(features)}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"*Auto-generated domain map — {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")
    lines.append("## Bounded Contexts")
    lines.append("")

    cluster_colors = ["#e1f5fe", "#e8f5e9", "#fff3e0", "#fce4ec", "#f3e5f5", "#e0f7fa", "#fff8e1", "#fbe9e7"]
    lines.append("```mermaid")
    lines.append("graph TD")
    for cid in sorted(cluster_members):
        color = cluster_colors[cid % len(cluster_colors)]
        label = cluster_names.get(cid, f"Context {cid}")
        member_ids = [m["node_id"] for m in cluster_members[cid]]
        lines.append(f'    subgraph C{cid}["{label}"]')
        for mid in member_ids:
            lines.append(f"        {mid}")
        lines.append("    end")
        lines.append(f"    style C{cid} fill:{color},stroke:#333,stroke-width:2px")
    for f, l in zip(features, labels, strict=False):
        for conn in f["connected_to"]:
            for other_f, other_l in zip(features, labels, strict=False):
                if other_f["node_id"] == conn and other_l != l:
                    lines.append(f"    {f['node_id']} -->|depends_on| {conn}")
    lines.append("```")
    lines.append("")

    lines.append("## Bounded Contexts Detail")
    lines.append("")
    for cid in sorted(cluster_members):
        name = cluster_names.get(cid, f"Context {cid}")
        lines.append(f"### {name}")
        lines.append("")
        lines.append("| Component | Type | Edges | Connected To |")
        lines.append("|-----------|------|-------|-------------|")
        for m in cluster_members[cid]:
            conn_str = ", ".join(m["connected_to"][:5])
            if len(m["connected_to"]) > 5:
                conn_str += "..."
            lines.append(f"| {m['node_id']} | {m['node_type']} | {m['edge_count']} | {conn_str or '-'} |")
        lines.append("")

    lines.append("## Inter-Context Dependency Matrix")
    lines.append("")
    headers = "| | " + " | ".join(cluster_names.get(i, f"C{i}") for i in range(n_clusters)) + " |"
    sep = "|---|" + "---|" * n_clusters
    lines.append(headers)
    lines.append(sep)
    for i in range(n_clusters):
        row = f"| **{cluster_names.get(i, f'C{i}')}** |"
        for j in range(n_clusters):
            val = dep_matrix.get(i, {}).get(j, 0)
            row += f" {val} |"
        lines.append(row)
    lines.append("")

    high_coupling = []
    for i in range(n_clusters):
        for j in range(n_clusters):
            if i != j and dep_matrix.get(i, {}).get(j, 0) > 2:
                high_coupling.append((i, j, dep_matrix[i][j]))
    if high_coupling:
        lines.append("### ⚠️ High Coupling Detected")
        lines.append("")
        for i, j, count in sorted(high_coupling, key=lambda x: -x[2]):
            lines.append(
                f"- **{cluster_names.get(i, f'C{i}')}** → **{cluster_names.get(j, f'C{j}')}**: {count} dependencies"
            )
        lines.append("")

    lines.append("## Glossary")
    lines.append("")
    lines.append("| Technical Term | Business Meaning |")
    lines.append("|---------------|-----------------|")
    all_types = sorted({f["node_type"] for f in features})
    type_biz_map = {
        "adr": "Architecture decision — why the system is built this way",
        "component": "System module or service",
        "decision": "Specific technical choice made",
        "smell": "Potential quality concern to review",
        "pattern": "Reusable architectural pattern in use",
        "agent_output": "AI-generated analysis or report",
    }
    for t in all_types:
        biz = type_biz_map.get(t, t.replace("_", " "))
        lines.append(f"| {t} | {biz} |")
    lines.append("")

    lines.append("---")
    lines.append("*Generated by Domain Mapper*")

    md = "\n".join(lines)
    _ensure_reports_dir()
    output_path.write_text(md, encoding="utf-8")
    logger.info("Domain map written to %s (%d clusters, %d nodes)", output_path, n_clusters, len(features))
    return md
