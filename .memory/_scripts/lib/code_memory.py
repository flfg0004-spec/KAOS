"""Code Experience Memory — FTS5 + AST + vector store for Kratos."""
import sqlite3, hashlib, json, re
from pathlib import Path

DB = (Path(__file__).resolve().parent.parent.parent / ".memory" / "cache" / "code_experiences.db")

_ERROR_KEYWORDS = {"error", "exception", "traceback", "failed", "failure",
                   "cannot", "unable", "denied", "not found", "syntax",
                   "typeerror", "valueerror", "keyerror", "attributeerror",
                   "importerror", "modulenotfound", "indexerror", "runtimeerror",
                   "panic", "unwrap", "expect", "assert"}

def _import_ast():
    try:
        from lib import ast_match
        return ast_match
    except ImportError:
        return None

def _detect_language(cwd: str = "") -> str:
    """Detect programming language from directory path or file extension."""
    cwd_lower = cwd.lower()
    if any(ext in cwd_lower for ext in [".py", "python"]):
        return "python"
    if any(ext in cwd_lower for ext in [".rs", "rust"]):
        return "rust"
    if any(ext in cwd_lower for ext in [".js", ".jsx", "javascript", "node"]):
        return "javascript"
    if any(ext in cwd_lower for ext in [".ts", ".tsx", "typescript"]):
        return "typescript"
    if any(ext in cwd_lower for ext in [".go", "golang"]):
        return "go"
    if any(ext in cwd_lower for ext in [".java", "java"]):
        return "java"
    return "unknown"

def capture_from_bash(exit_code: int, stderr: str, cmd: str = "", cwd: str = "") -> dict:
    """Capture error from bash execution into CodeExperience.

    Args:
        exit_code: Exit code from the command (0 = success)
        stderr: Standard error output
        cmd: The command that was executed (used as code snippet for AST)
        cwd: Current working directory (used to detect language)

    Returns:
        dict with status, confidence if exists, or created experience info
    """
    if exit_code == 0 or not stderr or not stderr.strip():
        return {"status": "ok"}

    # Only capture real errors (not warnings, info messages)
    stderr_lower = stderr.lower()
    if not any(kw in stderr_lower for kw in _ERROR_KEYWORDS):
        return {"status": "skipped", "reason": "no error keywords"}

    error_hash = hashlib.sha256(stderr.encode()).hexdigest()[:16]
    lang = _detect_language(cwd)

    conn = sqlite3.connect(str(DB))
    try:
        existing = conn.execute(
            "SELECT id, confidence FROM code_experiences WHERE error_hash = ?",
            (error_hash,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE code_experiences SET retrieval_count = retrieval_count + 1, last_retrieved = datetime('now') WHERE id = ?",
                (existing[0],)
            )
            conn.commit()
            return {"status": "exists", "id": existing[0], "confidence": existing[1]}

        return store(
            error_message=stderr[:500],
            language=lang,
            stack_trace=stderr[:2000],
            code_snippet=cmd[:500]
        )
    finally:
        conn.close()

def init():
    conn = sqlite3.connect(str(DB))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS code_experiences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_hash TEXT UNIQUE NOT NULL,
            error_message TEXT NOT NULL,
            stack_trace TEXT DEFAULT '',
            language TEXT NOT NULL DEFAULT 'unknown',
            framework TEXT DEFAULT '',
            file_path TEXT DEFAULT '',
            solution_diff TEXT DEFAULT '',
            explanation TEXT DEFAULT '',
            confidence REAL DEFAULT 0.5,
            ast_signature TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            last_retrieved TEXT,
            retrieval_count INTEGER DEFAULT 0,
            resolution_rate REAL DEFAULT 0.0,
            pattern_category TEXT DEFAULT '',
            source_agent TEXT DEFAULT 'kratos'
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS code_exp_fts
        USING fts5(error_message, stack_trace, explanation,
                   content='code_experiences', content_rowid='id')
    """)
    conn.executescript("""
        CREATE TRIGGER IF NOT EXISTS code_exp_ai AFTER INSERT ON code_experiences BEGIN
            INSERT INTO code_exp_fts(rowid, error_message, stack_trace, explanation)
            VALUES (new.id, new.error_message, new.stack_trace, new.explanation);
        END;
        CREATE TRIGGER IF NOT EXISTS code_exp_ad AFTER DELETE ON code_experiences BEGIN
            INSERT INTO code_exp_fts(code_exp_fts, rowid, error_message, stack_trace, explanation)
            VALUES ('delete', old.id, old.error_message, old.stack_trace, old.explanation);
        END;
        CREATE TRIGGER IF NOT EXISTS code_exp_au AFTER UPDATE ON code_experiences BEGIN
            INSERT INTO code_exp_fts(code_exp_fts, rowid, error_message, stack_trace, explanation)
            VALUES ('delete', old.id, old.error_message, old.stack_trace, old.explanation);
            INSERT INTO code_exp_fts(rowid, error_message, stack_trace, explanation)
            VALUES (new.id, new.error_message, new.stack_trace, new.explanation);
        END;
    """)
    conn.commit()
    conn.close()
    return f"CodeExperience DB initialized at {DB}"

def store(error_message: str, language: str = "unknown",
          stack_trace: str = "", solution_diff: str = "",
          explanation: str = "", framework: str = "",
          code_snippet: str = "") -> dict:
    error_hash = hashlib.sha256(error_message.encode()).hexdigest()[:16]
    conn = sqlite3.connect(str(DB))
    try:
        cur = conn.execute("SELECT id, confidence, retrieval_count FROM code_experiences WHERE error_hash = ?", (error_hash,))
        existing = cur.fetchone()
        if existing:
            conn.execute("UPDATE code_experiences SET retrieval_count = retrieval_count + 1, last_retrieved = datetime('now') WHERE id = ?", (existing[0],))
            conn.commit()
            return {"status": "exists", "id": existing[0], "confidence": existing[1], "retrieval_count": existing[2] + 1}

        ast_sig = ""
        ast_mod = _import_ast()
        if ast_mod and code_snippet and language in ("python", "rust", "javascript"):
            ast_sig = ast_mod.ast_signature(code_snippet, language)

        conn.execute("""
            INSERT INTO code_experiences
            (error_hash, error_message, stack_trace, language, framework,
             solution_diff, explanation, ast_signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (error_hash, error_message[:500], stack_trace[:2000], language,
              framework, solution_diff, explanation[:1000], ast_sig))
        conn.commit()
        return {"status": "created", "hash": error_hash, "ast_sig": ast_sig}
    finally:
        conn.close()

def search(query: str, top_k: int = 5,
           code_snippet: str = "", language: str = "") -> list:
    conn = sqlite3.connect(str(DB))
    try:
        fts_results = conn.execute("""
            SELECT c.id, c.error_hash, c.error_message, c.language, c.confidence,
                   c.retrieval_count, c.resolution_rate, c.solution_diff, c.ast_signature
            FROM code_exp_fts f JOIN code_experiences c ON f.rowid = c.id
            WHERE code_exp_fts MATCH ? AND c.confidence > 0.2
            ORDER BY rank
            LIMIT ?
        """, (query, top_k * 2)).fetchall()

        results = []
        for r in fts_results:
            score = 0.4
            score += r[4] * 0.2
            score += min(r[5] / 10, 0.1)
            ast_mod = _import_ast()
            if ast_mod and code_snippet and language and r[8]:
                query_sig = ast_mod.ast_signature(code_snippet, language)
                if query_sig and query_sig == r[8]:
                    score += 0.3
            results.append({
                "id": r[0], "hash": r[1], "error": r[2][:100],
                "language": r[3], "confidence": r[4],
                "retrievals": r[5], "rate": r[6],
                "solution": r[7][:200] if r[7] else "",
                "score": round(score, 2)
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    finally:
        conn.close()

def feedback(error_hash: str, success: bool):
    """Update confidence using LinUCB contextual bandit."""
    conn = sqlite3.connect(str(DB))
    try:
        row = conn.execute("SELECT id, confidence, retrieval_count, language, error_message, ast_signature FROM code_experiences WHERE error_hash = ?", (error_hash,)).fetchone()
        if not row:
            return {"status": "not_found"}
        
        # Use LinUCB bandit for adaptive confidence
        try:
            from lib.bandit import get_bandit, extract_features
            bandit = get_bandit()
            error_data = {
                "language": row[3],
                "error": row[4] or "",
                "stack_trace": row[4] or "",
                "solution": "",
                "retrievals": row[2],
                "ast_score": 1.0 if row[5] else 0.0,
            }
            features = extract_features(error_data)
            bandit.update(error_hash, features, 1.0 if success else 0.0)
            new_conf = bandit.get_confidence(error_hash)
        except Exception:
            if success:
                new_conf = min(1.0, row[1] + 0.1)
            else:
                new_conf = max(0.1, row[1] - 0.2)
        
        conn.execute("UPDATE code_experiences SET confidence = ?, retrieval_count = retrieval_count + 1 WHERE id = ?", (new_conf, row[0]))
        conn.commit()
        return {"status": "updated", "new_confidence": new_conf}
    finally:
        conn.close()

def prune(dry_run: bool = False) -> dict:
    """Archive old irrelevant experiences to control DB size.
    
    - Experiences with confidence < 0.2 and retrieval < 2 and age > 30 days → archive
    - Archived > 90 days → permanent delete
    - Max 10,000 active entries
    """
    conn = sqlite3.connect(str(DB))
    try:
        total = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE confidence >= 0").fetchone()[0]
        archived = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE confidence = -1").fetchone()[0]
        forgotten = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE confidence = -2").fetchone()[0]
        
        result = {"total_active": total, "archived": archived, "forgotten": forgotten}
        
        if dry_run:
            candidates = conn.execute("""
                SELECT COUNT(*) FROM code_experiences
                WHERE confidence >= 0 AND confidence < 0.2 
                AND retrieval_count < 2
                AND julianday('now') - julianday(created_at) > 30
            """).fetchone()[0]
            result["candidates_for_archive"] = candidates
            
            to_delete = conn.execute("""
                SELECT COUNT(*) FROM code_experiences
                WHERE confidence = -1
                AND julianday('now') - julianday(created_at) > 90
            """).fetchone()[0]
            result["candidates_for_delete"] = to_delete
        else:
            # Archive old low-confidence entries
            conn.execute("""
                UPDATE code_experiences SET confidence = -1 WHERE confidence >= 0
                AND confidence < 0.2 AND retrieval_count < 2
                AND julianday('now') - julianday(created_at) > 30
            """)
            result["archived_now"] = conn.execute("SELECT changes()").fetchone()[0]
            
            # Permanently delete old archived entries
            conn.execute("""
                DELETE FROM code_experiences WHERE confidence = -1
                AND julianday('now') - julianday(created_at) > 90
            """)
            result["deleted_now"] = conn.execute("SELECT changes()").fetchone()[0]
            
            # If total > 10k, archive oldest
            if total > 10000:
                conn.execute("""
                    UPDATE code_experiences SET confidence = -1 WHERE id IN (
                        SELECT id FROM code_experiences WHERE confidence >= 0
                        ORDER BY retrieval_count ASC, confidence ASC
                        LIMIT ?
                    )
                """, (total - 10000,))
                result["overflow_archived"] = conn.execute("SELECT changes()").fetchone()[0]
        
        conn.commit()
        return result
    finally:
        conn.close()

def status():
    conn = sqlite3.connect(str(DB))
    total = conn.execute("SELECT COUNT(*) FROM code_experiences").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE confidence >= 0").fetchone()[0]
    avg_conf = conn.execute("SELECT AVG(confidence) FROM code_experiences WHERE confidence >= 0").fetchone()[0] or 0
    with_ast = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE ast_signature != ''").fetchone()[0]
    top_lang = conn.execute("SELECT language, COUNT(*) as c FROM code_experiences WHERE confidence >= 0 GROUP BY language ORDER BY c DESC LIMIT 1").fetchone()
    archived = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE confidence = -1").fetchone()[0]
    forgotten = conn.execute("SELECT COUNT(*) FROM code_experiences WHERE confidence = -2").fetchone()[0]
    conn.close()
    return {"total_experiences": total, "active": active, "avg_confidence": round(avg_conf, 2),
            "with_ast": with_ast, "top_language": top_lang[0] if top_lang else "none",
            "archived": archived, "forgotten": forgotten}

if __name__ == "__main__":
    print(init())
    r = store("TypeError: NoneType object is not subscriptable", "python",
              code_snippet="result = data['key']",
              explanation="Check None before subscript")
    print(f"Store: {r}")
    results = search("NoneType subscriptable", code_snippet="value = obj['name']", language="python")
    for res in results:
        print(f"  [{res['language']}] score={res['score']} -> {res['solution'][:60]}")
    print(json.dumps(status(), indent=2))
