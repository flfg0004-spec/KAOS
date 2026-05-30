"""Mnemosyne GC Integration — Identify orphaned wiki files.

Orphans = files in .memory/wiki/ that are not linked from
any other wiki file, AGENTS.md, or SKILL.md.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

MEMORY_ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = MEMORY_ROOT / "wiki"
OPCODE_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".opencode"

WIKILINK_PATTERN = re.compile(r'\[\[([^\]|#]+)')


def find_orphan_wikilinks(dry_run: bool = True) -> list[Path]:
    """Find wiki files not referenced by any wikilink."""
    if not WIKI_DIR.exists():
        return []

    all_wiki_files = list(WIKI_DIR.rglob("*.md"))

    referenced: set[str] = set()
    for f in all_wiki_files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            for m in WIKILINK_PATTERN.finditer(content):
                referenced.add(m.group(1).strip())
        except Exception:
            continue

    for extra_dir in [OPCODE_DIR, MEMORY_ROOT]:
        if extra_dir.exists():
            for f in extra_dir.rglob("*.md"):
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                    for m in WIKILINK_PATTERN.finditer(content):
                        referenced.add(m.group(1).strip())
                except Exception:
                    continue

    orphans: list[Path] = []
    for f in all_wiki_files:
        stem = f.stem
        normalized = stem.replace(" ", "_").replace("-", "_")
        if normalized not in referenced and stem not in referenced:
            orphans.append(f)

    if dry_run:
        logger.info("Mnemosyne GC: %d orphan files found", len(orphans))
    else:
        logger.info("Mnemosyne GC: %d orphan files identified (quarantine not yet implemented)", len(orphans))

    return orphans
