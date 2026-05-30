#!/usr/bin/env python3
"""MCP server exposing the Hermes Tool Bridge as 3 MCP tools.

Tools:
  hermes_tool_search   — BM25 search over registered MCP tools
  hermes_tool_describe — full schema for a specific tool
  hermes_tool_call     — delegate execution to a real MCP tool

Usage:
  Direct:     py -3 .memory/_scripts/mcp_hermes_bridge.py
  Via proxy:  py -3 .memory/_scripts/mcp_proxy.py -- py -3 .memory/_scripts/mcp_hermes_bridge.py
"""
from __future__ import annotations

import json
import logging
import sys

from lib.bridge.hermes_bridge import HermesBridge

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)

bridge = HermesBridge()

MCP_TOOLS = {
    "hermes_tool_search": {
        "name": "hermes_tool_search",
        "description": "Search for MCP tools using BM25 retrieval. Returns matching tool IDs, names, descriptions and relevance scores. Core tools (terminal, read, write, glob, grep) always appear with max score.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query describing the tool needed"},
                "top_k": {"type": "number", "description": "Number of results (default 5)", "default": 5},
                "agent": {"type": "string", "description": "Optional agent name to scope search", "default": ""},
            },
            "required": ["query"],
        },
    },
    "hermes_tool_describe": {
        "name": "hermes_tool_describe",
        "description": "Get the full schema and metadata for a specific MCP tool by its ID. Returns parameters, input schema, and whether a real handler is registered.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool_id": {"type": "string", "description": "Tool ID to describe"},
            },
            "required": ["tool_id"],
        },
    },
    "hermes_tool_call": {
        "name": "hermes_tool_call",
        "description": "Execute a registered MCP tool with the given arguments. Delegates to the real tool handler. Returns the result or an error with the tool schema if not connected.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool_id": {"type": "string", "description": "Tool ID to execute"},
                "args": {"type": "object", "description": "Arguments to pass to the tool"},
            },
            "required": ["tool_id", "args"],
        },
    },
}


def handle_call(tool_name: str, arguments: dict) -> dict:
    if tool_name == "hermes_tool_search":
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        agent = arguments.get("agent", "")
        results = bridge.tool_search(query, top_k=top_k, agent=agent)
        return {"content": [{"type": "text", "text": json.dumps(results, indent=2, default=str)}]}

    elif tool_name == "hermes_tool_describe":
        tool_id = arguments.get("tool_id", "")
        schema = bridge.tool_describe(tool_id)
        return {"content": [{"type": "text", "text": json.dumps(schema, indent=2, default=str)}]}

    elif tool_name == "hermes_tool_call":
        tool_id = arguments.get("tool_id", "")
        args = arguments.get("args", {})
        result = bridge.tool_call(tool_id, args)
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]}

    else:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
        }


def main():
    """MCP stdio transport loop."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_id = msg.get("id")
        method = msg.get("method")

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                    },
                    "serverInfo": {
                        "name": "hermes-bridge",
                        "version": "0.1.0",
                    },
                },
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": list(MCP_TOOLS.values()),
                },
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        elif method == "tools/call":
            params = msg.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})

            result = handle_call(tool_name, arguments)
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result,
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
