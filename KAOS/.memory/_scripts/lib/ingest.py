"""Direct vault writer — writes content to .memory/raw/ with SHA-256 dedup."""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent.parent
RAW_DIR = BASE / ".memory" / "raw"
QUEUE_DIR = BASE / ".memory" / "ingest" / "queue"
MANIFEST_PATH = QUEUE_DIR / "manifest.json"

MIN_CONTENT_LENGTH = 50


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": 1, "items": [], "total_ingested": 0, "total_deduped": 0}


def _save_manifest(manifest: dict) -> None:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    manifest["last_updated"] = datetime.now().isoformat()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def _clean_slug(text: str) -> str:
    slug = text.lower().strip()[:60]
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-") or "untitled"


def ingest_text(text: str, title: str, source_type: str = "text", original_ref: str = "", profile: str = "standard") -> dict:
    """Write text directly to .memory/raw/ with dedup."""
    body = text.strip()
    if len(body) < MIN_CONTENT_LENGTH:
        return {"status": "error", "message": f"Content too short ({len(body)} chars)"}

    sha = _sha256(text)
    manifest = _load_manifest()
    for item in manifest["items"]:
        if item.get("sha256") == sha:
            manifest["total_deduped"] += 1
            _save_manifest(manifest)
            return {"status": "deduped", "sha256": sha, "path": ""}

    slug = _clean_slug(title)
    path = RAW_DIR / f"{slug}.md"
    disambiguator = 1
    while path.exists():
        disambiguator += 1
        path = RAW_DIR / f"{slug}-{disambiguator}.md"

    frontmatter = (
        f"---\ntype: ingest\nsource: {source_type}\n"
        f"original_ref: {original_ref}\nsha256: {sha}\n"
        f"ingested_at: {datetime.now().isoformat()}\nprofile: {profile}\n---\n\n"
    )
    path.write_text(frontmatter + body, encoding="utf-8")

    manifest["items"].append({
        "sha256": sha, "path": str(path.relative_to(BASE)),
        "source_type": source_type, "original_ref": original_ref,
        "ingested_at": datetime.now().isoformat(), "profile": profile,
    })
    manifest["total_ingested"] += 1
    _save_manifest(manifest)

    try:
        from lib.embeddings import update
        update(str(path.relative_to(BASE)))
    except Exception:
        pass

    return {"status": "ingested", "sha256": sha, "path": str(path.relative_to(BASE))}
