#!/usr/bin/env python3
"""MCP server: Strategic Memory Bank — persistent strategy storage with context recall and pattern detection."""

import json
import sys
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None

_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE))

from strategy_memory import StrategicMemoryBank

bank = StrategicMemoryBank()


def memory_store(context_json: str, content_json: str, plan_type: str, outcome_score: float = None, feedback: str = None) -> str:
    """Store a strategy in StrategicMemoryBank.

    Args:
        context_json: JSON string with context data (industry, team_size, etc.)
        content_json: JSON string with strategy content (OKRs, plans, etc.)
        plan_type: Type of plan (okr, roadmap, foda, strategic_analysis, etc.)
        outcome_score: Optional outcome score (0-10) for calibration
        feedback: Optional feedback text

    Returns:
        Confirmation string with the stored strategy id
    """
    context = json.loads(context_json)
    content = json.loads(content_json)
    sid = bank.store(context, content, plan_type, outcome_score, feedback)
    return f"Stored strategy id={sid}"


def memory_recall(context_json: str, top_k: int = 5) -> str:
    """Recall similar strategies by context similarity.

    Args:
        context_json: JSON string describing the current context
        top_k: Number of similar strategies to return (default: 5)

    Returns:
        Markdown table with similar strategies
    """
    context = json.loads(context_json)
    results = bank.recall_similar(context, top_k)
    if not results:
        return "No similar strategies found."
    lines = [
        "| ID | Plan Type | Timestamp | Outcome Score |",
        "|----|-----------|-----------|---------------|",
    ]
    for r in results:
        score = str(r["outcome_score"]) if r["outcome_score"] is not None else "N/A"
        lines.append(f"| {r['id']} | {r['plan_type']} | {r['timestamp'][:19]} | {score} |")
    return "\n".join(lines)


def memory_predict(context_json: str, plan_type: str = None) -> str:
    """Predict outcome probability based on similar past strategies.

    Args:
        context_json: JSON string describing the current context
        plan_type: Optional plan type filter

    Returns:
        Markdown with P(success) and interpretation message
    """
    context = json.loads(context_json)
    result = bank.predict_outcome(context, plan_type)
    prob = result.get("probability_success")
    if prob is None:
        return f"**Prediction**: {result.get('message', 'No data available.')}"
    parts = [
        f"**P(Success)**: {prob:.0%}",
        f"**Avg Outcome Score**: {result.get('avg_outcome_score', 'N/A')}/10",
        f"**Based on**: {result.get('based_on_n_strategies', 0)} similar strategies",
        f"**Plan Type**: {result.get('plan_type', 'any')}",
        f"**Interpretation**: {result.get('message', '')}",
    ]
    return "\n\n".join(parts)


def memory_patterns() -> str:
    """Get detected failure patterns with prevention suggestions.

    Returns:
        Markdown table with failure patterns and suggestions
    """
    patterns = bank.get_failure_patterns()
    if not patterns:
        return "No failure patterns detected."
    lines = [
        "| Plan Type | Pattern | Description | Suggestion |",
        "|-----------|---------|-------------|------------|",
    ]
    for p in patterns:
        desc = (p.get("description", "") or "")[:60]
        suggestion = (p.get("suggestion", "") or "")[:60]
        lines.append(f"| {p['plan_type']} | {p.get('pattern_name', 'N/A')} | {desc} | {suggestion} |")
    return "\n".join(lines)


def main():
    if FastMCP is None:
        msg = "ERROR: fastmcp not installed. Run: pip install 'mcp>=1.26.0'"
        print(msg, file=sys.stderr)
        sys.exit(1)

    mcp = FastMCP("mcp-strategy-memory")

    mcp.tool()(memory_store)
    mcp.tool()(memory_recall)
    mcp.tool()(memory_predict)
    mcp.tool()(memory_patterns)

    mcp.run()


if __name__ == "__main__":
    main()
