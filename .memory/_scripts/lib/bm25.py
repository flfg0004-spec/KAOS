"""Shared BM25 keyword search fallback for when embeddings are unavailable.

Consolidates 3 separate BM25 implementations into one module.
Used by: vectorstore.py, hydrate.py, synapse.py
"""

from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent


def _get_md_files(base_dir: Path | None = None) -> list[Path]:
    if base_dir is None:
        base_dir = VAULT_ROOT
    exclude_dirs = {"cache", "_pending", ".git", "_scripts", "dashboard", "_archive"}
    return [f for f in base_dir.rglob("*.md") if not any(p in exclude_dirs for p in f.parts)]


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def search(query: str, top_k: int = 5, base_dir: Path | None = None) -> list[dict]:
    """BM25 keyword overlap search.

    Args:
        query: Search query text
        top_k: Max results to return
        base_dir: Directory to search (default: vault root)

    Returns:
        List of {path, snippet, score} dicts sorted by score descending
    """
    query_tokens = set(query.lower().split())
    if not query_tokens:
        return []

    md_files = _get_md_files(base_dir)
    scores = []
    for f in md_files:
        content = _read_file(f)
        tokens = set(content.lower().split())
        overlap = len(query_tokens & tokens)
        if overlap > 0:
            rel = f.relative_to(VAULT_ROOT.parent).as_posix() if VAULT_ROOT.parent in f.parents else f.name
            scores.append({
                "path": rel,
                "snippet": content[:200],
                "score": overlap / len(query_tokens),
            })
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:top_k]
