"""HyDE — Hypothetical Document Embeddings para búsqueda mejorada."""
from lib.vectorstore import _import_model, query

HYDE_PROMPT = """Generate a short technical document that would comprehensively answer the following question.
Format as a markdown document with sections.

Question: {query}"""

def hyde_search(query: str, top_k: int = 5) -> list[dict]:
    """HyDE search: generate hypothetical document, then search by its embedding.
    
    Args:
        query: User search query
        top_k: Number of results to return
    
    Returns:
        List of result dicts with path, snippet, score
    """
    try:
        from lib.aether.client import generate_structured
        hyde_doc = generate_structured(HYDE_PROMPT.format(query=query))
        if isinstance(hyde_doc, dict) and "error" not in hyde_doc:
            hyde_text = json.dumps(hyde_doc) if isinstance(hyde_doc, dict) else str(hyde_doc)
        else:
            hyde_text = query  # fallback
    except Exception:
        hyde_text = query  # fallback
    
    # Re-embed the hypothetical document
    model = _import_model()
    if model is None:
        return []
    hyde_vec = model.encode([hyde_text[:2000]])[0]
    
    # Custom search by vector (bypasses chunk_text)
    import sqlite3, struct
    from pathlib import Path
    DB_FILE = Path(__file__).resolve().parent.parent.parent / ".memory" / "cache" / "vectors.db"
    conn = sqlite3.connect(str(DB_FILE))
    
    def serialize(v):
        return struct.pack(f"{len(v)}f", *v)
    
    try:
        results = conn.execute("""
            SELECT c.path, c.chunk_text, v.distance
            FROM vault_vectors v JOIN vault_chunks c ON v.rowid = c.rowid
            WHERE v.embedding MATCH ? AND k = ?
            ORDER BY v.distance
        """, [serialize(hyde_vec), top_k]).fetchall()
    except Exception:
        conn.close()
        return query(query, top_k)  # fallback to regular search
    
    conn.close()
    return [
        {"path": r[0], "snippet": r[1][:200], "score": round(1.0 / (1.0 + r[2]), 3)}
        for r in results
    ]

if __name__ == "__main__":
    import json, sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from lib.vectorstore import status as vs
    print(f"Vector store: {vs()}")
    results = hyde_search("how to fix Python NoneType error", top_k=3)
    if results:
        for r in results:
            print(f"  - [{r['path']}] score={r['score']}")
    else:
        print("  (no results)")
