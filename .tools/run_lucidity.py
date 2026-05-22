#!/usr/bin/env python3
"""Wrapper to run lucidity-mcp MCP server from the cloned repo."""
import subprocess, sys, os
repo = os.path.join(os.path.dirname(__file__), "lucidity-mcp")
os.chdir(repo)
sys.exit(subprocess.call(["lucidity-mcp"] + sys.argv[1:]))
