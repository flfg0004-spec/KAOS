import re
from pathlib import Path
from datetime import datetime
from lib.config import VAULT_ROOT, IGNORED_PAGES, IGNORED_WIKILINKS


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _all_md_files() -> list[Path]:
    exclude_dirs = {"cache", "_pending", ".git", "_scripts"}
    files = []
    for f in VAULT_ROOT.rglob("*.md"):
        if any(part in exclude_dirs for part in f.parts):
            continue
        files.append(f)
    return files


def _page_name(path: Path) -> str:
    return path.stem


def build_graph() -> dict:
    files = _all_md_files()
    page_map = {}

    for f in files:
        name = _page_name(f)
        rel = f.relative_to(VAULT_ROOT).as_posix()
        content = read_file(f)
        links = re.findall(r"\[\[([^\]]+?)\]\]", content)
        parsed_links = []
        for link in links:
            target = link.split("|")[0].split("#")[0].strip()
            section = ""
            if "#" in link:
                section = "#" + link.split("#", 1)[1]
            if target and target.lower() not in IGNORED_WIKILINKS and not target.isdigit() and len(target) > 1:
                parsed_links.append({"target": target, "section": section})

        h_pattern = re.compile(r"^#{1,3}\s+(.+)$", re.MULTILINE)
        headings = h_pattern.findall(content)

        page_map[name] = {
            "path": rel,
            "links": parsed_links,
            "backlinks": [],
            "headings": headings,
            "content": content,
        }

    for name, data in page_map.items():
        for link in data["links"]:
            tgt = link["target"].replace(".md", "")
            if tgt in page_map:
                page_map[tgt]["backlinks"].append(name)

    return page_map


def parse() -> dict:
    page_map = build_graph()
    broken = []
    valid = 0

    for name, data in page_map.items():
        for link in data["links"]:
            tgt = link["target"].replace(".md", "")
            if tgt in page_map:
                valid += 1
            else:
                broken.append({"source": name, "target": link["target"]})

    orphans = []
    for name, data in page_map.items():
        if name in IGNORED_PAGES:
            continue
        if not data["backlinks"]:
            orphans.append({"name": name, "path": data["path"]})

    return {
        "pages": len(page_map),
        "validLinks": valid,
        "brokenLinks": len(broken),
        "orphans": len(orphans),
        "broken": broken,
        "orphan_list": orphans,
        "page_map": page_map,
    }


def suggest(min_score: int = 2) -> list[dict]:
    page_map = build_graph()
    names = [n for n in page_map if n not in IGNORED_PAGES]
    suggestions = []

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            a_links = {l["target"] for l in page_map[a]["links"]}
            b_links = {l["target"] for l in page_map[b]["links"]}
            if a in b_links or b in a_links:
                continue

            a_words = set(
                w.lower().rstrip(":?.,!")
                for w in (a + " " + " ".join(page_map[a]["headings"])).split()
                if len(w) > 3
            )
            b_words = set(
                w.lower().rstrip(":?.,!")
                for w in (b + " " + " ".join(page_map[b]["headings"])).split()
                if len(w) > 3
            )
            overlap = sorted(a_words & b_words)
            score = len(overlap)
            if score >= min_score:
                suggestions.append({
                    "from": a,
                    "to": b,
                    "score": score,
                    "keywords": overlap,
                })

    return sorted(suggestions, key=lambda x: x["score"], reverse=True)


def report(suggestions_enabled: bool = False) -> str:
    data = parse()
    lines = [
        "# Wikilink Analysis",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Overview",
        f"- Pages analyzed: {data['pages']}",
        f"- Valid wikilinks: {data['validLinks']}",
        f"- Broken wikilinks: {data['brokenLinks']}",
        f"- Orphan pages: {data['orphans']}",
        "",
    ]

    if data["broken"]:
        lines.append("## Broken Links")
        lines.append("")
        for b in data["broken"]:
            src_path = data["page_map"][b["source"]]["path"]
            lines.append(f"- '{b['source']}' -> '{b['target']}' (in {src_path})")
        lines.append("")

    if data["orphan_list"]:
        lines.append("## Orphan Pages")
        lines.append("")
        for o in data["orphan_list"]:
            lines.append(f"- {o['name']} -- {o['path']}")
        lines.append("")

    if suggestions_enabled:
        suggs = suggest()
        if suggs:
            lines.append("## Suggested Links (top 20)")
            lines.append("*Based on keyword overlap in headings. Minimum 2 shared keywords.*")
            lines.append("")
            for s in suggs[:20]:
                kw = ", ".join(s["keywords"])
                lines.append(f"- {s['from']} <-> {s['to']} (score: {s['score']}) -- shared: {kw}")
            lines.append("")

    return "\n".join(lines)


def graph_dot() -> str:
    data = parse()
    page_map = data["page_map"]
    lines = [
        "digraph vault {",
        "    rankdir=LR;",
        "    node [shape=box, style=rounded];",
    ]
    for name, info in page_map.items():
        label = name.replace("_", " ").replace("-", " ")
        lines.append(f'    "{name}" [label="{label}", URL="{info["path"]}"];')

    for name, info in page_map.items():
        for link in info["links"]:
            tgt = link["target"].replace(".md", "")
            if tgt in page_map:
                lines.append(f'    "{name}" -> "{tgt}";')
            else:
                lines.append(f'    "{name}" -> "{tgt}" [style=dashed, color=red];')

    lines.append("}")
    return "\n".join(lines)
