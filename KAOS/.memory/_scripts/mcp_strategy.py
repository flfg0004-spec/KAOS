#!/usr/bin/env python3
"""MCP wrapper for strategy-mcp — 12 strategic frameworks as MCP tools.

Launches the strategy-mcp FastMCP server with stdio transport.
"""
import sys
from pathlib import Path

STRATEGY_MCP_DIR = Path(__file__).resolve().parent.parent.parent / ".tools" / "strategy-mcp"
SERVER_PY = STRATEGY_MCP_DIR / "app.py"

if not SERVER_PY.exists():
    print("ERROR: strategy-mcp not installed. Clone to .tools/strategy-mcp/", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(STRATEGY_MCP_DIR))
exec(compile(open(str(SERVER_PY)).read(), str(SERVER_PY), "exec"))
