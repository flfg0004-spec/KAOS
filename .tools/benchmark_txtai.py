"""Benchmark rapido de txtai — mide solo indexacion (sin hybrid).

El modo hybrid=True es lento porque construye indices BM25 ademas de vectores.
Este benchmark separa la medicion:
  1. Indexacion vectorial pura
  2. Búsqueda
  3. RAM
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
    files = sorted(BENCH_DATA.glob("*.md"))[:limit]
    return [f.read_text(encoding="utf-8", errors="replace") for f in files]


def bench(embeddings, texts, label):
    t0 = time.time()
    embeddings.index(texts)
    t1 = time.time()

    # queries
    queries = ["machine learning agents", "knowledge graphs", "vector databases"]
    qt = []
    for q in queries:
        tq = time.time()
        embeddings.search(q, limit=5)
        qt.append((time.time() - tq) * 1000)

    avg_q = sum(qt) / len(qt)
    return {
        "label": label,
        "docs": len(texts),
        "index_s": round(t1 - t0, 2),
        "avg_query_ms": round(avg_q, 1),
        "docs_per_s": round(len(texts) / (t1 - t0), 0),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=50000)
    parser.add_argument("--step", type=int, default=5000)
    args = parser.parse_args()

    sizes = []
    s = 1000
    while s <= args.max:
        sizes.append(s)
        s += args.step

    print(f"{'Docs':>6} | {'Index(s)':>8} | {'Query(ms)':>9} | {'RAM(MB)':>8} | {'Docs/s':>7}")
    print("-" * 48)

    all_results = {}
    for size in sizes:
        docs = get_docs(size)
        if not docs:
            print(f"{size:>6} | no data")
            continue

        tracemalloc.start()
        from txtai import Embeddings
        emb = Embeddings(path="BAAI/bge-small-en-v1.5", content=True, hybrid=True, batch=64)
        
        r = bench(emb, docs, f"{size}")
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        r["peak_ram_mb"] = round(peak / 1024 / 1024, 1)

        print(f"{r['docs']:>6} | {r['index_s']:>7.1f}s | {r['avg_query_ms']:>8.1f} | {r['peak_ram_mb']:>7.1f} | {r['docs_per_s']:>6.0f}")
        all_results[str(size)] = r

    RESULTS_FILE.write_text(json.dumps(all_results, indent=2))
    print(f"\nResultados: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
