"""Knowledge Gap Detection for the vault.

Identifies missing notes by analyzing:
  1. Structural gaps: paths of length 2 where a middle node is missing
  2. Topic gaps: clusters with high internal cohesion but low external linking
  3. Information sinks: nodes with high in-degree but zero out-degree
  4. Source orphans: nodes with high out-degree but zero in-degree
"""

import re
from pathlib import Path
from collections import defaultdict

import networkx as nx
from lib.wikilinks import build_graph
from lib.graph_analysis import VaultGraph

BASE = (Path(__file__).resolve().parent.parent.parent)


class GapDetector:
    """Detects knowledge gaps in the vault graph topology."""

    def __init__(self, page_map: dict = None):
        self.page_map = page_map or build_graph()
        self.vg = VaultGraph(self.page_map)
        self.graph = self.vg.graph

    def structural_gaps(self) -> list[dict]:
        """Find structural gaps: A→C exists but a concept B logically fits between them.

        Algorithm: for each edge A→C, check if there exists a node B such that
        A→B→C would form a more complete path (B shares significant content overlap with both).
        """
        gaps = []
        if self.graph.number_of_edges() < 2:
            return gaps

        for a, c in self.graph.edges():
            a_content = self.page_map.get(a, {}).get("content", "")
            c_content = self.page_map.get(c, {}).get("content", "")

            for b in self.graph.nodes():
                if b == a or b == c:
                    continue
                if self.graph.has_edge(a, b) or self.graph.has_edge(b, c):
                    continue

                b_content = self.page_map.get(b, {}).get("content", "")
                if not a_content or not b_content or not c_content:
                    continue

                ab_overlap = _token_overlap(a_content, b_content)
                bc_overlap = _token_overlap(b_content, c_content)

                if ab_overlap > 0.15 and bc_overlap > 0.15:
                    avg_score = (ab_overlap + bc_overlap) / 2
                    if avg_score > 0.2:
                        gaps.append({
                            "type": "structural_gap",
                            "from": a,
                            "to": c,
                            "missing": b,
                            "confidence": round(avg_score, 3),
                            "reason": f"'{b}' comparte vocabulario con '{a}' ({ab_overlap:.1%}) "
                                      f"y con '{c}' ({bc_overlap:.1%})",
                        })
        return sorted(gaps, key=lambda x: -x["confidence"])

    def topic_islands(self) -> list[dict]:
        """Detect clusters that lack bridging connections to other topic areas."""
        undirected = self.graph.to_undirected()
        try:
            from networkx.algorithms.community import louvain_communities
            communities = louvain_communities(undirected, seed=42)
        except Exception:
            return []

        islands = []
        for i, comm in enumerate(communities):
            comm_set = set(comm)
            external_edges = 0
            for node in comm:
                for neighbor in self.graph.successors(node):
                    if neighbor not in comm_set:
                        external_edges += 1
                for neighbor in self.graph.predecessors(node):
                    if neighbor not in comm_set:
                        external_edges += 1

            if external_edges == 0 and len(comm) > 1:
                islands.append({
                    "type": "topic_island",
                    "id": i,
                    "size": len(comm),
                    "members": sorted(comm),
                    "external_edges": 0,
                    "suggestion": "Crear notas puente que conecten este cluster con el grafo principal",
                })
        return sorted(islands, key=lambda x: -x["size"])

    def information_sinks(self) -> list[dict]:
        """Nodes that receive many links but don't link out (knowledge dead-ends)."""
        sinks = []
        for node in self.graph.nodes():
            in_deg = self.graph.in_degree(node)
            out_deg = self.graph.out_degree(node)
            if in_deg >= 3 and out_deg == 0 and node not in {"index", "log"}:
                sinks.append({
                    "type": "information_sink",
                    "node": node,
                    "in_degree": in_deg,
                    "suggestion": f"Añadir enlaces salientes desde '{node}' hacia conceptos relacionados",
                })
        return sorted(sinks, key=lambda x: -x["in_degree"])

    def source_orphans(self) -> list[dict]:
        """Nodes that link out heavily but receive no backlinks (unreferenced sources)."""
        orphans = []
        for node in self.graph.nodes():
            in_deg = self.graph.in_degree(node)
            out_deg = self.graph.out_degree(node)
            if out_deg >= 3 and in_deg == 0 and node not in {"index", "log"}:
                orphans.append({
                    "type": "source_orphan",
                    "node": node,
                    "out_degree": out_deg,
                    "suggestion": f"Agregar [[{node}]] en otras notas para que sea referenciado",
                })
        return sorted(orphans, key=lambda x: -x["out_degree"])

    def topic_bridge_gaps(self) -> list[dict]:
        """Find pairs of communities that should be connected via a bridge note."""
        undirected = self.graph.to_undirected()
        try:
            from networkx.algorithms.community import louvain_communities
            communities = list(louvain_communities(undirected, seed=42))
        except Exception:
            return []

        if len(communities) < 2:
            return []

        bridges = []
        for i in range(len(communities)):
            for j in range(i + 1, len(communities)):
                ci, cj = communities[i], communities[j]
                ci_set, cj_set = set(ci), set(cj)

                cross_edges = 0
                for node in ci:
                    for neighbor in self.graph.successors(node):
                        if neighbor in cj_set:
                            cross_edges += 1

                if cross_edges == 0:
                    ci_topics = _common_topics([self.page_map.get(n, {}).get("content", "") for n in ci])
                    cj_topics = _common_topics([self.page_map.get(n, {}).get("content", "") for n in cj])
                    shared = set(ci_topics) & set(cj_topics)

                    bridges.append({
                        "type": "bridge_gap",
                        "community_a": i,
                        "community_b": j,
                        "size_a": len(ci),
                        "size_b": len(cj),
                        "shared_topics": list(shared)[:5],
                        "suggestion": f"Crear nota puente entre comunidad {i} y {j} "
                                      f"sobre temas compartidos: {', '.join(list(shared)[:3])}" if shared
                                      else f"Crear nota puente entre comunidad {i} y {j}",
                    })
        return bridges

    def suggest_gaps(self, min_confidence: float = 0.2) -> list[dict]:
        """Combined gap detection, deduplicated and ranked."""
        all_gaps = []
        all_gaps.extend(self.structural_gaps())
        all_gaps.extend(self.topic_islands())
        all_gaps.extend(self.information_sinks())
        all_gaps.extend(self.source_orphans())
        all_gaps.extend(self.topic_bridge_gaps())

        seen = set()
        unique = []
        for gap in all_gaps:
            key = f"{gap.get('type', '')}:{gap.get('node', gap.get('from', gap.get('id', '')))}"
            if key not in seen:
                seen.add(key)
                if gap.get("confidence", 1.0) >= min_confidence:
                    unique.append(gap)

        return sorted(unique, key=lambda x: -x.get("confidence", 1.0))


def _token_overlap(content_a: str, content_b: str) -> float:
    """Jaccard-style token overlap for content similarity."""
    tokens_a = set(re.findall(r"\w{4,}", content_a.lower()))
    tokens_b = set(re.findall(r"\w{4,}", content_b.lower()))
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def _common_topics(contents: list[str], top_n: int = 10) -> list[str]:
    """Extract most common significant words across a set of contents."""
    word_counts = defaultdict(int)
    for content in contents:
        words = re.findall(r"\w{4,}", content.lower())
        for w in words:
            word_counts[w] += 1
    sorted_words = sorted(word_counts.items(), key=lambda x: -x[1])
    return [w for w, c in sorted_words[:top_n]]


def report(min_confidence: float = 0.2) -> str:
    """Generate a human-readable gap report."""
    detector = GapDetector()
    gaps = detector.suggest_gaps(min_confidence=min_confidence)

    lines = [
        "# Knowledge Gap Report",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        f"**Total gaps found: {len(gaps)}**",
        "",
    ]

    structural = [g for g in gaps if g["type"] == "structural_gap"]
    if structural:
        lines.append("## Structural Gaps\n")
        for g in structural[:10]:
            lines.append(f"- **{g['missing']}** entre '{g['from']}' y '{g['to']}' "
                         f"(confianza: {g['confidence']})")
            if g.get("reason"):
                lines.append(f"  - {g['reason']}")
        lines.append("")

    islands = [g for g in gaps if g["type"] == "topic_island"]
    if islands:
        lines.append("## Topic Islands\n")
        for g in islands[:5]:
            members = ", ".join(g["members"][:8])
            lines.append(f"- Cluster de {g['size']} notas sin conexión externa: {members}")
            lines.append(f"  - Sugerencia: {g['suggestion']}")
        lines.append("")

    sinks = [g for g in gaps if g["type"] == "information_sink"]
    if sinks:
        lines.append("## Information Sinks\n")
        for g in sinks[:10]:
            lines.append(f"- '{g['node']}' ({g['in_degree']} backlinks, 0 outbound)")
            lines.append(f"  - Sugerencia: {g['suggestion']}")
        lines.append("")

    orphans = [g for g in gaps if g["type"] == "source_orphan"]
    if orphans:
        lines.append("## Source Orphans\n")
        for g in orphans[:10]:
            lines.append(f"- '{g['node']}' ({g['out_degree']} outbound, 0 backlinks)")
            lines.append(f"  - Sugerencia: {g['suggestion']}")
        lines.append("")

    bridges = [g for g in gaps if g["type"] == "bridge_gap"]
    if bridges:
        lines.append("## Bridge Gaps\n")
        for g in bridges[:5]:
            topics = ", ".join(g["shared_topics"][:3]) if g["shared_topics"] else "temas diversos"
            lines.append(f"- Comunidad {g['community_a']} ({g['size_a']} notas) ↔ "
                         f"Comunidad {g['community_b']} ({g['size_b']} notas)")
            lines.append(f"  - Temas compartidos: {topics}")
            lines.append(f"  - Sugerencia: {g['suggestion']}")
        lines.append("")

    if not gaps:
        lines.append("No se detectaron gaps de conocimiento.")
        lines.append("")

    lines.append("---")
    lines.append(f"**Total: {len(gaps)} gaps** | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    return "\n".join(lines)
