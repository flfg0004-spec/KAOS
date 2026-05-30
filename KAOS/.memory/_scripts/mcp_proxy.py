#!/usr/bin/env python3
"""MCP stdio proxy — intercepts prompts/list for servers that don't implement it.

Usage:
  mcp_proxy.py -- <mcp-server-command> [args...]

Example:
  mcp_proxy.py -- npx -y excalidraw-mcp
"""

import json
import subprocess
import sys
import threading


def main():
    try:
        idx = sys.argv.index("--")
    except ValueError:
        print("Usage: mcp_proxy.py -- <command...>", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[idx + 1:]
    if not cmd:
        print("Error: no command specified after --", file=sys.stderr)
        sys.exit(1)

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        bufsize=1,
    )

    def forward_from_server():
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()

    threading.Thread(target=forward_from_server, daemon=True).start()

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

        if method in ("prompts/list",):
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"prompts": []},
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        elif method in ("prompts/get",):
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": "Method not found"},
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        else:
            proc.stdin.write(line + "\n")
            proc.stdin.flush()

    proc.stdin.close()
    proc.wait()


if __name__ == "__main__":
    main()
