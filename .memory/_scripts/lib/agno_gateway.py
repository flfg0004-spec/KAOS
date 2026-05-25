"""KAOS MCP Gateway — expone tools de KAOS como MCP server.

Usa el SDK oficial MCP (mcp v1.26.0) para exponer herramientas de KAOS
como servidor MCP bidireccional. Reemplaza la dependencia de Agno AgentOS
cuya API cambio en v2.6.9.

Decision ADR-012 (P4):
  MCP bidireccional para que DeerFlow (y otros MCP clients) consuman KAOS.
  Cuando PR #1845 se mergee, DeerFlow expondra MCP nativo.

Herramientas expuestas:
  - kaos_research: invoca Aletheia
  - kaos_analyze: invoca Kosmos
  - kaos_strategize: invoca Metis
  - vault_read: lee contenido del vault
  - vault_search: busca en el vault
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("kaos_mcp_gateway")

GATEWAY_LOG = Path(__file__).resolve().parent.parent.parent / "bridge" / "context" / "kaos-mcp-gateway.json"
MCP_AVAILABLE = False


def _check_mcp() -> bool:
    global MCP_AVAILABLE
    if MCP_AVAILABLE:
        return True
    try:
        import mcp.server.fastmcp
        MCP_AVAILABLE = True
        logger.info("MCP SDK detected — Gateway real mode")
        return True
    except ImportError:
        logger.warning("MCP SDK not installed — pip install mcp")
        return False


class KaosMCPGateway:
    """MCP server que expone tools de KAOS."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8010):
        self.host = host
        self.port = port
        self.server = None
        self._tools = {}
        self._real_mode = _check_mcp()

    def register_tool(self, name: str, fn, description: str = ""):
        self._tools[name] = {"fn": fn, "description": description}

    def start(self):
        if not self._real_mode:
            logger.info(f"[MOCK] KaosMCPGateway would start on {self.host}:{self.port}")
            self._log_status({"status": "mock", "tools": list(self._tools.keys())})
            return

        from mcp.server.fastmcp import FastMCP

        server = FastMCP("kaos-gateway")

        for name, tool in self._tools.items():
            fn = tool["fn"]
            description = tool["description"]
            # Registra la funcion como tool MCP
            wrapped = lambda *args, fn=fn, **kwargs: str(fn(*args, **kwargs))
            wrapped.__name__ = name
            wrapped.__doc__ = description
            server.add_tool(wrapped)

        self.server = server
        self._log_status({"status": "running", "endpoint": f"http://{self.host}:{self.port}/mcp"})
        logger.info(f"KAOS MCP Gateway starting on {self.host}:{self.port}")
        server.run(host=self.host, port=self.port)

    def stop(self):
        self.server = None
        logger.info("KAOS MCP Gateway stopped")

    def _log_status(self, data: dict):
        GATEWAY_LOG.parent.mkdir(parents=True, exist_ok=True)
        data["timestamp"] = datetime.now().isoformat()
        GATEWAY_LOG.write_text(json.dumps(data, indent=2))

    def status(self) -> dict:
        return {
            "available": MCP_AVAILABLE,
            "real_mode": self._real_mode,
            "tools_registered": list(self._tools.keys()),
            "server_running": self.server is not None,
        }


# ── KAOS Tools ──────────────────────────────────────────────

def _kaos_research(topic: str, depth: str = "standard") -> str:
    """Investiga un tema usando el agente Aletheia."""
    try:
        from lib.pipeline import init as pipeline_init
        result = pipeline_init(topic=topic, profile=depth)
        return result
    except Exception as e:
        return f"Error invoking research: {e}"


def _kaos_analyze(codebase_path: str = "") -> str:
    """Analiza la arquitectura del codebase usando Kosmos."""
    try:
        from lib.lint import run as lint_run
        result = lint_run()
        return f"Lint analysis: {result}"
    except Exception as e:
        return f"Error invoking analysis: {e}"


def _kaos_strategize(objective: str, context: str = "") -> str:
    """Analisis estrategico usando Metis."""
    return f"[MOCK] Strategy analysis for: {objective}"


def _vault_read(path: str) -> str:
    """Lee contenido del vault de memoria."""
    vault_root = Path(__file__).resolve().parent.parent.parent
    target = vault_root / path
    if target.exists() and target.is_file():
        return target.read_text(encoding="utf-8", errors="replace")[:5000]
    return f"File not found: {path}"


def _vault_search(query: str, max_results: int = 5) -> str:
    """Busca en el vault de memoria."""
    try:
        vault_root = Path(__file__).resolve().parent.parent.parent
        matches = list(vault_root.rglob(f"*{query}*.md")) + list(vault_root.rglob(f"**/*{query}*"))
        seen = set()
        results = []
        for m in matches:
            rel = str(m.relative_to(vault_root.parent))
            if rel not in seen and len(results) < max_results:
                seen.add(rel)
                results.append({"path": rel, "name": m.stem})
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "query": query})


def create_gateway(host: str = "127.0.0.1", port: int = 8010) -> KaosMCPGateway:
    gateway = KaosMCPGateway(host=host, port=port)

    gateway.register_tool(
        "kaos_research", _kaos_research,
        "Investiga un tema usando el agente Aletheia de KAOS"
    )
    gateway.register_tool(
        "kaos_analyze", _kaos_analyze,
        "Analiza la arquitectura del codebase usando Kosmos"
    )
    gateway.register_tool(
        "kaos_strategize", _kaos_strategize,
        "Analisis estrategico usando Metis"
    )
    gateway.register_tool(
        "vault_read", _vault_read,
        "Lee contenido del vault de memoria de KAOS"
    )
    gateway.register_tool(
        "vault_search", _vault_search,
        "Busca en el vault de memoria de KAOS"
    )

    return gateway


gateway = create_gateway()
