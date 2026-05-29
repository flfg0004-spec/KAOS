"""A-Pilot: Primer agente agno conectado al ecosistema KAOS.

Características:
- Memoria persistente vía SQLite
- Tools MCP de KAOS (vault, search) - opcionales
- Expuesto vía AgentOS con MCP habilitado
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from agno_kaos import AGNO_DB_PATH, default_model


def create_pilot(
    db_path: Path | None = None,
    model_id: str = "deepseek-v4-flash",
    with_mcp: bool = False,
) -> Agent:
    """Crea y configura el agente A-Pilot.

    Args:
        db_path: Ruta a la base de datos SQLite para memoria.
        model_id: ID del modelo LLM a usar.
        with_mcp: Si True, conecta herramientas MCP de KAOS.

    Returns:
        Agent configurado de agno.
    """
    if db_path is None:
        db_path = AGNO_DB_PATH

    agno_db = SqliteDb(db_file=str(db_path))

    tools = []
    if with_mcp:
        try:
            from agno.tools.mcp import MCPTools

            vault_tools = MCPTools(command="py -m lib.mcp_kratos_memory")
            tools.append(vault_tools)
        except Exception as e:
            print(f"[A-Pilot] MCP tools not available: {e}")

    pilot = Agent(
        name="A-Pilot",
        model=default_model(model_id),
        db=agno_db,
        tools=tools or None,
        description="Asistente principal del ecosistema A(gnO)-KAOS.",
        instructions=[
            "Eres un asistente de investigación y análisis.",
            "Usa las herramientas MCP disponibles para consultar información.",
            "Responde de forma clara, estructurada y en markdown.",
            "Si no puedes responder con las herramientas disponibles, usa tu conocimiento.",
        ],
        markdown=True,
        add_history_to_context=True,
        update_memory_on_run=True,
        search_knowledge=True,
    )

    return pilot


def create_pilot_agentos(with_mcp: bool = False):
    """Crea AgentOS con A-Pilot."""
    from agno.os import AgentOS

    pilot = create_pilot(with_mcp=with_mcp)
    os = AgentOS(agents=[pilot], enable_mcp_server=True)
    return os, pilot


if __name__ == "__main__":
    import uvicorn

    os, pilot = create_pilot_agentos(with_mcp=False)
    app = os.get_app()

    print("A-Pilot AgentOS corriendo en http://127.0.0.1:8022")
    uvicorn.run(app, host="127.0.0.1", port=8022)
