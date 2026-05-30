"""Wikilink analysis with semantic suggestions via embeddings + LLM.

Replaces keyword overlap with embedding-based cosine similarity (fastembed).
For high-confidence pairs, Gemini Flash suggests typed relationships.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import lib.llm as llm
from lib.config import IGNORED_PAGES, IGNORED_WIKILINKS, VAULT_ROOT

EMBEDDING_SIM_THRESHOLD = 0.75
LLM_SIM_THRESHOLD = 0.85
BASE = (Path(__file__).resolve().parent.parent.parent)


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _all_md_files() -> list[Path]:
    exclude_dirs = {"cache", "_pending", ".git", "_scripts", "_pipeline", "_archive", "dashboard"}
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
    import subprocess
    import sys as _sys
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


class VaultGraph:
    """Directed graph of the vault with topological analysis methods.

    Constructor accepts page_map from build_graph().
    Reexported from graph_analysis for backward compatibility.
    """

    def __init__(self, page_map: dict = None):
        self.page_map = page_map or build_graph()
        self.graph = self._build_digraph()

    def _build_digraph(self):
        try:
            import networkx as nx
        except ImportError:
            raise ImportError("networkx is required for VaultGraph")
        G = nx.DiGraph()
        for name, data in self.page_map.items():
            G.add_node(name, path=data["path"], headings=data["headings"])
        for name, data in self.page_map.items():
            for link in data["links"]:
                target = link["target"].replace(".md", "")
                if target in self.page_map:
                    G.add_edge(name, target)
        return G

    @property
    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    def page_rank(self, top_k: int = 10) -> list[dict]:
        import networkx as nx
        if self.node_count == 0:
            return []
        if self.node_count == 1:
            node = list(self.graph.nodes())[0]
            return [{"node": node, "score": 1.0, "path": self.page_map.get(node, {}).get("path", "")}]
        pr = nx.pagerank(self.graph, alpha=0.85)
        sorted_pr = sorted(pr.items(), key=lambda x: -x[1])
        return [
            {"node": n, "score": round(s, 4), "path": self.page_map.get(n, {}).get("path", "")}
            for n, s in sorted_pr[:top_k]
        ]

    def louvain_communities(self) -> list[dict]:
        if self.node_count < 2:
            return [{"error": "Need at least 2 nodes for community detection"}]
        undirected = self.graph.to_undirected()
        try:
            from networkx.algorithms.community import louvain_communities
            communities = louvain_communities(undirected, seed=42)
        except ImportError:
            return [{"error": "Louvain not available"}]
        except Exception:
            return [{"error": "Louvain community detection failed"}]

        results = []
        for i, comm in enumerate(communities):
            members = sorted(comm)
            internal_edges = undirected.subgraph(comm).number_of_edges()
            results.append({
                "id": i,
                "size": len(members),
                "members": members,
                "internal_edges": internal_edges,
                "density": round(internal_edges / max(len(members) * (len(members) - 1) / 2, 1), 3),
            })
        return sorted(results, key=lambda x: -x["size"])

    def betweenness_centrality(self, top_k: int = 10) -> list[dict]:
        import networkx as nx
        bc = nx.betweenness_centrality(self.graph, k=min(top_k * 2, self.node_count), seed=42)
        sorted_bc = sorted(bc.items(), key=lambda x: -x[1])
        return [
            {"node": n, "score": round(s, 4), "path": self.page_map.get(n, {}).get("path", "")}
            for n, s in sorted_bc[:top_k]
        ]

    def hub_scores(self, top_k: int = 10) -> list[dict]:
        import networkx as nx
        try:
            hubs, _ = nx.hits(self.graph, max_iter=100, tol=1e-6)
        except Exception:
            deg = dict(self.graph.out_degree())
            total = sum(deg.values()) or 1
            hubs = {n: d / total for n, d in deg.items()}
        sorted_h = sorted(hubs.items(), key=lambda x: -x[1])
        return [
            {"node": n, "score": round(s, 4), "out_degree": self.graph.out_degree(n)}
            for n, s in sorted_h[:top_k]
        ]

    def bridge_notes(self) -> list[dict]:
        import networkx as nx
        communities = self.louvain_communities()
        if not communities or "error" in communities[0]:
            return []

        comm_map = {}
        for comm in communities:
            for member in comm["members"]:
                comm_map[member] = comm["id"]

        bc = nx.betweenness_centrality(self.graph, k=min(30, self.node_count), seed=42)
        bridges = []
        for node, score in bc.items():
            if node not in comm_map:
                continue
            node_comm = comm_map[node]
            out_edges = list(self.graph.successors(node))
            cross_comm = sum(1 for t in out_edges if t in comm_map and comm_map[t] != node_comm)
            in_edges = list(self.graph.predecessors(node))
            cross_in = sum(1 for s in in_edges if s in comm_map and comm_map[s] != node_comm)
            if cross_comm + cross_in > 0:
                bridges.append({
                    "node": node,
                    "betweenness": round(score, 4),
                    "cross_out": cross_comm,
                    "cross_in": cross_in,
                    "community": node_comm,
                })

        return sorted(bridges, key=lambda x: -x["betweenness"])[:10]

    def cluster_islands(self) -> list[dict]:
        import networkx as nx
        undirected = self.graph.to_undirected()
        components = list(nx.connected_components(undirected))
        if not components:
            return []

        main = max(components, key=len)
        islands = []
        for comp in components:
            if comp is main:
                continue
            members = sorted(comp)
            subgraph = undirected.subgraph(comp)
            islands.append({
                "size": len(members),
                "members": members,
                "edges": subgraph.number_of_edges(),
                "density": round(nx.density(subgraph), 3),
            })
        return sorted(islands, key=lambda x: -x["size"])

    def in_out_ratio(self) -> dict:
        in_deg = dict(self.graph.in_degree())
        out_deg = dict(self.graph.out_degree())
        in_vals = list(in_deg.values())
        out_vals = list(out_deg.values())
        info_sinks = [n for n, d in in_deg.items() if d >= 3 and out_deg.get(n, 0) == 0]
        source_orphans = [n for n, d in out_deg.items() if d >= 3 and in_deg.get(n, 0) == 0]
        return {
            "avg_in_degree": round(sum(in_vals) / max(len(in_vals), 1), 2),
            "avg_out_degree": round(sum(out_vals) / max(len(out_vals), 1), 2),
            "max_in_degree": max(in_vals) if in_vals else 0,
            "max_out_degree": max(out_vals) if out_vals else 0,
            "info_sinks": len(info_sinks),
            "info_sink_list": info_sinks[:10],
            "source_orphans": len(source_orphans),
            "source_orphan_list": source_orphans[:10],
        }

    def summary(self) -> dict:
        import networkx as nx
        try:
            pr = self.page_rank(top_k=3)
            communities = self.louvain_communities()
            islands = self.cluster_islands()
            bridges = self.bridge_notes()
            ratios = self.in_out_ratio()
        except Exception as e:
            return {"error": str(e)}

        avg_pr = round(sum(n["score"] for n in pr) / max(len(pr), 1), 4) if pr else 0
        return {
            "nodes": self.node_count,
            "edges": self.edge_count,
            "density": round(nx.density(self.graph), 4),
            "avg_page_rank": avg_pr,
            "avg_page_rank": avg_pr,
            "communities": len(communities),
            "islands": len(islands),
            "bridges": len(bridges),
            "info_sinks": ratios["info_sinks"],
            "source_orphans": ratios["source_orphans"],
            "link_ratio": ratios["avg_out_degree"],
        }


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
