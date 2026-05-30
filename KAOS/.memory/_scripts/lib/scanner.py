"""Scanner: detect dead refs, duplicates, orphans, stale files."""

import re
from datetime import datetime, timedelta
from pathlib import Path

VAULT = (Path(__file__).resolve().parent.parent.parent)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def dead_refs() -> list[dict]:
    """Find references in index.md to concept/source files that don't exist.
    Resolves paths relative to wiki/ where index.md lives."""
    index_path = VAULT / "wiki" / "index.md"
    if not index_path.exists():
        return []
    content = _read(index_path)
    refs = re.findall(r'\(([^)]+)\)', content)
    results = []
    for ref in refs:
        ref_clean = ref.split("../")[-1].split("(")[0].strip()
        if not ref_clean.endswith(".md"):
            continue
        # Try multiple resolutions
        candidates = [
            VAULT / ref_clean,
            VAULT / "wiki" / ref_clean,
            VAULT / "schema" / ref_clean,
            VAULT / "raw" / ref_clean,
        ]
        found = any(c.exists() for c in candidates)
        if not found:
            results.append({"ref": ref_clean, "file": ref_clean, "status": "missing"})
    # Filter to only concept/source/entity/schema files (not markdown links to external)
    results = [r for r in results if not r["ref"].startswith("http")]
    return results


def duplicates() -> list[dict]:
    """Find duplicate entries in index.md by normalized name similarity."""
    index_path = VAULT / "wiki" / "index.md"
    if not index_path.exists():
        return []
    content = _read(index_path)
    entries = re.findall(r'- \[([^\]]+)\]', content)
    normalized = {}
    for e in entries:
        key = re.sub(r'^[\d\.\-]+\s*', '', e.lower().strip())
        key = re.sub(r'[\(\)\[\]]', '', key)
        if key in normalized:
            results = []
            for existing in normalized[key]:
                results.append({"a": existing, "b": e, "type": "duplicate"})
            return results
        normalized.setdefault(key, []).append(e)
    return []


def orphans() -> list[dict]:
    """Find wiki pages without backlinks (reuses lint logic)."""
    from lib.lint import orphan_pages, read_file
    files = list((VAULT / "wiki").rglob("*.md"))
    combined = ""
    for f in files:
        combined += read_file(f) + "\n"
    combined += read_file(VAULT / "schema" / "vault-policy.md") + "\n"
    orphaned = orphan_pages(files, combined)
    return [{"name": o.stem, "path": str(o.relative_to(VAULT))} for o in orphaned]


def stale(days: int = 90) -> list[dict]:
    """Find files not modified in >days."""
    cutoff = datetime.now() - timedelta(days=days)
    results = []
    for f in sorted((VAULT / "wiki").rglob("*.md")):
        if f.name == "log.md":
            continue
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < cutoff:
            age = (datetime.now() - mtime).days
            results.append({"path": str(f.relative_to(VAULT)), "days": age})
    return results


def pycache_dirs() -> list[Path]:
    """Find all __pycache__ directories."""
    return list(VAULT.rglob("__pycache__"))


def deprecated_ps() -> list[Path]:
    """Find all .ps1 files with DEPRECATED header."""
    results = []
    for f in (VAULT / "_scripts").glob("*.ps1"):
        content = _read(f)
        if "DEPRECATED" in content:
            results.append(f)
    return results


def summary() -> str:
    d = dead_refs()
    dup = duplicates()
    o = orphans()
    s = stale()
    pc = pycache_dirs()
    ps = deprecated_ps()
    return (
        f"Scanner Report:\n"
        f"  Dead refs: {len(d)}\n"
        f"  Duplicates: {len(dup)}\n"
        f"  Orphans: {len(o)}\n"
        f"  Stale files: {len(s)}\n"
        f"  __pycache__ dirs: {len(pc)}\n"
        f"  Deprecated PS: {len(ps)}"
    )
