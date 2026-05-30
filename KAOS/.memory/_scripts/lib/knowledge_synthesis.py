"""Automatic knowledge synthesis for low-scoring documents.

Detects which metrics are deficient and applies targeted corrections:
- Frontmatter missing → generated
- Low wikilinks → txtai semantic search for suggestions
- Poor structure → heading reorganization
- Missing sources → URL extraction
"""

import difflib
import logging
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

from lib.config import KNOWLEDGE_SYNTHESIS_MAX_DIFF_RATIO
from lib.frontmatter_utils import extract_frontmatter
from lib.knowledge_levels import needs_synthesis

logger = logging.getLogger(__name__)

SYNTHESIS_OPERATIONS = {
    "frontmatter": lambda content, scores: None,
    "wikilinks": lambda content, scores: None,
    "structure": lambda content, scores: None,
    "sources": lambda content, scores: None,
}


def synthesize(path: str | Path, scores: dict, dry_run: bool = True) -> dict:
    """Execute targeted synthesis for a low-scoring document.

    Args:
        path: Path to the .md file
        scores: Result from knowledge_scorer.score_document()
        dry_run: If True, don't write changes, just report what would change

    Returns:
        Dict with:
          - path: str
          - score_before: float
          - score_after: float (None if dry_run)
          - operations: list of operations performed
          - diff_ratio: float (0.0-1.0)
          - backup_path: str or None
          - error: str or None
    """
    result = {
        "path": str(path),
        "score_before": scores.get("score", 0),
        "score_after": None,
        "operations": [],
        "diff_ratio": 0.0,
        "backup_path": None,
        "error": None,
    }

    path_obj = Path(path)

    if not path_obj.exists():
        result["error"] = f"File not found: {path}"
        return result

    score = scores.get("score", 100)
    if not needs_synthesis(score):
        result["error"] = f"Score {score} >= 60, no synthesis needed"
        return result

    try:
        original_content = path_obj.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        result["error"] = f"Failed to read: {e}"
        return result

    # Check if document was already synthesized (dedup)
    if "synthesized_at" in _extract_frontmatter(original_content):
        result["error"] = "Document already synthesized, skipping"
        return result

    # Check if document is CANONICAL
    level = scores.get("level", "")
    if level == "CANONICAL":
        result["error"] = "CANONICAL documents are never synthesized"
        return result

    content = original_content
    metrics = scores.get("metrics", {})

    # ---- Perform operations ----
    fm = _extract_frontmatter(content)
    needs_fm = not fm or not all(k in fm for k in ("title", "tags", "created"))

    if needs_fm:
        new_content = _synthesize_frontmatter(content, fm, path_obj)
        if new_content != content:
            result["operations"].append("frontmatter")
            content = new_content

    # wikilinks: if conectividad score < 30
    conectividad = metrics.get("conectividad", {})
    if conectividad.get("score", 100) < 30:
        new_content = _synthesize_wikilinks(content, scores, path_obj)
        if new_content != content:
            result["operations"].append("wikilinks")
            content = new_content

    # structure: if legibilidad score < 40 and content has > 500 words
    legibilidad = metrics.get("legibilidad", {})
    word_count = len(re.findall(r"\w+", content))
    if legibilidad.get("score", 100) < 40 and word_count > 500:
        new_content = _synthesize_structure(content, scores)
        if new_content != content:
            result["operations"].append("structure")
            content = new_content

    # sources: if precision_factual score < 30
    precision = metrics.get("precision_factual", {})
    if precision.get("score", 100) < 30:
        new_content = _synthesize_sources(content, scores)
        if new_content != content:
            result["operations"].append("sources")
            content = new_content

    # ---- Calculate diff ratio ----
    diff_ratio = estimate_diff_ratio(original_content, content)
    result["diff_ratio"] = diff_ratio

    if not result["operations"]:
        result["error"] = "No operations performed"
        return result

    # ---- Guard: diff ratio must be within limits, retry if exceeded ----
    if diff_ratio > KNOWLEDGE_SYNTHESIS_MAX_DIFF_RATIO:
        logger.info("Diff ratio %.2f exceeds limit, retrying with single operations", diff_ratio)
        content = original_content
        result["operations"] = []
        single_ops = [
            ("frontmatter", needs_fm, lambda: _synthesize_frontmatter(content, fm, path_obj)),
            ("wikilinks", conectividad.get("score", 100) < 30, lambda: _synthesize_wikilinks(content, scores, path_obj)),
            ("sources", precision.get("score", 100) < 30, lambda: _synthesize_sources(content, scores)),
        ]
        for op_name, should_run, fn in single_ops:
            if not should_run:
                continue
            new_c = fn()
            if new_c != content:
                op_diff = estimate_diff_ratio(original_content, new_c)
                if op_diff <= KNOWLEDGE_SYNTHESIS_MAX_DIFF_RATIO:
                    result["operations"].append(op_name)
                    content = new_c
                else:
                    logger.info("Skipped %s: diff ratio %.2f exceeds limit", op_name, op_diff)
        diff_ratio = estimate_diff_ratio(original_content, content)
        result["diff_ratio"] = diff_ratio

    if not result["operations"]:
        result["error"] = (
            f"Diff ratio {diff_ratio:.2f} exceeds max "
            f"{KNOWLEDGE_SYNTHESIS_MAX_DIFF_RATIO}"
        )
        result["operations"] = []
        return result

    # ---- Dry-run or write ----
    if dry_run:
        return result

    # ---- OPA governance check before write (fail-closed) ----
    try:
        from lib.opa_bridge import check_synthesis

        gov = check_synthesis({
            "path": str(path_obj),
            "score": score,
            "level": level,
            "diff_ratio": diff_ratio,
            "operations": result["operations"],
            "dry_run": dry_run,
            "max_diff_ratio": KNOWLEDGE_SYNTHESIS_MAX_DIFF_RATIO,
        })
        if not gov.get("allowed", True):
            denials = gov.get("denials", ["OPA policy denied synthesis"])
            result["error"] = "; ".join(denials)
            result["opa_denied"] = True
            return result
        result["opa_allowed"] = True
    except Exception as e:
        logger.warning("OPA check failed, denying synthesis: %s", e)
        result["error"] = f"OPA check unavailable: {e}"
        result["opa_denied"] = True
        return result

    # Create backup
    backup = create_backup(path_obj)
    result["backup_path"] = str(backup) if backup else None

    try:
        path_obj.write_text(content, encoding="utf-8")
    except Exception as e:
        result["error"] = f"Failed to write: {e}"
        return result

    # Mark document as synthesized (dedup for future cycles)
    try:
        stamped = path_obj.read_text(encoding="utf-8")
        if stamped.startswith("---"):
            end = stamped.find("---", 3)
            if end != -1:
                today = datetime.now().strftime("%Y-%m-%d")
                if "synthesized_at" not in stamped[:end]:
                    new_fm = stamped[3:end].rstrip() + f"\nsynthesized_at: {today}\n"
                    stamped = "---" + new_fm + "---" + stamped[end + 3:]
                    path_obj.write_text(stamped, encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to mark synthesized_at: %s", e)

    # Re-score after synthesis
    try:
        from lib.knowledge_scorer import score_document

        post_scores = score_document(path_obj)
        result["score_after"] = post_scores.get("score")
    except Exception as e:
        logger.warning("Re-scoring failed after synthesis: %s", e)

    # Auto-rollback if score degraded significantly
    if result.get("score_after") is not None and backup:
        try:
            rollback_result = auto_rollback(path_obj, backup, score, result["score_after"])
            if rollback_result["rolled_back"]:
                result["rolled_back"] = True
                result["rollback_reason"] = rollback_result["reason"]
                result["score_after"] = score
                logger.info("Auto-rollback executed: %s", rollback_result["reason"])
        except Exception as e:
            logger.warning("Auto-rollback failed: %s", e)

    return result


def auto_rollback(path: Path, backup_path: Path, score_before: float, score_after: float) -> dict:
    """Restore backup if score degraded significantly after synthesis.

    Args:
        path: Original file path
        backup_path: Path to .bak backup
        score_before: Score before synthesis
        score_after: Score after synthesis

    Returns:
        Dict with rolled_back (bool) and reason (str)
    """
    result = {"rolled_back": False, "reason": ""}
    if score_after is None or score_before is None:
        return result
    if score_after >= score_before - 10:
        return result
    if not backup_path.exists():
        result["reason"] = "Backup file not found"
        return result
    try:
        import shutil
        shutil.copy2(str(backup_path), str(path))
        result["rolled_back"] = True
        result["reason"] = (
            f"Score dropped from {score_before:.1f} to {score_after:.1f} "
            f"(delta: {score_after - score_before:+.1f})"
        )
    except Exception as e:
        result["reason"] = f"Rollback failed: {e}"
    return result


def estimate_diff_ratio(original: str, modified: str) -> float:
    """Estimate what fraction of the document changed."""
    if not original and not modified:
        return 0.0
    if not original or not modified:
        return 1.0

    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)

    matcher = difflib.SequenceMatcher(None, orig_lines, mod_lines)
    # Count changed lines
    added = 0
    removed = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            added += j2 - j1
            removed += i2 - i1
        elif tag == "delete":
            removed += i2 - i1
        elif tag == "insert":
            added += j2 - j1

    total = max(len(orig_lines), len(mod_lines))
    if total == 0:
        return 0.0
    ratio = (added + removed) / (2.0 * total)
    return round(min(1.0, ratio), 4)


def create_backup(path: Path) -> Path | None:
    """Create .bak backup before modifying."""
    try:
        backup_path = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(str(path), str(backup_path))
        logger.info("Backup created: %s", backup_path)
        return backup_path
    except Exception as e:
        logger.warning("Failed to create backup for %s: %s", path, e)
        return None


# ── Internal helpers ─────────────────────────────────────────────


def _extract_frontmatter(content: str) -> dict:
    return extract_frontmatter(content)


def _extract_keywords(content: str, top_n: int = 5) -> list[str]:
    """Extract top-N keywords from document content.

    Filters out common stopwords and sorts by frequency.
    """
    stopwords = {
        "el", "la", "los", "las", "un", "una", "unos", "unas",
        "y", "e", "o", "u", "pero", "sino", "porque", "como",
        "que", "de", "en", "a", "al", "del", "con", "por",
        "para", "es", "son", "su", "sus", "se", "no", "lo",
        "le", "les", "este", "esta", "esto", "entre",
        "ser", "estar", "haber", "tener", "hacer", "poder",
        "más", "muy", "tan", "tanto", "todo", "cada", "sin",
        "sobre", "tras", "durante", "mediante", "excepto",
        "the", "and", "for", "are", "but", "not", "you", "all",
        "can", "had", "her", "was", "one", "our", "out", "has",
    }
    # Remove frontmatter, headings, wikilinks, code blocks for keyword extraction
    text = re.sub(r"^---.*?---\s*", "", content, flags=re.DOTALL)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"^#+\s*.*$", "", text, flags=re.MULTILINE)

    words = re.findall(r"[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+", text.lower())
    words = [w for w in words if len(w) > 3 and w not in stopwords]

    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda x: -x[1])
    return [w for w, _ in sorted_words[:top_n]]


def _synthesize_frontmatter(content: str, fm: dict, path: Path) -> str:
    """Add missing frontmatter fields."""
    today = datetime.now().strftime("%Y-%m-%d")

    # If no frontmatter at all, generate from first heading
    if not fm:
        first_heading = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = first_heading.group(1).strip() if first_heading else path.stem.replace("-", " ").title()

        keywords = _extract_keywords(content, top_n=5)
        tags_str = ", ".join(keywords) if keywords else title.lower()

        new_fm = (
            "---\n"
            f"title: {title}\n"
            f"tags: [{tags_str}]\n"
            f"created: {today}\n"
            f"modified: {today}\n"
            f"confidence: media\n"
            "---\n"
        )
        return new_fm + content.lstrip()

    # Fill missing fields
    lines = content.split("\n")
    fm_end = content.find("---", 3)
    fm_text = content[3:fm_end]

    new_fields = []
    if "title" not in fm:
        first_heading = re.search(r"^#\s+(.+)$", content[fm_end + 3:], re.MULTILINE)
        title = first_heading.group(1).strip() if first_heading else path.stem.replace("-", " ").title()
        new_fields.append(f"title: {title}")
    if "tags" not in fm:
        keywords = _extract_keywords(content, top_n=5)
        tags_str = ", ".join(keywords) if keywords else "general"
        new_fields.append(f"tags: [{tags_str}]")
    if "created" not in fm:
        new_fields.append(f"created: {today}")
    if "modified" not in fm:
        new_fields.append(f"modified: {today}")
    if "confidence" not in fm:
        new_fields.append("confidence: media")

    if not new_fields:
        return content

    new_fm_text = fm_text.rstrip() + "\n" + "\n".join(new_fields) + "\n"
    return "---\n" + new_fm_text + "---" + content[fm_end + 3:]


def _synthesize_wikilinks(content: str, scores: dict, path: Path) -> str:
    """Suggest wikilinks based on txtai semantic similarity or keywords."""
    # Don't add if section already exists
    if re.search(r"##\s*Véase también", content) or re.search(r"##\s*See also", content):
        return content

    keywords = _extract_keywords(content, top_n=5)
    wikilinks = []

    if os.environ.get("KAOS_TESTING") != "1":
        try:
            from lib.vectorstore import query

            for kw in keywords:
                results = query(kw, top_k=3)
                for r in results:
                    link_text = r.get("title") or r.get("path", "")
                    if link_text:
                        link = link_text.replace(".md", "").replace("/", ":")
                        if link not in wikilinks:
                            wikilinks.append(link)
        except Exception as e:
            logger.debug("txtai query failed for wikilinks: %s", e)
    else:
        # In testing mode, use keywords as wikilinks
        wikilinks = [w.capitalize() for w in keywords]

    if not wikilinks:
        return content

    # Limit to 5 wikilinks
    wikilinks = wikilinks[:5]

    links_md = "\n".join(f"- [[{w}]]" for w in wikilinks)
    see_also = f"\n\n## Véase también\n\n{links_md}\n"

    return content.rstrip() + see_also


def _synthesize_structure(content: str, scores: dict) -> str:
    """Improve heading structure for documents with poor organization.

    Preserves existing structure if:
    - Document has 2+ ``##`` headings (already organized)
    - Document contains numbered lists or tables (intentional structure)
    - Document has <= 500 words (too short to restructure)
    """
    word_count = len(re.findall(r"\w+", content))
    if word_count <= 500:
        return content

    # Preserve if already has 2+ ## headings
    headings = re.findall(r"^##\s.+", content, re.MULTILINE)
    if len(headings) >= 2:
        return content

    # Preserve numbered lists and tables — indicate intentional structure
    if re.search(r"(?:^|\n)\s*\d+\.\s", content) or re.search(r"\|.*\|.*\|", content):
        return content

    # Remove frontmatter for structure detection
    body = content
    fm_end = 0
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            fm_end = end + 3

    body = content[fm_end:].strip()

    # Split into paragraphs
    paragraphs = [p.strip() for p in body.split("\n\n") if len(p.strip()) > 20]

    if len(paragraphs) < 3:
        return content

    third = max(1, len(paragraphs) // 3)

    intro_paras = "\n\n".join(paragraphs[:third])
    dev_paras = "\n\n".join(paragraphs[third:2 * third])
    conc_paras = "\n\n".join(paragraphs[2 * third:])

    structured = content[:fm_end]
    if structured:
        structured += "\n\n"

    structured += (
        f"## Introducción\n\n{intro_paras}\n\n"
        f"## Desarrollo\n\n{dev_paras}\n\n"
        f"## Conclusión\n\n{conc_paras}\n"
    )

    return structured


def _synthesize_sources(content: str, scores: dict) -> str:
    """Extract URLs and create a references section."""
    # Check if references section already exists
    if re.search(r"##\s*(Referencias|References|Fuentes|Sources)", content):
        return content

    urls = re.findall(r"https?://[^\s\)\"'<>]+", content)
    if not urls:
        return content

    # Deduplicate
    unique_urls = list(set(urls))[:10]

    refs = "\n\n## Referencias\n\n"
    for i, url in enumerate(unique_urls, 1):
        refs += f"{i}. {url}\n"
    refs += "\n"

    return content.rstrip() + refs


# ── CLI entry point ──────────────────────────────────────────────


def main():
    """Simple CLI to synthesize documents."""
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Synthesis CLI")
    parser.add_argument("path", nargs="?", help="Path to document or directory")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Don't write changes (default: True)")
    parser.add_argument("--write", action="store_true",
                        help="Actually write changes (overrides --dry-run)")

    args = parser.parse_args()

    if args.write:
        args.dry_run = False

    from lib.knowledge_scorer import score_directory, score_document

    if args.path and Path(args.path).is_dir():
        results = score_directory(args.path)
    elif args.path:
        results = [score_document(args.path)]
    else:
        from lib.config import VAULT_ROOT
        results = score_directory(VAULT_ROOT / "wiki")

    print(f"Found {len(results)} documents")
    low_score = [r for r in results if r.get("score", 100) < 60]
    print(f"Low-scoring (< 60): {len(low_score)}")

    for r in low_score:
        res = synthesize(r["path"], r, dry_run=args.dry_run)
        ops = ", ".join(res.get("operations", [])) or "none"
        err = res.get("error") or ""
        print(f"  {Path(r['path']).name}: score={r['score']:.1f} ops=[{ops}] {err}")


if __name__ == "__main__":
    main()
