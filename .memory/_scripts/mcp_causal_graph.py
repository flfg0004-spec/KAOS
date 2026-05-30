#!/usr/bin/env python3
"""MCP server for causal_graph.py — Causal DAG modeler.

Exposes 3 tools: causal_analyze, causal_leverage, causal_chain.
JSON-RPC 2.0 over stdio. No external dependencies.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".tools"))
from causal_graph import CausalModeler

TOOLS = [
    {
        "name": "causal_analyze",
        "description": "Build a causal DAG from context text and return a full markdown report with nodes, edges, leverage points, and second-order effects",
        "inputSchema": {
            "type": "object",
            "properties": {
                "context_text": {
                    "type": "string",
                    "description": "Strategic context text describing metrics, actions, outcomes, and causal relationships",
                }
            },
            "required": ["context_text"],
        },
    },
    {
        "name": "causal_leverage",
        "description": "Find leverage points (high out-degree nodes) in the causal graph built from context text",
        "inputSchema": {
            "type": "object",
            "properties": {
                "context_text": {
                    "type": "string",
                    "description": "Strategic context text describing metrics, actions, outcomes, and causal relationships",
                }
            },
            "required": ["context_text"],
        },
    },
    {
        "name": "causal_chain",
        "description": "Trace causal chains starting from a given node in the graph built from context text",
        "inputSchema": {
            "type": "object",
            "properties": {
                "context_text": {
                    "type": "string",
                    "description": "Strategic context text describing metrics, actions, outcomes, and causal relationships",
                },
                "start_node": {
                    "type": "string",
                    "description": "Name of the starting node to trace causal chains from",
                },
            },
            "required": ["context_text", "start_node"],
        },
    },
]


def _respond(id_val, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_val}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def _format_leverage(points):
    lines = []
    lines.append("## Leverage Points in Causal Graph")
    lines.append("")
    if not points:
        lines.append("No leverage points detected (requires nodes with 2+ outgoing edges).")
        return "\n".join(lines)
    lines.append("| Node | Out-Degree | In-Degree | Leverage Score |")
    lines.append("|------|-----------|-----------|----------------|")
    for lp in points:
        lines.append(f"| {lp['node']} | {lp['out_degree']} | {lp['in_degree']} | {lp['score']:.3f} |")
    lines.append("")
    lines.append("### Recommended Interventions")
    lines.append("")
    for lp in points[:3]:
        lines.append(f"- **{lp['node']}** (score: {lp['score']:.3f}) — high out-degree ({lp['out_degree']}), likely a high-impact lever")
    return "\n".join(lines)


def _format_chains(chains, start_node):
    lines = []
    lines.append(f"## Causal Chains from '{start_node}'")
    lines.append("")
    if not chains:
        lines.append(f"No chains found starting from '{start_node}'.")
        return "\n".join(lines)
    for chain in chains:
        lines.append(" → ".join(chain))
    lines.append("")
    lines.append(f"**Total chains:** {len(chains)}")
    return "\n".join(lines)


def _run_mcp():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = msg.get("method")
        req_id = msg.get("id")
        params = msg.get("params") or {}
        if method == "initialize":
            _respond(req_id, {
                "protocolVersion": "2026-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mcp-causal-graph", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _respond(req_id, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                modeler = CausalModeler()
                if tool_name == "causal_analyze":
                    text = modeler.generate_report(args["context_text"])
                    _respond(req_id, {"content": [{"type": "text", "text": text}]})
                elif tool_name == "causal_leverage":
                    modeler.build_from_context(args["context_text"])
                    points = modeler.find_leverage_points()
                    text = _format_leverage(points)
                    _respond(req_id, {"content": [{"type": "text", "text": text}]})
                elif tool_name == "causal_chain":
                    modeler.build_from_context(args["context_text"])
                    chains = modeler.trace_chains(args["start_node"])
                    text = _format_chains(chains, args["start_node"])
                    _respond(req_id, {"content": [{"type": "text", "text": text}]})
                else:
                    _respond(req_id, error={"code": -32601, "message": f"Tool not found: {tool_name}"})
            except Exception as e:
                _respond(req_id, error={"code": -32603, "message": str(e)})
        elif method == "prompts/list":
            _respond(req_id, {"prompts": []})
        else:
            _respond(req_id, error={"code": -32601, "message": f"Method not found: {method}"})


if __name__ == "__main__":
    _run_mcp()
