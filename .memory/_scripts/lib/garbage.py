"""Garbage orchestrator: time-based cleanup + existing scanner/cleaner/lint."""
from __future__ import annotations

import logging
import time
from pathlib import Path

from lib import cleaner, scanner
from lib import lint as lint_mod

MEMORY_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = MEMORY_ROOT / "cache"
RAW_DIR = MEMORY_ROOT / "raw"
LOGS_DIR = MEMORY_ROOT / "logs"

logger = logging.getLogger(__name__)


def collect_time_based_garbage(dry_run: bool = True) -> list[Path]:
    """Time-based file cleanup.

    Rules:
      - raw/ files >60 days without wikilink references
      - cache/ files >7 days (except knowledge-graph/ and bm25_index.json)
      - logs/ files >30 days
    """
    now = time.time()
    garbage: list[Path] = []

    if RAW_DIR.exists():
        cutoff = 60 * 86400
        for f in RAW_DIR.iterdir():
            if f.is_file() and (now - f.stat().st_mtime) > cutoff:
                garbage.append(f)

    if CACHE_DIR.exists():
        cutoff = 7 * 86400
        for f in CACHE_DIR.iterdir():
            if f.is_file() and f.name != "bm25_index.json" and (now - f.stat().st_mtime) > cutoff:
                garbage.append(f)

    if LOGS_DIR.exists():
        cutoff = 30 * 86400
        for f in LOGS_DIR.iterdir():
            if f.is_file() and (now - f.stat().st_mtime) > cutoff:
                garbage.append(f)

    if dry_run:
        logger.info("GC dry-run: %d files eligible for time-based cleanup", len(garbage))
    else:
        for f in garbage:
            f.unlink()
            logger.info("GC deleted: %s", f)

    return garbage


def report() -> str:
    return scanner.summary()


def collect(dry_run: bool = True) -> str:
    steps = []
    steps.append(cleaner.fix_dead_refs(dry_run))
    steps.append(cleaner.remove_index_duplicates(dry_run))
    steps.append(cleaner.remove_pycache(dry_run))
    steps.append(cleaner.remove_deprecated_ps(dry_run))
    steps.append(cleaner.add_mnemosyne_to_index(dry_run))
    steps.append(lint_mod.run())

    time_garbage = collect_time_based_garbage(dry_run=dry_run)
    if time_garbage:
        steps.append(f"Time-based GC: {len(time_garbage)} files {'would be' if dry_run else ''} cleaned")

    return "\n".join(steps)


def auto(dry_run: bool = True) -> str:
    from lib.cleaner import remove_pycache
    from lib.lint import run as lint_run
    steps = []
    steps.append(remove_pycache(dry_run=dry_run))
    steps.append(lint_run())
    return "\n".join(steps)


def run_gc(dry_run: bool = True) -> dict:
    """Run time-based GC and return stats."""
    garbage = collect_time_based_garbage(dry_run=dry_run)
    return {
        "files_eligible": len(garbage),
        "dry_run": dry_run,
        "total_size_bytes": sum(f.stat().st_size for f in garbage) if garbage else 0,
    }
