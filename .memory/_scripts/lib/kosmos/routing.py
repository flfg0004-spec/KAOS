"""kosmos/routing.py — DSOL Routing Table for KosmosV2 pipeline.

Router de modelos vía DSOL:
- Flash: Discover, Visualize, Govern (tareas simples/mecánicas)
- Pro: Model, Analyze, Document (razonamiento arquitectónico profundo)
- Kimi: Quality, Validate (verificación independiente)
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


ROUTING_TABLE: Dict[str, Dict[str, Any]] = {
    "discover": {
        "model": "go-flash",
        "thinking": None,
        "reason": "tarea simple de escaneo del codebase",
    },
    "model": {
        "model": "go-pro",
        "thinking": "high",
        "reason": "razonamiento arquitectónico C4",
    },
    "analyze": {
        "model": "go-pro",
        "thinking": "high",
        "reason": "análisis de impacto multicriterio",
    },
    "quality": {
        "model": "go-kimi-latest",
        "thinking": None,
        "reason": "verificación independiente, reduce sesgo",
    },
    "visualize": {
        "model": "go-flash",
        "thinking": None,
        "reason": "generación de diagramas",
    },
    "document": {
        "model": "go-pro",
        "thinking": "high",
        "reason": "decisión arquitectónica crítica",
    },
    "govern": {
        "model": "go-flash",
        "thinking": None,
        "reason": "operación mecánica de tripletas RDF",
    },
    "validate": {
        "model": "go-kimi-latest",
        "thinking": None,
        "reason": "verificación objetiva sin sesgo",
    },
}


def resolve_routing(node_name: str, state: dict = None) -> Dict[str, Any]:
    """Resolve DSOL routing for a pipeline node (Fase 3 — Aether integration).

    Priority:
      1. Local ROUTING_TABLE (Kosmos-specific routing, including Kimi for bias reduction)
      2. aether.router.resolve_model() for budget/quality-aware routing when no local entry
      3. Hardcoded fallback for unknown nodes

    Args:
        node_name: The pipeline node name (discover, model, etc.).
        state: Optional pipeline state for context (prompt_size, etc.).

    Returns:
        Dict with model, thinking, reason keys.
    """
    # Intent 1: Local ROUTING_TABLE (Kosmos-specific, con Kimi para verificación cruzada)
    if node_name in ROUTING_TABLE:
        return dict(ROUTING_TABLE[node_name])

    # Intent 2: Aether router (budget/quality-aware, para nodos no mapeados)
    try:
        from lib.aether.router import resolve_model as aether_resolve
        task_type_map: Dict[str, str] = {
            "discover": "lint", "model": "analyze", "analyze": "analyze",
            "quality": "verify", "visualize": "lint", "document": "adr",
            "govern": "lint", "validate": "verify",
        }
        task = task_type_map.get(node_name, "general")
        prompt_size = (state or {}).get("prompt_size", 0)
        result = aether_resolve(
            task_type=task, agent="kosmos",
            model_override=None, prompt_size=prompt_size,
        )
        return {
            "model": result.get("model", "go-flash"),
            "thinking": result.get("thinking"),
            "reason": f"Aether: {result.get('resolved_by', 'direct')}",
            "tier": result.get("tier", "flash"),
        }
    except Exception:
        pass

    # Intent 3: Hardcoded fallback
    return {
        "model": "go-flash",
        "thinking": None,
        "reason": "fallback: tarea no clasificada",
    }


# ── C4: Auto-tuning routing table ──


def auto_tune(dry_run: bool = True) -> dict:
    """Analyze metrics and suggest routing table optimizations (KosmosV3 C4).

    Lee métricas de PipelineCache (hit_rate), traces (latencia por nodo),
    y rate limiter (timeouts) para ajustar ROUTING_TABLE.

    Args:
        dry_run: If True, only report; if False, apply changes.

    Returns:
        Dict with suggested changes, current metrics, and changes applied.
    """
    import json
    from datetime import datetime

    suggestions: list = []
    node_latencies: dict = {}

    # 1. Cache hit rate
    try:
        from lib.kosmos.cache import PipelineCache
        from lib.kosmos._state import get_pipeline_cache
        stats = get_pipeline_cache().stats()
        if stats.get("hit_rate", 100) < 30:
            suggestions.append({
                "node": "all",
                "metric": "cache_hit_rate",
                "value": stats["hit_rate"],
                "suggestion": "Increase TTL or maxsize",
                "action": {"ttl_seconds": 3600},
            })
    except Exception:
        pass

    # 2. Latency per node from traces
    try:
        from lib.kosmos.otel import get_trace_files
        node_counts: dict = {}
        for tf in get_trace_files()[:7]:
            for line in open(str(tf), encoding="utf-8"):
                try:
                    span = json.loads(line)
                    name = span.get("name", "")
                    dur = span.get("duration_ms", 0)
                    if name in ROUTING_TABLE:
                        node_latencies.setdefault(name, []).append(dur)
                        node_counts[name] = node_counts.get(name, 0) + 1
                except (json.JSONDecodeError, OSError):
                    pass

        for node, latencies in node_latencies.items():
            avg_lat = sum(latencies) / len(latencies)
            if avg_lat > 5000 and ROUTING_TABLE.get(node, {}).get("model") == "go-pro":
                suggestions.append({
                    "node": node, "metric": "avg_latency_ms",
                    "value": round(avg_lat, 1),
                    "suggestion": "Consider go-flash for faster responses",
                    "action": {"model": "go-flash", "thinking": None},
                })
    except Exception:
        pass

    # 3. Rate limiter timeouts
    try:
        from lib.kosmos.ratelimit import rate_limit_status
        rl = rate_limit_status()
        if rl.get("total_timeout", 0) > 10:
            suggestions.append({
                "node": "all", "metric": "rate_limiter_timeouts",
                "value": rl["total_timeout"],
                "suggestion": "Increase max_concurrent",
                "action": {"max_concurrent": rl.get("max_concurrent", 3) + 1},
            })
    except Exception:
        pass

    # Apply
    changes_made: list = []
    if not dry_run:
        for s in suggestions:
            action = s.get("action", {})
            node = s.get("node", "")
            if node == "all":
                if "ttl_seconds" in action:
                    try:
                        from lib.kosmos._state import get_pipeline_cache
                        get_pipeline_cache()._ttl = action["ttl_seconds"]
                        changes_made.append(f"TTL -> {action['ttl_seconds']}s")
                    except Exception:
                        pass
                if "max_concurrent" in action:
                    try:
                        from lib.kosmos.ratelimit import _RATE_LIMITER
                        _RATE_LIMITER._max = action["max_concurrent"]
                        changes_made.append(f"max_concurrent -> {action['max_concurrent']}")
                    except Exception:
                        pass
            elif node in ROUTING_TABLE and "model" in action:
                ROUTING_TABLE[node]["model"] = action["model"]
                if action.get("thinking") is not None:
                    ROUTING_TABLE[node]["thinking"] = action["thinking"]
                changes_made.append(f"{node}: {action['model']}")

    return {
        "timestamp": datetime.now().isoformat(),
        "dry_run": dry_run,
        "suggestions": suggestions,
        "changes_made": changes_made,
        "nodes_analyzed": len(node_latencies),
    }
