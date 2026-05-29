"""A-Kosmos: Agente de análisis de arquitectura y código.

Tools: depwire, structurizr, lucidity, vault, txtai
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from agno_kaos import AGNO_DB_PATH, default_model
from agno_kaos.mcp_utils import safe_mcp_tools

MCP_SERVERS = [
    "npx -y @iflow-mcp/depwire-depwire",
    "py -3 .memory/_scripts/mcp_structurizr.py",
    "npx -y mcp-knowledge-graph --memory-path .memory/cache/knowledge-graph",
    "py -3 .memory/_scripts/mcp_txtai.py",
    "py -3 .memory/_scripts/mcp_proxy.py -- npx -y @modelcontextprotocol/server-filesystem .memory",
    "npx -y @modelcontextprotocol/server-sequential-thinking",
]


def create_kosmos(db_path: Path | None = None, model_id: str = "deepseek-v4-flash", with_mcp: bool = False) -> Agent:
    if db_path is None:
        db_path = AGNO_DB_PATH.parent / "a_kosmos.db"
    agno_db = SqliteDb(db_file=str(db_path))

    tools = []
    if with_mcp:
        tools = safe_mcp_tools(MCP_SERVERS)

    return Agent(
        name="A-Kosmos",
        model=default_model(model_id),
        db=agno_db,
        tools=tools or None,
        description="Agente de análisis de arquitectura y código del ecosistema A(gnO)-KAOS.",
        instructions=[
            "Eres un agente especializado en análisis de arquitectura de software.",
            "Usa depwire para analizar dependencias entre módulos.",
            "Usa structurizr para generar diagramas de arquitectura C4.",
            "Usa lucidity para analizar cambios en el código.",
            "Consulta el vault y txtai para documentación existente.",
            "Estructura tus respuestas con secciones claras y diagramas.",
            "Responde SIEMPRE en markdown.",
        ],
        markdown=True,
        add_history_to_context=True,
        update_memory_on_run=True,
        search_knowledge=True,
    )


if __name__ == "__main__":
    import uvicorn
    from agno.os import AgentOS

    agent = create_kosmos(with_mcp=False)
    os = AgentOS(agents=[agent], enable_mcp_server=True)
    print("A-Kosmos AgentOS en http://127.0.0.1:8024")
    uvicorn.run(os.get_app(), host="127.0.0.1", port=8024)
