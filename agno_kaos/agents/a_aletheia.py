"""A-Aletheia: Agente de investigación profunda.

Tools: exa-search, searxng, crawl4ai, vault, txtai, knowledge-graph, scholar-search
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from agno_kaos import AGNO_DB_PATH, default_model
from agno_kaos.mcp_utils import safe_mcp_tools

MCP_SERVERS = [
    "npx -y exa-mcp-server",
    "npx -y searxng-mcp --url http://127.0.0.1:8888",
    "npx -y crawl4ai-mcp-sse-stdio --url http://127.0.0.1:11235",
    "npx -y scholar-search-mcp",
    "npx -y mcp-knowledge-graph --memory-path .memory/cache/knowledge-graph",
    "py -3 .memory/_scripts/mcp_txtai.py",
    "py -3 .memory/_scripts/mcp_proxy.py -- npx -y @modelcontextprotocol/server-filesystem .memory",
    "npx -y @modelcontextprotocol/server-sequential-thinking",
]


def create_aletheia(db_path: Path | None = None, model_id: str = "deepseek-v4-flash", with_mcp: bool = False) -> Agent:
    if db_path is None:
        db_path = AGNO_DB_PATH.parent / "a_aletheia.db"
    agno_db = SqliteDb(db_file=str(db_path))

    tools = []
    if with_mcp:
        tools = safe_mcp_tools(MCP_SERVERS)

    return Agent(
        name="A-Aletheia",
        model=default_model(model_id),
        db=agno_db,
        tools=tools or None,
        description="Agente de investigación profunda del ecosistema A(gnO)-KAOS.",
        instructions=[
            "Eres un agente de investigación especializado.",
            "Usa las herramientas disponibles para buscar información actualizada en la web.",
            "Para investigación académica usa scholar-search.",
            "Para búsqueda general usa exa-search o searxng.",
            "Para extraer contenido de páginas usa crawl4ai.",
            "Consulta el vault y txtai para información interna de KAOS.",
            "Estructura tus respuestas con secciones claras, fuentes y referencias.",
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

    agent = create_aletheia(with_mcp=False)
    os = AgentOS(agents=[agent], enable_mcp_server=True)
    print("A-Aletheia AgentOS en http://127.0.0.1:8023")
    uvicorn.run(os.get_app(), host="127.0.0.1", port=8023)
