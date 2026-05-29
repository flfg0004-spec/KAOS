"""A-Aletheia: Agente de investigación profunda.

Tools: exa-search, searxng, crawl4ai, vault, txtai, knowledge-graph, scholar-search
"""

from pathlib import Path
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from agno_kaos import AGNO_DB_PATH, default_model
from agno_kaos.mcp_utils import safe_mcp_tools, load_mcp_config


def create_aletheia(db_path: Path | None = None, model_id: str = "deepseek-v4-flash", with_mcp: bool = False) -> Agent:
    if db_path is None:
        db_path = AGNO_DB_PATH.parent / "a_aletheia.db"
    agno_db = SqliteDb(db_file=str(db_path))

    tools = []
    if with_mcp:
        tools = safe_mcp_tools(load_mcp_config("aletheia"))

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
