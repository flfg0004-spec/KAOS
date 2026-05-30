import logging

logger = logging.getLogger("aether")
logger.debug("Loading aether package")
try:
    from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER, CircuitBreaker
except ImportError:
    logger.warning("aether.circuit not available")
    CircuitBreaker = None
try:
    from lib.aether.client import (
        allocate,
        build_optimized_context,
        build_prompt,
        call_api,
        call_structured,
        chat,
        configure_thinking,
        estimate_cache_ratio,
        extract_cache_metrics,
        generate_structured,
        get_output_config,
        reset_tracker,
        status,
    )
except ImportError:
    logger.exception("aether.client not available")
    raise
try:
    from lib.aether.config import (
        AGENT_DEFAULT_TASK,
        BUDGETS,
        MODEL_FALLBACK_CHAIN,
        MODEL_TIERS,
        TASK_MODEL_MAP,
        THINKING_CONFIG,
    )
except ImportError:
    logger.exception("aether.config not available")
    raise
try:
    from lib.aether.limiter import RateLimiter, check_rate_limit
except ImportError:
    logger.warning("aether.limiter not available")
    RateLimiter = check_rate_limit = None
try:
    from lib.aether.router import resolve_model
except ImportError:
    logger.warning("aether.router not available")
    resolve_model = lambda **kw: {"model": kw.get("default", "go-flash")}
try:
    from lib.aether.config_loader import reload_config
except ImportError:
    logger.warning("aether.config_loader not available")
    reload_config = lambda **kw: None
try:
    from lib.aether.env import detect_caller, reset_caller_cache
except ImportError:
    logger.warning("aether.env not available")
    detect_caller = lambda: "unknown"
    reset_caller_cache = lambda: None
try:
    from lib.aether.tracker import EtherTracker
except ImportError:
    logger.warning("aether.tracker not available")
    EtherTracker = None
try:
    from lib.aether.quality_store import QualityStore
except ImportError:
    logger.warning("aether.quality_store not available")
    QualityStore = None
try:
    from lib.aether.eval import EvalPipeline, auto_eval_if_needed, run_eval_pipeline, trigger_eval
except ImportError:
    logger.warning("aether.eval not available")
    EvalPipeline = auto_eval_if_needed = run_eval_pipeline = trigger_eval = None
try:
    from lib.aether.ab_testing import ABTest
except ImportError:
    logger.warning("aether.ab_testing not available")
    ABTest = None
try:
    from lib.aether.observability import Timer, observe
except ImportError:
    logger.warning("aether.observability not available")
    Timer = observe = None

__all__ = [
    "resolve_model", "chat", "call_structured", "generate_structured",
    "CircuitBreaker", "EtherTracker", "RateLimiter", "check_rate_limit",
    "TASK_MODEL_MAP", "AGENT_DEFAULT_TASK", "MODEL_FALLBACK_CHAIN",
    "MODEL_TIERS", "BUDGETS", "THINKING_CONFIG", "build_optimized_context",
    "estimate_cache_ratio", "configure_thinking", "allocate",
    "get_output_config", "extract_cache_metrics", "status", "reset_tracker",
    "build_prompt", "call_api", "QualityStore", "EvalPipeline",
    "auto_eval_if_needed", "run_eval_pipeline", "trigger_eval", "ABTest",
    "Timer", "observe",
]
