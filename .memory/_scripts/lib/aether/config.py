"""Ether configuration — constants, model maps, pricing, env vars. version: 3

Loaded from aether.yaml by default. Falls back to hardcoded values if YAML not found.
Env vars always override feature flags (highest priority).
"""

import os
from dataclasses import dataclass

try:
    from lib.aether.config_loader import get_config
    _cfg = get_config()
    _cfg.validate()
except Exception:
    _cfg = None


# ── Data Structures ──────────────────────────────────────────


@dataclass
class ModelTaskRule:
    """Regla de enrutamiento para un modelo en una tarea específica."""

    model: str
    thinking: str | None = None
    tier: str = "flash"
    priority: int = 0
    supports_multimodal: bool = False


@dataclass
class ModelResolution:
    """Resultado de la resolución de modelo."""

    model: str
    thinking: str | None = None
    tier: str = "flash"
    resolved_by: str = ""


def _normalize_task_model_map(raw: dict) -> dict[str, list[ModelTaskRule]]:
    """Normaliza TASK_MODEL_MAP a {task: [ModelTaskRule, ...]}."""
    result = {}
    for task, rules in raw.items():
        if isinstance(rules, dict):
            rules = [rules]
        normalized = []
        for r in rules:
            if isinstance(r, dict):
                normalized.append(ModelTaskRule(**r))
            elif isinstance(r, ModelTaskRule):
                normalized.append(r)
            else:
                normalized.append(r)
        result[task] = normalized
    return result


# ── Fallback constants (used when YAML is unavailable) ────────
_FALLBACK_TASK_MODEL_MAP = {
    "lint": [
        {"model": "go-gemini-flash", "thinking": None, "tier": "flash", "priority": 1},
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 2},
    ],
    "extract": [
        {"model": "go-mimo", "thinking": None, "tier": "mimo", "priority": 1},
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 2},
    ],
    "health": [
        {"model": "go-gemini-flash", "thinking": None, "tier": "flash", "priority": 1},
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 2},
    ],
    "hydrate": [
        {"model": "go-mimo", "thinking": None, "tier": "mimo", "priority": 1},
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 2},
    ],
    "wikilinks": [
        {"model": "go-mimo", "thinking": None, "tier": "mimo", "priority": 1},
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 2},
    ],
    "curation": [
        {"model": "go-mimo", "thinking": None, "tier": "mimo", "priority": 1},
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 2},
    ],
    "code_gen": [
        {"model": "go-mimo", "thinking": None, "tier": "mimo", "priority": 1},
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 2},
    ],
    "code_simple": [
        {"model": "go-mimo", "thinking": None, "tier": "mimo", "priority": 1},
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 2},
    ],
    "general": [
        {"model": "go-gemini-flash", "thinking": None, "tier": "flash", "priority": 1},
        {"model": "go-mimo", "thinking": None, "tier": "mimo", "priority": 2},
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 3},
    ],
    "research": [
        {"model": "go-pro", "thinking": "high", "tier": "pro", "priority": 1},
        {"model": "go-mimo", "thinking": "high", "tier": "mimo", "priority": 2},
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 3},
    ],
    "analyze": [
        {"model": "go-pro", "thinking": "high", "tier": "pro", "priority": 1},
        {"model": "go-mimo", "thinking": "high", "tier": "mimo", "priority": 2},
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 3},
    ],
    "adr": [
        {"model": "go-pro", "thinking": "high", "tier": "pro", "priority": 1},
        {"model": "go-mimo", "thinking": "high", "tier": "mimo", "priority": 2},
    ],
    "factual": [
        {"model": "go-pro", "thinking": "high", "tier": "pro", "priority": 1},
    ],
    "synthesize": [
        {"model": "go-kimi-latest", "thinking": None, "tier": "kimi", "priority": 1},
        {"model": "go-mimo", "thinking": None, "tier": "mimo", "priority": 2},
        {"model": "go-pro", "thinking": "high", "tier": "pro", "priority": 3},
    ],
    "strategy": [
        {"model": "go-kimi-latest", "thinking": None, "tier": "kimi", "priority": 1},
        {"model": "go-mimo", "thinking": "high", "tier": "mimo", "priority": 2},
        {"model": "go-pro", "thinking": "high", "tier": "pro", "priority": 3},
    ],
    "verify": [
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 1},
    ],
    "cross_check": [
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 1},
    ],
    "code_agentic": [
        {"model": "go-kimi-latest", "thinking": None, "tier": "kimi", "priority": 1},
        {"model": "go-mimo", "thinking": None, "tier": "mimo", "priority": 2},
        {"model": "go-flash", "thinking": None, "tier": "flash", "priority": 3},
    ],
    "diversity": [
        {"model": "go-mimo", "thinking": None, "tier": "mimo", "priority": 1},
        {"model": "go-kimi-latest", "thinking": None, "tier": "kimi", "priority": 2},
        {"model": "go-pro", "thinking": "high", "tier": "pro", "priority": 3},
    ],
}

_FALLBACK_MODEL_TIERS = {
    "flash": {"description": "Base — alta velocidad, bajo costo", "target_pct": 40},
    "mimo": {"description": "Ultra-económico — tareas simples, cache pesado", "target_pct": 40},
    "pro": {"description": "Calidad — razonamiento profundo, factual", "target_pct": 5},
    "kimi": {"description": "Diversidad — pensamiento estratégico", "target_pct": 15},
}

_FALLBACK_THINKING = {
    None: {"description": "No thinking — fastest, JSON mode, tool calls available"},
    "high": {"description": "Thinking enabled — balanced speed vs depth"},
    "xmax": {"description": "Maximum thinking — deepest reasoning, slowest"},
}

_FALLBACK_BUDGETS = {
    "flash": {"min": 1024, "optimal": 8192, "max": 32768},
    "pro": {"min": 4096, "optimal": 16384, "max": 65536},
    "kimi": {"min": 4096, "optimal": 16384, "max": 65536},
    "kimi_long": {"min": 4096, "optimal": 16384, "max": 131072},
}

_FALLBACK_AGENT_DEFAULT = {
    "aletheia": "research",
    "kosmos": "analyze",
    "metis": "strategy",
    "kratos": "code_gen",
    "mnemosyne": "curation",
    "kronos": "general",
    "critic": "verify",
    "planner": "general",
}

_FALLBACK_AGENT_TASK = {
    "aletheia": {"default_task": "research", "default_model": "go-pro"},
    "kosmos": {"default_task": "code_review", "default_model": "go-pro"},
    "metis": {"default_task": "strategy", "default_model": "go-kimi-latest"},
    "kratos": {"default_task": "code_gen", "default_model": "go-flash"},
    "mnemosyne": {"default_task": "curation", "default_model": "go-flash"},
    "bcg": {"default_task": "evaluation", "default_model": "go-pro"},
    "critic": {"default_task": "verify", "default_model": "go-pro"},
    "planner": {"default_task": "general", "default_model": "go-flash"},
}

_FALLBACK_FALLBACK_CHAIN = {
    "go-flash": ["go-flash", "go-mimo", "go-qwen", "go-pro", "go-kimi-latest"],
    "go-pro": ["go-pro", "go-mimo", "go-kimi-latest", "go-flash", "go-qwen"],
    "go-kimi-latest": ["go-kimi-latest", "mimo-direct", "go-pro", "go-flash", "go-qwen"],
    "mimo-direct": ["mimo-direct", "go-kimi-latest", "go-pro", "go-flash", "go-qwen"],
    "go-mimo": ["go-mimo", "go-flash", "go-qwen", "go-pro", "go-kimi-latest"],
    "go-qwen": ["go-qwen", "go-mimo", "go-flash", "go-qwen", "go-pro", "go-kimi-latest"],
    "go-gemini-flash": ["go-gemini-flash", "go-flash", "go-mimo", "go-qwen", "go-pro", "go-kimi-latest"],
    "deepseek-direct-flash": ["deepseek-direct-flash", "go-flash", "go-mimo", "mimo-direct"],
    "deepseek-direct-pro": ["deepseek-direct-pro", "go-pro", "deepseek-pro", "go-kimi-latest"],
}

_FALLBACK_COST_RATES = {
    "flash": {"input": 0.00014, "cache_read": 0.000028, "output": 0.00028},
    "pro": {"input": 0.00174, "cache_read": 0.000145, "output": 0.00348},
    "go-flash": {"input": 0.00014, "cache_read": 0.000028, "output": 0.00028},
    "go-pro": {"input": 0.00174, "cache_read": 0.000145, "output": 0.00348},
    "go-kimi-latest": {"input": 0.00095, "cache_read": 0.00016, "output": 0.00400},
    "moonshotai/kimi-k2.5": {"input": 0.00060, "output": 0.00300, "cache_read": 0.00016},
    "moonshotai/kimi-k2.6": {"input": 0.00090, "output": 0.00372, "cache_read": 0.00020},
    "mimo": {"input": 0.000014, "cache_read": 0.0000028, "output": 0.000028},
    "mimo-direct": {"input": 0.000014, "cache_read": 0.0000028, "output": 0.000028},
    "go-mimo": {"input": 0.000014, "cache_read": 0.0000028, "output": 0.000028},
    "go-gemini-flash": {"input": 0.0, "cache_read": 0.0, "output": 0.0},
    "go-qwen": {"input": 0.00010, "cache_read": 0.00002, "output": 0.00020},
    "router9-minimax": {"input": 0.0000002, "cache_read": 0.00000004, "output": 0.0000002},
    "router9-glm": {"input": 0.0000006, "cache_read": 0.00000012, "output": 0.0000006},
    "router9-default": {"input": 0.000001, "cache_read": 0.0000002, "output": 0.000002},
}

_FALLBACK_COST_CAPS = {
    "flash": {"weekly_usd": 3.00, "daily_calls": 500},
    "mimo": {"weekly_usd": 2.00, "daily_calls": 1000},
    "pro": {"weekly_usd": 0.50, "daily_calls": 50},
    "kimi": {"weekly_usd": 1.00, "daily_calls": 30},
}


def refresh_constants():
    """Re-deriva todas las constantes del módulo desde _cfg.

    Llamada al importar y por reload_config() para que los cambios en
    aether.yaml se reflejen sin reiniciar el proceso.
    """
    global THINKING_CONFIG, BUDGETS, KIMI_BUDGETS, TASK_MODEL_MAP
    global MODEL_TIERS, AGENT_DEFAULT_TASK, AGENT_TASK_MODEL
    global MODEL_FALLBACK_CHAIN, COST_RATES, COST_CAPS
    global FLAGS, ETHER_MIMO_ENABLED, ETHER_MIMO_DIRECT_ENABLED
    global ETHER_KIMI_ENABLED, ETHER_CONTEXT_ROUTING, ETHER_MULTIMODAL_ENABLED
    global ETHER_BUDGET_ENFORCEMENT, ETHER_LANGFUSE_ENABLED, ETHER_DEEPEVAL_ENABLED
    global QUALITY_ROUTING_ENABLED, ETHER_EVAL_SAMPLE_SIZE, ETHER_ROUTER9_ENABLED

    cfg = _cfg  # may be None if YAML unavailable

    THINKING_CONFIG = cfg.THINKING_CONFIG if cfg else _FALLBACK_THINKING
    BUDGETS = cfg.BUDGETS if cfg else _FALLBACK_BUDGETS
    KIMI_BUDGETS = cfg.KIMI_BUDGETS if cfg else {"kimi": {"min": 4096, "optimal": 16384, "max": 131072}}
    TASK_MODEL_MAP = _normalize_task_model_map(cfg.TASK_MODEL_MAP) if cfg else _normalize_task_model_map(_FALLBACK_TASK_MODEL_MAP)
    MODEL_TIERS = dict(cfg.MODEL_TIERS) if cfg else dict(_FALLBACK_MODEL_TIERS)
    if "mimo" in MODEL_TIERS and "max_budget_pct" not in MODEL_TIERS["mimo"]:
        MODEL_TIERS["mimo"]["max_budget_pct"] = 30
    AGENT_DEFAULT_TASK = dict(cfg.AGENT_DEFAULT_TASK) if cfg else dict(_FALLBACK_AGENT_DEFAULT)
    AGENT_TASK_MODEL = dict(cfg.AGENT_TASK_MODEL) if (cfg and hasattr(cfg, 'AGENT_TASK_MODEL') and cfg.AGENT_TASK_MODEL) else dict(_FALLBACK_AGENT_TASK)
    MODEL_FALLBACK_CHAIN = dict(cfg.MODEL_FALLBACK_CHAIN) if cfg else dict(_FALLBACK_FALLBACK_CHAIN)
    COST_RATES = dict(cfg.COST_RATES) if cfg else dict(_FALLBACK_COST_RATES)
    COST_CAPS = dict(cfg.COST_CAPS) if cfg else dict(_FALLBACK_COST_CAPS)

    FLAGS = dict(cfg.FEATURE_FLAGS) if cfg else {}
    ETHER_MIMO_ENABLED = os.environ.get("ETHER_MIMO_ENABLED", str(FLAGS.get("ether_mimo_enabled", "true"))).lower() == "true"
    ETHER_MIMO_DIRECT_ENABLED = os.environ.get("ETHER_MIMO_DIRECT_ENABLED", str(FLAGS.get("ether_mimo_direct_enabled", "true"))).lower() == "true"
    ETHER_KIMI_ENABLED = os.environ.get("ETHER_KIMI_ENABLED", str(FLAGS.get("ether_kimi_enabled", "true"))).lower() == "true"
    ETHER_CONTEXT_ROUTING = os.environ.get("ETHER_CONTEXT_ROUTING", str(FLAGS.get("ether_context_routing", "true"))).lower() == "true"
    ETHER_MULTIMODAL_ENABLED = os.environ.get("ETHER_MULTIMODAL_ENABLED", str(FLAGS.get("ether_multimodal_enabled", "true"))).lower() == "true"
    ETHER_BUDGET_ENFORCEMENT = os.environ.get("ETHER_BUDGET_ENFORCEMENT", str(FLAGS.get("ether_budget_enforcement", "true"))).lower() == "true"
    ETHER_LANGFUSE_ENABLED = os.environ.get("ETHER_LANGFUSE_ENABLED", str(FLAGS.get("ether_langfuse_enabled", "true"))).lower() == "true"
    ETHER_DEEPEVAL_ENABLED = os.environ.get("ETHER_DEEPEVAL_ENABLED", str(FLAGS.get("ether_deepeval_enabled", "true"))).lower() == "true"
    QUALITY_ROUTING_ENABLED = os.environ.get("ETHER_QUALITY_ROUTING", str(FLAGS.get("quality_routing_enabled", "true"))).lower() in ("1", "true")
    ETHER_EVAL_SAMPLE_SIZE = int(os.environ.get("ETHER_EVAL_SAMPLE_SIZE", str(FLAGS.get("ether_eval_sample_size", "10"))))
    ETHER_ROUTER9_ENABLED = os.environ.get("ETHER_ROUTER9_ENABLED", str(FLAGS.get("ether_router9_enabled", "true"))).lower() == "true"


# ── Initialize constants from config ─────────────────────────
refresh_constants()

ETHER_CIRCUIT_BREAKER_ENABLED = (
    os.environ.get(
        "ETHER_CIRCUIT_BREAKER_ENABLED",
        os.environ.get("ROUTER_CIRCUIT_BREAKER_ENABLED", "true"),
    ).lower()
    == "true"
)

ETHER_CIRCUIT_RESET_TIMEOUT = int(
    os.environ.get(
        "ETHER_CIRCUIT_RESET_TIMEOUT",
        os.environ.get("ROUTER_CIRCUIT_RESET_TIMEOUT", "300"),
    )
)

ETHER_FAILURE_THRESHOLD = int(
    os.environ.get(
        "ETHER_FAILURE_THRESHOLD",
        os.environ.get("ROUTER_FAILURE_THRESHOLD", "3"),
    )
)

ETHER_HALF_OPEN_MAX = int(
    os.environ.get(
        "ETHER_HALF_OPEN_MAX",
        os.environ.get("ROUTER_HALF_OPEN_MAX", "1"),
    )
)
