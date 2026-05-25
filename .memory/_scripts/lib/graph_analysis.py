"""Topological graph analysis for the knowledge vault.
 
Computes PageRank, Louvain communities, Betweenness Centrality,
hub/bridge detection, and cluster isolation analysis using networkx.
Integrates with wikilinks.parse() for graph construction.
"""

import re
from pathlib import Path
from collections import Counter

try:
    import networkx as nx
except ImportError:
    nx = None

from lib.wikilinks import build_graph

BASE = (Path(__file__).resolve().parent.parent.parent)


class VaultGraph:
    """Directed graph of the vault with topological analysis methods."""

    def __init__(self, page_map: dict = None):
        if nx is None:
            raise ImportError("networkx is required for VaultGraph")
        self.page_map = page_map or build_graph()
        self.graph = self._build_digraph()

    def _build_digraph(self) -> nx.DiGraph:
        G = nx.DiGraph()
        for name, data in self.page_map.items():
            G.add_node(name, path=data["path"], headings=data["headings"])
        for name, data in self.page_map.items():
            for link in data["links"]:
                target = link["target"].replace(".md", "")
                if target in self.page_map:
                    G.add_edge(name, target)
        return G

    @property
    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    def page_rank(self, top_k: int = 10) -> list[dict]:
        """Top-K notes by PageRank (authoritative hubs)."""
        if self.node_count == 0:
            return []
        if self.node_count == 1:
            node = list(self.graph.nodes())[0]
            return [{"node": node, "score": 1.0, "path": self.page_map.get(node, {}).get("path", "")}]
        pr = nx.pagerank(self.graph, alpha=0.85)
        sorted_pr = sorted(pr.items(), key=lambda x: -x[1])
        return [
            {"node": n, "score": round(s, 4), "path": self.page_map.get(n, {}).get("path", "")}
            for n, s in sorted_pr[:top_k]
        ]

    def louvain_communities(self) -> list[dict]:
        """Detect communities using Louvain method on undirected projection."""
        if self.node_count < 2:
            return [{"error": "Need at least 2 nodes for community detection"}]
        undirected = self.graph.to_undirected()
        try:
            from networkx.algorithms.community import louvain_communities
            communities = louvain_communities(undirected, seed=42)
        except ImportError:
            return [{"error": "Louvain not available (networkx version)"}]
        except Exception:
            return [{"error": "Louvain community detection failed"}]

        results = []
        for i, comm in enumerate(communities):
            members = sorted(comm)
            internal_edges = undirected.subgraph(comm).number_of_edges()
            results.append({
                "id": i,
                "size": len(members),
                "members": members,
                "internal_edges": internal_edges,
                "density": round(internal_edges / max(len(members) * (len(members) - 1) / 2, 1), 3),
            })
        return sorted(results, key=lambda x: -x["size"])

    def betweenness_centrality(self, top_k: int = 10) -> list[dict]:
        """Top-K bridge notes by betweenness centrality."""
        bc = nx.betweenness_centrality(self.graph, k=min(top_k * 2, self.node_count), seed=42)
        sorted_bc = sorted(bc.items(), key=lambda x: -x[1])
        return [
            {"node": n, "score": round(s, 4), "path": self.page_map.get(n, {}).get("path", "")}
            for n, s in sorted_bc[:top_k]
        ]

    def hub_scores(self, top_k: int = 10) -> list[dict]:
        """Top-K hubs (high out-degree, link to many others)."""
        try:
            hubs, _ = nx.hits(self.graph, max_iter=100, tol=1e-6)
        except Exception:
            deg = dict(self.graph.out_degree())
            total = sum(deg.values()) or 1
            hubs = {n: d / total for n, d in deg.items()}
        sorted_h = sorted(hubs.items(), key=lambda x: -x[1])
        return [
            {"node": n, "score": round(s, 4), "out_degree": self.graph.out_degree(n)}
            for n, s in sorted_h[:top_k]
        ]

    def bridge_notes(self) -> list[dict]:
        """Notes that connect different communities (high betweenness, low community affinity)."""
        communities = self.louvain_communities()
        if not communities or "error" in communities[0]:
            return []

        comm_map = {}
        for comm in communities:
            for member in comm["members"]:
                comm_map[member] = comm["id"]

        bc = nx.betweenness_centrality(self.graph, k=min(30, self.node_count), seed=42)
        bridges = []
        for node, score in bc.items():
            if node not in comm_map:
                continue
            node_comm = comm_map[node]
            out_edges = list(self.graph.successors(node))
            cross_comm = sum(1 for t in out_edges if t in comm_map and comm_map[t] != node_comm)
            in_edges = list(self.graph.predecessors(node))
            cross_in = sum(1 for s in in_edges if s in comm_map and comm_map[s] != node_comm)
            if cross_comm + cross_in > 0:
                bridges.append({
                    "node": node,
                    "betweenness": round(score, 4),
                    "cross_out": cross_comm,
                    "cross_in": cross_in,
                    "community": node_comm,
                })

        return sorted(bridges, key=lambda x: -x["betweenness"])[:10]

    def cluster_islands(self) -> list[dict]:
        """Detect isolated subgraphs (clusters with 0 edges to main graph)."""
        undirected = self.graph.to_undirected()
        components = list(nx.connected_components(undirected))
        if not components:
            return []

        main = max(components, key=len)
        islands = []
        for comp in components:
            if comp is main:
                continue
            members = sorted(comp)
            subgraph = undirected.subgraph(comp)
            islands.append({
                "size": len(members),
                "members": members,
                "edges": subgraph.number_of_edges(),
                "density": round(nx.density(subgraph), 3),
            })
        return sorted(islands, key=lambda x: -x["size"])

    def in_out_ratio(self) -> dict:
        """Average in-degree and out-degree statistics."""
        in_deg = dict(self.graph.in_degree())
        out_deg = dict(self.graph.out_degree())
        in_vals = list(in_deg.values())
        out_vals = list(out_deg.values())
        info_sinks = [n for n, d in in_deg.items() if d >= 3 and out_deg.get(n, 0) == 0]
        source_orphans = [n for n, d in out_deg.items() if d >= 3 and in_deg.get(n, 0) == 0]
        return {
            "avg_in_degree": round(sum(in_vals) / max(len(in_vals), 1), 2),
            "avg_out_degree": round(sum(out_vals) / max(len(out_vals), 1), 2),
            "max_in_degree": max(in_vals) if in_vals else 0,
            "max_out_degree": max(out_vals) if out_vals else 0,
            "info_sinks": len(info_sinks),
            "info_sink_list": info_sinks[:10],
            "source_orphans": len(source_orphans),
            "source_orphan_list": source_orphans[:10],
        }

    def summary(self) -> dict:
        """Complete graph health summary."""
        try:
            pr = self.page_rank(top_k=3)
            communities = self.louvain_communities()
            islands = self.cluster_islands()
            bridges = self.bridge_notes()
            ratios = self.in_out_ratio()
        except Exception as e:
            return {"error": str(e)}

        avg_pr = round(sum(n["score"] for n in pr) / max(len(pr), 1), 4) if pr else 0
        return {
            "nodes": self.node_count,
            "edges": self.edge_count,
            "density": round(nx.density(self.graph), 4),
            "avg_page_rank": avg_pr,
            "communities": len(communities),
            "islands": len(islands),
            "bridges": len(bridges),
            "info_sinks": ratios["info_sinks"],
            "source_orphans": ratios["source_orphans"],
            "link_ratio": ratios["avg_out_degree"],
        }


def analyze() -> dict:
    """Convenience: build graph and return full analysis."""
    vg = VaultGraph()
    return {
        "summary": vg.summary(),
        "top_hubs": vg.hub_scores(top_k=5),
        "top_bridges": vg.bridge_notes(),
        "communities": vg.louvain_communities()[:5],
        "islands": vg.cluster_islands(),
    }
