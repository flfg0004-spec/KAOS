"""Interfaz Pythonica para Obsidian Local REST API & MCP Server.

Obsidian MCP corre en http://127.0.0.1:27123/mcp/ (HTTP, sin certificado)
Requiere API key desde Settings -> Local REST API en Obsidian.

Uso:
    from lib.obsidian import ObsidianClient
    client = ObsidianClient(api_key="<key>")
    results = client.search("agent memory", top_k=5)
"""

import os
from typing import Optional

OBSIDIAN_URL = "http://127.0.0.1:27123"
API_KEY = os.environ.get("OBSIDIAN_API_KEY", "")


class ObsidianClient:
    """Helper para interactuar con Obsidian vía su REST API + MCP."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or API_KEY
        self._session = None

    def _get_session(self):
        import requests
        if not self._session:
            self._session = requests.Session()
            self._session.headers.update({"Authorization": f"Bearer {self.api_key}"})
            self._session.verify = False
        return self._session

    def _request(self, method: str, path: str, **kwargs):
        s = self._get_session()
        try:
            r = s.request(method, f"{OBSIDIAN_URL}{path}", timeout=10, **kwargs)
            return r.json() if r.ok and r.text else {}
        except Exception:
            return {}

    def search(self, query: str, top_k: int = 10) -> list:
        """Full-text search via Obsidian."""
        result = self._request("POST", f"/search/simple/", params={"query": query, "maxResults": top_k})
        return result if isinstance(result, list) else []

    def read(self, path: str) -> dict:
        """Read file: content, frontmatter, tags, stat."""
        return self._request("GET", f"/vault/{path.lstrip('/')}")

    def get_document_map(self, path: str) -> dict:
        """Get headings, blocks, frontmatter structure of a file."""
        return self._request("GET", f"/vault/{path.lstrip('/')}/document-map")

    def tags(self) -> list:
        """List all tags with usage counts."""
        result = self._request("GET", "/tags/")
        return result if isinstance(result, list) else []

    def write(self, path: str, content: str) -> bool:
        """Create or overwrite a file."""
        s = self._get_session()
        try:
            r = s.put(f"{OBSIDIAN_URL}/vault/{path.lstrip('/')}", data=content,
                      headers={"Content-Type": "text/markdown"}, timeout=10)
            return r.ok
        except Exception:
            return False

    def append(self, path: str, content: str) -> bool:
        """Append content to end of a file."""
        s = self._get_session()
        try:
            r = s.post(f"{OBSIDIAN_URL}/vault/{path.lstrip('/')}", data=content,
                       headers={"Content-Type": "text/markdown"}, timeout=10)
            return r.ok
        except Exception:
            return False

    def patch(self, path: str, target: str, target_type: str,
              operation: str, content: str) -> bool:
        """Patch specific heading, block, or frontmatter field."""
        s = self._get_session()
        try:
            r = s.patch(f"{OBSIDIAN_URL}/vault/{path.lstrip('/')}",
                        data=content,
                        headers={
                            "Target-Type": target_type,
                            "Target": target,
                            "Operation": operation,
                            "Content-Type": "text/plain",
                        }, timeout=10)
            return r.ok
        except Exception:
            return False

    def status(self) -> str:
        """Check if Obsidian MCP server is running."""
        s = self._get_session()
        try:
            r = s.get(f"{OBSIDIAN_URL}/", timeout=5)
            if r.ok:
                data = r.json()
                auth = data.get("authenticated", False)
                return f"Obsidian MCP: {'authenticated' if auth else 'running but not authenticated'}"
            return f"Obsidian MCP: HTTP {r.status_code}"
        except Exception as e:
            return f"Obsidian MCP: not available ({e})"
