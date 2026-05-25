"""Interfaz Pythonica para Obsidian via CLI MCP (mcp-obsidian-cli).

Reemplaza la antigua integración REST API (plugin abandonado) por subprocess
contra el CLI oficial: npx mcp-obsidian-cli.

Uso:
    from lib.obsidian import ObsidianClient
    client = ObsidianClient()
    results = client.search("agent memory", top_k=5)
"""

import json
import subprocess
import sys
from typing import Optional

MCP_CLI_CMD = ["npx", "-y", "mcp-obsidian-cli"]


def _mcp_call(tool_name: str, arguments: dict = None, timeout: int = 15) -> dict:
    """Call a tool on mcp-obsidian-cli via JSON-RPC over stdio."""
    req = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {},
        },
    })
    try:
        r = subprocess.run(
            MCP_CLI_CMD,
            input=req,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if r.returncode == 0 and r.stdout.strip():
            resp = json.loads(r.stdout.strip())
            content = resp.get("result", {}).get("content", [])
            if content:
                text = content[0].get("text", "")
                if text:
                    try:
                        return json.loads(text)
                    except (json.JSONDecodeError, TypeError):
                        return {"text": text}
    except Exception:
        pass
    return {}


class ObsidianClient:
    """Helper para interactuar con Obsidian via CLI MCP."""

    def __init__(self, vault: Optional[str] = None):
        self.vault = vault

    def search(self, query: str, top_k: int = 10) -> list:
        """Full-text search via Obsidian CLI."""
        args = {"query": query, "limit": top_k}
        if self.vault:
            args["vault"] = self.vault
        result = _mcp_call("search", args)
        return result if isinstance(result, list) else []

    def read(self, path: str) -> dict:
        """Read file: content, frontmatter, tags, stat."""
        return _mcp_call("read", {"path": path})

    def tags(self) -> list:
        """List all tags with usage counts."""
        result = _mcp_call("tags")
        return result if isinstance(result, list) else []

    def write(self, path: str, content: str) -> bool:
        """Create or overwrite a file."""
        result = _mcp_call("write", {"path": path, "content": content})
        return bool(result)

    def append(self, path: str, content: str) -> bool:
        """Append content to end of a file."""
        result = _mcp_call("append", {"path": path, "content": content})
        return bool(result)

    def get_backlinks(self, path: str) -> list:
        """Get all backlinks to a file."""
        result = _mcp_call("get_backlinks", {"path": path})
        return result if isinstance(result, list) else []

    def find_orphan_notes(self) -> list:
        """Find notes with no incoming links."""
        result = _mcp_call("find_orphan_notes")
        return result if isinstance(result, list) else []

    def find_unresolved_links(self) -> list:
        """Find broken [[wikilinks]] with no target file."""
        result = _mcp_call("find_unresolved_links")
        return result if isinstance(result, list) else []

    def suggest_links(self, path: str, top_k: int = 5) -> list:
        """Suggest related files for linking."""
        result = _mcp_call("suggest_links", {"path": path, "limit": top_k})
        return result if isinstance(result, list) else []

    def status(self) -> str:
        """Check if Obsidian CLI MCP is operational."""
        try:
            r = subprocess.run(
                MCP_CLI_CMD + ["--version"],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode == 0:
                version = r.stdout.strip() or r.stderr.strip()
                return f"Obsidian CLI MCP: {version or 'available'}"
            return f"Obsidian CLI MCP: error ({r.stderr.strip()})"
        except Exception as e:
            return f"Obsidian CLI MCP: not available ({e})"
