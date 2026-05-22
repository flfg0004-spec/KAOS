#!/usr/bin/env python3
"""
vault-sync.py — Sync .memory/wiki/ enriched content to KAOS Obsidian vault.

The vault is a READ-ONLY enriched view. Source of truth is .memory/wiki/.

Usage:
    python vault-sync.py                  # Full sync (overwrite all)
    python vault-sync.py --dry-run        # Preview only
    python vault-sync.py --force          # Overwrite even if unchanged
    python vault-sync.py --quick          # Only new/changed files
    python vault-sync.py --help           # Show help
"""

import argparse
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    raise SystemExit(1)

# ─── Paths ────────────────────────────────────────────────────────────────────

SOURCE_BASE = Path(r"C:\Users\LeonX\Documents\KAOS\.memory")
VAULT_BASE = Path(r"C:\Users\LeonX\Documents\KAOS\KAOS")

WIKI = SOURCE_BASE / "wiki"
WIKI_ENTITIES = WIKI / "entities"
WIKI_CONCEPTS = WIKI / "concepts"
WIKI_SOURCES = WIKI / "sources"
SCHEMA = SOURCE_BASE / "schema"
CONCEPTS = SOURCE_BASE / "concepts"
DASHBOARD = SOURCE_BASE / ".vault" / "quality" / "dashboard.md"

DEST_AGENTES = VAULT_BASE / "01-agentes"
DEST_CONCEPTOS = VAULT_BASE / "02-conceptos"
DEST_REFERENCIAS = VAULT_BASE / "03-referencias"
DEST_ESQUEMA = VAULT_BASE / "04-esquema"
DEST_CALIDAD = VAULT_BASE / "05-calidad"

TODAY = datetime.now().strftime("%Y-%m-%d")

KNOWN_CONFIDENCE = {"alta", "media", "baja"}
KNOWN_STATUS = {"draft", "complete", "stub"}

# ─── Helpers ──────────────────────────────────────────────────────────────────


def sanitize_filename(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    ascii_str = ascii_str.replace("`", "").replace("'", "").replace('"', "")
    return ascii_str


def parse_frontmatter(content: str):
    fm = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw = parts[1]
            try:
                fm = yaml.safe_load(raw) or {}
            except yaml.YAMLError:
                fm = {}
            body = parts[2].strip()
    return fm, body


def build_frontmatter(content: str, src_path: Path, default_type: str = "concept") -> str:
    orig_fm, body = parse_frontmatter(content)
    raw_stem = src_path.stem
    clean_stem = sanitize_filename(raw_stem)

    # ── type ──
    fm_type = orig_fm.get("type", default_type)

    # ── title (H1 > existing frontmatter > filename) ──
    h1 = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = orig_fm.get("title")
    if not title:
        title = h1.group(1).strip() if h1 else raw_stem.replace("-", " ").title()

    # ── aliases: slug variants + related values ──
    aliases = []
    if clean_stem != raw_stem:
        aliases.append(clean_stem)
    if raw_stem not in aliases:
        aliases.append(raw_stem)

    # Convert related: to aliases
    if "related" in orig_fm:
        rel = orig_fm.pop("related")
        items = rel if isinstance(rel, list) else [x.strip() for x in str(rel).strip("[]").split(",") if x.strip()]
        for r in items:
            if r not in aliases:
                aliases.append(r)

    # ── tags ──
    tags = orig_fm.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.replace("[", "").replace("]", "").split(",") if t.strip()]
    if fm_type not in tags:
        tags.insert(0, fm_type)

    # ── created ──
    created = orig_fm.get("created") or orig_fm.get("date")
    if not created and src_path.exists():
        created = datetime.fromtimestamp(src_path.stat().st_ctime).strftime("%Y-%m-%d")
    if not created:
        created = TODAY

    # ── modified ──
    modified = TODAY
    if src_path.exists():
        modified = datetime.fromtimestamp(src_path.stat().st_mtime).strftime("%Y-%m-%d")

    # ── confidence (infer from existing if present) ──
    confidence = orig_fm.get("confidence", "media")
    if confidence not in KNOWN_CONFIDENCE:
        confidence = "media"

    # ── status ──
    status = orig_fm.get("status", "draft")
    if status not in KNOWN_STATUS:
        status = "draft"

    new_fm = {
        "type": fm_type,
        "title": title,
        "aliases": aliases,
        "tags": tags,
        "created": created,
        "modified": modified,
        "confidence": confidence,
        "status": status,
    }

    # Preserve agent-specific & metadata fields
    for key in ("role", "description", "mode", "agent", "source", "category",
                "mcp-servers", "permission", "skill", "url", "auto-distilled",
                "distill-engine", "related"):
        if key in orig_fm:
            new_fm[key] = orig_fm[key]

    yaml_str = yaml.dump(new_fm, default_flow_style=False, allow_unicode=True,
                         sort_keys=False, width=1000)
    return f"---\n{yaml_str}---\n\n{body}\n"


def resolve_duplicates(files: list[Path]) -> list[tuple[str, Path]]:
    groups = defaultdict(list)
    for fp in files:
        groups[sanitize_filename(fp.stem)].append(fp)

    result = []
    for clean_stem, entries in groups.items():
        if len(entries) == 1:
            result.append((clean_stem, entries[0]))
        else:
            entries.sort(key=lambda p: (
                0 if p.stem == clean_stem else 1,
                0 if "`" not in p.stem else 1,
                -len(p.stem),
            ))
            result.append((clean_stem, entries[0]))
    return result


# ─── File Collection ──────────────────────────────────────────────────────────


def collect_source_files():
    items = []

    # 1. wiki/entities/* → 01-agentes
    for fp in sorted(WIKI_ENTITIES.glob("*.md")):
        dest = DEST_AGENTES / sanitize_filename(fp.name)
        items.append((dest, fp, "agent"))

    # 2. wiki/concepts/* → 02-conceptos (resolve colliding names)
    wiki_concept_files = sorted(WIKI_CONCEPTS.glob("*.md"))
    for clean_stem, fp in resolve_duplicates(wiki_concept_files):
        items.append((DEST_CONCEPTOS / f"{clean_stem}.md", fp, "concept"))

    # 3. wiki/sources/* → 03-referencias (resolve colliding names)
    wiki_source_files = sorted(WIKI_SOURCES.glob("*.md"))
    for clean_stem, fp in resolve_duplicates(wiki_source_files):
        items.append((DEST_REFERENCIAS / f"{clean_stem}.md", fp, "source"))

    # 4. schema/* → 04-esquema
    for fp in sorted(SCHEMA.glob("*.md")):
        dest = DEST_ESQUEMA / sanitize_filename(fp.name)
        items.append((dest, fp, "adr"))

    # 5. quality dashboard → 05-calidad
    if DASHBOARD.exists():
        items.append((DEST_CALIDAD / "dashboard.md", DASHBOARD, "concept"))

    # 6. wiki root → vault root
    for fname in ("index.md", "glosario-kaos.md"):
        fp = WIKI / fname
        if fp.exists():
            items.append((VAULT_BASE / fname, fp, "concept"))

    # 7. strategy files in wiki root (*-strategy.md) → 02-conceptos
    for fp in sorted(WIKI.glob("*-strategy.md")):
        dest = DEST_CONCEPTOS / sanitize_filename(fp.name)
        items.append((dest, fp, "strategy"))

    # 8. .memory/concepts/* → 02-conceptos (skip if wiki/concepts has same name)
    if CONCEPTS.exists():
        wiki_stems = {sanitize_filename(f.stem) for f in WIKI_CONCEPTS.glob("*.md")}
        for fp in sorted(CONCEPTS.glob("*.md")):
            clean_stem = sanitize_filename(fp.stem)
            if clean_stem in wiki_stems:
                continue
            items.append((DEST_CONCEPTOS / f"{clean_stem}.md", fp, "concept"))

    return items


# ─── Generated Files ──────────────────────────────────────────────────────────


def generate_moc() -> str:
    return """---
type: moc
title: "Mapa de Contenido — Vault Enriquecido KAOS"
aliases: [moc, index, mapa]
tags: [moc, kaos, index]
created: 2026-05-21
modified: 2026-05-21
---

# Mapa de Contenido — Vault Enriquecido KAOS

## Agentes (1-agentes/)
```dataview
TABLE role AS Rol, file.outlinks AS Conexiones
FROM "01-agentes"
SORT file.name ASC
```

## Conceptos (2-conceptos/)
```dataview
TABLE confidence AS Confianza, status AS Estado, agent AS Agente
FROM "02-conceptos"
SORT file.name ASC
```

## Referencias (3-referencias/)
```dataview
TABLE category AS Categoria, confidence AS Confianza
FROM "03-referencias"
SORT file.name ASC
```

## Esquema (4-esquema/)
```dataview
TABLE file.name AS ADR
FROM "04-esquema"
SORT file.name ASC
```
"""


def generate_concept_index() -> str:
    return """---
type: index
title: "Conceptos — Indice"
tags: [index, conceptos]
---

# Conceptos

```dataview
TABLE type, confidence, agent
FROM "02-conceptos"
WHERE file.name != "_index_"
SORT file.name ASC
```
"""


# ─── Sync Engine ──────────────────────────────────────────────────────────────


def needs_sync(dest: Path, src: Path, force: bool, quick: bool) -> bool:
    if not dest.exists():
        return True
    if force:
        return True
    if quick:
        return dest.stat().st_mtime < src.stat().st_mtime
    return True  # full sync = always overwrite


def main():
    parser = argparse.ArgumentParser(
        description="Sync .memory/wiki/ enriched content to KAOS Obsidian vault."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing files even if unchanged")
    parser.add_argument("--quick", action="store_true",
                        help="Only sync new/changed files (check mtime)")
    args = parser.parse_args()

    items = collect_source_files()

    stats = {
        "synced": 0,
        "skipped": 0,
        "sanitized": 0,
        "errors": [],
    }

    # -- DRY RUN ---------------------------------------------------------------
    if args.dry_run:
        print("DRY RUN — No files will be written\n")
        print(f"{'Dest (relative to vault)':<55} {'Source (relative to .memory)':<65} Type")
        print("-" * 130)
        for dest, src, dtype in sorted(items, key=lambda x: (x[0].parent, x[0].name)):
            d = str(dest.relative_to(VAULT_BASE))
            s = str(src.relative_to(SOURCE_BASE))
            print(f"  {d:<53} {s:<65} {dtype}")
        count_renamed = sum(1 for _, src, _ in items if sanitize_filename(src.stem) != src.stem)
        print(f"\n  Total: {len(items)} files  |  Would sanitize: {count_renamed}")
        return

    # -- Ensure directories ----------------------------------------------------
    for d in (DEST_AGENTES, DEST_CONCEPTOS, DEST_REFERENCIAS,
              DEST_ESQUEMA, DEST_CALIDAD):
        d.mkdir(parents=True, exist_ok=True)

    # -- Process files ---------------------------------------------------------
    for dest, src, dtype in sorted(items, key=lambda x: (x[0].parent, x[0].name)):
        if not needs_sync(dest, src, args.force, args.quick):
            stats["skipped"] += 1
            continue

        try:
            content = src.read_text(encoding="utf-8")
            new_content = build_frontmatter(content, src, dtype)
            dest.write_text(new_content, encoding="utf-8")
            stats["synced"] += 1
            if sanitize_filename(src.stem) != src.stem:
                stats["sanitized"] += 1
        except Exception as e:
            stats["errors"].append(f"{src.relative_to(SOURCE_BASE)}: {e}")

    # -- Generate MOC ----------------------------------------------------------
    moc_path = VAULT_BASE / "00-MOC.md"
    moc_path.write_text(generate_moc(), encoding="utf-8")
    stats["synced"] += 1

    # -- Generate concept index ------------------------------------------------
    ci_path = DEST_CONCEPTOS / "_index_.md"
    ci_path.write_text(generate_concept_index(), encoding="utf-8")
    stats["synced"] += 1

    # -- Report ----------------------------------------------------------------
    print()
    print("=" * 62)
    print("  VAULT SYNC REPORT")
    print("=" * 62)
    print(f"  Files synced:     {stats['synced']}")
    print(f"  Files skipped:    {stats['skipped']}")
    print(f"  Files sanitized:  {stats['sanitized']}")
    if stats["errors"]:
        print(f"  Errors:           {len(stats['errors'])}")
        for err in stats["errors"]:
            print(f"    - {err}")
    print("=" * 62)


if __name__ == "__main__":
    main()
