#!/usr/bin/env python3
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

KAOS_ROOT = Path(__file__).resolve().parents[2]
OPCODE_CONFIG = KAOS_ROOT / ".opencode" / "opencode.json"
HEALTH_DIR = KAOS_ROOT / ".memory" / "cache" / "health"

METIS_SERVERS = [
    "mcp-simulate",
    "mcp-causal-graph",
    "mcp-strategy-feedback",
    "mcp-pandas",
    "mcp-post-output-hook",
    "mcp-creative-spark",
    "mcp-roadmap-3h",
    "mcp-verification-chain",
    "mcp-session-runner",
]


def load_config():
    return json.loads(OPCODE_CONFIG.read_text(encoding="utf-8"))


def get_server_command(config, server_key):
    servers = config.get("mcp", {})
    entry = servers.get(server_key)
    if not entry:
        return None
    cmd = entry.get("command", [])
    if not cmd:
        return None
    resolved = []
    for part in cmd:
        if part.startswith("."):
            resolved.append(str((KAOS_ROOT / part).resolve()))
        else:
            resolved.append(part)
    return resolved


def test_server(server_key, command):
    result = {
        "server": server_key,
        "command": command,
        "initialize": {"status": "unknown", "error": None},
        "tools_list": {"status": "unknown", "tool_count": 0, "tools": [], "error": None},
    }
    try:
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(KAOS_ROOT),
        )
    except FileNotFoundError as e:
        result["initialize"] = {"status": "error", "error": f"FileNotFoundError: {e}"}
        result["tools_list"] = {"status": "error", "tool_count": 0, "tools": [], "error": str(e)}
        return result
    except Exception as e:
        result["initialize"] = {"status": "error", "error": str(e)}
        result["tools_list"] = {"status": "error", "tool_count": 0, "tools": [], "error": str(e)}
        return result

    init_msg = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2026-03-26",
            "capabilities": {},
            "clientInfo": {"name": "health-check", "version": "1.0.0"},
        },
    })
    try:
        proc.stdin.write(init_msg + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        if not line:
            result["initialize"]["status"] = "error"
            result["initialize"]["error"] = "No response from server"
        else:
            response = json.loads(line.strip())
            if "result" in response:
                caps = response["result"].get("capabilities", {})
                if "tools" in caps:
                    result["initialize"]["status"] = "ok"
                else:
                    result["initialize"]["status"] = "warning"
                    result["initialize"]["error"] = "capabilities.tools not found in response"
            else:
                result["initialize"]["status"] = "error"
                err = response.get("error", {})
                result["initialize"]["error"] = err.get("message", str(response))
    except Exception as e:
        result["initialize"]["status"] = "error"
        result["initialize"]["error"] = str(e)

    if result["initialize"]["status"] != "error":
        list_msg = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        try:
            proc.stdin.write(list_msg + "\n")
            proc.stdin.flush()
            line = proc.stdout.readline()
            if not line:
                result["tools_list"]["status"] = "error"
                result["tools_list"]["error"] = "No response from server"
            else:
                response = json.loads(line.strip())
                if "result" in response:
                    tools = response["result"].get("tools", [])
                    result["tools_list"]["status"] = "ok"
                    result["tools_list"]["tool_count"] = len(tools)
                    result["tools_list"]["tools"] = [t["name"] for t in tools]
                else:
                    result["tools_list"]["status"] = "error"
                    err = response.get("error", {})
                    result["tools_list"]["error"] = err.get("message", str(response))
        except Exception as e:
            result["tools_list"]["status"] = "error"
            result["tools_list"]["error"] = str(e)

    try:
        proc.stdin.close()
    except Exception:
        pass
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

    return result


def run_checks():
    config = load_config()
    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []
    summary = {"total": 0, "ok": 0, "warning": 0, "error": 0}
    for server_key in METIS_SERVERS:
        cmd = get_server_command(config, server_key)
        if cmd is None:
            results.append({
                "server": server_key,
                "command": None,
                "initialize": {"status": "error", "error": "Server not found in opencode.json"},
                "tools_list": {"status": "error", "tool_count": 0, "tools": [], "error": "Not found"},
            })
            summary["total"] += 1
            summary["error"] += 1
            continue
        r = test_server(server_key, cmd)
        results.append(r)
        summary["total"] += 1
        if r["initialize"]["status"] == "ok" and r["tools_list"]["status"] == "ok":
            summary["ok"] += 1
        elif r["initialize"]["status"] == "error" or r["tools_list"]["status"] == "error":
            summary["error"] += 1
        else:
            summary["warning"] += 1
    report = {
        "timestamp": timestamp,
        "summary": summary,
        "results": results,
    }
    report_path = HEALTH_DIR / f"health_{timestamp}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    latest_path = HEALTH_DIR / "latest.json"
    latest_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def generate_markdown(report):
    lines = []
    lines.append("# Health Check Report\n")
    lines.append(f"**Timestamp**: {report['timestamp']}\n")
    lines.append("## Summary\n")
    lines.append("| Status | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| OK | {report['summary']['ok']} |")
    lines.append(f"| Warning | {report['summary']['warning']} |")
    lines.append(f"| Error | {report['summary']['error']} |")
    lines.append(f"| **Total** | {report['summary']['total']} |")
    lines.append("")
    lines.append("## Server Details\n")
    for r in report["results"]:
        init_status = r["initialize"]["status"]
        tools_status = r["tools_list"]["status"]
        if init_status == "ok" and tools_status == "ok":
            status_icon = "OK"
        elif "error" in [init_status, tools_status]:
            status_icon = "FAIL"
        else:
            status_icon = "WARN"
        cmd_str = " ".join(r["command"]) if r["command"] else "NOT FOUND"
        lines.append(f"### {r['server']} [{status_icon}]\n")
        lines.append(f"- **Command**: `{cmd_str}`")
        lines.append(f"- **Initialize**: {init_status}")
        if r["initialize"].get("error"):
            lines.append(f"  - Error: {r['initialize']['error']}")
        lines.append(f"- **tools/list**: {tools_status}")
        if r["tools_list"].get("error"):
            lines.append(f"  - Error: {r['tools_list']['error']}")
        if r["tools_list"]["tool_count"] > 0:
            lines.append(f"- **Tools ({r['tools_list']['tool_count']})**:")
            for t in r["tools_list"]["tools"]:
                lines.append(f"  - `{t}`")
        lines.append("")
    fails = report["summary"]["error"]
    overall = "ALL PASS" if fails == 0 else f"{fails} FAILURE(S)"
    lines.append("---\n")
    lines.append(f"**Result**: {overall}\n")
    return "\n".join(lines)


def cmd_run():
    report = run_checks()
    md = generate_markdown(report)
    md_path = HEALTH_DIR / f"health_{report['timestamp']}.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"Health check complete. Report: {md_path}")
    print(f"Summary: {report['summary']['ok']} OK, {report['summary']['warning']} warning(s), {report['summary']['error']} error(s)")


def cmd_report():
    latest_json = HEALTH_DIR / "latest.json"
    if not latest_json.exists():
        print("No health check data found. Run 'py -3 .memory/_scripts/health_check.py run' first.", file=sys.stderr)
        sys.exit(1)
    report = json.loads(latest_json.read_text(encoding="utf-8"))
    md = generate_markdown(report)
    print(md)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Metis MCP Health Check")
        print()
        print("Usage:")
        print("  py -3 .memory/_scripts/health_check.py run     Run health checks on all Metis MCP servers")
        print("  py -3 .memory/_scripts/health_check.py report  Show latest health check report")
        print("  py -3 .memory/_scripts/health_check.py --help  Show this help")
        return
    cmd = sys.argv[1]
    if cmd == "run":
        cmd_run()
    elif cmd == "report":
        cmd_report()
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Use --help for usage information", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
