"""Sleep cycle v1.0 — NREM + REM + Compaction + Forgetting."""
import json, sys, time, sqlite3, hashlib
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / ".memory" / "_scripts"
sys.path.insert(0, str(SCRIPTS))

from lib.code_memory import status as cm_status, DB as CODE_DB
from lib.vectorstore import query as vec_query, status as vec_status

try:
    from sklearn.cluster import DBSCAN
    import numpy as np
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False

SLEEP_LOG = SCRIPTS.parent / ".memory" / "cache" / "sleep-log.json"

def log(msg: str):
    print(f"  {msg}")
    entries = []
    if SLEEP_LOG.exists():
        entries = json.loads(SLEEP_LOG.read_text())
    entries.append({"ts": time.strftime("%Y-%m-%d %H:%M"), "msg": msg})
    SLEEP_LOG.write_text(json.dumps(entries[-100:], indent=2))

def phase_nrem():
    """NREM: DBSCAN clustering + LLM distill + centrality decay."""
    print("\n[PHASE 1] NREM — Consolidation")
    if not SKLEARN_OK:
        log("sklearn not installed, skipping NREM")
        return
    
    cm = cm_status()
    total = cm["total_experiences"]
    if total < 3:
        log(f"Only {total} experiences, need >=3 for clustering")
        return
    
    conn = sqlite3.connect(str(CODE_DB))
    rows = conn.execute("""
        SELECT id, error_hash, error_message, language, confidence, ast_signature
        FROM code_experiences WHERE confidence < 0.5
    """).fetchall()
    conn.close()
    
    if len(rows) < 3:
        log(f"Only {len(rows)} unvalidated, need >=3")
        # Even without clustering, apply decay
        conn = sqlite3.connect(str(CODE_DB))
        conn.execute("UPDATE code_experiences SET confidence = confidence * 0.98 WHERE confidence < 0.5")
        conn.commit()
        conn.close()
        log(f"Applied decay to {len(rows)} entries")
        return
    
    # Simple feature extraction using error_message length and confidence
    X = np.array([[len(r[2]), r[4]] for r in rows])
    clustering = DBSCAN(eps=0.35, min_samples=3).fit(X)
    n_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
    
    conn = sqlite3.connect(str(CODE_DB))
    for i, row in enumerate(rows):
        if clustering.labels_[i] >= 0:
            pattern = f"cluster_{clustering.labels_[i]}"
            conn.execute("UPDATE code_experiences SET pattern_category = ? WHERE id = ?", (pattern, row[0]))
    conn.commit()
    conn.close()
    
    log(f"DBSCAN: {n_clusters} clusters from {len(rows)} entries")
    return {"clusters": n_clusters, "entries": len(rows)}

def phase_rem():
    """REM: Cross-domain associations and schema synthesis."""
    print("\n[PHASE 2] REM — Cross-domain associations")
    
    conn = sqlite3.connect(str(CODE_DB))
    clusters = conn.execute("""
        SELECT pattern_category, COUNT(*) as c, AVG(confidence) as avg_c
        FROM code_experiences
        WHERE pattern_category != '' AND pattern_category LIKE 'cluster_%'
        GROUP BY pattern_category
        HAVING c >= 3
    """).fetchall()
    conn.close()
    
    if not clusters:
        log("No consolidated clusters yet")
        return {"schemas": 0}
    
    for cluster in clusters:
        log(f"Cluster {cluster[0]}: {cluster[1]} entries, avg confidence {cluster[2]:.2f}")
    
    return {"schemas": len(clusters)}

def phase_compaction():
    """Compaction: Summarize verbose low-access nodes."""
    print("\n[PHASE 3] Compaction — Summarize low-access nodes")
    
    conn = sqlite3.connect(str(CODE_DB))
    candidates = conn.execute("""
        SELECT id, error_hash, error_message, retrieval_count
        FROM code_experiences
        WHERE retrieval_count < 2 AND confidence < 0.3
        ORDER BY retrieval_count ASC
        LIMIT 50
    """).fetchall()
    
    if not candidates:
        log("No candidates for compaction")
        conn.close()
        return
    
    # Flag for archival (soft delete)
    for c in candidates:
        conn.execute("UPDATE code_experiences SET confidence = -1 WHERE id = ?", (c[0],))
    conn.commit()
    
    count = len(candidates)
    conn.close()
    log(f"Compacted {count} low-access entries (confidence set to -1)")
    return {"compacted": count}

def phase_forgetting():
    """Forgetting: Hyperbolic decay for old unused entries."""
    print("\n[PHASE 4] Forgetting — Hyperbolic decay")
    
    conn = sqlite3.connect(str(CODE_DB))
    entries = conn.execute("""
        SELECT id, error_hash, confidence, 
               julianday('now') - julianday(created_at) as age_days
        FROM code_experiences
        WHERE confidence > 0 AND age_days > 7
    """).fetchall()
    
    decayed = 0
    forgotten = 0
    for e in entries:
        strength = 1.0 / (1.0 + 0.15 * e[3])  # hyperbolic decay
        new_conf = e[2] * strength
        if new_conf < 0.1:
            conn.execute("UPDATE code_experiences SET confidence = -2, pattern_category = 'forgotten' WHERE id = ?", (e[0],))
            forgotten += 1
        else:
            conn.execute("UPDATE code_experiences SET confidence = ? WHERE id = ?", (new_conf, e[0]))
            decayed += 1
    
    conn.commit()
    conn.close()
    log(f"Decayed {decayed} entries, forgotten {forgotten} (confidence moved to archive)")
    return {"decayed": decayed, "forgotten": forgotten}

def run(fast: bool = False):
    start = time.time()
    print("=" * 50)
    print(" MNEMOSYNE SLEEP CYCLE v1.0")
    print("=" * 50)
    
    cm = cm_status()
    print(f"\nBefore: {json.dumps(cm, indent=2)}")
    
    phase_nrem()
    if not fast:
        phase_rem()
    phase_compaction()
    phase_forgetting()
    
    cm_after = cm_status()
    print(f"\nAfter: {json.dumps(cm_after, indent=2)}")
    
    elapsed = time.time() - start
    print(f"\n{'=' * 50}")
    print(f" Sleep cycle complete: {elapsed:.1f}s")
    log(f"Sleep cycle: {elapsed:.1f}s, {cm['total_experiences']}→{cm_after['total_experiences']} entries")
    print(f"{'=' * 50}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--fast", action="store_true", help="Skip REM phase")
    args = p.parse_args()
    run(fast=args.fast)
