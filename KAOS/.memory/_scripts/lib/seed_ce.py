"""Seed CodeExperience with initial entries for bootstrap.
Uses code_memory.store() — no own schema. Multi-language support."""

from lib.code_memory import init, store

SEEDS = [
    # ── Python (10) ──
    {"code": "x = None; print(x['key'])", "error": "TypeError: 'NoneType' object is not subscriptable", "lang": "python"},
    {"code": "d = {}; print(d['missing'])", "error": "KeyError: 'missing'", "lang": "python"},
    {"code": "import nonexistent_module", "error": "ModuleNotFoundError: No module named 'nonexistent_module'", "lang": "python"},
    {"code": "items = [1,2,3]; print(items[5])", "error": "IndexError: list index out of range", "lang": "python"},
    {"code": "print(1/0)", "error": "ZeroDivisionError: division by zero", "lang": "python"},
    {"code": "int('abc')", "error": "ValueError: invalid literal for int() with base 10: 'abc'", "lang": "python"},
    {"code": "open('nonexistent.txt')", "error": "FileNotFoundError: [Errno 2] No such file or directory", "lang": "python"},
    {"code": "import json; json.loads('{invalid}')", "error": "json.decoder.JSONDecodeError: Expecting value", "lang": "python"},
    {"code": "def f(): pass; f(1, 2, 3)", "error": "TypeError: f() takes 0 positional arguments but 3 were given", "lang": "python"},
    {"code": "import os; os.chmod('file.txt', 0o777)", "error": "PermissionError: [Errno 13] Permission denied", "lang": "python"},
    # ── Rust (5) ──
    {"code": "let x: i32 = \"hello\";", "error": "error[E0308]: mismatched types expected i32, found &str", "lang": "rust"},
    {"code": "let x = vec![1,2,3]; println!(\"{}\", x[5]);", "error": "thread 'main' panicked at 'index out of bounds'", "lang": "rust"},
    {"code": "None.unwrap()", "error": "thread 'main' panicked at 'called `Option::unwrap()` on a `None` value'", "lang": "rust"},
    {"code": "let s: &str = String::from(\"hi\");", "error": "error[E0308]: mismatched types expected &str, found String", "lang": "rust"},
    {"code": "fn main() { let x = &y; }", "error": "error[E0425]: cannot find value `y` in this scope", "lang": "rust"},
    # ── JavaScript/TypeScript (5) ──
    {"code": "console.log(obj.key)", "error": "TypeError: Cannot read properties of undefined (reading 'key')", "lang": "javascript"},
    {"code": "JSON.parse('{invalid}')", "error": "SyntaxError: Unexpected token i in JSON at position 0", "lang": "javascript"},
    {"code": "null.map(x => x)", "error": "TypeError: Cannot read properties of null (reading 'map')", "lang": "javascript"},
    {"code": "console.log(x)", "error": "ReferenceError: x is not defined", "lang": "javascript"},
    {"code": "const a = 1; a = 2;", "error": "TypeError: Assignment to constant variable", "lang": "javascript"},
    # ── Go (3) ──
    {"code": "var s string; s = 42", "error": "cannot use 42 (type int) as type string in assignment", "lang": "go"},
    {"code": "m := make(map[string]int); m[\"k\"] = 1; delete(m, \"k\"); fmt.Println(m[\"k\"])", "error": "ok (zero value, not an error but common gotcha)", "lang": "go"},
    {"code": "s := \"hi\"; s[0] = 'H'", "error": "cannot assign to s[0] (strings are immutable)", "lang": "go"},
]


def seed_code_experiences(count: int = 10) -> dict:
    """Seed initial CodeExperience entries if DB is empty.

    Args:
        count: Number of seeds to insert (cap to len(SEEDS))

    Returns:
        dict with status and count
    """
    init()

    import sqlite3

    from lib.code_memory import DB
    conn = sqlite3.connect(str(DB))
    try:
        existing = conn.execute("SELECT COUNT(*) FROM code_experiences").fetchone()[0]
        if existing > 0:
            return {"status": "skipped", "reason": f"already has {existing} entries", "count": existing}
    except Exception:
        pass
    finally:
        conn.close()

    inserted = 0
    for seed in SEEDS[:min(count, len(SEEDS))]:
        result = store(
            error_message=seed["error"][:500],
            language=seed["lang"],
            code_snippet=seed["code"][:500],
            explanation=f"Seed: common {seed['lang']} error pattern"
        )
        if result["status"] == "created":
            inserted += 1

    import sqlite3
    conn = sqlite3.connect(str(DB))
    total = conn.execute("SELECT COUNT(*) FROM code_experiences").fetchone()[0]
    conn.close()
    return {"status": "ok", "inserted": inserted, "total": total}


if __name__ == "__main__":
    result = seed_code_experiences()
    print(f"Seed: {result}")
