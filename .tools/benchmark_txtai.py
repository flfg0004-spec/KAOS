"""Benchmark de escalabilidad para txtai.

Mide latencia, RAM y tiempo de indexación para:
  1K, 5K, 10K, 25K, 50K documentos

Uso:
    py .tools/benchmark_txtai.py        # Ejecuta benchmark completo
    py .tools/benchmark_txtai.py --quick # Solo 1K + 5K
"""
import json
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".memory" / "_scripts"))

BENCH_DATA = Path(__file__).resolve().parent / "bench_data"
RESULTS_FILE = Path(__file__).resolve().parent / "benchmark_results.json"


def get_docs(limit: int):
    """Obtiene los primeros N documentos del dataset."""
    files = sorted(BENCH_DATA.glob("*.md"))[:limit]
    return [(f.name, f.read_text(encoding="utf-8", errors="replace")) for f in files]


def run_benchmark(sizes):
    results = {}
    print(f"{'Size':>6} | {'Index(s)':>9} | {'Query(ms)':>9} | {'RAM(MB)':>8} | {'Docs/s':>7}")
    print("-" * 50)

    for size in sizes:
        docs = get_docs(size)
        if not docs:
            print(f"{size:>6} | {'NO DATA':>9}")
            continue

        tracemalloc.start()
        t0 = time.time()

        from txtai import Embeddings
        embeddings = Embeddings(path="BAAI/bge-small-en-v1.5", content=True, hybrid=True)

        texts = [d[1] for d in docs]
        embeddings.index(texts)

        t1 = time.time()
        index_time = t1 - t0

        # Query benchmark (5 queries)
        queries = [
            "machine learning agents", "knowledge graphs",
            "attention mechanism", "vector databases", "multi-agent systems",
        ]
        query_times = []
        for q in queries:
            tq0 = time.time()
            embeddings.search(q, limit=5)
            query_times.append((time.time() - tq0) * 1000)

        avg_query = sum(query_times) / len(query_times)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        ram_mb = peak / 1024 / 1024

        docs_per_sec = size / index_time if index_time > 0 else 0

        print(f"{size:>6} | {index_time:>8.1f}s | {avg_query:>8.1f} | {ram_mb:>7.1f} | {docs_per_sec:>6.0f}")

        results[str(size)] = {
            "index_time_s": round(index_time, 2),
            "avg_query_ms": round(avg_query, 2),
            "peak_ram_mb": round(ram_mb, 1),
            "docs_per_second": round(docs_per_sec, 0),
        }

    RESULTS_FILE.write_text(json.dumps(results, indent=2))
    print(f"\nResultados guardados en {RESULTS_FILE}")
    return results


def main():
    quick = "--quick" in sys.argv
    sizes = [1000, 5000] if quick else [1000, 5000, 10000, 25000, 50000]
    return run_benchmark(sizes)


if __name__ == "__main__":
    main()
