"""AST Skill Library — transforms high-confidence experiences into reusable skills.

Inspired by PYTHALAB-MERA (arXiv 2605.08468):
  - Experiences with confidence > 0.8 and resolution_rate > 0.9 → skills
  - Cluster by AST structural signature
  - Each skill: name, description, language, AST pattern, usage metrics
  - Skills indexed in separate code_skills.db for fast retrieval
"""

import sqlite3
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path

DB = (Path(__file__).resolve().parent.parent.parent / "cache" / "code_experiences.db")
SKILL_DB = DB.parent / "code_skills.db"

SKILL_CONFIDENCE_THRESHOLD = 0.8
SKILL_RESOLUTION_THRESHOLD = 0.9
MIN_EXPERIENCES_FOR_SKILL = 2


def _init_skill_db():
    """Initialize skill database."""
    conn = sqlite3.connect(str(SKILL_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS code_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            language TEXT NOT NULL DEFAULT 'unknown',
            ast_pattern TEXT DEFAULT '',
            source_experiences TEXT DEFAULT '[]',
            confidence REAL DEFAULT 0.5,
            usage_count INTEGER DEFAULT 0,
            last_used TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_skills_lang ON code_skills(language)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_skills_conf ON code_skills(confidence)
    """)
    conn.commit()
    conn.close()


def _extract_skill_name(error_message: str) -> str:
    """Generate a concise skill name from an error message."""
    # Remove common prefixes
    name = re.sub(r'^(error|exception|thread.*panicked):\s*', '', error_message, flags=re.IGNORECASE)
    # Take first meaningful phrase
    name = re.sub(r'[Ee]rror\s*\d*\s*:\s*', '', name)
    name = name.strip().rstrip('.')
    if len(name) > 60:
        name = name[:57] + '...'
    return name if name else "unknown_skill"


def mine_skills(dry_run: bool = False) -> dict:
    """Mine high-confidence experiences and convert them to skills.
    
    Args:
        dry_run: If True, only report without inserting
    
    Returns:
        dict with mining results
    """
    _init_skill_db()
    
    conn = sqlite3.connect(str(DB))
    skill_conn = sqlite3.connect(str(SKILL_DB))
    
    try:
        # Get high-confidence experiences grouped by AST signature
        rows = conn.execute("""
            SELECT id, error_hash, error_message, language, ast_signature,
                   confidence, resolution_rate, retrieval_count, solution_diff
            FROM code_experiences
            WHERE confidence >= ? AND resolution_rate >= ?
            AND ast_signature != ''
            ORDER BY confidence DESC
        """, (SKILL_CONFIDENCE_THRESHOLD, SKILL_RESOLUTION_THRESHOLD)).fetchall()
        
        # Group by AST signature + language
        groups = {}
        for r in rows:
            key = (r[3], r[4])  # (language, ast_signature)
            if key not in groups:
                groups[key] = []
            groups[key].append({
                "id": r[0], "hash": r[1], "error": r[2],
                "confidence": r[5], "resolution": r[6],
                "retrievals": r[7], "solution": r[8] or "",
            })
        
        mined = []
        for (lang, ast_sig), experiences in groups.items():
            if len(experiences) < MIN_EXPERIENCES_FOR_SKILL:
                continue
            
            # Aggregate metrics
            avg_confidence = sum(e["confidence"] for e in experiences) / len(experiences)
            avg_resolution = sum(e["resolution"] for e in experiences) / len(experiences)
            total_retrievals = sum(e["retrievals"] for e in experiences)
            
            # Generate skill name from most common error
            error_counts = {}
            for e in experiences:
                name = _extract_skill_name(e["error"])
                error_counts[name] = error_counts.get(name, 0) + 1
            skill_name = max(error_counts, key=error_counts.get)
            
            # Generate description
            examples = [e["error"][:80] for e in experiences[:3]]
            description = f"Skill: {skill_name}. Patterns: {'; '.join(examples)}"
            
            # Source experience IDs
            source_ids = [str(e["id"]) for e in experiences]
            
            if not dry_run:
                existing = skill_conn.execute(
                    "SELECT id FROM code_skills WHERE ast_pattern = ? AND language = ?",
                    (ast_sig, lang)
                ).fetchone()
                
                if existing:
                    skill_conn.execute("""
                        UPDATE code_skills SET 
                            confidence = ?, usage_count = usage_count + ?,
                            description = ?, source_experiences = ?
                        WHERE id = ?
                    """, (avg_confidence, MIN_EXPERIENCES_FOR_SKILL, description,
                          json.dumps(source_ids), existing[0]))
                else:
                    skill_conn.execute("""
                        INSERT INTO code_skills 
                        (name, description, language, ast_pattern, source_experiences, confidence)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (skill_name, description, lang, ast_sig,
                          json.dumps(source_ids), avg_confidence))
            
            mined.append({
                "name": skill_name,
                "language": lang,
                "ast_pattern": ast_sig,
                "source_count": len(experiences),
                "avg_confidence": round(avg_confidence, 2),
                "avg_resolution": round(avg_resolution, 2),
                "total_retrievals": total_retrievals,
            })
        
        if not dry_run:
            skill_conn.commit()
        
        return {"skills_mined": len(mined), "skills": mined[:20], "dry_run": dry_run}
    
    finally:
        conn.close()
        skill_conn.close()


def search_skills(query: str, language: str = "", top_k: int = 5) -> list:
    """Search skills by name, description, or language.
    
    Args:
        query: Search text
        language: Filter by language (empty = all)
        top_k: Max results
    
    Returns:
        List of matching skills
    """
    _init_skill_db()
    
    conn = sqlite3.connect(str(SKILL_DB))
    try:
        rows = conn.execute("""
            SELECT id, name, description, language, ast_pattern, 
                   source_experiences, confidence, usage_count, created_at
            FROM code_skills
            WHERE (name LIKE ? OR description LIKE ? OR ast_pattern LIKE ?)
            AND (? = '' OR language = ?)
            AND confidence >= 0.6
            ORDER BY confidence DESC, usage_count DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", language, language, top_k)).fetchall()
        
        skills = []
        for r in rows:
            skills.append({
                "id": r[0], "name": r[1], "description": r[2][:300],
                "language": r[3], "ast_pattern": r[4],
                "source_experiences": json.loads(r[5]) if r[5] else [],
                "confidence": r[6], "usage_count": r[7],
                "created_at": r[8],
            })
        return skills
    finally:
        conn.close()


def record_usage(skill_id: int) -> dict:
    """Record that a skill was used (increments usage_count).
    
    Args:
        skill_id: Skill ID to record usage for
    
    Returns:
        dict with status
    """
    _init_skill_db()
    conn = sqlite3.connect(str(SKILL_DB))
    try:
        conn.execute("""
            UPDATE code_skills SET 
                usage_count = usage_count + 1,
                last_used = datetime('now')
            WHERE id = ?
        """, (skill_id,))
        conn.commit()
        return {"status": "updated", "skill_id": skill_id}
    finally:
        conn.close()


def status() -> dict:
    """Get skill library status."""
    _init_skill_db()
    conn = sqlite3.connect(str(SKILL_DB))
    try:
        total = conn.execute("SELECT COUNT(*) FROM code_skills").fetchone()[0]
        by_lang = conn.execute("""
            SELECT language, COUNT(*) as c FROM code_skills 
            GROUP BY language ORDER BY c DESC
        """).fetchall()
        avg_conf = conn.execute("SELECT AVG(confidence) FROM code_skills").fetchone()[0] or 0
        return {
            "total_skills": total,
            "by_language": [{"language": r[0], "count": r[1]} for r in by_lang],
            "avg_confidence": round(avg_conf, 2),
        }
    finally:
        conn.close()


if __name__ == "__main__":
    import json as _json
    print("=== Skill Library Status ===")
    print(_json.dumps(status(), indent=2))
    print("\n=== Mining Skills ===")
    result = mine_skills(dry_run=True)
    print(f"Skills to mine: {result['skills_mined']}")
    for s in result["skills"][:5]:
        print(f"  [{s['language']}] {s['name']} (conf={s['avg_confidence']}, n={s['source_count']})")
