"""Wikilink analysis with semantic suggestions via embeddings + LLM.

Replaces keyword overlap with embedding-based cosine similarity (fastembed).
For high-confidence pairs, Gemini Flash suggests typed relationships.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

from lib.config import VAULT_ROOT, IGNORED_PAGES, IGNORED_WIKILINKS
import lib.llm as llm

EMBEDDING_SIM_THRESHOLD = 0.75
LLM_SIM_THRESHOLD = 0.85
BASE = (Path(__file__).resolve().parent.parent.parent)


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


def _get_embedding(text: str) -> list[float] | None:
    """Get embedding via mcp_embed subprocess."""
    import os
    if os.environ.get("KAOS_TESTING") == "1":
        return None
    import subprocess, sys as _sys
    mcp_embed = BASE / "_scripts" / "mcp_embed.py"
    req = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "embed", "arguments": {"texts": [text[:2000]]}}
    })
    try:
        r = subprocess.run(
            [_sys.executable, str(mcp_embed)],
            input=req, capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0 and r.stdout.strip():
            resp = json.loads(r.stdout.strip())
            content = resp.get("result", {}).get("content", [])
            if content:
                vecs = json.loads(content[0]["text"])
                return vecs[0] if vecs else None
    except Exception:
        pass
    return None


def _cosine_sim(a: list[float], b: list[float]) -> float:
    import numpy as np
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


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


def _get_embedding_batch(texts: list[str]) -> list[list[float] | None]:
    """Get embeddings for multiple texts, filtering failures."""
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_get_embedding, t): t for t in texts}
        for future in as_completed(futures, timeout=30):
            try:
                results.append(future.result())
            except Exception:
                results.append(None)
    return results


def suggest(min_confidence: float = 0.75, mode: str = "hybrid", top_k: int = 20) -> list[dict]:
    """Semantic wikilink suggestions via embeddings + optional LLM context.

    Args:
        min_confidence: Minimum similarity threshold (0-1)
        mode: 'embedding' (fast), 'llm' (with context analysis), or 'hybrid'
        top_k: Max suggestions to return
    """
    import os
    if os.environ.get("KAOS_TESTING") == "1":
        return []
    page_map = build_graph()
    names = [n for n in page_map if n not in IGNORED_PAGES]
    if len(names) < 2:
        return []

    # Get embeddings for all pages
    contents = [
        (n + " " + " ".join(page_map[n]["headings"]) + " " + page_map[n]["content"][:1000])
        for n in names
    ]
    embeds = _get_embedding_batch(contents)
    name_embed = [(n, e) for n, e in zip(names, embeds) if e is not None]

    suggestions = []
    for i in range(len(name_embed)):
        for j in range(i + 1, len(name_embed)):
            a, ea = name_embed[i]
            b, eb = name_embed[j]
            a_links = {l["target"] for l in page_map[a]["links"]}
            b_links = {l["target"] for l in page_map[b]["links"]}
            if a in b_links or b in a_links:
                continue

            sim = _cosine_sim(ea, eb)
            if sim < min_confidence:
                continue

            entry = {
                "from": a,
                "to": b,
                "score": round(sim, 4),
                "method": "embedding",
            }

            if mode in ("llm", "hybrid") and sim >= 0.85:
                llm_result = _llm_link_context(
                    page_map[a]["content"][:1500],
                    page_map[b]["content"][:1500],
                    a, b
                )
                if llm_result:
                    entry.update(llm_result)
                    entry["method"] = "llm"

            suggestions.append(entry)

    suggestions.sort(key=lambda x: -x["score"])
    return suggestions[:top_k]


def _llm_link_context(content_a: str, content_b: str, name_a: str, name_b: str) -> dict | None:
    """Ask Gemini Flash for link context between two notes."""
    prompt = (
        f"Analiza estas 2 notas de conocimiento:\n\n"
        f"--- NOTA A: {name_a} ---\n{content_a[:1200]}\n\n"
        f"--- NOTA B: {name_b} ---\n{content_b[:1200]}\n\n"
        "Responde SOLO con JSON:\n"
        '{"relation": "supports|contradicts|extends|depends-on|example-of", '
        '"anchor_text": "palabra o frase corta", '
        '"reason": "una linea de explicacion"}'
    )
    try:
        response = llm.llm_call(
            prompt=prompt,
            system="Eres un analista de relaciones entre conceptos. Respondes solo JSON.",
            model="go-gemini-flash",
            temperature=0.1,
            max_tokens=300,
        )
        response = response.strip()
        if response.startswith("```"):
            response = response.split("\n", 1)[-1].rsplit("```", 1)[0]
        parsed = json.loads(response)
        if isinstance(parsed, dict) and "relation" in parsed:
            return {
                "relation": parsed["relation"],
                "anchor_text": parsed.get("anchor_text", name_b),
                "reason": parsed.get("reason", ""),
            }
    except Exception:
        pass
    return None


def apply_suggestion(suggestion: dict, page_map: dict = None, dry_run: bool = True) -> dict:
    """Insert a typed [[wikilink]] into the source note."""
    if page_map is None:
        page_map = build_graph()

    source = suggestion["from"]
    target = suggestion["to"]
    if source not in page_map:
        return {"error": f"Source '{source}' not found"}

    source_path = VAULT_ROOT / page_map[source]["path"]
    if not source_path.exists():
        return {"error": f"Source file not found: {source_path}"}

    content = read_file(source_path)
    link_text = suggestion.get("anchor_text", target)
    relation = suggestion.get("relation", "")
    link = f"[[{target}|{link_text}]]"

    if relation:
        section_link = f"\n\n*Esto {relation} [[{target}]]*"
    else:
        section_link = f"\n\n*Relacionado: [[{target}]]*"

    if f"[[{target}" in content:
        return {"path": str(source_path), "status": "already_exists", "link": link}

    if dry_run:
        return {"path": str(source_path), "status": "would_add", "link": link}

    updated = content.rstrip() + section_link
    source_path.write_text(updated, encoding="utf-8")

    # Add backlink metadata to target
    target_name = target.replace(".md", "")
    if target_name in page_map:
        target_path = VAULT_ROOT / page_map[target_name]["path"]
        if target_path.exists():
            target_content = read_file(target_path)
            fm_note = f"\n\n*Enlazado desde: [[{source}]]*"
            if fm_note not in target_content and f"[[{source}" not in target_content:
                target_path.write_text(target_content.rstrip() + fm_note, encoding="utf-8")

    return {"path": str(source_path), "status": "added", "link": link}


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
        lines.append("## Broken Links\n")
        for b in data["broken"]:
            src_path = data["page_map"][b["source"]]["path"]
            lines.append(f"- '{b['source']}' -> '{b['target']}' (in {src_path})")
        lines.append("")
    if data["orphan_list"]:
        lines.append("## Orphan Pages\n")
        for o in data["orphan_list"]:
            lines.append(f"- {o['name']} -- {o['path']}")
        lines.append("")
    if suggestions_enabled:
        suggs = suggest()
        if suggs:
            lines.append("## Suggested Links (embedding-based, top 20)")
            lines.append("")
            for s in suggs[:20]:
                rel = s.get("relation", "")
                rel_str = f" ({rel})" if rel else ""
                lines.append(f"- {s['from']} <-> {s['to']} (score: {s['score']}, method: {s['method']}){rel_str}")
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
