"""MCP server for verification_chain.py — verificación cruzada entre agentes."""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".tools"))
from verification_chain import run

TOOLS = [
    {"name": "run_verification", "description": "Ejecuta verification_chain con perfil y retorna reporte markdown", "inputSchema": {"type": "object", "properties": {"report_file": {"type": "string", "description": "Ruta al reporte markdown a verificar"}, "profile": {"type": "string", "description": "Perfil de evaluacion (exploracion, desarrollo, produccion, auditoria, qa)", "default": "desarrollo"}}, "required": ["report_file"]}},
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
            _respond(req_id, {"protocolVersion": "2026-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "mcp-verification-chain", "version": "1.0.0"}})
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _respond(req_id, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                if tool_name == "run_verification":
                    result = run(args.get("report_file", ""), args.get("profile", "desarrollo"))
                    if "error" in result:
                        _respond(req_id, error={"code": -32603, "message": result["error"]})
                    else:
                        _respond(req_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]})
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
