"""Topological graph analysis for the knowledge vault.

Re-exports VaultGraph from lib.wikilinks for backward compatibility.
Additional convenience methods live here.
"""

from lib.wikilinks import VaultGraph

BASE = None  # legacy, kept for imports that reference graph_analysis.BASE


def analyze() -> dict:
    """Convenience: build graph and return full analysis."""
    vg = VaultGraph()
    try:
        return {
            "summary": vg.summary(),
            "top_hubs": vg.hub_scores(top_k=5),
            "top_bridges": vg.bridge_notes(),
            "communities": vg.louvain_communities()[:5],
            "islands": vg.cluster_islands(),
        }
    except Exception as e:
        return {"error": str(e)}
