import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

VAULT_ROOT: Final[Path] = (Path(__file__).resolve().parent.parent.parent)

MAX_TOKENS: Final[int] = 128000
TOKEN_RATIO: Final[float] = 3.0  # chars per token for Spanish/English mixed

PRESSURE_THRESHOLDS: Final[dict] = {
    "critical": 0.95,  # 95%+ → archive
    "high": 0.85,      # 85-95% → compress
    "warning": 0.70,   # 70-85% → trim
}

PRIORITY_ORDER: Final[list[str]] = [
    "wiki/entities/",
    "wiki/concepts/",
    "wiki/sources/",
    "raw/",
    "schema/",
]

IGNORED_PAGES: Final[set[str]] = {"index", "log"}
IGNORED_WIKILINKS: Final[set[str]] = {"wikilink", "wikilinks", "todo", "wip", "update"}

# LLM Provider config
DEEPSEEK_API_KEY: Final[str] = os.environ.get("DEEPSEEK_API_KEY", "")
OPENCODE_GO_KEY: Final[str] = os.environ.get("OPENCODE_GO_KEY", "")
OPENCODE_GO_ENDPOINT: Final[str] = os.environ.get(
    "OPENCODE_GO_ENDPOINT", "https://opencode.ai/zen/go/v1"
)
LLM_DIRECT_ENABLED: Final[bool] = os.environ.get("LLM_DIRECT_ENABLED", "true").lower() == "true"
LLM_FALLBACK_ENABLED: Final[bool] = True
EXECUTOR_ENABLED: Final[bool] = os.environ.get("EXECUTOR_ENABLED", "false").lower() == "true"
EXECUTOR_TIMEOUT: Final[int] = int(os.environ.get("EXECUTOR_TIMEOUT", "300"))
XIAOMI_API_KEY: Final[str] = os.environ.get("XIAOMI_API_KEY", "")
XIAOMI_API_ENDPOINT: Final[str] = os.environ.get("XIAOMI_API_ENDPOINT", "https://token-plan-sgp.xiaomimimo.com/v1")
RAG_ENABLED: Final[bool] = os.environ.get("RAG_ENABLED", "true").lower() == "true"
RAG_TOP_K: Final[int] = max(1, int(os.environ.get("RAG_TOP_K", "5")))
HERMES_ENABLED: Final[bool] = os.environ.get("HERMES_ENABLED", "true").lower() == "true"
HERMES_CHANNEL: Final[str] = os.environ.get("HERMES_CHANNEL", "kaos-ci")
DEERFLOW_ENABLED: Final[bool] = os.environ.get("DEERFLOW_ENABLED", "false").lower() == "true"
AGNO_ENABLED: Final[bool] = os.environ.get("AGNO_ENABLED", "false").lower() == "true"
MOME_THRESHOLD: Final[int] = int(os.environ.get("MOME_THRESHOLD", "10000"))
HYBRID_PRO_ENABLED: Final[bool] = os.environ.get("HYBRID_PRO_ENABLED", "false").lower() == "true"
PRO_COMPLEXITY_THRESHOLD: Final[str] = os.environ.get("PRO_COMPLEXITY_THRESHOLD", "alta")

CACHE_MAX_ENTRIES: Final[int] = 30
CACHE_DEFAULT_TTL: Final[int] = 3600  # seconds

# Multi-Model Router config
ROUTER_DEFAULT_MODEL: Final[str] = os.environ.get("ROUTER_DEFAULT_MODEL", "go-flash")
ROUTER_CIRCUIT_BREAKER_ENABLED: Final[bool] = os.environ.get(
    "ROUTER_CIRCUIT_BREAKER_ENABLED", "true"
).lower() == "true"
ROUTER_CIRCUIT_RESET_TIMEOUT: Final[int] = int(
    os.environ.get("ROUTER_CIRCUIT_RESET_TIMEOUT", "300")
)
ROUTER_FAILURE_THRESHOLD: Final[int] = int(
    os.environ.get("ROUTER_FAILURE_THRESHOLD", "3")
)
ROUTER_HALF_OPEN_MAX: Final[int] = int(
    os.environ.get("ROUTER_HALF_OPEN_MAX", "1")
)

# Phase B parallelism
PHASE_B_WORKERS: Final[int] = int(os.environ.get("KAOS_PHASE_B_WORKERS", "5"))

# Quality engine thresholds
QUALITY_THRESHOLD_WARN: Final[int] = 80
QUALITY_THRESHOLD_CRIT: Final[int] = 60

# OPA Governance configuration
OPA_EVAL_MODE: Final[str] = os.environ.get("OPA_EVAL_MODE", "auto")

# Knowledge Scorer thresholds
KNOWLEDGE_SCORE_THRESHOLDS: Final[dict] = {
    "synthesis_threshold": 60,
    "canonical_min": 91,
    "curated_min": 76,
    "review_min": 61,
    "draft_min": 41,
    "rough_min": 21,
    "raw_min": 0,
}
KNOWLEDGE_SYNTHESIS_MAX_ATTEMPTS: Final[int] = int(os.environ.get("KAOS_SYNTHESIS_MAX_ATTEMPTS", "3"))
KNOWLEDGE_SYNTHESIS_MAX_DOCS: Final[int] = int(os.environ.get("KAOS_SYNTHESIS_MAX_DOCS", "5"))
KNOWLEDGE_SYNTHESIS_MAX_DIFF_RATIO: Final[float] = float(os.environ.get("KAOS_SYNTHESIS_MAX_DIFF_RATIO", "0.5"))
KNOWLEDGE_SYNTHESIS_TOKEN_BUDGET: Final[int] = int(os.environ.get("KAOS_SYNTHESIS_TOKEN_BUDGET", "100000"))

CACHE_DIR: Final[Path] = VAULT_ROOT / "cache"
GAP_FEEDBACK_FILE: Path = CACHE_DIR / "gap_feedback.jsonl"

# Kratos sleep cycle
KRATOS_SLEEP_ENABLED: Final[bool] = os.environ.get("KRATOS_SLEEP_ENABLED", "false").lower() == "true"
KRATOS_SLEEP_IDLE_MINUTES: Final[int] = int(os.environ.get("KRATOS_SLEEP_IDLE_MINUTES", "30"))

# Kratos auto-pruning
KRATOS_PRUNE_ENABLED: Final[bool] = os.environ.get("KRATOS_PRUNE_ENABLED", "true").lower() == "true"
KRATOS_PRUNE_THRESHOLD: Final[int] = int(os.environ.get("KRATOS_PRUNE_THRESHOLD", "5000"))
