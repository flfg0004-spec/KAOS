"""Interfaz Pythonica para Obsidian via CLI MCP (mcp-obsidian-cli).

Reemplaza la antigua integración REST API (plugin abandonado) por subprocess
contra el CLI oficial: npx mcp-obsidian-cli.

Uso:
    from lib.obsidian import ObsidianClient
    client = ObsidianClient()
    results = client.search("agent memory", top_k=5)

B5: sync_properties() — sincroniza frontmatter con formato Obsidian Properties.
"""

import json
import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("obsidian")

MCP_CLI_CMD = ["npx", "-y", "mcp-obsidian-cli"]

# Regex para extraer frontmatter YAML entre --- markers
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


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

    def __init__(self, vault: str | None = None):
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


def sync_properties(path: str | Path, merge: bool = True) -> dict:
    """Sincroniza frontmatter YAML con formato Obsidian Properties.

    Obsidian Properties requiere que el frontmatter YAML siga un formato
    específico. Esta función normaliza listas a sintaxis YAML inline [] y
    asegura formato consistente clave: valor.

    Args:
        path: Ruta al archivo .md
        merge: Si True, preserva campos existentes que no están en frontmatter

    Returns:
        dict con {path, status, fields_added, fields_removed, fields_unchanged}
    """
    path = Path(path)
    if not path.exists():
        return {
            "path": str(path),
            "status": "not_found",
            "fields_added": 0,
            "fields_removed": 0,
            "fields_unchanged": 0,
        }

    content = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {
            "path": str(path),
            "status": "no_frontmatter",
            "fields_added": 0,
            "fields_removed": 0,
            "fields_unchanged": 0,
        }

    fm_text = match.group(1)

    # Parse existing frontmatter lines
    lines = fm_text.split("\n")
    parsed = {}
    order = []
    for line in lines:
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        key = key.strip()
        val = val.strip()
        if key not in parsed:
            parsed[key] = val
            order.append(key)

    added = 0
    removed = 0
    unchanged = len(parsed)

    # Normalize each line for Obsidian Properties format
    new_lines = []
    for key in order:
        val = parsed[key]
        # Convert comma-separated strings to YAML inline list
        if "," in val and not val.startswith("[") and not val.endswith("]"):
            # Check it's not just a sentence with commas
            # Heuristic: if any value looks like a tag/keyword list, wrap it
            items = [v.strip() for v in val.split(",")]
            if all(len(v) < 60 and " " not in v.strip() for v in items):
                val = "[" + ", ".join(items) + "]"
                parsed[key] = val
        new_lines.append(f"{key}: {val}")

    new_fm = "\n".join(new_lines)

    if new_fm != fm_text:
        new_content = content.replace(fm_text, new_fm, 1)
        path.write_text(new_content, encoding="utf-8")
        return {
            "path": str(path),
            "status": "synced",
            "fields_added": added,
            "fields_removed": removed,
            "fields_unchanged": unchanged,
        }

    return {
        "path": str(path),
        "status": "unchanged",
        "fields_added": added,
        "fields_removed": removed,
        "fields_unchanged": unchanged,
    }
