"""Memory lifecycle management with Ebbinghaus decay.

Tiers:
  new (0-7d) → active (7-14d) → frozen (14-30d) → archive (30-90d) → stale (>90d)

Confidence decays exponentially: confidence *= exp(-0.02 * days_since_modification)
"""

import re
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta

BASE = (Path(__file__).resolve().parent.parent.parent)
ARCHIVE = BASE / "_archive"
LIFECYCLE_FILE = BASE / "cache" / "lifecycle.json"

DECAY_RATE = 0.02
TIER_THRESHOLDS = {
    "new": (0, 7),
    "active": (7, 14),
    "frozen": (14, 30),
    "archive": (30, 90),
    "stale": (90, float("inf")),
}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _get_md_files() -> list[Path]:
    exclude = {".git", "cache", "_pending", "_scripts", "dashboard"}
    return [f for f in (BASE / "wiki").rglob("*.md") if not any(p in exclude for p in f.parts)]


def _get_tier(days_since_mod: float) -> str:
    for tier, (low, high) in TIER_THRESHOLDS.items():
        if low <= days_since_mod < high:
            return tier
    return "stale"


def evaluate(path: Path) -> dict:
    """Evaluate a single file's lifecycle state."""
    if not path.exists():
        return {"path": str(path), "error": "File not found"}
    if not path.is_file():
        return {"path": str(path), "error": "Not a file"}
    if path.suffix != ".md":
        return {"path": str(path), "error": "Not a markdown file"}

    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
    except (OSError, ValueError) as e:
        return {"path": str(path), "error": f"Cannot read mtime: {e}"}
    days_since_mod = max(0, (datetime.now() - mtime).days)
    tier = _get_tier(days_since_mod)
    confidence = _confidence_score(days_since_mod)

    content = _read(path)
    has_frontmatter = content.startswith("---")
    has_tags = bool(re.search(r"^tags:", content, re.MULTILINE))
    link_count = len(re.findall(r"\[\[([^\]]+?)\]\]", content))
    word_count = len(re.findall(r"\w+", content))

    return {
        "path": str(path.relative_to(BASE) if BASE in path.parents else path),
        "tier": tier,
        "days_since_mod": days_since_mod,
        "confidence": round(confidence, 3),
        "frontmatter": has_frontmatter,
        "tags": has_tags,
        "links": link_count,
        "words": word_count,
        "recommendation": _recommendation(tier, confidence, has_frontmatter, link_count),
    }


def _confidence_score(days: float) -> float:
    return max(0.0, 1.0 * (1.0 - (1.0 - 0.05) * days / 365))


def _recommendation(tier: str, confidence: float, has_frontmatter: bool, link_count: int) -> str:
    if tier == "stale" and confidence < 0.3:
        return "ARCHIVE: Stale with low confidence"
    if tier == "archive":
        return "REVIEW: Consider archival or refresh"
    if tier == "frozen":
        return "OK: Stable, no action needed"
    if tier == "active" and link_count < 2:
        return "LINK: Add more [[wikilinks]]"
    if not has_frontmatter:
        return "FM: Add frontmatter"
    if tier == "new":
        return "GROW: Recently created, allow to mature"
    return "OK"


def run_evaluate_all(dry_run: bool = True) -> list[dict]:
    """Evaluate all wiki files and return lifecycle report."""
    results = []
    for f in _get_md_files():
        try:
            r = evaluate(f)
            if "error" not in r:
                results.append(r)
        except Exception:
            pass
    return sorted(results, key=lambda x: x.get("confidence", 1))


def run_promotion(dry_run: bool = True) -> list[dict]:
    """Auto-promote/demote notes based on tier thresholds."""
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    actions = []
    for f in _get_md_files():
        try:
            eval_result = evaluate(f)
        except Exception:
            continue
        tier = eval_result.get("tier", "unknown")

        if tier == "stale" and not dry_run:
            try:
                rel = f.relative_to(BASE)
            except ValueError:
                continue
            archive_path = ARCHIVE / rel
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            if f.exists():
                shutil.move(str(f), str(archive_path))
                actions.append({"path": str(rel), "action": "archived", "reason": "Stale > 90 days"})

        elif tier == "archive" and not dry_run:
            actions.append({"path": str(f.relative_to(BASE)), "action": "flag_review", "reason": "Archive tier, needs review"})

    return actions


def status() -> str:
    """Generate a human-readable lifecycle status."""
    results = run_evaluate_all(dry_run=True)
    tiers = {}
    for r in results:
        t = r.get("tier", "unknown")
        tiers[t] = tiers.get(t, 0) + 1

    avg_conf = sum(r.get("confidence", 0) for r in results) / max(len(results), 1)
    flagged = [r for r in results if r.get("recommendation", "OK") != "OK"]

    lines = [
        "# Memory Lifecycle Status",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Tier Distribution",
    ]
    for tier in ["new", "active", "frozen", "archive", "stale"]:
        count = tiers.get(tier, 0)
        lines.append(f"- **{tier}**: {count}")
    lines.append("")
    lines.append(f"**Average confidence:** {avg_conf:.3f}")
    lines.append(f"**Flagged notes:** {len(flagged)}")
    lines.append("")

    if flagged:
        lines.append("## Recommendations\n")
        for r in flagged[:20]:
            lines.append(f"- {r['path']}: {r['recommendation']} (tier: {r['tier']}, conf: {r['confidence']})")
        lines.append("")

    return "\n".join(lines)
