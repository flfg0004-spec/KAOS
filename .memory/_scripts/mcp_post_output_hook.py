"""MCP server for post_output_hook.py — verification post-output automática."""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".tools"))
from post_output_hook import load_output, check_okrs, check_foda, check_roadmap, check_risks, run_bcg, generate_report

TOOLS = [
    {"name": "verify_output", "description": "Ejecuta verificacion post-output (OKR, FODA, Roadmap, Riesgos, BCG)", "inputSchema": {"type": "object", "properties": {"output_file": {"type": "string"}, "checklist": {"type": "string", "enum": ["quality", "strategy", "both"], "default": "both"}}, "required": ["output_file"]}},
    {"name": "verify_with_monitor", "description": "Verificacion post-output con monitoreo proactivo", "inputSchema": {"type": "object", "properties": {"output_file": {"type": "string"}}, "required": ["output_file"]}},
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
            _respond(req_id, {"protocolVersion": "2026-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "mcp-post-output-hook", "version": "1.0.0"}})
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _respond(req_id, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                if tool_name == "verify_output":
                    text = load_output(args.get("output_file", ""))
                    okr = check_okrs(text)
                    foda = check_foda(text)
                    rdm = check_roadmap(text)
                    rsk = check_risks(text)
                    bcg = run_bcg(text) if okr["count"] > 0 else None
                    report = generate_report(okr, foda, rdm, rsk, bcg, args.get("checklist", "both"), args.get("output_file", ""))
                    _respond(req_id, {"content": [{"type": "text", "text": report}]})
                elif tool_name == "verify_with_monitor":
                    text = load_output(args.get("output_file", ""))
                    okr = check_okrs(text)
                    foda = check_foda(text)
                    rdm = check_roadmap(text)
                    rsk = check_risks(text)
                    bcg = run_bcg(text) if okr["count"] > 0 else None
                    report = generate_report(okr, foda, rdm, rsk, bcg, "both", args.get("output_file", ""))
                    passed = okr["passed"] and foda["passed"] and rsk["passed"]
                    report += f"\n\n**Monitor Status**: {'✅ PASS' if passed else '❌ FAIL'}"
                    _respond(req_id, {"content": [{"type": "text", "text": report}]})
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
