"""Error Daemon — watchdog + tree-sitter + ErrorCatalog + auto-fix pipeline."""
import json, os, re, sqlite3, time, hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent.parent
CACHE = ROOT / ".memory" / "cache"
DB_PATH = CACHE / "error_catalog.db"
CACHE.mkdir(parents=True, exist_ok=True)

LANGUAGE_MAP = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".go": "go", ".rs": "rust",
}

_parsers = {}

def _get_parser(lang: str):
    if lang not in _parsers:
        from tree_sitter import Language, Parser
        lang_map = {
            "python": "tree_sitter_python",
            "javascript": "tree_sitter_javascript",
            "typescript": "tree_sitter_typescript",
            "go": "tree_sitter_go",
            "rust": "tree_sitter_rust",
        }
        mod_name = lang_map.get(lang)
        if not mod_name:
            return None
        try:
            mod = __import__(mod_name)
            lang_obj = Language(mod.language())
            _parsers[lang] = Parser(lang_obj)
        except Exception:
            return None
    return _parsers[lang]


def _init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            error_type TEXT NOT NULL,
            line INTEGER DEFAULT 0,
            message TEXT,
            language TEXT,
            hash TEXT UNIQUE,
            count INTEGER DEFAULT 1,
            first_seen TEXT,
            last_seen TEXT,
            auto_fixed INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_errors_file ON errors(file_path)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_errors_count ON errors(count DESC)
    """)
    conn.commit()
    return conn


class SyntaxChecker:
    """Check files for syntax errors using tree-sitter."""

    def check_file(self, path: Path) -> list[dict]:
        ext = path.suffix.lower()
        lang = LANGUAGE_MAP.get(ext)
        if not lang:
            return []
        parser = _get_parser(lang)
        if not parser:
            return []
        try:
            source = path.read_bytes()
            tree = parser.parse(source)
            errors = []
            if tree and tree.root_node:
                self._collect_errors(tree.root_node, source, errors, path)
            return errors
        except Exception as e:
            return [{"file": str(path), "error_type": "parse_error",
                     "line": 0, "message": str(e), "language": lang}]

    def _collect_errors(self, node, source: bytes, errors: list, path: Path):
        if node.type == "ERROR":
            line = source[:node.start_byte].count(b"\n") + 1
            errors.append({
                "file": str(path),
                "error_type": "syntax_error",
                "line": line,
                "message": f"Syntax error at line {line}",
                "language": LANGUAGE_MAP.get(path.suffix.lower(), "unknown"),
            })
            return  # Don't recurse into ERROR node
        for child in node.children:
            self._collect_errors(child, source, errors, path)


class ErrorCatalog:
    """Tracks errors with heatmap in SQLite."""

    def __init__(self):
        self.conn = _init_db()

    def record(self, errors: list[dict]) -> int:
        new_count = 0
        now = datetime.now().isoformat()
        for err in errors:
            hash_key = hashlib.md5(
                f"{err.get('file','')}:{err.get('line',0)}:{err.get('error_type','')}".encode()
            ).hexdigest()
            row = self.conn.execute(
                "SELECT id, count FROM errors WHERE hash = ?", (hash_key,)
            ).fetchone()
            if row:
                self.conn.execute(
                    "UPDATE errors SET count = count + 1, last_seen = ? WHERE id = ?",
                    (now, row[0])
                )
            else:
                self.conn.execute("""
                    INSERT INTO errors (file_path, error_type, line, message, language, hash, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (err.get("file",""), err.get("error_type",""), err.get("line",0),
                      err.get("message",""), err.get("language",""), hash_key, now, now))
                new_count += 1
        self.conn.commit()
        return new_count

    def heatmap(self, min_count: int = 3, limit: int = 20) -> list[dict]:
        rows = self.conn.execute("""
            SELECT file_path, error_type, line, message, count, first_seen, last_seen
            FROM errors
            WHERE count >= ?
            ORDER BY count DESC
            LIMIT ?
        """, (min_count, limit)).fetchall()
        return [
            {"file": r[0], "error_type": r[1], "line": r[2],
             "message": r[3], "frequency": r[4],
             "first_seen": r[5], "last_seen": r[6]}
            for r in rows
        ]

    def hot_files(self, threshold: int = 5) -> list[dict]:
        rows = self.conn.execute("""
            SELECT file_path, SUM(count) as total, COUNT(*) as errors
            FROM errors
            GROUP BY file_path
            HAVING total >= ?
            ORDER BY total DESC
        """, (threshold,)).fetchall()
        return [{"file": r[0], "total_errors": r[1], "unique_errors": r[2]} for r in rows]

    def stats(self) -> dict:
        total = self.conn.execute("SELECT COUNT(*) FROM errors").fetchone()[0]
        hot = self.conn.execute("SELECT COUNT(*) FROM errors WHERE count >= 3").fetchone()[0]
        files = self.conn.execute("SELECT COUNT(DISTINCT file_path) FROM errors").fetchone()[0]
        fixed = self.conn.execute("SELECT COUNT(*) FROM errors WHERE auto_fixed = 1").fetchone()[0]
        return {"total_errors": total, "hot_errors": hot, "files_affected": files, "auto_fixed": fixed}

    def mark_fixed(self, file_path: str):
        self.conn.execute("UPDATE errors SET auto_fixed = 1 WHERE file_path = ?", (file_path,))
        self.conn.commit()

    def close(self):
        self.conn.close()


class FileWatcher:
    """Watch for file changes and check syntax."""

    def __init__(self, paths: list[Path] = None, extensions: set = None):
        self.paths = paths or [
            ROOT / ".memory" / "_scripts",
            ROOT / ".opencode" / "skills",
            ROOT / ".tools",
        ]
        self.extensions = extensions or set(LANGUAGE_MAP.keys())
        self.checker = SyntaxChecker()
        self.catalog = ErrorCatalog()

    def scan_all(self) -> dict:
        total_errors = 0
        new_errors = 0
        files_scanned = 0
        for base in self.paths:
            if not base.exists():
                continue
            for ext in self.extensions:
                for f in base.rglob(f"*{ext}"):
                    if "node_modules" in str(f) or ".git" in str(f):
                        continue
                    files_scanned += 1
                    errors = self.checker.check_file(f)
                    if errors:
                        total_errors += len(errors)
                        new_errors += self.catalog.record(errors)
        return {"files_scanned": files_scanned, "errors_found": total_errors,
                "new_errors": new_errors, "timestamp": datetime.now().isoformat()}

    def watch(self, interval: int = 30, max_cycles: int = 0):
        cycle = 0
        while True:
            if max_cycles and cycle >= max_cycles:
                break
            result = self.scan_all()
            if result["errors_found"] > 0:
                hot = self.catalog.hot_files()
                if hot:
                    print(f"[error-daemon] Hot files detected: {len(hot)}")
                    for hf in hot[:3]:
                        print(f"  {hf['file']}: {hf['total_errors']} errors")
            cycle += 1
            time.sleep(interval)
        self.catalog.close()


def trigger_auto_fix(file_path: str, topic: str = None) -> dict:
    """Trigger pipeline for auto-fix of a file."""
    from lib.pipeline import init
    if not topic:
        topic = f"auto-fix: corregir errores en {Path(file_path).name}"
    pipeline_id = init(topic=topic, profile="auto-fix")
    return {"pipeline_id": pipeline_id, "file": file_path, "topic": topic}


def run_daemon_scan(paths: list[str] = None) -> dict:
    """Run a single scan cycle (for CLI/scheduler use)."""
    scan_paths = [Path(p) for p in paths] if paths else None
    watcher = FileWatcher(paths=scan_paths)
    result = watcher.scan_all()
    catalog = watcher.catalog
    result["stats"] = catalog.stats()
    hot = catalog.hot_files()
    if hot:
        result["hot_files"] = hot
    catalog.close()
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        watcher = FileWatcher()
        print(f"[error-daemon] Watching {len(watcher.paths)} directories...")
        watcher.watch(interval=30, max_cycles=0)
    else:
        result = run_daemon_scan()
        print(json.dumps(result, indent=2, default=str))
        print(f"\nErrors: {result['errors_found']} | New: {result['new_errors']} | Files: {result['files_scanned']}")
