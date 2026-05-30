"""Tests for lib.domain_mapper — feature extraction, clustering, and report generation."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def _sample_graph():
    return {
        "nodes": [
            {"id": "adr-001", "type": "adr", "properties": {"title": "Memory System"}},
            {"id": "adr-002", "type": "adr", "properties": {"title": "Vector Store"}},
            {"id": "auth-service", "type": "component", "properties": {"language": "python"}},
            {"id": "api-gateway", "type": "component", "properties": {"language": "python"}},
            {"id": "use-postgres", "type": "decision", "properties": {}},
            {"id": "use-redis", "type": "decision", "properties": {}},
        ],
        "edges": [
            {"source": "adr-001", "target": "auth-service", "type": "references"},
            {"source": "adr-002", "target": "api-gateway", "type": "references"},
            {"source": "auth-service", "target": "use-postgres", "type": "depends_on"},
            {"source": "api-gateway", "target": "use-redis", "type": "depends_on"},
        ],
    }


def test_extract_node_features():
    from lib.domain_mapper import extract_node_features

    graph = _sample_graph()
    features = extract_node_features(graph)
    assert len(features) == 6
    for f in features:
        assert "node_id" in f
        assert "node_type" in f
        assert "edge_count" in f
        assert "connected_to" in f
    auth = [f for f in features if f["node_id"] == "auth-service"][0]
    assert auth["edge_count"] == 1


def test_extract_node_features_empty():
    from lib.domain_mapper import extract_node_features

    features = extract_node_features({"nodes": [], "edges": []})
    assert features == []


def test_fallback_cluster():
    from lib.domain_mapper import _fallback_cluster

    features = [
        {"node_id": "a", "node_type": "adr"},
        {"node_id": "b", "node_type": "adr"},
        {"node_id": "c", "node_type": "component"},
        {"node_id": "d", "node_type": "component"},
    ]
    labels = _fallback_cluster(features, n_clusters=4)
    assert len(labels) == 4
    assert labels[0] == labels[1]
    assert labels[2] == labels[3]


def test_cluster_nodes_fallback():
    from lib.domain_mapper import cluster_nodes

    features = [
        {
            "node_id": "a",
            "node_type": "adr",
            "property_text": "",
            "connected_to": [],
            "edge_count": 0,
            "properties": {},
        },
        {
            "node_id": "b",
            "node_type": "component",
            "property_text": "",
            "connected_to": [],
            "edge_count": 0,
            "properties": {},
        },
    ]
    labels = cluster_nodes(features, n_clusters=2)
    assert len(labels) == 2


def test_name_clusters():
    from lib.domain_mapper import name_clusters

    features = [
        {"node_id": "a", "node_type": "adr"},
        {"node_id": "b", "node_type": "adr"},
        {"node_id": "c", "node_type": "component"},
    ]
    labels = [0, 0, 1]
    names = name_clusters(features, labels)
    assert 0 in names
    assert 1 in names


def test_generate_report_contains_sections():
    from lib.domain_mapper import generate_report

    features = [
        {
            "node_id": "adr-001",
            "node_type": "adr",
            "edge_count": 1,
            "connected_to": ["auth-service"],
            "property_text": "Memory",
            "properties": {},
        },
        {
            "node_id": "auth-service",
            "node_type": "component",
            "edge_count": 0,
            "connected_to": [],
            "property_text": "Auth",
            "properties": {},
        },
    ]
    labels = [0, 0]
    cluster_names = {0: "Core (2 nodes)"}
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "test-domain.md"
        md = generate_report(features, labels, cluster_names, output_path=output, title="Test Map")
        assert "Test Map" in md
        assert "Bounded Contexts" in md
        assert "Inter-Context Dependency Matrix" in md
        assert "```mermaid" in md


def test_generate_report_empty():
    from lib.domain_mapper import generate_report

    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "empty-domain.md"
        md = generate_report([], [], {}, output_path=output, title="Empty")
        assert "Empty" in md
