"""Tests for lib.graph_analysis (F2 topological graph analysis)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_test_page_map():
    """Create a simple 5-node graph:
    A → B → C
    A → D
    D → C
    E (isolated)
    """
    return {
        "A": {"path": "wiki/concepts/a.md", "headings": ["A"], "links": [{"target": "B", "section": ""}, {"target": "D", "section": ""}], "backlinks": []},
        "B": {"path": "wiki/concepts/b.md", "headings": ["B"], "links": [{"target": "C", "section": ""}], "backlinks": ["A"]},
        "C": {"path": "wiki/concepts/c.md", "headings": ["C"], "links": [], "backlinks": ["B", "D"]},
        "D": {"path": "wiki/concepts/d.md", "headings": ["D"], "links": [{"target": "C", "section": ""}], "backlinks": ["A"]},
        "E": {"path": "wiki/concepts/e.md", "headings": ["E"], "links": [], "backlinks": []},
    }


def test_vaultgraph_creation():
    from lib.graph_analysis import VaultGraph
    vg = VaultGraph(_make_test_page_map())
    assert vg.node_count == 5
    assert vg.edge_count == 4


def test_page_rank():
    from lib.graph_analysis import VaultGraph
    vg = VaultGraph(_make_test_page_map())
    pr = vg.page_rank(top_k=5)
    assert len(pr) == 5
    # A is source, C is sink — C should have higher PageRank (authority)
    pr_map = {n["node"]: n["score"] for n in pr}
    assert pr_map.get("C", 0) >= pr_map.get("A", 0), "Sink node C should have higher PageRank than source A"


def test_louvain_communities():
    from lib.graph_analysis import VaultGraph
    vg = VaultGraph(_make_test_page_map())
    communities = vg.louvain_communities()
    assert len(communities) >= 1
    total_members = sum(c["size"] for c in communities)
    assert total_members == 5


def test_betweenness_centrality():
    from lib.graph_analysis import VaultGraph
    vg = VaultGraph(_make_test_page_map())
    bc = vg.betweenness_centrality(top_k=5)
    assert len(bc) <= 5
    for entry in bc:
        assert "node" in entry
        assert "score" in entry
        assert 0 <= entry["score"] <= 1


def test_hub_scores():
    from lib.graph_analysis import VaultGraph
    vg = VaultGraph(_make_test_page_map())
    hubs = vg.hub_scores(top_k=3)
    assert len(hubs) >= 1
    # Should return at least 1 hub
    assert len(hubs) >= 1
    for h in hubs:
        assert "node" in h
        assert "score" in h


def test_cluster_islands():
    from lib.graph_analysis import VaultGraph
    vg = VaultGraph(_make_test_page_map())
    islands = vg.cluster_islands()
    assert len(islands) >= 1
    assert islands[0]["members"] == ["E"]


def test_in_out_ratio():
    from lib.graph_analysis import VaultGraph
    vg = VaultGraph(_make_test_page_map())
    ratio = vg.in_out_ratio()
    assert "avg_in_degree" in ratio
    assert "avg_out_degree" in ratio
    assert "info_sinks" in ratio
    assert "source_orphans" in ratio


def test_summary():
    from lib.graph_analysis import VaultGraph
    vg = VaultGraph(_make_test_page_map())
    s = vg.summary()
    assert s["nodes"] == 5
    assert s["edges"] == 4
    assert s["communities"] >= 1
    assert s["islands"] >= 1


def test_analyze_convenience():
    from lib.graph_analysis import analyze
    result = analyze()
    assert "summary" in result
    assert "top_hubs" in result
    assert "top_bridges" in result
    assert "communities" in result
