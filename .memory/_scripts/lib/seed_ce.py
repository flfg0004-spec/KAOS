"""Seed CodeExperience with initial entries for bootstrap."""
import sqlite3
from pathlib import Path

DB = (Path(__file__).resolve().parent.parent.parent / ".memory" / "cache" / "code_experiences.db")

SEEDS = [
    {
        "code": "x = None; print(x['key'])",
        "error": "TypeError: 'NoneType' object is not subscriptable",
        "cmd": "py -3 -c 'x = None; print(x[\"key\"])'",
    },
    {
        "code": "d = {}; print(d['missing'])",
        "error": "KeyError: 'missing'",
        "cmd": "py -3 -c \"d = {}; print(d['missing'])\"",
    },
    {
        "code": "import nonexistent_module",
        "error": "ModuleNotFoundError: No module named 'nonexistent_module'",
        "cmd": "py -3 -c 'import nonexistent_module'",
    },
    {
        "code": "items = [1,2,3]; print(items[5])",
        "error": "IndexError: list index out of range",
        "cmd": "py -3 -c 'items = [1,2,3]; print(items[5])'",
    },
    {
        "code": "print(1/0)",
        "error": "ZeroDivisionError: division by zero",
        "cmd": "py -3 -c 'print(1/0)'",
    },
    {
        "code": "int('abc')",
        "error": "ValueError: invalid literal for int() with base 10: 'abc'",
        "cmd": "py -3 -c \"int('abc')\"",
    },
    {
        "code": "open('nonexistent.txt')",
        "error": "FileNotFoundError: [Errno 2] No such file or directory: 'nonexistent.txt'",
        "cmd": "py -3 -c \"open('nonexistent.txt')\"",
    },
    {
        "code": "import json; json.loads('{invalid}')",
        "error": "json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes",
        "cmd": "py -3 -c \"import json; json.loads('{invalid}')\"",
    },
    {
        "code": "def f(): pass; f(1, 2, 3)",
        "error": "TypeError: f() takes 0 positional arguments but 3 were given",
        "cmd": "py -3 -c 'def f(): pass; f(1, 2, 3)'",
    },
    {
        "code": "import os; os.chmod('file.txt', 0o777)",
        "error": "PermissionError: [Errno 13] Permission denied",
        "cmd": "py -3 -c \"import os; os.chmod('file.txt', 0o777)\"",
    },
]

def seed_code_experiences(count: int = 10) -> dict:
    """Seed initial CodeExperience entries if DB is empty.
    
    Args:
        count: Number of seeds to insert (cap to len(SEEDS))
    
    Returns:
        dict with status and count
    """
    conn = sqlite3.connect(str(DB))
    try:
        existing = conn.execute("SELECT COUNT(*) FROM code_experiences").fetchone()[0]
        if existing > 0:
            conn.close()
            return {"status": "skipped", "reason": f"already has {existing} entries", "count": existing}
    except Exception:
        pass
    
    # Create table if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS code_experiences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_hash TEXT UNIQUE,
            code_snippet TEXT,
            error_message TEXT,
            ast_signature TEXT,
            language TEXT DEFAULT 'python',
            confidence REAL DEFAULT 0.5,
            retrieval_count INTEGER DEFAULT 0,
            last_retrieved TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            command TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ce_hash ON code_experiences(error_hash)")
    
    import hashlib
    inserted = 0
    for seed in SEEDS[:min(count, len(SEEDS))]:
        error_hash = hashlib.sha256(seed["error"].encode()).hexdigest()[:16]
        try:
            conn.execute(
                "INSERT OR IGNORE INTO code_experiences(error_hash, code_snippet, error_message, command, language) VALUES (?, ?, ?, ?, 'python')",
                (error_hash, seed["code"], seed["error"][:500], seed["cmd"][:500])
            )
            if conn.total_changes > 0:
                inserted += 1
        except Exception:
            pass
    
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM code_experiences").fetchone()[0]
    conn.close()
    return {"status": "ok", "inserted": inserted, "total": total}

if __name__ == "__main__":
    result = seed_code_experiences()
    print(f"Seed: {result}")
