"""KAOS Markmap MCP — interactive mindmaps from markdown.

Tools:
  render_mindmap(markdown_text, output_path) -> str (path to generated HTML)

Requires: Node.js/npx (markmap CLI)
Graceful fallback when npx markmap is unavailable.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "mindmaps"
MARKMAP_TIMEOUT = int(os.environ.get("MARKMAP_TIMEOUT", "30"))

mcp = FastMCP(
    name="kaos-markmap",
    instructions=(
        "Interactive mindmap generator from markdown. "
        "Use render_mindmap to convert hierarchical markdown into "
        "an HTML mindmap with zoom, pan, and collapsible branches. "
        "Output saved to .memory/dashboard/mindmaps/"
    ),
)


@mcp.tool(
    name="render_mindmap",
    description=(
        "Convert markdown headings into an interactive HTML mindmap. "
        "Heading level determines tree depth (# → root, ## → child, etc.). "
        "Returns the absolute path to the generated HTML file."
    ),
)
def render_mindmap(markdown_text: str, output_path: str | None = None) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not markdown_text or not markdown_text.strip():
        return json.dumps(
            {
                "success": False,
                "error": "Markdown text is empty",
            },
            ensure_ascii=False,
        )

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(OUTPUT_DIR / f"mindmap_{timestamp}.html")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(markdown_text)
            md_path = f.name

        result = subprocess.run(
            ["npx", "markmap", md_path, "--output", str(output)],
            capture_output=True,
            text=True,
            timeout=MARKMAP_TIMEOUT,
        )

        os.unlink(md_path)

        if result.returncode != 0:
            return json.dumps(
                {
                    "success": False,
                    "error": f"markmap CLI failed: {result.stderr.strip()[:500]}",
                },
                ensure_ascii=False,
            )

        if not output.exists():
            return json.dumps(
                {
                    "success": False,
                    "error": "markmap did not produce output file",
                },
                ensure_ascii=False,
            )

        return json.dumps(
            {
                "success": True,
                "path": str(output.resolve()),
                "size_bytes": output.stat().st_size,
            },
            ensure_ascii=False,
        )

    except FileNotFoundError:
        return json.dumps(
            {
                "success": False,
                "error": "npx not found — is Node.js installed? Install from https://nodejs.org/",
            },
            ensure_ascii=False,
        )
    except subprocess.TimeoutExpired:
        return json.dumps(
            {
                "success": False,
                "error": f"markmap timed out after {MARKMAP_TIMEOUT}s",
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            },
            ensure_ascii=False,
        )
