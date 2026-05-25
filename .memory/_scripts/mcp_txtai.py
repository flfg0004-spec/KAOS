#!/usr/bin/env python3
"""MCP server: semantic search & deduplication via real embeddings (fastembed).

Delegates embedding computation to mcp_embed.py (shared model singleton)
instead of using sklearn TF-IDF. Default similarity threshold: 0.85.
"""

import json
import subprocess
import sys
import numpy as np
from pathlib import Path
from typing import Any

KAOS = Path(__file__).resolve().parent.parent.parent
MCP_EMBED = KAOS / ".memory" / "_scripts" / "mcp_embed.py"

_embeddings_cache: dict[str, list[float]] = {}
_file_index: list[tuple[str, str]] = []


def _call_embed(texts: list[str]) -> list[list[float]]:
    """Get embeddings from mcp_embed service via subprocess."""
    uncached = [t for t in texts if t not in _embeddings_cache]
    if uncached:
        req = json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "embed", "arguments": {"texts": uncached}}
        })
        try:
            r = subprocess.run(
                [sys.executable, str(MCP_EMBED)],
                input=req, capture_output=True, text=True, timeout=30
            )
            if r.returncode == 0 and r.stdout.strip():
                resp = json.loads(r.stdout.strip())
                content = resp.get("result", {}).get("content", [])
                if content:
                    vecs = json.loads(content[0]["text"])
                    for t, v in zip(uncached, vecs):
                        _embeddings_cache[t] = v
        except Exception:
            return []
    return [_embeddings_cache[t] for t in texts if t in _embeddings_cache]


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
    global _file_index
    new = _load_files(path)
    if new != _file_index:
        _file_index = new


def _embed_matrix(texts: list[str]) -> np.ndarray:
    vecs = _call_embed(texts)
    if not vecs:
        return np.array([])
    return np.array(vecs)


def _semantic_search(query: str, path: str, top_k: int) -> list[dict]:
    _ensure_index(path)
    if not _file_index:
        return []

    q_vecs = _call_embed([query])
    if not q_vecs:
        return []

    texts = [c for _, c in _file_index]
    all_vecs = _embed_matrix(texts)
    if all_vecs.size == 0:
        return []

    q_vec = np.array(q_vecs[0])
    scores = np.dot(all_vecs, q_vec) / (np.linalg.norm(all_vecs, axis=1) * np.linalg.norm(q_vec) + 1e-10)
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

    texts = [c for _, c in _file_index]
    all_vecs = _embed_matrix(texts)
    if all_vecs.size == 0:
        return []

    norms = np.linalg.norm(all_vecs, axis=1, keepdims=True)
    sim = np.dot(all_vecs, all_vecs.T) / (norms * norms.T + 1e-10)

    dups = []
    for i in range(len(_file_index)):
        for j in range(i + 1, len(_file_index)):
            score = float(sim[i][j])
            if score >= threshold:
                dups.append({
                    "file_a": _file_index[i][0],
                    "file_b": _file_index[j][0],
                    "similarity": round(score, 4),
                })
    return sorted(dups, key=lambda x: -x["similarity"])


def _similarity_matrix(path: str) -> list[dict]:
    """Return full pairwise similarity matrix for all files (used by graph)."""
    _ensure_index(path)
    if len(_file_index) < 2:
        return []
    texts = [c for _, c in _file_index]
    all_vecs = _embed_matrix(texts)
    if all_vecs.size == 0:
        return []
    norms = np.linalg.norm(all_vecs, axis=1, keepdims=True)
    sim = np.dot(all_vecs, all_vecs.T) / (norms * norms.T + 1e-10)
    pairs = []
    for i in range(len(_file_index)):
        for j in range(i + 1, len(_file_index)):
            pairs.append({
                "file_a": _file_index[i][0],
                "file_b": _file_index[j][0],
                "similarity": round(float(sim[i][j]), 4),
            })
    return sorted(pairs, key=lambda x: -x["similarity"])


TOOLS = [
    {
        "name": "semantic_search",
        "description": "Search vault markdown files by semantic similarity (fastembed)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "path": {"type": "string", "description": "Directory to search", "default": ""},
                "top_k": {"type": "integer", "description": "Number of results", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "deduplicate",
        "description": "Find semantically similar/duplicate markdown files via embeddings",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory to scan", "default": ""},
                "threshold": {"type": "number", "description": "Similarity threshold 0-1", "default": 0.85},
            },
            "required": [],
        },
    },
    {
        "name": "similarity_matrix",
        "description": "Full pairwise similarity matrix for graph analysis",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory to scan", "default": ""},
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
                "serverInfo": {"name": "txtai-mcp", "version": "2.0.0"},
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
                elif tool_name == "similarity_matrix":
                    result = _similarity_matrix(args.get("path", ""))
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
