#!/usr/bin/env python3
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".tools"))
from creative_spark import generate_options, evaluate_options

TOOLS = [
    {
        "name": "creative_generate",
        "description": "Generate divergent strategic options using lateral thinking templates (First Principles, Inversion, Analogy, What If, Devil's Advocate)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "problem": {
                    "type": "string",
                    "description": "Strategic problem description to generate options for",
                },
                "count": {
                    "type": "number",
                    "description": "Number of options to generate (default: 3, max: 5)",
                    "default": 3,
                },
            },
            "required": ["problem"],
        },
    },
    {
        "name": "creative_evaluate",
        "description": "Evaluate and score strategic options against impact, effort, risk, and vision alignment criteria",
        "inputSchema": {
            "type": "object",
            "properties": {
                "options_json": {
                    "type": "string",
                    "description": "JSON string with options array or object with options key, each option must have name/template and option_text fields",
                },
            },
            "required": ["options_json"],
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
                "serverInfo": {"name": "mcp-creative-spark", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _respond(req_id, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                if tool_name == "creative_generate":
                    problem = args["problem"]
                    count = int(args.get("count", 3))
                    options = generate_options(problem, count)
                    text = json.dumps(options, indent=2, ensure_ascii=False)
                    _respond(req_id, {"content": [{"type": "text", "text": text}]})
                elif tool_name == "creative_evaluate":
                    options_json = args["options_json"]
                    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
                        f.write(options_json)
                        tmp_path = f.name
                    try:
                        results = evaluate_options(tmp_path)
                    finally:
                        os.unlink(tmp_path)
                    text = json.dumps(results, indent=2, ensure_ascii=False)
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
