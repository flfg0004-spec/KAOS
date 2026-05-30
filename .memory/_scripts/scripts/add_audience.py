#!/usr/bin/env python3
"""Añade campo audience al frontmatter de archivos wiki/ si no existe.

Uso:
  py -3 _scripts/scripts/add_audience.py --dry-run   # solo reporta
  py -3 _scripts/scripts/add_audience.py --apply     # escribe cambios
"""

import argparse
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent  # .memory/
WIKI_DIRS = [BASE / "wiki" / "concepts", BASE / "wiki" / "entities"]

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def has_audience(frontmatter: str) -> bool:
    return bool(re.search(r"^audience:", frontmatter, re.MULTILINE))


def infer_audience(frontmatter: str, content: str, path: Path) -> str:
    """Infer audience based on tags and content patterns."""
    fm_lower = frontmatter.lower()
    if any(tag in fm_lower for tag in ["guide", "tutorial", "reference", "how-to"]):
        return "both"
    path_lower = path.stem.lower()
    if any(w in path_lower for w in ["guia", "tutorial", "guide", "reference", "intro"]):
        return "both"
    return "agent"


def add_audience_to_file(path: Path, dry_run: bool = True) -> dict:
    content = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {"path": str(path), "status": "no_frontmatter"}

    fm_text = match.group(1)
    if has_audience(fm_text):
        return {"path": str(path), "status": "already_has_audience"}

    audience = infer_audience(fm_text, content, path)
    new_fm = f"audience: {audience}\n" + fm_text
    new_content = content.replace(fm_text, new_fm, 1)

    if not dry_run:
        path.write_text(new_content, encoding="utf-8")

    return {"path": str(path), "status": "updated", "audience": audience}


def main():
    parser = argparse.ArgumentParser(description="Add audience field to wiki frontmatter")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Only report (default)")
    parser.add_argument("--apply", action="store_true", help="Actually write changes")
    args = parser.parse_args()

    dry_run = not args.apply
    total = {"updated": 0, "skipped": 0, "no_fm": 0}

    for wiki_dir in WIKI_DIRS:
        if not wiki_dir.exists():
            continue
        for f in sorted(wiki_dir.glob("*.md")):
            result = add_audience_to_file(f, dry_run=dry_run)
            if result["status"] == "updated":
                total["updated"] += 1
                if dry_run:
                    print(f"[DRY-RUN] {result['path']} -> audience: {result['audience']}")
                else:
                    print(f"[UPDATED] {result['path']} -> audience: {result['audience']}")
            elif result["status"] == "already_has_audience":
                total["skipped"] += 1
            elif result["status"] == "no_frontmatter":
                total["no_fm"] += 1

    print(f"\nResumen: {total['updated']} actualizados, {total['skipped']} ya tenian audience, {total['no_fm']} sin frontmatter")
    return 0


if __name__ == "__main__":
    sys.exit(main())
