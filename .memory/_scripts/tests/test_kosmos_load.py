"""Load tests for KosmosV2 pipeline (KosmosV3 D6)."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["LLM_DIRECT_ENABLED"] = "false"
os.environ["KAOS_TESTING"] = "1"


def test_load_sequential_10():
    from lib.kosmos_node_v2 import KosmosPipelineV2
    topics = [f"load test seq {i}" for i in range(10)]
    times = []
    for t in topics:
        start = time.time()
        p = KosmosPipelineV2({"topic": t, "parallel_enabled": False, "cache_enabled": False})
        r = p.run_all()
        times.append(time.time() - start)
        assert r["nodes_executed"] == 8, f"Expected 8 nodes, got {r['nodes_executed']}"
    avg = sum(times) / len(times)
    total = sum(times)
    print(f"\n[D6] Sequential 10: avg={avg:.2f}s, total={total:.2f}s, min={min(times):.2f}s, max={max(times):.2f}s")


def test_load_parallel_5():
    from lib.kosmos_node_v2 import KosmosPipelineV2
    from concurrent.futures import ThreadPoolExecutor, as_completed
    topics = [f"load test par {i}" for i in range(5)]
    start = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        fut_map = {ex.submit(lambda t=t: KosmosPipelineV2(
            {"topic": t, "parallel_enabled": True, "cache_enabled": False}).run_all()): t for t in topics}
        for f in as_completed(fut_map):
            r = f.result()
            results.append(r)
    total = time.time() - start
    ok = all(r["nodes_with_errors"] == 0 for r in results)
    print(f"[D6] Parallel 5: total={total:.2f}s, all_ok={ok}")


def test_load_rate_limiter():
    from lib.kosmos.ratelimit import rate_limit_status
    rl = rate_limit_status()
    assert "max_concurrent" in rl
    assert rl["max_concurrent"] >= 1


def test_load_health():
    from lib.kosmos.health import serve_daemon
    import urllib.request, json
    serve_daemon()
    time.sleep(0.5)
    r = json.loads(urllib.request.urlopen("http://localhost:9876/health").read())
    assert r["status"] == "ok"
    r2 = json.loads(urllib.request.urlopen("http://localhost:9876/metrics/v2").read())
    assert "cache" in r2
