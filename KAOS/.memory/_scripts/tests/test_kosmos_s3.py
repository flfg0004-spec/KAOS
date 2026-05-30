"""Integration tests for S3 endurecimiento: cache real, locks, Aletheia, paralelismo."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
os.environ["LLM_DIRECT_ENABLED"] = "false"
os.environ["KAOS_TESTING"] = "1"

def test_s3_cache_hit_miss():
    from lib.kosmos_node_v2 import KosmosPipelineV2
    topic = "s3 cache test"
    p1 = KosmosPipelineV2({"topic": topic, "cache_enabled": True, "parallel_enabled": False})
    r1 = p1.run_all()
    p2 = KosmosPipelineV2({"topic": topic, "cache_enabled": True, "parallel_enabled": False})
    r2 = p2.run_all()
    assert r2.get("cache_hit", False) or r2.get("cached", False), "Same topic should produce cache hit"

def test_s3_cache_miss_different_topic():
    from lib.kosmos_node_v2 import KosmosPipelineV2
    p1 = KosmosPipelineV2({"topic": "s3 cache miss A", "cache_enabled": True, "parallel_enabled": False})
    p1.run_all()
    p2 = KosmosPipelineV2({"topic": "s3 cache miss B", "cache_enabled": True, "parallel_enabled": False})
    r2 = p2.run_all()
    assert not r2.get("cache_hit", False), "Different topic should NOT produce cache hit"

def test_s3_cache_disabled():
    from lib.kosmos_node_v2 import KosmosPipelineV2
    p1 = KosmosPipelineV2({"topic": "s3 cache disabled", "cache_enabled": False, "parallel_enabled": False})
    r1 = p1.run_all()
    p2 = KosmosPipelineV2({"topic": "s3 cache disabled", "cache_enabled": False, "parallel_enabled": False})
    r2 = p2.run_all()
    assert not r2.get("cache_hit", False), "cache_enabled=False should never produce cache hit"

def test_s3_parallel_consistency():
    """Pipeline produce same results with parallel_enabled True vs False."""
    from lib.kosmos_node_v2 import KosmosPipelineV2
    topic = "s3 parallel consistency"
    p_seq = KosmosPipelineV2({"topic": topic, "parallel_enabled": False, "cache_enabled": False})
    r_seq = p_seq.run_all()
    p_par = KosmosPipelineV2({"topic": topic, "parallel_enabled": True, "cache_enabled": False})
    r_par = p_par.run_all()
    assert r_seq["nodes_executed"] == r_par["nodes_executed"], "Parallel should execute same number of nodes"
    assert p_seq.state.get("kosmos_adr", "") == p_par.state.get("kosmos_adr", ""), "ADR should be identical"

def test_s3_locks_thread_safe():
    """Stress test: multiple parallel runs should not corrupt state."""
    from lib.kosmos_node_v2 import KosmosPipelineV2
    from concurrent.futures import ThreadPoolExecutor, as_completed
    topics = [f"s3 stress {i}" for i in range(5)]
    results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        fut_map = {ex.submit(lambda t=t: KosmosPipelineV2({"topic": t, "parallel_enabled": True, "cache_enabled": False}).run_all()): t for t in topics}
        for f in as_completed(fut_map):
            results.append(f.result())
    assert len(results) == 5, f"Expected 5 results, got {len(results)}"
    for r in results:
        assert r["nodes_executed"] >= 6, f"Expected >=6 nodes, got {r['nodes_executed']}"
        assert r["nodes_with_errors"] == 0, f"Errors: {r['errors']}"

def test_s3_aletheia_structure():
    """Aletheia contract returns valid verification structure."""
    from lib.kosmos_contracts import KosmosAletheiaContract
    ac = KosmosAletheiaContract(real_mode=False)
    result = ac.request_verification("SQLite FTS5 soporta búsqueda full-text en español", context="Prueba técnica")
    assert result.verified is not None, "verified should be bool"
    assert 0 <= result.confidence <= 1, f"confidence should be 0-1, got {result.confidence}"
    assert isinstance(result.claims, list), "claims should be list"
    assert isinstance(result.sources, list), "sources should be list"
    st = ac.status()
    assert "total_runs" in st
    assert st["total_runs"] >= 1
