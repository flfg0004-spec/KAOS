import json
from pathlib import Path
from datetime import datetime
from lib.config import VAULT_ROOT, CACHE_MAX_ENTRIES
from lib.pressure import estimate_tokens, get_level


def _rrf_fusion(results: list[list[dict]], k: int = 60, top_n: int = 10) -> list[dict]:
    """Reciprocal Rank Fusion — combina múltiples retrievers con ranking."""
    scores = {}
    for retriever_results in results:
        for rank, item in enumerate(retriever_results):
            doc_id = item.get("path", item.get("error_hash", str(id(item))))
            if doc_id not in scores:
                scores[doc_id] = {"item": item, "score": 0}
            scores[doc_id]["score"] += 1.0 / (k + rank + 1)
    ranked = sorted(scores.values(), key=lambda x: -x["score"])
    return [r["item"] for r in ranked[:top_n]]


def _embedding_search(task: str, top_k: int = 3) -> str:
    """Query embeddings for semantically similar pages."""
    try:
        from lib import embeddings
        results = embeddings.query(task, top_k=top_k)
        if not results or "error" in results[0]:
            return ""
        lines = ["\n---\n## Semantic Context\n"]
        for r in results:
            lines.append(f"- [{r['path']}] (score {r['score']}): {r['snippet']}\n")
        return "".join(lines)
    except Exception:
        return ""


def _obsidian_search(task: str, top_k: int = 3) -> str:
    """Search Obsidian vault via REST API for relevant context."""
    try:
        from lib.obsidian import ObsidianClient
        import json
        config_path = Path(__file__).parents[2] / ".opencode" / "opencode.json"
        api_key = ""
        if config_path.exists():
            config = json.loads(config_path.read_text())
            api_key = config.get("mcp", {}).get("obsidian", {}).get("env", {}).get("OBSIDIAN_API_KEY", "")
        client = ObsidianClient(api_key=api_key)
        results = client.search(task, top_k=top_k)
        if results:
            lines = ["\n---\n## Obsidian Vault Context\n"]
            if isinstance(results, list):
                for r in results:
                    path = r.get("path", r.get("filename", "unknown"))
                    snippet = r.get("content", r.get("match", ""))[:200]
                    lines.append(f"- [{path}]({path}): {snippet}\n")
            return "".join(lines)
        return ""
    except Exception:
        import logging
        logging.warning("Obsidian API not available — continuing without vault context")
        return ""


def _code_memory_search(task: str, top_k: int = 3) -> str:
    """Search CodeExperience for relevant error/solution patterns."""
    try:
        from lib.code_memory import search
        results = search(task, top_k=top_k)
        if results:
            lines = ["\n---\n## Code Experience Memory\n"]
            for r in results:
                lang = r.get("language", "?")
                score = r.get("score", 0)
                error = r.get("error", "")[:80]
                solution = r.get("solution", "")
                lines.append(f"- [{lang}] (score {score}) `{error}`\n")
                if solution:
                    lines.append(f"  -> {solution[:120]}\n")
            return "".join(lines)
        return ""
    except Exception:
        return ""


def _kg_search(task: str, top_k: int = 5) -> str:
    """Search Knowledge Graph for relevant entities and relations."""
    try:
        import json
        from lib.config import VAULT_ROOT
        seed_path = VAULT_ROOT / "cache" / "knowledge-graph" / "seed.json"
        if not seed_path.exists():
            return ""
        kg = json.loads(seed_path.read_text(encoding="utf-8"))
        query_words = set(task.lower().split())
        entities = kg.get("entities", [])
        
        relevant = set()
        for e in entities:
            title = e.get("title", "").lower()
            label = e.get("label", "").lower()
            tags = [t.lower() for t in e.get("tags", [])]
            searchable = f"{title} {label} {' '.join(tags)}"
            if any(w in searchable for w in query_words):
                relevant.add(e["title"])
        
        if not relevant:
            return ""
        lines = ["\n---\n## Knowledge Graph Context\n"]
        count = 0
        for e in entities:
            if e["title"] in relevant and count < top_k:
                tags_str = ", ".join(e.get("tags", [])[:3])
                lines.append(f"- {e['title']} ({e.get('type', 'concept')}) [{tags_str}]\n")
                count += 1
        return "".join(lines)
    except Exception:
        return ""


CACHE_FILE = VAULT_ROOT / "cache" / "hydrate-cache.json"


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            return {
                "entries": data.get("entries", []),
                "maxEntries": data.get("maxEntries", CACHE_MAX_ENTRIES),
                "pressure": data.get("pressure", "normal"),
            }
        except Exception:
            pass
    return {"entries": [], "maxEntries": CACHE_MAX_ENTRIES, "pressure": "normal"}


def _save_cache(cache: dict) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2, default=str), encoding="utf-8")


def _update_cache(cache: dict, entry_path: str) -> dict:
    entries = [e for e in cache["entries"] if e["path"] != entry_path]
    entries.insert(0, {"path": entry_path, "lastAccess": datetime.now().isoformat()})
    if len(entries) > cache["maxEntries"]:
        entries = entries[:cache["maxEntries"]]
    cache["entries"] = entries
    max_e = cache.get("maxEntries", CACHE_MAX_ENTRIES)
    ratio = len(entries) / max_e if max_e > 0 else 0
    if ratio < 0.5:
        cache["pressure"] = "normal"
    elif ratio < 0.8:
        cache["pressure"] = "warning"
    else:
        cache["pressure"] = "high"
    return cache


def _read_page(path: Path, level: str) -> str | None:
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8", errors="replace")
    if level == "critical":
        return None
    if level in ("warning", "high") and len(content) > 500:
        return content[:500] + f"\n[...truncated, +{len(content) - 500} total chars]"
    return content


def check_pipeline(agent: str) -> str | None:
    status_path = VAULT_ROOT / "_pipeline" / "status.md"
    if not status_path.exists():
        return None
    content = status_path.read_text(encoding="utf-8")
    pattern = agent + r"\s*\|\s*(\S+)"
    import re
    m = re.search(pattern, content)
    if m and m.group(1) == "ready":
        topic = ""
        tm = re.search(r"\*\*topic\*\*:\s*(.+?)$", content, re.MULTILINE)
        if tm:
            topic = tm.group(1).strip()
        return (
            f"\n---\n## Pipeline Task\n"
            f"There is a pipeline task waiting for you.\n"
            f"  Topic: {topic}\n"
            f"  Read `_pipeline/input.md` for context.\n"
            f"  Write output to assigned path, then run: vault.py pipeline step --done --agent {agent}\n"
        )
    return None


def load(agent: str = "", task: str = "") -> str:
    cache = _load_cache()
    vault = VAULT_ROOT
    context = []
    total_chars = 0

    # Intentar cargar contexto compartido del pipeline
    pipeline_ctx = None
    try:
        from lib.pipeline import load_context
        pipeline_ctx = load_context()
    except Exception:
        pass

    # Usar DSOL optimizado si está disponible y hay contexto compartido
    if agent and pipeline_ctx and pipeline_ctx.get("pipeline_id"):
        try:
            from lib.aether.client import build_optimized_context
            optimized = build_optimized_context(agent, task, pipeline_ctx)
            if optimized.strip():
                context.append(optimized)
                total_chars += len(optimized)
                cache = _update_cache(cache, "_pipeline/context.json")
        except Exception:
            pass

    # Siempre incluir index.md (es la entrada principal al vault)
    if not context:
        index = (vault / "wiki" / "index.md").read_text(encoding="utf-8", errors="replace")
        context.append(f"## Memory Vault Index\n{index}")
        total_chars += len(index)
        cache = _update_cache(cache, "wiki/index.md")

    agent_page = vault / "wiki" / "entities" / f"{agent}.md"
    if agent and agent_page.exists():
        entity_content = agent_page.read_text(encoding="utf-8", errors="replace")
        context.append(f"\n---\n## Agent Context\n{entity_content}")
        total_chars += len(entity_content)
        cache = _update_cache(cache, f"wiki/entities/{agent}.md")

    if task:
        try:
            from lib.mome_router import is_mome_active, MoMERouter, query_partitioned
            if is_mome_active():
                _router = MoMERouter()
                _domains = _router.route_with_gating(task)
                for _d in _domains:
                    _mome_results = query_partitioned(task, _d, top_k=3)
                    if _mome_results:
                        _lines = [f"\n---\n## MoME Context ({_d})"]
                        for _r in _mome_results:
                            _lines.append(f"- [{_r['path']}] (score {_r['score']}): {_r['snippet']}")
                        context.append("\n".join(_lines))
        except Exception:
            pass

        semantic = _embedding_search(task)
        if semantic:
            context.append(semantic)
        obsidian_results = _obsidian_search(task)
        if obsidian_results:
            context.append(obsidian_results)
        code_mem_results = _code_memory_search(task)
        if code_mem_results:
            context.append(code_mem_results)
        kg_results = _kg_search(task)
        if kg_results:
            context.append(kg_results)

    schema_content = (vault / "schema" / "KAOS.md").read_text(encoding="utf-8", errors="replace")
    context.append(f"\n---\n## Vault Rules\n{schema_content}")
    total_chars += len(schema_content)
    cache = _update_cache(cache, "schema/KAOS.md")

    log_path = vault / "wiki" / "log.md"
    if log_path.exists():
        log_lines = log_path.read_text(encoding="utf-8", errors="replace").split("\n")
        context.append(f"\n---\n## Recent Vault Activity\n" + "\n".join(log_lines[-5:]))

    policy_path = vault / "schema" / "vault-policy.md"
    if policy_path.exists():
        policy = policy_path.read_text(encoding="utf-8", errors="replace")
        context.append(f"\n---\n## Vault Policy\n{policy}")
        total_chars += len(policy)
        cache = _update_cache(cache, "schema/vault-policy.md")

    estimated_tokens = estimate_tokens("\n".join(context))
    pressure_info = get_level(estimated_tokens)
    level = pressure_info["level"]
    cache["pressure"] = level

    if level in ("warning", "high"):
        keep = min(2, len(context))
        context = context[:keep]
        context.append(f"\n---\n[Context TRIM: {level} ({pressure_info['pressure']}%) — schema/log/policy removed]\n")
    elif level == "critical":
        keep = min(2, len(context))
        context = context[:keep]
        context.append(f"\n---\n[Context CRITICAL: only index+entity loaded ({pressure_info['pressure']}%)]\n")

    if agent:
        task = check_pipeline(agent)
        if task:
            context.append(task)
            cache = _update_cache(cache, "_pipeline/status.md")

    _save_cache(cache)

    header = f"\n[HYDRATE] Agent: {agent} | Level: {level} ({pressure_info['pressure']}%) | Est. tokens: {estimated_tokens} | Cache: {len(cache['entries'])}/{cache['maxEntries']} entries | Action: {pressure_info['action']}\n"
    output = "\n".join(context)
    return header + output
