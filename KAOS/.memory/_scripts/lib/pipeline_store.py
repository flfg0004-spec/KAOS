"""Pipeline Store — public API for pipeline persistence.

Provides core storage primitives used by mcp_pipeline and dashboard.
Refactored from mcp_pipeline private symbols to break coupling.
"""

import json
from datetime import datetime
from pathlib import Path

from lib.config import VAULT_ROOT

# ── Public constants ──
PIPELINE_DIR = VAULT_ROOT / "cache" / "pipeline_runs"
PRIORITY_ORDER: dict[str, int] = {"critical": 0, "high": 1, "normal": 2, "low": 3}
VALID_PRIORITIES: frozenset[str] = frozenset(PRIORITY_ORDER.keys())
DEFAULT_TIMEOUT: int = 300


# ── Internal helpers ──

def _pipeline_path(pipeline_id: str) -> Path:
    return PIPELINE_DIR / f"{pipeline_id}.json"


# ── Public API ──

def now_iso() -> str:
    """Returns current ISO datetime string."""
    return datetime.now().isoformat()


def load_pipeline(pipeline_id: str) -> dict | None:
    """Load a pipeline from the store. Returns None if not found."""
    path = _pipeline_path(pipeline_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_pipeline(pipeline_id: str, data: dict):
    """Save a pipeline to the store."""
    PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
    path = _pipeline_path(pipeline_id)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
