import importlib
import sys

print(f"Python: {sys.version}")

for mod_name in ["agno", "mcp", "lancedb", "anthropic", "openai"]:
    try:
        mod = importlib.import_module(mod_name)
        ver = getattr(mod, "__version__", "unknown")
        print(f"{mod_name}: {ver}")
    except ImportError:
        print(f"{mod_name}: NOT FOUND")
    except Exception as e:
        print(f"{mod_name}: ERROR: {e}")

try:
    import sqlite3

    print(f"sqlite3: {sqlite3.sqlite_version}")
except:
    print("sqlite3: ERROR")

try:
    from mcp.server.fastmcp import FastMCP

    print("fastmcp: available")
except ImportError:
    print("fastmcp: NOT FOUND")
