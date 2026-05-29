"""Sandbox 01: Agente agno conectado a MCP server de KAOS.

Uso: python agno_kaos/sandbox/01_mcp.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / ".memory" / "_scripts"))

from agno.agent import Agent
from agno.tools.mcp import MCPTools

from agno_kaos import default_model


def main():
    vault_tools = MCPTools(
        command="py -m lib.mcp_kratos_memory",
    )

    agent = Agent(
        name="MCPAgent",
        model=default_model(),
        tools=[vault_tools],
        instructions="Usa las herramientas MCP disponibles para responder.",
        markdown=True,
        add_history_to_context=True,
    )
    agent.print_response("¿Qué experiencias tienes almacenadas? Usa ce_search o ce_status.", stream=True)


if __name__ == "__main__":
    main()
