"""
Test: Ingesta Masiva de Wikipedia
Prueba el pipeline de ingesta con artículos reales de Wikipedia.
Fases: 1 (100 art) → 2 (1,000 art) → 3 (queries) → 4 (escalado)
"""

import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE / ".tools"))
sys.path.insert(0, str(BASE / ".memory/_scripts/lib"))

try:
    from ingest import ingest_wikipedia_topic, ingest_text, queue_status
    HAS_INGEST = True
except ImportError:
    HAS_INGEST = False

try:
    from embeddings import query as emb_query, build_index
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False


def phase_1_small_batch(topic: str = "machine learning", max_articles: int = 5):
    """Phase 1: Ingest a small batch of Wikipedia articles."""
    print(f"\n{'='*60}")
    print(f"Phase 1: Small batch ingest ({max_articles} articles)")
    print(f"{'='*60}")

    if not HAS_INGEST:
        print("SKIP: ingest module not available")
        return False

    start = time.time()
    result = ingest_wikipedia_topic(topic, max_articles, "deep")
    elapsed = time.time() - start

    print(f"Result: {json.dumps(result, indent=2)}")
    print(f"Time: {elapsed:.1f}s")

    # Show queue status
    print(f"\nQueue status:\n{queue_status()}")

    return result.get("total", 0) > 0


def phase_2_index_check():
    """Phase 2: Verify embeddings index was updated."""
    print(f"\n{'='*60}")
    print(f"Phase 2: Embeddings index check")
    print(f"{'='*60}")

    if not HAS_EMBEDDINGS:
        print("SKIP: embeddings module not available")
        return False

    result = build_index()
    print(f"Index result: {result}")

    return True


def phase_3_query_test(queries: list[str] = None):
    """Phase 3: Test semantic queries on the ingested data."""
    if queries is None:
        queries = [
            "What is deep learning?",
            "neural network architectures",
            "transformer models attention",
            "reinforcement learning algorithms",
            "computer vision applications",
        ]

    print(f"\n{'='*60}")
    print(f"Phase 3: Semantic query test ({len(queries)} queries)")
    print(f"{'='*60}")

    if not HAS_EMBEDDINGS:
        print("SKIP: embeddings module not available")
        return False

    total_time = 0
    for q in queries:
        start = time.time()
        results = emb_query(q, top_k=3)
        elapsed = time.time() - start
        total_time += elapsed
        print(f"\nQuery: {q}")
        print(f"  Time: {elapsed:.3f}s")
        for r in results:
            print(f"  [{r['score']}] {r['path']}: {r['snippet'][:80]}...")

    avg_time = total_time / len(queries)
    print(f"\nAverage query time: {avg_time:.3f}s")
    print(f"Target: <1.0s {'✅ PASS' if avg_time < 1.0 else '❌ FAIL'}")

    return avg_time < 1.0


def phase_4_scale_recommendation():
    """Phase 4: Analyze results and recommend scaling."""
    print(f"\n{'='*60}")
    print(f"Phase 4: Scaling recommendation")
    print(f"{'='*60}")

    raw_files = list((BASE / ".memory" / "raw").glob("*.md"))
    concept_files = list((BASE / ".memory" / "wiki" / "concepts").glob("*.md"))

    print(f"Current vault state:")
    print(f"  raw/ files: {len(raw_files)}")
    print(f"  wiki/concepts/ files: {len(concept_files)}")

    if len(raw_files) >= 100:
        print("\n✅ RECOMMENDATION: Ready for full Wikipedia category ingest")
        print(f"  Next: ingest.py wikipedia --topic 'Artificial Intelligence' --max 1000 --profile massive")
    elif len(raw_files) >= 10:
        print("\n⚠️ PARTIAL: Ingest more articles before full scale")
        print(f"  Next: ingest.py wikipedia --topic 'Machine Learning' --max 100 --profile deep")
    else:
        print("\n🔄 INSUFFICIENT DATA: Complete Phase 1 first")


def run_all():
    print("=" * 60)
    print("  KAOS Wikipedia Ingest Test Suite")
    print("=" * 60)

    p1 = phase_1_small_batch()
    p2 = phase_2_index_check()
    p3 = phase_3_query_test()
    phase_4_scale_recommendation()

    print(f"\n{'='*60}")
    print(f"Results: P1={'✅' if p1 else '❌'} P2={'✅' if p2 else '⬜'} P3={'✅' if p3 else '⬜'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_all()
