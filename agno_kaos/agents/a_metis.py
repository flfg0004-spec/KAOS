"""A-Metis: Agente de estrategia y planeación.

Tools: strategy-mcp, strategy-extras, paperjsx, vault
"""

from pathlib import Path
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from agno_kaos import AGNO_DB_PATH, default_model
from agno_kaos.mcp_utils import safe_mcp_tools, load_mcp_config


def create_metis(db_path: Path | None = None, model_id: str = "deepseek-v4-flash", with_mcp: bool = False) -> Agent:
    if db_path is None:
        db_path = AGNO_DB_PATH.parent / "a_metis.db"
    agno_db = SqliteDb(db_file=str(db_path))

    tools = []
    if with_mcp:
        tools = safe_mcp_tools(load_mcp_config("metis"))

    return Agent(
        name="A-Metis",
        model=default_model(model_id),
        db=agno_db,
        tools=tools or None,
        description="Agente de estrategia y planeación del ecosistema A(gnO)-KAOS.",
        instructions=[
            "Eres un agente especializado en estrategia y planeación.",
            "Usa strategy-mcp y strategy-extras para análisis estratégico.",
            "Usa paperjsx para investigación de papers y tendencias.",
            "Estructura tus respuestas con OKRs, roadmaps y análisis competitivo.",
            "Incluye métricas y KPIs cuando sea relevante.",
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

    agent = create_metis(with_mcp=False)
    os = AgentOS(agents=[agent], enable_mcp_server=True)
    print("A-Metis AgentOS en http://127.0.0.1:8025")
    uvicorn.run(os.get_app(), host="127.0.0.1", port=8025)
