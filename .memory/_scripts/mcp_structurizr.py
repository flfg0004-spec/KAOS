#!/usr/bin/env python3
"""MCP server: Structurizr CLI wrapper — validate DSL, export diagrams."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

KAOS = Path(__file__).resolve().parent.parent.parent
SD = KAOS / ".tools/structurizr"

# Java 17+ installed at Zulu JDK 17
JAVA17 = r"C:\Program Files\Zulu\zulu-17\bin\java.exe"
STRUCTURIZR_AVAILABLE = os.path.exists(JAVA17)
if STRUCTURIZR_AVAILABLE:
    STRUCTURIZR_CLI = [JAVA17, "-cp", f"{SD};{SD / 'lib/*'};", "com.structurizr.cli.StructurizrCliApplication"]
else:
    STRUCTURIZR_CLI = None


def _run_structurizr(args: list[str], input_str: str | None = None) -> dict:
    if STRUCTURIZR_CLI is None:
        return {"success": False, "stderr": "Java 17+ required for structurizr-cli. Install from https://adoptium.net/",
                "exit_code": -1}
    cmd = STRUCTURIZR_CLI + args
    try:
        result = subprocess.run(
            cmd,
            input=input_str,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(KAOS),
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Command timed out", "exit_code": -1}
    except FileNotFoundError:
        return {"success": False, "stdout": "", "stderr": "npx not found — is Node.js installed?", "exit_code": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}


def _validate_dsl(dsl_content: str) -> dict:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".dsl", delete=False, encoding="utf-8") as f:
        f.write(dsl_content)
        tmp = f.name
    try:
        result = _run_structurizr(["validate", "--workspace", tmp])
        return result
    finally:
        os.unlink(tmp)


def _export_diagram(dsl_content: str, fmt: str) -> dict:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".dsl", delete=False, encoding="utf-8") as f:
        f.write(dsl_content)
        tmp = f.name
    out_dir = Path(tempfile.mkdtemp())
    try:
        result = _run_structurizr(["export", "--workspace", tmp, "--format", fmt, "--output", str(out_dir)])
        if result["success"]:
            files = list(out_dir.iterdir())
            result["files"] = [str(f.relative_to(KAOS) if f.is_relative_to(KAOS) else f) for f in files]
            file_contents = {}
            for f in files:
                try:
                    file_contents[f.name] = f.read_text(encoding="utf-8", errors="replace")[:3000]
                except Exception:
                    pass
            result["contents"] = file_contents
        return result
    finally:
        os.unlink(tmp)
        for f in out_dir.iterdir():
            os.unlink(f)
        os.rmdir(out_dir)


def _list_views(dsl_content: str) -> dict:
    result = _validate_dsl(dsl_content)
    if result["success"]:
        # Parse DSL for view statements
        views = []
        for line in dsl_content.splitlines():
            line = line.strip()
            if any(line.lower().startswith(v) for v in
                   ("views.", "systemcontext", "containerview", "componentview",
                    "deploymentview", "dynamicview", "filteredview")):
                views.append(line)
        result["views"] = views if views else ["No explicit views found in DSL"]
    return result


# ── MCP stdio server ────────────────────────────────────────────────

TOOLS = [
    {
        "name": "validate_dsl",
        "description": "Validate Structurizr DSL syntax",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dsl_content": {"type": "string", "description": "Structurizr DSL content to validate"},
            },
            "required": ["dsl_content"],
        },
    },
    {
        "name": "export_diagram",
        "description": "Export Structurizr DSL to diagram format (plantuml, mermaid, json)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dsl_content": {"type": "string", "description": "Structurizr DSL content"},
                "format": {"type": "string", "description": "Export format: plantuml, mermaid, json", "default": "plantuml"},
            },
            "required": ["dsl_content"],
        },
    },
    {
        "name": "list_views",
        "description": "List all view definitions in a Structurizr DSL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dsl_content": {"type": "string", "description": "Structurizr DSL content"},
            },
            "required": ["dsl_content"],
        },
    },
]


def _respond(id_val: Any, result: Any = None, error: Any = None):
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
                "serverInfo": {"name": "structurizr-mcp", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _respond(req_id, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                if tool_name == "validate_dsl":
                    result = _validate_dsl(args.get("dsl_content", ""))
                    _respond(req_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})
                elif tool_name == "export_diagram":
                    result = _export_diagram(args.get("dsl_content", ""), args.get("format", "plantuml"))
                    _respond(req_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})
                elif tool_name == "list_views":
                    result = _list_views(args.get("dsl_content", ""))
                    _respond(req_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})
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
