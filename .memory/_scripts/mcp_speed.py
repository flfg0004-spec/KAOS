#!/usr/bin/env python3
"""MCP server: speed metrics for the dual system (Gemini Flash + DeepSeek).

Wraps lib.speed.report() as an MCP tool callable by any agent.
Folllows the same FastMCP pattern as mcp_strategy_extras.py.
"""

import sys
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None

# Add the _scripts directory to sys.path so we can import lib.speed
_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE))

from lib.speed import report as _speed_report

# ── Tools ────────────────────────────────────────────────────


def speed_report() -> str:
    """Generate speed metrics report for the dual system.

    Returns a markdown report with:
    - Flash call counts (24h / 1h)
    - Flash → Production ratio
    - Average time-to-commit
    - Pipeline benchmarks by profile
    - Recent bridge report files
    """
    return _speed_report()


# ── Server ───────────────────────────────────────────────────


def main():
    if FastMCP is None:
        msg = "ERROR: fastmcp not installed. Run: pip install 'mcp>=1.26.0'"
        print(msg, file=sys.stderr)
        sys.exit(1)

    mcp = FastMCP("mcp-speed")

    mcp.tool()(speed_report)

    mcp.run()


if __name__ == "__main__":
    main()
