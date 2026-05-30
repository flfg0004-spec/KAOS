"""Hebbian Memory — co-retrieval strengthens connections between experiences.

Principio Hebbiano: "Neurons that fire together, wire together."
  - Cuando dos experiencias se recuperan juntas frecuentemente, se crea un edge
  - La próxima vez que se recupere una, la otra también aparece como sugerencia
  - Edges tienen peso que se fortalece/débilita con el uso

Inspirado en ZenBrain y Mnemoria:
  - Graph memory con edges ponderados
  - Co-retrieval tracking
  - Decay de edges no usados
  - Asociaciones transitivas (amigo de mi amigo)
"""

import json
import sqlite3
from pathlib import Path

DB = (Path(__file__).resolve().parent.parent.parent / "cache" / "code_experiences.db")
HEBBIAN_DB = DB.parent / "hebbian_edges.db"

STRENGTH_INITIAL = 0.3
STRENGTH_INCREMENT = 0.15
STRENGTH_DECAY_RATE = 0.02  # per day
STRENGTH_THRESHOLD = 0.15  # below this, edge is removed
TRANSITIVE_DEPTH = 2  # "friend of my friend" depth


def _init_hebbian_db():
    """Initialize the Hebbian memory graph database."""
    conn = sqlite3.connect(str(HEBBIAN_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hebbian_edges (
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            strength REAL DEFAULT 0.3,
            co_retrievals INTEGER DEFAULT 1,
            last_updated TEXT DEFAULT (datetime('now')),
            created_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (source_id, target_id)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_hebbian_source ON hebbian_edges(source_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_hebbian_target ON hebbian_edges(target_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_hebbian_strength ON hebbian_edges(strength)
    """)
    conn.commit()
    conn.close()


def record_co_retrieval(experience_ids: list[int]) -> dict:
    """Record that a set of experiences were retrieved together.
    
    For each pair in the set, strengthen their Hebbian edge.
    
    Args:
        experience_ids: List of experience IDs that were co-retrieved
    
    Returns:
        dict with number of edges created/updated
    """
    _init_hebbian_db()
    
    if len(experience_ids) < 2:
        return {"edges_affected": 0}
    
    conn = sqlite3.connect(str(HEBBIAN_DB))
    try:
        edges = 0
        for i in range(len(experience_ids)):
            for j in range(i + 1, len(experience_ids)):
                src, tgt = experience_ids[i], experience_ids[j]
                if src == tgt:
                    continue
                
                existing = conn.execute(
                    "SELECT strength, co_retrievals FROM hebbian_edges WHERE source_id = ? AND target_id = ?",
                    (min(src, tgt), max(src, tgt))
                ).fetchone()
                
                if existing:
                    new_strength = min(1.0, existing[0] + STRENGTH_INCREMENT)
                    conn.execute("""
                        UPDATE hebbian_edges SET 
                            strength = ?,
                            co_retrievals = co_retrievals + 1,
                            last_updated = datetime('now')
                        WHERE source_id = ? AND target_id = ?
                    """, (new_strength, min(src, tgt), max(src, tgt)))
                else:
                    conn.execute("""
                        INSERT INTO hebbian_edges (source_id, target_id, strength, co_retrievals)
                        VALUES (?, ?, ?, 1)
                    """, (min(src, tgt), max(src, tgt), STRENGTH_INITIAL))
                
                edges += 1
        
        conn.commit()
        return {"edges_affected": edges}
    finally:
        conn.close()


def get_associated(experience_id: int, min_strength: float = 0.3) -> list[dict]:
    """Get experiences associated with the given one via Hebbian edges.
    
    Uses direct edges + transitive associations.
    
    Args:
        experience_id: The experience to find associations for
        min_strength: Minimum edge strength to include
    
    Returns:
        List of associated experience dicts
    """
    _init_hebbian_db()
    
    conn = sqlite3.connect(str(HEBBIAN_DB))
    try:
        # Direct associations
        direct = conn.execute("""
            SELECT 
                CASE WHEN source_id = ? THEN target_id ELSE source_id END as other_id,
                strength,
                co_retrievals
            FROM hebbian_edges
            WHERE (source_id = ? OR target_id = ?)
            AND strength >= ?
            ORDER BY strength DESC
            LIMIT 10
        """, (experience_id, experience_id, experience_id, min_strength)).fetchall()
        
        results = []
        for row in direct:
            other_id, strength, co_ret = row
            
            # Get experience details from main DB
            exp = _get_experience(other_id)
            if exp:
                results.append({
                    "experience": exp,
                    "hebbian_strength": round(strength, 2),
                    "co_retrievals": co_ret,
                    "association_type": "direct",
                })
        
        # Transitive associations (friend of my friend)
        if len(results) > 0:
            transitive = conn.execute("""
                SELECT DISTINCT 
                    CASE WHEN e2.source_id = e1.other_id THEN e2.target_id ELSE e2.source_id END as transit_id,
                    e2.strength * e1.strength as combined_strength
                FROM (
                    SELECT 
                        CASE WHEN source_id = ? THEN target_id ELSE source_id END as other_id,
                        strength
                    FROM hebbian_edges
                    WHERE (source_id = ? OR target_id = ?)
                    AND strength >= ?
                ) e1
                JOIN hebbian_edges e2 ON (e2.source_id = e1.other_id OR e2.target_id = e1.other_id)
                WHERE e2.strength >= ?
                AND (CASE WHEN e2.source_id = e1.other_id THEN e2.target_id ELSE e2.source_id END) != ?
                AND (CASE WHEN e2.source_id = e1.other_id THEN e2.target_id ELSE e2.source_id END) NOT IN (
                    SELECT CASE WHEN source_id = ? THEN target_id ELSE source_id END
                    FROM hebbian_edges WHERE strength >= ?
                )
                ORDER BY combined_strength DESC
                LIMIT 5
            """, (experience_id, experience_id, experience_id, min_strength,
                  min_strength, experience_id,
                  experience_id, min_strength)).fetchall()
            
            for row in transitive:
                transit_id, combined = row
                exp = _get_experience(transit_id)
                if exp:
                    results.append({
                        "experience": exp,
                        "hebbian_strength": round(combined, 2),
                        "association_type": "transitive",
                    })
        
        return results
    finally:
        conn.close()


def _get_experience(exp_id: int) -> dict:
    """Get experience details from the main code_experiences DB."""
    try:
        conn = sqlite3.connect(str(DB))
        row = conn.execute("""
            SELECT id, error_hash, error_message, language, confidence, retrieval_count
            FROM code_experiences WHERE id = ?
        """, (exp_id,)).fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "hash": row[1],
                "error": row[2][:100],
                "language": row[3],
                "confidence": row[4],
                "retrievals": row[5],
            }
    except Exception:
        pass
    return None


def decay_edges(dry_run: bool = False) -> dict:
    """Apply exponential decay to all edges based on age.
    
    Edges below STRENGTH_THRESHOLD are removed.
    
    Args:
        dry_run: If True, only report without removing
    
    Returns:
        dict with decay results
    """
    _init_hebbian_db()
    
    conn = sqlite3.connect(str(HEBBIAN_DB))
    try:
        total = conn.execute("SELECT COUNT(*) FROM hebbian_edges").fetchone()[0]
        
        # Apply decay
        candidate_ids = conn.execute("""
            SELECT id FROM hebbian_edges
            WHERE strength < ? 
            OR julianday('now') - julianday(last_updated) > 90
        """, (STRENGTH_THRESHOLD,)).fetchall() if not dry_run else []
        
        if not dry_run:
            conn.execute("""
                DELETE FROM hebbian_edges
                WHERE strength < ?
                OR julianday('now') - julianday(last_updated) > 90
            """, (STRENGTH_THRESHOLD,))
            conn.commit()
            
            for edge_id in [r[0] for r in candidate_ids]:
                conn.execute("DELETE FROM hebbian_edges WHERE id = ?", (edge_id,))
            conn.commit()
        
        remaining = conn.execute("SELECT COUNT(*) FROM hebbian_edges").fetchone()[0]
        
        return {
            "status": "dry_run" if dry_run else "decayed",
            "total_before": total,
            "candidates": len(candidate_ids),
            "remaining": remaining,
            "removed": total - remaining if not dry_run else 0,
        }
    finally:
        conn.close()


def get_graph_stats() -> dict:
    """Get statistics about the Hebbian memory graph."""
    _init_hebbian_db()
    
    conn = sqlite3.connect(str(HEBBIAN_DB))
    try:
        total_edges = conn.execute("SELECT COUNT(*) FROM hebbian_edges").fetchone()[0]
        avg_strength = conn.execute("SELECT AVG(strength) FROM hebbian_edges").fetchone()[0] or 0
        max_strength = conn.execute("SELECT MAX(strength) FROM hebbian_edges").fetchone()[0] or 0
        nodes_with_edges = conn.execute("""
            SELECT COUNT(DISTINCT node) FROM (
                SELECT source_id as node FROM hebbian_edges
                UNION
                SELECT target_id as node FROM hebbian_edges
            )
        """).fetchone()[0]
        
        return {
            "total_edges": total_edges,
            "nodes_with_edges": nodes_with_edges,
            "avg_strength": round(avg_strength, 2),
            "max_strength": round(max_strength, 2),
        }
    finally:
        conn.close()


def record_retrieval_and_get_associations(experience_ids: list[int]) -> dict:
    """Record co-retrieval and return associated experiences.
    
    Convenience function for the retrieval pipeline.
    
    Args:
        experience_ids: IDs that were retrieved together
    
    Returns:
        dict with edges info + associated experiences
    """
    edges_result = record_co_retrieval(experience_ids)
    
    all_associations = []
    seen_ids = set()
    for eid in experience_ids:
        for assoc in get_associated(eid):
            if assoc["experience"]["id"] not in seen_ids:
                seen_ids.add(assoc["experience"]["id"])
                all_associations.append(assoc)
    
    return {
        "edges_affected": edges_result["edges_affected"],
        "associations": all_associations[:10],
        "association_count": len(all_associations),
    }


if __name__ == "__main__":
    import json
    
    _init_hebbian_db()
    
    print("=== Hebbian Memory Graph ===")
    print(json.dumps(get_graph_stats(), indent=2))
    
    # Simulate co-retrievals
    print("\n=== Recording Co-retrievals ===")
    for i in range(5):
        r = record_co_retrieval([1, 2, 3])
        print(f"  Batch {i+1}: {r}")
    
    # Check associations
    print("\n=== Associations for exp 1 ===")
    assoc = get_associated(1)
    for a in assoc:
        print(f"  [{a['association_type']}] {a['experience']['error'][:50]} (strength={a['hebbian_strength']})")
    
    print("\n=== Stats ===")
    print(json.dumps(get_graph_stats(), indent=2))
