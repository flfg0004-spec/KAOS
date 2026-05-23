import re
from pathlib import Path
from datetime import datetime, timedelta
from lib.config import VAULT_ROOT, IGNORED_PAGES, IGNORED_WIKILINKS


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def broken_links(files: list[Path]) -> tuple[list[str], str]:
    combined = ""
    for f in files:
        combined += read_file(f) + "\n"
    combined += read_file(VAULT_ROOT / "schema" / "vault-policy.md") + "\n"

    links = re.findall(r"\[\[([^\]]+?)\]\]", combined)
    unique = set()
    for link in links:
        target = link.split("|")[0].split("#")[0].strip()
        if target:
            unique.add(target)

    broken = []
    for target in unique:
        if target.lower() in IGNORED_WIKILINKS:
            continue
        found = False
        for ext in ("", ".md"):
            for base in ("wiki", "raw", "schema"):
                p = VAULT_ROOT / base / f"{target}{ext}"
                if p.exists():
                    found = True
                    break
                for md in (VAULT_ROOT / base).rglob(f"*{ext}"):
                    if md.stem == target:
                        found = True
                        break
                if found:
                    break
            if found:
                break
        if not found:
            broken.append(target)
    return broken, combined


def orphan_pages(files: list[Path], combined: str) -> list[Path]:
    orphans = []
    for f in files:
        name = f.stem
        if name in IGNORED_PAGES:
            continue
        pattern = re.escape(name)
        if not re.search(r"\[\[" + pattern + r"(?:\|[\w\s-]+)?\]\]", combined):
            orphans.append(f)
    return orphans


def stale_pages(files: list[Path], max_days: int = 90) -> list[tuple[Path, int]]:
    cutoff = datetime.now() - timedelta(days=max_days)
    stale = []
    for f in files:
        if f.name == "log.md":
            continue
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < cutoff:
            days_old = (datetime.now() - mtime).days
            stale.append((f, days_old))
    return stale


def contradictions(files: list[Path]) -> list[Path]:
    result = []
    for f in files:
        content = read_file(f)
        if "Contradiction" in content or "contradiction" in content:
            result.append(f)
    return result


def run() -> str:
    files = list((VAULT_ROOT / "wiki").rglob("*.md"))
    files += list((VAULT_ROOT / "schema").glob("adr-*.md"))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    combined = ""
    broken, combined = broken_links(files)
    wiki_only = [f for f in files if "schema" not in f.parts and "sources" not in f.parts]
    orphans = orphan_pages(wiki_only, combined)
    stale = stale_pages(files)
    contras = contradictions(files)

    lines = [
        "# Vault Lint Report",
        f"*Generated: {now_str}*",
        "",
        "## Broken [[wikilinks]]",
        "",
    ]
    if broken:
        for b in broken:
            lines.append(f"- Broken link: [[{b}]]")
    else:
        lines.append("Found 0 broken links.")
    lines.append("")

    lines.append("## Orphan Pages")
    lines.append("")
    if orphans:
        for o in orphans:
            rel = o.relative_to(VAULT_ROOT)
            lines.append(f"- Orphan: {rel}")
    else:
        lines.append("Found 0 orphan pages.")
    lines.append("")

    lines.append("## Stale Pages (>90 days without modification)")
    lines.append("")
    if stale:
        for s, days in stale:
            rel = s.relative_to(VAULT_ROOT)
            lines.append(f"- {rel} ({days} days)")
    else:
        lines.append("Found 0 stale pages.")
    lines.append("")

    lines.append("## Contradictions")
    lines.append("")
    if contras:
        for c in contras:
            rel = c.relative_to(VAULT_ROOT)
            lines.append(f"- {rel}")
    else:
        lines.append("- None found.")
    lines.append("")

    total = len(broken) + len(orphans) + len(stale) + len(contras)
    lines.append("---")
    lines.append(f"**Total issues: {total}** | {now_str}")
    lines.append("")

    report = "\n".join(lines)
    report_path = VAULT_ROOT / "schema" / "lint-report.md"
    report_path.write_text(report, encoding="utf-8")

    return f"Lint report generated with {total} issues."



def coverage_check():
    from pathlib import Path
    raw = Path(__file__).resolve().parent.parent.parent / "raw"
    if not raw.exists():
        return "No raw/ investigations found."
    items = []
    for f in sorted(raw.glob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        sources = len(re.findall(r"\[\[([^\]]+)\]\]", text))
        matrix = "## Matriz de Confianza" in text
        ok = sources >= 3 and matrix
        tag = "OK" if ok else "WARN" if (sources >= 1 or matrix) else "FAIL"
        items.append(tag + " " + f.name + ": " + str(sources) + " sources, matrix=" + ("yes" if matrix else "no"))
    good = sum(1 for x in items if x.startswith("OK"))
    pct = round(good / max(len(items), 1) * 100, 1)
    sep = chr(10)
    result = "Coverage: " + str(good) + "/" + str(len(items)) + " with matrix (" + str(pct) + "%)" + sep + sep.join(items)
    return result
