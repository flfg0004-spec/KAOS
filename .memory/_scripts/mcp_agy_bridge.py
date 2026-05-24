"""KAOS agy-bridge — MCP server for model-tiered agy access.

Exposes 4 tools to OpenCode agents:
- agy_ask_flash: Gemini Flash (FREE) — review, explore, routine
- agy_ask_sonnet: Claude Sonnet — ADR validation, design review
- agy_ask_opus: Claude Opus — strategy, critical decisions
- agy_status: health check (no LLM)

Filesystem signaling: all calls logged to .memory/bridge/
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from lib.agy_client import call_agy, bridge_reports
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="kaos-agy-bridge",
    instructions=(
        "KAOS bridge to agy with model-tiered access. "
        "agy_ask_flash = FREE Gemini Flash. "
        "agy_ask_sonnet = Claude Sonnet. "
        "agy_ask_opus = Claude Opus (expensive, use only for critical). "
        "agy_status = health check, no LLM cost."
    ),
)


# ---------------------------------------------------------------------------
# Tool: agy_ask_flash — Gemini Flash (FREE)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="agy_ask_flash",
    description=(
        "Ask agy with Gemini 3.5 Flash (FREE model). "
        "Use for: code review, quick questions, documentation, exploration. "
        "Returns JSON with success, text, error, model, report_path."
    ),
)
def agy_ask_flash(PROMPT: str, timeout: int = 120) -> str:
    result = call_agy(PROMPT, tier="flash", timeout=timeout)
    return json.dumps(result, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: agy_ask_sonnet — Claude Sonnet
# ---------------------------------------------------------------------------


@mcp.tool(
    name="agy_ask_sonnet",
    description=(
        "Ask agy with Claude Sonnet 4.6. "
        "Use for: ADR validation, architectural review, design analysis. "
        "Returns JSON with success, text, error, model, report_path."
    ),
)
def agy_ask_sonnet(PROMPT: str, timeout: int = 180) -> str:
    result = call_agy(PROMPT, tier="sonnet", timeout=timeout)
    return json.dumps(result, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: agy_ask_opus — Claude Opus (crítico)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="agy_ask_opus",
    description=(
        "Ask agy with Claude Opus 4.6 (expensive). "
        "Use ONLY for: strategy, critical architecture decisions, complex analysis. "
        "Returns JSON with success, text, error, model, report_path."
    ),
)
def agy_ask_opus(PROMPT: str, timeout: int = 300) -> str:
    result = call_agy(PROMPT, tier="opus", timeout=timeout)
    return json.dumps(result, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: agy_status — health check (sin LLM)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="agy_status",
    description=(
        "KAOS bridge + agy health check. No LLM cost. "
        "Returns bridge status, agy version, current model, recent reports."
    ),
)
def agy_status() -> str:
    import subprocess
    try:
        agy_ver = subprocess.run(
            ["agy", "--version"], capture_output=True, text=True, timeout=5
        ).stdout.strip() or "unknown"
    except Exception:
        agy_ver = "not found"

    settings_path = Path.home() / ".gemini" / "antigravity-cli" / "settings.json"
    current_model = "unknown"
    if settings_path.exists():
        try:
            current_model = json.loads(settings_path.read_text()).get("model", "unknown")
        except Exception:
            pass

    reports = bridge_reports(5)

    return json.dumps({
        "bridge": "online",
        "agy_version": agy_ver,
        "current_model": current_model,
        "reports_available": len(reports),
        "recent_reports": reports,
        "timestamp": datetime.now().isoformat(),
    }, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
