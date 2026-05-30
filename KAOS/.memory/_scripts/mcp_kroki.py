"""KAOS Kroki MCP — native diagram rendering with Docker fallback.

Tools:
  render_diagram(diagram_type, source, output_format) -> str (SVG/PNG)

Native rendering (no Docker):
  blockdiag, seqdiag, actdiag, nwdiag, packetdiag, rackdiag → pip install blockdiag
  Uses CLI tools via subprocess.

Fallback to Kroki Docker (http://localhost:8000):
  mermaid, plantuml, vega, vegalite, excalidraw, bpmn, structurizr, d2, graphviz, bytefield
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

KROKI_URL = os.environ.get("KROKI_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = int(os.environ.get("KROKI_TIMEOUT", "30"))

NATIVE_TYPES = frozenset(
    {
        "blockdiag",
        "seqdiag",
        "actdiag",
        "nwdiag",
        "packetdiag",
        "rackdiag",
    }
)

KROKI_TYPES = frozenset(
    {
        "mermaid",
        "plantuml",
        "graphviz",
        "structurizr",
        "d2",
        "vega",
        "vegalite",
        "excalidraw",
        "bpmn",
        "bytefield",
    }
)

SUPPORTED_TYPES = NATIVE_TYPES | KROKI_TYPES

mcp = FastMCP(
    name="kaos-kroki",
    instructions=(
        "Unified diagram rendering. "
        f"Natives: {', '.join(sorted(NATIVE_TYPES))} (no Docker). "
        f"Kroki: {', '.join(sorted(KROKI_TYPES))} (needs Docker)."
    ),
)


def _render_native(diagram_type: str, source: str, output_format: str) -> dict:
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".diag", delete=False) as f:
            f.write(source)
            tmpfile = f.name

        outfile = tempfile.mktemp(suffix=f".{output_format}")
        cmd = [diagram_type, "-T", output_format, "-o", outfile, tmpfile]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        Path(tmpfile).unlink(missing_ok=True)

        if result.returncode != 0:
            return {"success": False, "error": f"CLI error: {result.stderr[:500]}"}

        with open(outfile, "rb") as f:
            data = f.read()
        Path(outfile).unlink(missing_ok=True)

        if output_format == "svg":
            return {"success": True, "format": "svg", "content": data.decode("utf-8"), "diagram_type": diagram_type}
        else:
            return {
                "success": True,
                "format": "png",
                "content": base64.b64encode(data).decode("ascii"),
                "diagram_type": diagram_type,
            }

    except FileNotFoundError:
        return {"success": False, "error": f"CLI '{diagram_type}' not found. Run: pip install blockdiag"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Native {diagram_type} timed out after 30s"}
    except Exception as e:
        return {"success": False, "error": f"Native {diagram_type} error: {str(e)}"}


def _render_via_kroki(diagram_type: str, source: str, output_format: str) -> dict:
    url = f"{KROKI_URL}/{diagram_type}/{output_format}"
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.post(url, content=source.encode("utf-8"))
            resp.raise_for_status()
            content = resp.text if output_format == "svg" else resp.content.hex()
            return {"success": True, "format": output_format, "content": content, "diagram_type": diagram_type}
    except httpx.ConnectError:
        return {"success": False, "error": f"Cannot connect to Kroki server at {KROKI_URL}. Try: .\\kaos start kroki"}
    except httpx.TimeoutException:
        return {"success": False, "error": f"Kroki request timed out after {DEFAULT_TIMEOUT}s"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Kroki returned HTTP {e.response.status_code}: {e.response.text[:500]}"}
    except Exception as e:
        return {"success": False, "error": f"Kroki error: {str(e)}"}


@mcp.tool(
    name="render_diagram",
    description="Render a diagram. Natives (blockdiag, seqdiag, actdiag, nwdiag) work without Docker. "
    "Others (mermaid, plantuml, etc.) need Kroki server on :8000.",
)
def render_diagram(diagram_type: str, source: str, output_format: str = "svg") -> str:
    diagram_type = diagram_type.lower().strip()
    output_format = output_format.lower().strip()

    if diagram_type not in SUPPORTED_TYPES:
        return json.dumps(
            {
                "success": False,
                "error": f"Unsupported: {diagram_type}. Supported: {', '.join(sorted(SUPPORTED_TYPES))}",
            },
            ensure_ascii=False,
        )

    if output_format not in ("svg", "png"):
        output_format = "svg"

    if diagram_type in NATIVE_TYPES:
        result = _render_native(diagram_type, source, output_format)
    else:
        result = _render_via_kroki(diagram_type, source, output_format)

    return json.dumps(result, ensure_ascii=False)
