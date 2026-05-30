#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".tools"))
from roadmap_3h import classify_horizon, compute_rice, find_critical_path, generate_markdown

TOOLS = [
    {
        "name": "roadmap_generate",
        "description": "Generate a complete 3-horizon strategic roadmap with RICE scoring, horizon classification (H1/H2/H3), dependency analysis, and critical path identification",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vision": {
                    "type": "string",
                    "description": "Strategic vision description for the roadmap",
                },
                "initiatives_json": {
                    "type": "string",
                    "description": "JSON string with array of initiative objects. Each requires: name, description, effort_days, dependencies (list), rice_reach (1-10), rice_impact (1-5), rice_confidence (0.0-1.0), category",
                },
            },
            "required": ["vision", "initiatives_json"],
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
                "serverInfo": {"name": "mcp-roadmap-3h", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _respond(req_id, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                if tool_name == "roadmap_generate":
                    vision = args["vision"]
                    initiatives = json.loads(args["initiatives_json"])
                    if isinstance(initiatives, dict) and "initiatives" in initiatives:
                        initiatives = initiatives["initiatives"]
                    horizons, assigned = classify_horizon(initiatives)
                    rice_scores = {}
                    for ini in initiatives:
                        rice_scores[ini["name"]] = compute_rice(ini)
                    critical_path = find_critical_path(initiatives)
                    markdown = generate_markdown(
                        initiatives, vision, horizons, assigned, rice_scores, critical_path,
                        dashboard_mode=False,
                    )
                    _respond(req_id, {"content": [{"type": "text", "text": markdown}]})
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
