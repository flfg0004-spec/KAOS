"""Agno MCP Gateway — expone tools de KAOS como MCP server via Agno AgentOS.

Decision ADR-012 (P4):
  PR #1845 de DeerFlow (MCP Server) no esta mergeado. Agno AgentOS con
  enable_mcp_server=True es la unica forma de exponer KAOS como MCP server hoy.
  Cuando PR #1845 se mergee, podemos migrar a DeerFlow nativo.

Herramientas expuestas:
  - kaos_research: invoca Aletheia para investigacion web
  - kaos_analyze: invoca Kosmos para analisis arquitectonico
  - kaos_strategize: invoca Metis para analisis estrategico
  - vault_read: lee contenido del vault de memoria
  - vault_search: busca en el vault de memoria

Auto-deteccion: si agno no esta instalado, opera en modo 'mock'.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("agno_gateway")

GATEWAY_LOG = Path(__file__).resolve().parent.parent.parent / "bridge" / "context" / "agno-gateway.json"

AGNO_AVAILABLE = False
MOCK_MODE = False


def _check_agno() -> bool:
    global AGNO_AVAILABLE, MOCK_MODE
    if AGNO_AVAILABLE:
        return True
    try:
        from agno.os.agentos import AgentOS
        AGNO_AVAILABLE = True
        MOCK_MODE = False
        logger.info("Agno AgentOS detected — MCP Gateway active")
        return True
    except ImportError:
        MOCK_MODE = True
        logger.warning("Agno not installed — MCP Gateway in MOCK mode")
        return False


class AgnoGateway:
    def __init__(self, host: str = "0.0.0.0", port: int = 8010):
        self.host = host
        self.port = port
        self.server = None
        self.tools = {}
        _check_agno()

    def register_tool(self, name: str, fn, description: str = ""):
        self.tools[name] = {"fn": fn, "description": description}

    def start(self):
        if MOCK_MODE:
            logger.info(f"[MOCK] Agno MCP Gateway would start on {self.host}:{self.port}")
            self._log_status({"status": "mock", "tools": list(self.tools.keys())})
            return

        from agno.os.agentos import AgentOS
        from agno.agent import Agent

        class KAOSAgent(Agent):
            name = "kaos-gateway"
            description = "KAOS Memory & Quality System MCP Gateway"

        kaos_agent = KAOSAgent(
            tools=list(self.tools.values()),
            enable_mcp_server=True,
        )

        agent_os = AgentOS(
            agents=[kaos_agent],
            enable_mcp_server=True,
        )
        agent_os.run(host=self.host, port=self.port)
        self.server = agent_os
        self._log_status({"status": "running", "tools": list(self.tools.keys())})

    def stop(self):
        if self.server:
            self.server.stop()
            logger.info("Agno MCP Gateway stopped")

    def _log_status(self, data: dict):
        GATEWAY_LOG.parent.mkdir(parents=True, exist_ok=True)
        data["timestamp"] = datetime.now().isoformat()
        GATEWAY_LOG.write_text(json.dumps(data, indent=2))

    def status(self) -> dict:
        return {
            "available": AGNO_AVAILABLE,
            "mock_mode": MOCK_MODE,
            "tools_registered": list(self.tools.keys()),
            "server_running": self.server is not None,
        }


# Tools de KAOS que se exponen via MCP

def _kaos_research(topic: str, depth: str = "standard") -> str:
    """Invoca Aletheia para investigar un topic."""
    try:
        from lib.pipeline import init as pipeline_init
        result = pipeline_init(topic=topic, profile=depth)
        return result
    except Exception as e:
        return f"Error invoking research: {e}"


def _kaos_analyze(codebase_path: str = "") -> str:
    """Invoca Kosmos para analisis arquitectonico."""
    try:
        from lib.lint import run as lint_run
        result = lint_run()
        return f"Lint analysis: {result}"
    except Exception as e:
        return f"Error invoking analysis: {e}"


def _kaos_strategize(objective: str, context: str = "") -> str:
    """Invoca Metis para analisis estrategico."""
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


def create_gateway(host: str = "0.0.0.0", port: int = 8010) -> AgnoGateway:
    gateway = AgnoGateway(host=host, port=port)

    gateway.register_tool(
        "kaos_research", _kaos_research,
        description="Investiga un tema usando el agente Aletheia de KAOS"
    )
    gateway.register_tool(
        "kaos_analyze", _kaos_analyze,
        description="Analiza la arquitectura del codebase usando Kosmos"
    )
    gateway.register_tool(
        "kaos_strategize", _kaos_strategize,
        description="Analisis estrategico usando Metis"
    )
    gateway.register_tool(
        "vault_read", _vault_read,
        description="Lee contenido del vault de memoria de KAOS"
    )
    gateway.register_tool(
        "vault_search", _vault_search,
        description="Busca en el vault de memoria de KAOS"
    )

    return gateway


gateway = create_gateway()
