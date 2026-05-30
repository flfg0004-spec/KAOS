#!/usr/bin/env python3
"""MCP server: persistent embedding service.

Loads fastembed ONCE and serves embeddings + semantic search via stdio MCP.
All other processes (vectorstore, txtai, hydrate) call this instead of
loading their own model instance.

Protocol: JSON-RPC 2.0 over stdio (standard MCP)
"""

import json
import sys
import struct
import numpy as np
from pathlib import Path

_model = None


def _get_model():
    global _model
    if _model is not None:
        return _model
    try:
        from fastembed import TextEmbedding
        _model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        return _model
    except ImportError:
        return None


def _embed(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    if not model:
        return []
    vecs = list(model.embed(texts))
    return [v.tolist() if hasattr(v, "tolist") else list(v) for v in vecs]


def _search_sqlite(query: str, top_k: int, db_path: str) -> list[dict]:
    """Search existing sqlite-vec vectors without reloading a model locally."""
    model = _get_model()
    if not model:
        return []
    import sqlite3, struct
    try:
        import sqlite_vec
    except ImportError:
        return [{"error": "sqlite-vec not installed"}]

    q_vec = list(model.embed([query]))[0]
    if hasattr(q_vec, "tolist"):
        q_vec = q_vec.tolist()
    q_bytes = struct.pack(f"{len(q_vec)}f", *q_vec)

    conn = sqlite3.connect(str(db_path))
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    rows = conn.execute(
        "SELECT c.path, c.chunk_text, v.distance "
        "FROM vault_vectors v JOIN vault_chunks c ON v.rowid = c.rowid "
        "WHERE v.embedding MATCH ? AND k = ? "
        "ORDER BY v.distance",
        [q_bytes, top_k]
    ).fetchall()
    conn.close()

    return [
        {"path": r[0], "snippet": r[1][:200], "score": round(1.0 / (1.0 + r[2]), 3)}
        for r in rows
    ]


TOOLS = [
    {
        "name": "embed",
        "description": "Convert text to embedding vector",
        "inputSchema": {
            "type": "object",
            "properties": {
                "texts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Texts to embed",
                },
            },
            "required": ["texts"],
        },
    },
    {
        "name": "search",
        "description": "Semantic search over sqlite-vec vault",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
                "db_path": {"type": "string",
                            "default": str(Path(__file__).resolve().parent.parent / "cache" / "vectors.db")},
            },
            "required": ["query"],
        },
    },
    {
        "name": "status",
        "description": "Embedding server status",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


def _respond(req_id, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": req_id}
    if error:
        msg["error"] = {"code": -32603, "message": str(error)}
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
                "serverInfo": {"name": "mcp-embed", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _respond(req_id, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                if tool_name == "embed":
                    result = _embed(args.get("texts", []))
                    _respond(req_id, {"content": [{"type": "text", "text": json.dumps(result)}]})
                elif tool_name == "search":
                    result = _search_sqlite(
                        args.get("query", ""),
                        int(args.get("top_k", 5)),
                        args.get("db_path", ""),
                    )
                    _respond(req_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})
                elif tool_name == "status":
                    model = _get_model()
                    _respond(req_id, {"content": [{"type": "text", "text": json.dumps({
                        "model": "BAAI/bge-small-en-v1.5" if model else "none",
                        "loaded": model is not None,
                        "dim": 384,
                    })}]})
                else:
                    _respond(req_id, error={"code": -32601, "message": f"Unknown tool: {tool_name}"})
            except Exception as e:
                _respond(req_id, error=str(e))
        elif method == "prompts/list":
            _respond(req_id, {"prompts": []})
        else:
            _respond(req_id, error={"code": -32601, "message": f"Unknown method: {method}"})


if __name__ == "__main__":
    main()
