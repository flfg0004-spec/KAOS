"""Bidirectional wikilink verification — Phase 11 cross-reference.

Verifies that every [[wikilink]] A→B has a corresponding ←A backlink in B.
Also suggests backlinks for semantically close pages that should reference each other.
"""

import re
from datetime import datetime
from pathlib import Path

from lib.config import IGNORED_PAGES
from lib.wikilinks import build_graph

BASE = (Path(__file__).resolve().parent.parent.parent)


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def verify_bidirectional() -> list[dict]:
    """Find wikilinks that are NOT reciprocated (A→B exists but B !→ A).

    Returns:
        List of unidirectional links with source, target, and suggestion.
    """
    page_map = build_graph()
    unidirectional = []

    for name, data in page_map.items():
        if name in IGNORED_PAGES:
            continue
        for link in data["links"]:
            target = link["target"].replace(".md", "")
            if target not in page_map:
                continue
            if target in IGNORED_PAGES:
                continue
            target_links = {l["target"].replace(".md", "") for l in page_map[target]["links"]}
            if name not in target_links:
                section = link.get("section", "")
                unidirectional.append({
                    "from": name,
                    "to": target,
                    "from_path": data["path"],
                    "to_path": page_map[target]["path"],
                    "section": section,
                    "fix": f"Añadir [[{name}]] en '{target}'",
                })

    return sorted(unidirectional, key=lambda x: x["from"])


def suggest_backlinks(top_k: int = 20) -> list[dict]:
    """Suggest orphan pages that should be backlinked from semantically similar content.

    Uses token-overlap similarity (fast, no external API).

    Args:
        top_k: Max suggestions to return

    Returns:
        List of suggested backlink additions.
    """
    page_map = build_graph()
    names = [n for n in page_map if n not in IGNORED_PAGES]
    if len(names) < 2:
        return []

    orphan_names = [
        n for n in names
        if not page_map[n].get("backlinks") and n not in {"index", "log"}
    ]
    if not orphan_names:
        return []

    suggestions = []
    for orphan in orphan_names:
        orphan_content = page_map[orphan].get("content", "")[:2000]
        orphan_tokens = set(re.findall(r"\w{4,}", orphan_content.lower()))
        if not orphan_tokens:
            continue

        scored = []
        for name in names:
            if name == orphan or name in IGNORED_PAGES:
                continue
            if orphan in {l["target"].replace(".md", "") for l in page_map[name]["links"]}:
                continue

            content = page_map[name].get("content", "")[:2000]
            tokens = set(re.findall(r"\w{4,}", content.lower()))
            overlap = len(orphan_tokens & tokens)
            if overlap >= 3:
                score = round(overlap / len(orphan_tokens), 3)
                scored.append((name, score))

        scored.sort(key=lambda x: -x[1])
        for name, score in scored[:3]:
            suggestions.append({
                "source": name,
                "target": orphan,
                "score": score,
                "from_path": page_map[name]["path"],
                "to_path": page_map[orphan]["path"],
                "suggestion": f"Añadir [[{orphan}]] en '{name}' (score: {score})",
            })

    suggestions.sort(key=lambda x: -x["score"])
    return suggestions[:top_k]


def report() -> str:
    """Generate a cross-reference report as markdown."""
    unidirectional = verify_bidirectional()
    backlink_suggestions = suggest_backlinks()

    lines = [
        "# Cross-Reference Report",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Unidirectional Wikilinks",
        f"**Total: {len(unidirectional)}**",
        "",
    ]

    if unidirectional:
        for u in unidirectional[:30]:
            lines.append(
                f"- [[{u['from']}]] → [[{u['to']}]] "
                f"*(falta backlink en `{u['to_path']}`)*"
            )
        if len(unidirectional) > 30:
            lines.append(f"\n*... y {len(unidirectional) - 30} más*")
        lines.append("")
    else:
        lines.append("Todos los wikilinks son bidireccionales. ✅\n")

    lines.append("## Suggested Backlinks for Orphans")
    lines.append(f"**Total: {len(backlink_suggestions)}**\n")
    if backlink_suggestions:
        for s in backlink_suggestions[:20]:
            lines.append(
                f"- [[{s['source']}]] ← [[{s['target']}]] "
                f"(score: {s['score']}, path: `{s['to_path']}`)"
            )
        if len(backlink_suggestions) > 20:
            lines.append(f"\n*... y {len(backlink_suggestions) - 20} más*")
        lines.append("")
    else:
        lines.append("No hay huérfanos que necesiten backlinks. ✅\n")

    if not unidirectional and not backlink_suggestions:
        lines.append("**Estado de salud del grafo: Cruzado perfecto.** ✅\n")

    lines.append(
        f"**Resumen: {len(unidirectional)} unidireccionales, "
        f"{len(backlink_suggestions)} backlinks sugeridos**"
    )
    return "\n".join(lines)
