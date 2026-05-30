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

    # === Hermes Tool Bridge (WS-1) ===
    "use_progressive_disclosure": False,
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
    if not _flags:
        init()
    return _flags.get(flag_name, False)


def enable(flag_name: str) -> None:
    if not _flags:
        init()
    if flag_name not in DEFAULT_FLAGS:
        raise ValueError(f"Unknown feature flag: {flag_name}")
    old = _flags[flag_name]
    _flags[flag_name] = True
    if old is not True:
        logger.info("Feature flag %s: %s → True", flag_name, old)


def disable(flag_name: str) -> None:
    if not _flags:
        init()
    if flag_name not in DEFAULT_FLAGS:
        raise ValueError(f"Unknown feature flag: {flag_name}")
    old = _flags[flag_name]
    _flags[flag_name] = False
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
