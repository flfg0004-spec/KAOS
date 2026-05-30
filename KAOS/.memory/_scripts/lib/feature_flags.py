import json
import logging
import os
from typing import Final

logger = logging.getLogger(__name__)

DEFAULT_FLAGS: Final[dict[str, bool]] = {
    "use_new_agent_executor": False,
    "use_unified_circuit_breaker": False,
    "use_dag_verification": False,
    "use_event_coordination": False,
    "use_new_quality_engine": False,
    "use_incremental_analysis": True,
    "use_enhanced_parallelism": True,
    "use_knowledge_tour": True,
    "use_domain_mapper": True,
    "use_kroki_diagrams": True,
    "use_markmap_mindmaps": True,
    "use_plotly_dashboard": True,
    "use_cytoscape_graph": True,
    "use_pdf_reports": True,
    "use_knowledge_scorer": True,
    "use_knowledge_synthesis": True,
    "use_curation_pipeline": True,
    "ether_docker_enabled": False,
    "ether_searxng_enabled": False,
    "ether_crawl4ai_enabled": False,
    "ether_agno_pg_enabled": False,
    "ether_sandbox_enabled": False,
    "ether_langfuse_enabled": False,

    # === Kratos 2.0 Alpha — Track A (Foundation) ===
    "use_kratos_v2": False,
    "use_real_coverage": False,
    "use_kratos_telemetry": False,

    # === Kratos 2.0 Alpha — Track D (Multi-lang) ===
    "use_rust_gates": False,
    "use_ts_gates": False,
    "use_go_gates": False,

    # === Kratos 2.0 Alpha — Track B (Performance) ===
    "use_parallel_gates": False,
    "use_early_exit": False,

    # === Kratos 2.0 Alpha — Track C (Quality) ===
    "use_real_mypy": False,
    "use_circuit_breaker": False,

    # === H3 Sprint 3 — Governance & Dashboard ===
    "opa_strict_mode": False,
    "use_kratos_dashboard": False,

    # === Kratos 2.0 Alpha — Shadow Mode ===
    "kratos_shadow_mode": False,

    # === Hermes Tool Bridge (WS-1) ===
    "use_progressive_disclosure": False,

    # === Harness Lite (WS-2) ===
    "use_hard_quality_gates": False,

    # === H3 Sprint 4 — MCP Quality Gates (Phase 2) ===
    "mcp_quality_server": False,
    "mcp_quality_client": False,

    # === Namespaced names (aliased from legacy flat names) ===
    "kratos_new_executor": False,
    "kratos_circuit_breaker": False,
    "kratos_dag_verification": False,
    "kratos_event_coordination": False,
    "kratos_parallel_gates": False,
    "kratos_early_exit": False,
    "kratos_mypy": False,
    "kratos_circuit_breaker_legacy": False,
    "kratos_telemetry": False,
    "kratos_coverage": False,
    "kratos_dashboard": False,
    "kratos_rust_gates": False,
    "kratos_ts_gates": False,
    "kratos_go_gates": False,
    "kratos_hard_gates": False,
    "kratos_shadow_mode": False,
    "quality_new_engine": False,
    "mnemosyne_incremental": True,
    "mnemosyne_parallelism": True,
    "quality_knowledge_tour": True,
    "quality_domain_mapper": True,
    "quality_knowledge_scorer": True,
    "quality_knowledge_synthesis": True,
    "quality_curation": True,
    "viz_kroki": True,
    "viz_markmap": True,
    "viz_plotly": True,
    "viz_cytoscape": True,
    "viz_pdf": True,
    "infra_docker": False,
    "infra_searxng": False,
    "infra_crawl4ai": False,
    "infra_agno_pg": False,
    "infra_sandbox": False,
    "infra_langfuse": False,
    "ux_progressive_disclosure": False,
    "opa_strict_mode": False,
    "mcp_quality_server": False,
    "mcp_quality_client": False,
}

# === Pilot agents for phased rollouts (Fase 1: Metis) ===
PILOT_AGENTS: Final[set[str]] = {"metis"}


def is_enabled_for_agent(flag_name: str, agent_name: str) -> bool:
    """Check if a feature flag is enabled, with agent-specific override.

    Resolution order:
        1. Env var ``KAOS_FLAG_OVERRIDES`` (JSON dict of ``{flag_name: [agent_list]}``)
        2. Default flag value (via :func:`is_enabled`)
        3. Pilot agent list (if flag is ``use_progressive_disclosure``)

    Args:
        flag_name: The feature flag name.
        agent_name: The agent attempting to use the feature.

    Returns:
        True if the flag is enabled for this agent.
    """
    # 1. Check env var override
    raw = os.environ.get("KAOS_FLAG_OVERRIDES", "")
    if raw:
        try:
            overrides: dict[str, list[str]] = json.loads(raw)
            if flag_name in overrides and agent_name in overrides[flag_name]:
                logger.debug(
                    "Feature flag %s enabled for agent %s (via KAOS_FLAG_OVERRIDES)",
                    flag_name, agent_name,
                )
                return True
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Invalid KAOS_FLAG_OVERRIDES: %s", e)

    # 2. Check default flag value
    if is_enabled(flag_name):
        return True

    # 3. Special case: pilot agents for use_progressive_disclosure
    resolved = _resolve_flag(flag_name)
    if resolved == "ux_progressive_disclosure" and agent_name in PILOT_AGENTS:
        logger.info(
            "Progressive disclosure enabled for pilot agent '%s' (phase 1)",
            agent_name,
        )
        return True

    return False


FLAG_ALIASES: Final[dict[str, str]] = {
    # ── Kratos domain ──
    "use_new_agent_executor": "kratos_new_executor",
    "use_kratos_v2": "kratos_new_executor",
    "use_unified_circuit_breaker": "kratos_circuit_breaker",
    "use_dag_verification": "kratos_dag_verification",
    "use_event_coordination": "kratos_event_coordination",
    "use_parallel_gates": "kratos_parallel_gates",
    "use_early_exit": "kratos_early_exit",
    "use_real_mypy": "kratos_mypy",
    "use_circuit_breaker": "kratos_circuit_breaker_legacy",
    "use_kratos_telemetry": "kratos_telemetry",
    "use_real_coverage": "kratos_coverage",
    "use_kratos_dashboard": "kratos_dashboard",
    "use_rust_gates": "kratos_rust_gates",
    "use_ts_gates": "kratos_ts_gates",
    "use_go_gates": "kratos_go_gates",
    "use_hard_quality_gates": "kratos_hard_gates",
    "kratos_shadow_mode": "kratos_shadow_mode",

    # ── Quality domain ──
    "use_new_quality_engine": "quality_new_engine",
    "use_incremental_analysis": "mnemosyne_incremental",
    "use_enhanced_parallelism": "mnemosyne_parallelism",
    "use_knowledge_tour": "quality_knowledge_tour",
    "use_domain_mapper": "quality_domain_mapper",
    "use_knowledge_scorer": "quality_knowledge_scorer",
    "use_knowledge_synthesis": "quality_knowledge_synthesis",
    "use_curation_pipeline": "quality_curation",

    # ── Viz domain ──
    "use_kroki_diagrams": "viz_kroki",
    "use_markmap_mindmaps": "viz_markmap",
    "use_plotly_dashboard": "viz_plotly",
    "use_cytoscape_graph": "viz_cytoscape",
    "use_pdf_reports": "viz_pdf",

    # ── Infra domain ──
    "ether_docker_enabled": "infra_docker",
    "ether_searxng_enabled": "infra_searxng",
    "ether_crawl4ai_enabled": "infra_crawl4ai",
    "ether_agno_pg_enabled": "infra_agno_pg",
    "ether_sandbox_enabled": "infra_sandbox",
    "ether_langfuse_enabled": "infra_langfuse",

    # ── UX domain ──
    "use_progressive_disclosure": "ux_progressive_disclosure",

    # ── OPA / MCP (identity aliases) ──
    "opa_strict_mode": "opa_strict_mode",
    "mcp_quality_server": "mcp_quality_server",
    "mcp_quality_client": "mcp_quality_client",
}

_flags: dict[str, bool] = {}


def _load_env_overrides() -> dict[str, bool]:
    overrides: dict[str, bool] = {}

    raw = os.environ.get("KAOS_FEATURE_FLAGS", "")
    if raw:
        try:
            parsed = json.loads(raw)
            for k, v in parsed.items():
                if k in DEFAULT_FLAGS:
                    overrides[k] = bool(v)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Invalid KAOS_FEATURE_FLAGS: %s", e)

    for key in os.environ:
        flag = key.lower()
        if flag in DEFAULT_FLAGS:
            overrides[flag] = os.environ[key].lower() in ("true", "1", "yes")

    return overrides


def _resolve_flag(flag_name: str) -> str:
    resolved = FLAG_ALIASES.get(flag_name, flag_name)
    if resolved != flag_name:
        import warnings
        warnings.warn(
            f"Flag '{flag_name}' is deprecated. Use '{resolved}' instead.",
            DeprecationWarning,
            stacklevel=3,
        )
    return resolved


def init() -> None:
    global _flags
    _flags = dict(DEFAULT_FLAGS)
    overrides = _load_env_overrides()
    for k, v in overrides.items():
        old = _flags.get(k)
        _flags[k] = v
        if old != v:
            logger.info("Feature flag %s: %s → %s (via env)", k, old, v)


def is_enabled(flag_name: str) -> bool:
    resolved = _resolve_flag(flag_name)
    if not _flags:
        init()
    return _flags.get(resolved, False)


def enable(flag_name: str) -> None:
    resolved = _resolve_flag(flag_name)
    if not _flags:
        init()
    if resolved not in DEFAULT_FLAGS:
        valid = sorted(set(DEFAULT_FLAGS.keys()) | set(FLAG_ALIASES.values()))
        raise ValueError(f"Unknown feature flag: '{flag_name}' (resolved: '{resolved}'). Valid: {valid}")
    old = _flags[resolved]
    _flags[resolved] = True
    if old is not True:
        logger.info("Feature flag %s: %s → True", flag_name, old)


def disable(flag_name: str) -> None:
    resolved = _resolve_flag(flag_name)
    if not _flags:
        init()
    if resolved not in DEFAULT_FLAGS:
        valid = sorted(set(DEFAULT_FLAGS.keys()) | set(FLAG_ALIASES.values()))
        raise ValueError(f"Unknown feature flag: '{flag_name}' (resolved: '{resolved}'). Valid: {valid}")
    old = _flags[resolved]
    _flags[resolved] = False
    if old is not False:
        logger.info("Feature flag %s: %s → False", flag_name, old)


def list_flags() -> dict[str, bool]:
    if not _flags:
        init()
    return dict(_flags)


def reset() -> None:
    global _flags
    _flags = dict(DEFAULT_FLAGS)
    logger.info("Feature flags reset to defaults")


init()
