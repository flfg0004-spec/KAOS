#!/usr/bin/env python3
"""MCP server: DeepSeek Optimization Layer v2 — model resolution & token tracking.

Wraps lib.aether.resolve_model() and lib.aether.EtherTracker as MCP tools.
"""

import json
import sys
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None

# Add the _scripts directory to sys.path so we can import lib.aether
_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE))

from lib.aether import resolve_model
from lib.aether.tracker import EtherTracker as TokenTracker

# ── Tools ────────────────────────────────────────────────────


def dsol_resolve_model(
    task_type: str = "",
    agent: str = "",
    model_override: str = "",
) -> str:
    """Resolve which model should handle a task based on DSOL routing rules.

    Order of precedence:
        1. model_override (explicit, e.g. "go-pro")
        2. TASK_MODEL_MAP by task_type (e.g. "research" → go-pro)
        3. AGENT_DEFAULT_TASK by agent name (e.g. "aletheia" → research → go-pro)
        4. Absolute default: go-flash

    Args:
        task_type: Task category (lint, research, strategy, code_gen, …)
        agent:     Agent name (aletheia, kosmos, metis, kratos, …)
        model_override: Explicit model override (e.g. "go-pro", "go-kimi-latest")

    Returns:
        JSON string: {"model": str, "thinking": str | null, "tier": str, "resolved_by": str}
    """
    result = resolve_model(
        task_type=task_type or None,
        agent=agent,
        model_override=model_override or None,
    )
    return json.dumps(result, indent=2, ensure_ascii=False)


def dsol_token_tracker() -> str:
    """Get token usage statistics across all agents, models, and daily breakdown.

    Returns:
        JSON string with total_calls, prompt/completion tokens, cache metrics,
        daily breakdown (last 7 days), and per-agent breakdown.
    """
    tracker = TokenTracker()
    stats = tracker.get_stats()
    return json.dumps(stats, indent=2, ensure_ascii=False)


# ── Server ───────────────────────────────────────────────────


def main():
    if FastMCP is None:
        msg = "ERROR: fastmcp not installed. Run: pip install 'mcp>=1.26.0'"
        print(msg, file=sys.stderr)
        sys.exit(1)

    mcp = FastMCP("mcp-dsol")

    mcp.tool()(dsol_resolve_model)
    mcp.tool()(dsol_token_tracker)

    mcp.run()


if __name__ == "__main__":
    main()
