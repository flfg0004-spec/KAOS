"""MCP server for session_runner.py — smoke, functional, audit profiles."""
import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".tools"))
from session_runner import cmd_smoke, cmd_functional, cmd_audit

TOOLS = [
    {"name": "session_smoke", "description": "Ejecuta smoke test (2 min — quick post-output check)", "inputSchema": {"type": "object", "properties": {"profile": {"type": "string", "description": "Perfil de evaluacion", "default": "desarrollo"}}, "required": []}},
    {"name": "session_functional", "description": "Ejecuta functional test (15 min — full verification + scoring + session save)", "inputSchema": {"type": "object", "properties": {"profile": {"type": "string", "description": "Perfil de evaluacion", "default": "desarrollo"}}, "required": []}},
    {"name": "session_audit", "description": "Ejecuta audit test (60 min — full evaluation + weekly report)", "inputSchema": {"type": "object", "properties": {"profile": {"type": "string", "description": "Perfil de evaluacion", "default": "desarrollo"}}, "required": []}},
]


def _respond(id_val, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_val}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def _capture_call(fn, profile):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = fn(profile)
    output = buf.getvalue()
    return {"output": output, "result": str(result)}


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
            _respond(req_id, {"protocolVersion": "2026-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "mcp-session-runner", "version": "1.0.0"}})
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _respond(req_id, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                profile = args.get("profile", "desarrollo")
                if tool_name == "session_smoke":
                    data = _capture_call(cmd_smoke, profile)
                    _respond(req_id, {"content": [{"type": "text", "text": data["output"] + f"\nResult: {data['result']}"}]})
                elif tool_name == "session_functional":
                    data = _capture_call(cmd_functional, profile)
                    _respond(req_id, {"content": [{"type": "text", "text": data["output"] + f"\nResult: {data['result']}"}]})
                elif tool_name == "session_audit":
                    data = _capture_call(cmd_audit, profile)
                    _respond(req_id, {"content": [{"type": "text", "text": data["output"] + f"\nResult: {data['result']}"}]})
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
