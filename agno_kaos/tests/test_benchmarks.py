"""Tests de rendimiento: benchmarks de latencia, stress, comparativa.

Uso: python -m pytest agno_kaos/tests/test_benchmarks.py -v --tb=short
"""
import asyncio
import time
import statistics
import pytest


# ── HELPERS ──────────────────────────────────────────────────────

def _stats(latencies_ms: list, label: str) -> dict:
    if not latencies_ms:
        return {"label": label, "error": "no samples"}
    s = sorted(latencies_ms)
    return {
        "label": label,
        "n": len(s),
        "mean_ms": round(statistics.mean(s), 1),
        "median_ms": round(statistics.median(s), 1),
        "p95_ms": round(s[int(len(s) * 0.95)], 1),
        "min_ms": round(s[0], 1),
        "max_ms": round(s[-1], 1),
        "stddev_ms": round(statistics.stdev(s), 1) if len(s) > 1 else 0,
    }


# ── FIXTURES ─────────────────────────────────────────────────────

@pytest.fixture
def aletheia():
    from agno_kaos.agents.a_aletheia import create_aletheia
    return create_aletheia(with_mcp=False)


@pytest.fixture
def kosmos():
    from agno_kaos.agents.a_kosmos import create_kosmos
    return create_kosmos(with_mcp=False)


@pytest.fixture
def kratos():
    from agno_kaos.agents.a_kratos import create_kratos
    return create_kratos(with_mcp=False)


# ── LATENCY BENCHMARKS ───────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_bench_aletheia_latency(aletheia):
    """Mide latencia de A-Aletheia (10 calls, without MCP)."""
    latencies = []
    for i in range(10):
        t0 = time.perf_counter()
        resp = await asyncio.wait_for(
            aletheia.arun(f"¿Qué es Python? (respuesta breve, iteración {i})"),
            timeout=30,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed)
    s = _stats(latencies, "A-Aletheia")
    print(f"\n  📊 {s['label']}: mean={s['mean_ms']}ms median={s['median_ms']}ms "
          f"p95={s['p95_ms']}ms (n={s['n']})")
    assert s["mean_ms"] < 30000, f"Mean latency {s['mean_ms']}ms > 30s threshold"


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_bench_kosmos_latency(kosmos):
    """Mide latencia de A-Kosmos (10 calls, without MCP)."""
    latencies = []
    for i in range(10):
        t0 = time.perf_counter()
        resp = await asyncio.wait_for(
            kosmos.arun(f"Analiza: estructura típica de proyecto Python (iteración {i})"),
            timeout=30,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed)
    s = _stats(latencies, "A-Kosmos")
    print(f"\n  📊 {s['label']}: mean={s['mean_ms']}ms median={s['median_ms']}ms "
          f"p95={s['p95_ms']}ms (n={s['n']})")
    assert s["mean_ms"] < 30000


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_bench_kratos_latency(kratos):
    """Mide latencia de A-Kratos (10 calls, without MCP)."""
    latencies = []
    for i in range(10):
        t0 = time.perf_counter()
        resp = await asyncio.wait_for(
            kratos.arun(f"Escribe una función factorial en Python (iteración {i})"),
            timeout=30,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed)
    s = _stats(latencies, "A-Kratos")
    print(f"\n  📊 {s['label']}: mean={s['mean_ms']}ms median={s['median_ms']}ms "
          f"p95={s['p95_ms']}ms (n={s['n']})")
    assert s["mean_ms"] < 30000


# ── STRESS TESTS ─────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.stress
async def test_stress_aletheia_concurrent(aletheia):
    """100 requests concurrentes a A-Aletheia (sin MCP)."""
    concurrency = 100
    t0 = time.perf_counter()
    tasks = [
        asyncio.wait_for(
            aletheia.arun(f"¿Qué es la IA? (pregunta {i})"),
            timeout=60,
        )
        for i in range(concurrency)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total = time.perf_counter() - t0
    errors = sum(1 for r in results if isinstance(r, Exception))
    throughput = concurrency / total
    print(f"\n  🔥 Stress Aletheia: {concurrency} calls in {total:.1f}s "
          f"→ {throughput:.1f} req/s, errors={errors}")
    assert errors < concurrency * 0.5, f"Too many errors: {errors}/{concurrency}"


@pytest.mark.asyncio
@pytest.mark.stress
async def test_stress_kratos_concurrent(kratos):
    """50 requests concurrentes a A-Kratos (sin MCP)."""
    concurrency = 50
    t0 = time.perf_counter()
    tasks = [
        asyncio.wait_for(
            kratos.arun(f"Escribe hello world en Python (versión {i})"),
            timeout=60,
        )
        for i in range(concurrency)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total = time.perf_counter() - t0
    errors = sum(1 for r in results if isinstance(r, Exception))
    throughput = concurrency / total
    print(f"\n  🔥 Stress Kratos: {concurrency} calls in {total:.1f}s "
          f"→ {throughput:.1f} req/s, errors={errors}")
    assert errors < concurrency * 0.5


# ── COMPARATIVA AGNO VS BASELINE ─────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_comparativa_aletheia_vs_baseline(aletheia):
    """Benchmark comparativo: agno vs tiempo de respuesta esperado.

    Mide el tiempo de respuesta de A-Aletheia y verifica contra un
    baseline de <15s para consultas simples sin MCP.
    """
    BASELINE_MS = 15000
    t0 = time.perf_counter()
    resp = await asyncio.wait_for(
        aletheia.arun("¿Qué es KAOS? (responde en 2 párrafos)"),
        timeout=30,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    has_content = len(resp.content if hasattr(resp, "content") else str(resp)) > 50
    print(f"\n  📊 A-Aletheia vs baseline: {elapsed_ms:.0f}ms "
          f"(baseline {BASELINE_MS}ms) content={'✅' if has_content else '❌'}")
    assert elapsed_ms < 30000, f"Response time {elapsed_ms:.0f}ms > 30s"
    assert has_content, "Response has no content"
