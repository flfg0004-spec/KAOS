"""MCP Server for CodeExperience Memory — exposes CE tools over stdio MCP.

Tools:
  - ce_search: Search experiences by query, language, code snippet
  - ce_store: Store a new error/solution experience
  - ce_status: Get memory health status
  - ce_feedback: Provide success/failure feedback on an experience
  - ce_skill_search: Search AST-derived skills

Other agents (Aletheia, Kosmos, Metis) can call these tools via MCP.
Protocol: JSON-RPC 2.0 over stdio (standard MCP transport).
"""

import json
import sqlite3
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS.parent))

from lib.code_memory import DB
from lib.code_memory import feedback as ce_feedback
from lib.code_memory import search as ce_search
from lib.code_memory import status as ce_status

SKILL_DB = DB.parent / "code_skills.db"


def _handle_ce_search(params: dict) -> dict:
    """ce_search(query, top_k=5, language="", code_snippet="")"""
    query = params.get("query", "")
    top_k = params.get("top_k", 5)
    language = params.get("language", "")
    code_snippet = params.get("code_snippet", "")
    
    if not query:
        return {"error": "query is required"}
    
    results = ce_search(query=query, top_k=top_k, language=language, code_snippet=code_snippet)
    return {"results": results, "count": len(results)}


def _handle_ce_store(params: dict) -> dict:
    """ce_store(error_message, language, stack_trace="", solution_diff="", code_snippet="")"""
    error_message = params.get("error_message", "")
    language = params.get("language", "unknown")
    stack_trace = params.get("stack_trace", "")
    solution_diff = params.get("solution_diff", "")
    explanation = params.get("explanation", "")
    code_snippet = params.get("code_snippet", "")
    
    if not error_message:
        return {"error": "error_message is required"}
    
    from lib.code_memory import store
    result = store(
        error_message=error_message[:500],
        language=language,
        stack_trace=stack_trace[:2000],
        solution_diff=solution_diff[:2000],
        explanation=explanation[:1000],
        code_snippet=code_snippet[:500],
    )
    return result


def _handle_ce_status(params: dict) -> dict:
    """ce_status() — no params required"""
    return ce_status()


def _handle_ce_feedback(params: dict) -> dict:
    """ce_feedback(hash, success=True)"""
    error_hash = params.get("hash", "")
    success = params.get("success", True)
    
    if not error_hash:
        return {"error": "hash is required"}
    
    result = ce_feedback(error_hash, success=success)
    return result


def _handle_ce_skill_search(params: dict) -> dict:
    """ce_skill_search(query, language="", top_k=5)"""
    query = params.get("query", "")
    language = params.get("language", "")
    top_k = min(params.get("top_k", 5), 20)
    
    if not query:
        return {"error": "query is required"}
    
    try:
        conn = sqlite3.connect(str(SKILL_DB))
        rows = conn.execute("""
            SELECT id, name, description, language, ast_pattern, 
                   source_experiences, confidence, usage_count
            FROM code_skills
            WHERE (name LIKE ? OR description LIKE ? OR ast_pattern LIKE ?)
            AND (? = '' OR language = ?)
            AND confidence >= 0.6
            ORDER BY confidence DESC, usage_count DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", language, language, top_k)).fetchall()
        conn.close()
        
        skills = []
        for r in rows:
            skills.append({
                "id": r[0], "name": r[1], "description": r[2][:200],
                "language": r[3], "ast_pattern": r[4][:100],
                "source_experiences": r[5], "confidence": r[6],
                "usage_count": r[7],
            })
        return {"skills": skills, "count": len(skills)}
    except Exception as e:
        return {"skills": [], "error": str(e)}


TOOL_HANDLERS = {
    "ce_search": _handle_ce_search,
    "ce_store": _handle_ce_store,
    "ce_status": _handle_ce_status,
    "ce_feedback": _handle_ce_feedback,
    "ce_skill_search": _handle_ce_skill_search,
}


def process_request(request: dict) -> dict:
    """Process a single MCP JSON-RPC request."""
    req_id = request.get("id", 0)
    method = request.get("method", "")
    params = request.get("params", {})
    
    if method == "list_tools":
        return {
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "ce_search",
                        "description": "Search CodeExperience for similar errors and solutions",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search query (error message, keyword)"},
                                "top_k": {"type": "number", "default": 5},
                                "language": {"type": "string", "default": ""},
                                "code_snippet": {"type": "string", "default": ""},
                            },
                            "required": ["query"],
                        },
                    },
                    {
                        "name": "ce_store",
                        "description": "Store a new error/solution experience in CodeExperience",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "error_message": {"type": "string"},
                                "language": {"type": "string", "default": "unknown"},
                                "stack_trace": {"type": "string", "default": ""},
                                "solution_diff": {"type": "string", "default": ""},
                                "explanation": {"type": "string", "default": ""},
                                "code_snippet": {"type": "string", "default": ""},
                            },
                            "required": ["error_message"],
                        },
                    },
                    {
                        "name": "ce_status",
                        "description": "Get CodeExperience memory health status",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                    {
                        "name": "ce_feedback",
                        "description": "Provide success/failure feedback on an experience",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "hash": {"type": "string"},
                                "success": {"type": "boolean", "default": True},
                            },
                            "required": ["hash"],
                        },
                    },
                    {
                        "name": "ce_skill_search",
                        "description": "Search AST-derived coding skills in the skill library",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "language": {"type": "string", "default": ""},
                                "top_k": {"type": "number", "default": 5},
                            },
                            "required": ["query"],
                        },
                    },
                ]
            },
        }
    
    if method not in TOOL_HANDLERS:
        return {"id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    
    try:
        result = TOOL_HANDLERS[method](params)
        return {"id": req_id, "result": result}
    except Exception as e:
        return {"id": req_id, "error": {"code": -32603, "message": str(e)}}


def serve_stdio():
    """Run MCP server over stdio (standard MCP transport)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            response = {"id": 0, "error": {"code": -32700, "message": f"Parse error: {e}"}}
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue
        
        response = process_request(request)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    serve_stdio()
