"""Smoke test for Fase 1 UA — verify all new modules import and have expected interfaces."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_incremental_imports():
    from lib import incremental

    assert hasattr(incremental, "hash_file")
    assert hasattr(incremental, "detect_changed_files")
    assert hasattr(incremental, "get_modified_files")
    assert hasattr(incremental, "git_changed_files")


def test_knowledge_tour_imports():
    from lib import knowledge_tour

    assert hasattr(knowledge_tour, "topological_layers")
    assert hasattr(knowledge_tour, "detect_cycles")
    assert hasattr(knowledge_tour, "generate_tour")


def test_domain_mapper_imports():
    from lib import domain_mapper

    assert hasattr(domain_mapper, "extract_node_features")
    assert hasattr(domain_mapper, "cluster_nodes")
    assert hasattr(domain_mapper, "generate_report")


def test_feature_flags_new():
    from lib.feature_flags import DEFAULT_FLAGS, is_enabled

    for flag in ("use_incremental_analysis", "use_enhanced_parallelism", "use_knowledge_tour", "use_domain_mapper"):
        assert flag in DEFAULT_FLAGS
        assert is_enabled(flag) is True


def test_config_phase_b_workers():
    from lib.config import PHASE_B_WORKERS

    assert PHASE_B_WORKERS >= 1


def test_mnemosyne_incremental_keys():
    import inspect

    from lib.agent_nodes.mnemosyne import _mnemosyne_node_impl

    source = inspect.getsource(_mnemosyne_node_impl)
    assert "incremental" in source
    assert "files_skipped" in source
    assert "files_processed" in source


def test_mnemosyne_enhanced_parallelism():
    import inspect

    from lib.agent_nodes.mnemosyne import _mnemosyne_node_impl

    source = inspect.getsource(_mnemosyne_node_impl)
    assert "use_enhanced_parallelism" in source
    assert "PHASE_B_WORKERS" in source


def test_knowledge_tour_algorithms():
    import networkx as nx
    from lib.knowledge_tour import detect_cycles, topological_layers

    G = nx.DiGraph()
    G.add_edge("A", "B")
    G.add_edge("B", "C")
    layers = topological_layers(G)
    assert layers == [["A"], ["B"], ["C"]]
    cycles = detect_cycles(G)
    assert cycles == []


def test_domain_mapper_empty():
    from lib.domain_mapper import extract_node_features

    features = extract_node_features({"nodes": [], "edges": []})
    assert features == []
