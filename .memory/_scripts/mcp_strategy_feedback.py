import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".tools"))
from strategy_feedback import dispatch_strategy, poll_feedback, generate_report, list_initiatives


TOOLS = [
    {
        "name": "feedback_dispatch",
        "description": "Dispatch a strategic initiative from Metis to Kratos",
        "inputSchema": {
            "type": "object",
            "properties": {
                "okr_id": {"type": "string", "description": "OKR ID (e.g. O1-KR3)"},
                "initiative": {"type": "string", "description": "Initiative name"},
                "criteria_json": {"type": "string", "description": "Optional JSON string with success criteria", "default": "{}"},
            },
            "required": ["okr_id", "initiative"],
        },
    },
    {
        "name": "feedback_poll",
        "description": "Poll current feedback status for an initiative",
        "inputSchema": {
            "type": "object",
            "properties": {
                "okr_id": {"type": "string", "description": "OKR ID"},
            },
            "required": ["okr_id"],
        },
    },
    {
        "name": "feedback_report",
        "description": "Generate a markdown feedback report for an initiative",
        "inputSchema": {
            "type": "object",
            "properties": {
                "okr_id": {"type": "string", "description": "OKR ID"},
            },
            "required": ["okr_id"],
        },
    },
    {
        "name": "feedback_list",
        "description": "List all initiatives with their current status",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
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


def main():
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
                "serverInfo": {"name": "mcp-strategy-feedback", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            pass
        elif method == "ping":
            _respond(req_id, {})
        elif method == "tools/list":
            _respond(req_id, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                if tool_name == "feedback_dispatch":
                    okr_id = args.get("okr_id", "")
                    initiative = args.get("initiative", "")
                    criteria = {}
                    raw = args.get("criteria_json", "{}")
                    if raw and raw != "{}":
                        criteria = json.loads(raw)
                    with StringIO() as buf, redirect_stdout(buf):
                        dispatch_strategy(okr_id, initiative, criteria)
                    _respond(req_id, {"content": [{"type": "text", "text": f"Dispatched OKR {okr_id}"}]})

                elif tool_name == "feedback_poll":
                    okr_id = args.get("okr_id", "")
                    with StringIO() as buf, redirect_stdout(buf):
                        state = poll_feedback(okr_id)
                    if state:
                        _respond(req_id, {"content": [{"type": "text", "text": json.dumps(state, indent=2, ensure_ascii=False)}]})
                    else:
                        _respond(req_id, {"content": [{"type": "text", "text": f"No feedback yet for {okr_id}"}]})

                elif tool_name == "feedback_report":
                    okr_id = args.get("okr_id", "")
                    report = generate_report(okr_id)
                    _respond(req_id, {"content": [{"type": "text", "text": report}]})

                elif tool_name == "feedback_list":
                    items = list_initiatives()
                    if not items:
                        _respond(req_id, {"content": [{"type": "text", "text": "No initiatives found."}]})
                    else:
                        header = f"{'OKR ID':<15} {'Initiative':<35} {'Type':<12} {'Status':<18} {'Updated':<20}"
                        sep = "-" * 100
                        rows = [header, sep]
                        for item in items:
                            rows.append(f"{item['okr_id']:<15} {item['initiative'][:33]:<35} {item['type']:<12} {item['status']:<18} {item['updated']:<20}")
                        _respond(req_id, {"content": [{"type": "text", "text": "\n".join(rows)}]})

                else:
                    _respond(req_id, error={"code": -32601, "message": f"Tool not found: {tool_name}"})
            except Exception as e:
                _respond(req_id, error={"code": -32603, "message": str(e)})
        elif method == "prompts/list":
            _respond(req_id, {"prompts": []})
        else:
            _respond(req_id, error={"code": -32601, "message": f"Method not found: {method}"})


if __name__ == "__main__":
    main()
