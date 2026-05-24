#!/usr/bin/env python3
"""MCP server: semantic search & deduplication for vault content."""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KAOS = Path(__file__).resolve().parent.parent.parent  # KAOS root

_vectorizer = None
_matrix = None
_file_index: list[tuple[str, str]] = []  # (path, content)


def _mcp_embed_query(texts: list[str]) -> list[list[float]]:
    """Try to get embeddings from mcp_embed server via subprocess call."""
    try:
        import subprocess, json
        req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                          "params": {"name": "embed", "arguments": {"texts": texts}}})
        r = subprocess.run(
            ["py", "-3", str(KAOS / ".memory/_scripts/mcp_embed.py")],
            input=req, capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0 and r.stdout.strip():
            resp = json.loads(r.stdout.strip())
            content = resp.get("result", {}).get("content", [])
            if content:
                return json.loads(content[0]["text"])
    except Exception:
        pass
    return []


def _load_files(path: str) -> list[tuple[str, str]]:
    base = Path(path).resolve() if path else KAOS / ".memory" / "wiki"
    if not base.exists():
        return []
    files = []
    for f in sorted(base.rglob("*.md")):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
            if text.strip():
                files.append((str(f.relative_to(KAOS)), text[:5000]))
        except Exception:
            pass
    return files


def _ensure_index(path: str):
    global _file_index, _vectorizer, _matrix
    new = _load_files(path)
    if new != _file_index:
        _file_index = new
        if not new:
            _vectorizer = None
            _matrix = None
            return
        texts = [c for _, c in new]
        _vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
        _matrix = _vectorizer.fit_transform(texts)


def _semantic_search(query: str, path: str, top_k: int) -> list[dict]:
    _ensure_index(path)
    if not _file_index:
        return []

    query_vec = _vectorizer.transform([query]) if _vectorizer else None
    if query_vec is None or _matrix is None:
        return []

    scores = cosine_similarity(query_vec, _matrix).flatten()
    top_indices = scores.argsort()[-top_k:][::-1]
    results = []
    for idx in top_indices:
        if scores[idx] > 0.05:
            results.append({
                "file": _file_index[idx][0],
                "score": round(float(scores[idx]), 4),
                "preview": _file_index[idx][1][:200],
            })
    return results


def _deduplicate(path: str, threshold: float) -> list[dict]:
    _ensure_index(path)
    if len(_file_index) < 2:
        return []

    dups = []
    sim = cosine_similarity(_matrix)
    for i in range(len(_file_index)):
        for j in range(i + 1, len(_file_index)):
            score = sim[i][j]
            if score >= threshold:
                dups.append({
                    "file_a": _file_index[i][0],
                    "file_b": _file_index[j][0],
                    "similarity": round(float(score), 4),
                })
    return sorted(dups, key=lambda x: -x["similarity"])


# ── MCP stdio server ────────────────────────────────────────────────

TOOLS = [
    {
        "name": "semantic_search",
        "description": "Search vault markdown files by semantic similarity",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "path": {"type": "string", "description": "Directory to search (default: .memory/wiki)", "default": ""},
                "top_k": {"type": "integer", "description": "Number of results", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "deduplicate",
        "description": "Find semantically similar/duplicate markdown files",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory to scan (default: .memory/wiki)", "default": ""},
                "threshold": {"type": "number", "description": "Similarity threshold 0-1 (default: 0.85)", "default": 0.85},
            },
            "required": [],
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
                "serverInfo": {"name": "txtai-mcp", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _respond(req_id, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                if tool_name == "semantic_search":
                    result = _semantic_search(
                        args.get("query", ""),
                        args.get("path", ""),
                        int(args.get("top_k", 10)),
                    )
                    _respond(req_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})
                elif tool_name == "deduplicate":
                    result = _deduplicate(args.get("path", ""), float(args.get("threshold", 0.85)))
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
