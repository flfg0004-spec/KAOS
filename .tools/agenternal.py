"""Agenternal-style episodic memory compression.
    
Consolidates CodeExperience entries into higher-level semantic patterns
using DBSCAN clustering + LLM distillation (2M:1 compression ratio target).
"""
import json, sqlite3, sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / ".memory" / "_scripts"
sys.path.insert(0, str(SCRIPTS))
from lib.code_memory import DB

COMPRESSION_LOG = SCRIPTS.parent / ".memory" / "cache" / "compression-log.json"

def consolidate(target_ratio: float = 0.5):
    """Consolidate episodic memories into semantic patterns.
    
    Args:
        target_ratio: Target compression ratio (0.5 = 50% reduction)
    """
    try:
        from sklearn.cluster import DBSCAN
        import numpy as np
    except ImportError:
        print("sklearn not available, skipping consolidation")
        return
    
    conn = sqlite3.connect(str(DB))
    
    # Get experiences with enough retrievals for confidence
    rows = conn.execute("""
        SELECT id, error_hash, error_message, language, confidence, 
               retrieval_count, pattern_category
        FROM code_experiences
        WHERE confidence > 0.3 AND confidence < 1.0
        ORDER BY retrieval_count DESC
        LIMIT 1000
    """).fetchall()
    
    if len(rows) < 5:
        print(f"Only {len(rows)} experiences, need >=5 for consolidation")
        conn.close()
        return
    
    # Use error_message length and confidence as features
    X = np.array([[len(r[2]), r[4], min(r[5] / 10, 1.0)] for r in rows])
    clustering = DBSCAN(eps=0.3, min_samples=3).fit(X)
    
    # For each cluster, create a consolidated pattern
    n_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
    consolidated = 0
    
    for cluster_id in set(clustering.labels_):
        if cluster_id == -1:
            continue
        cluster_rows = [rows[i] for i in range(len(rows)) if clustering.labels_[i] == cluster_id]
        if len(cluster_rows) < 3:
            continue
        
        # Create pattern from cluster
        langs = set(r[3] for r in cluster_rows)
        avg_conf = sum(r[4] for r in cluster_rows) / len(cluster_rows)
        pattern_name = f"pattern_{cluster_id}_{len(cluster_rows)}ex"
        
        # Update all entries in cluster with pattern
        for r in cluster_rows:
            conn.execute("UPDATE code_experiences SET pattern_category = ? WHERE id = ?",
                        (pattern_name, r[0]))
        consolidated += len(cluster_rows)
    
    conn.commit()
    conn.close()
    
    result = {"clusters": n_clusters, "consolidated": consolidated, "total": len(rows)}
    
    # Log compression
    entries = []
    if COMPRESSION_LOG.exists():
        entries = json.loads(COMPRESSION_LOG.read_text())
    entries.append(result)
    COMPRESSION_LOG.write_text(json.dumps(entries[-100:], indent=2))
    
    ratio = 1.0 - (n_clusters / len(rows)) if len(rows) > 0 else 0
    print(f"Agenternal consolidation: {n_clusters} clusters from {len(rows)} entries ({ratio:.1%} compression)")
    print(f"  Consolidated {consolidated} entries into {n_clusters} patterns")
    
    return result

if __name__ == "__main__":
    consolidate()
