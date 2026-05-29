"""A-Kratos: Agente de generación y revisión de código.

Tools: git, vault, sequential-thinking
"""

from pathlib import Path
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from agno_kaos import AGNO_DB_PATH, default_model
from agno_kaos.mcp_utils import safe_mcp_tools, load_mcp_config


def create_kratos(db_path: Path | None = None, model_id: str = "deepseek-v4-flash", with_mcp: bool = False) -> Agent:
    if db_path is None:
        db_path = AGNO_DB_PATH.parent / "a_kratos.db"
    agno_db = SqliteDb(db_file=str(db_path))

    tools = []
    if with_mcp:
        tools = safe_mcp_tools(load_mcp_config("kratos"))

    return Agent(
        name="A-Kratos",
        model=default_model(model_id),
        db=agno_db,
        tools=tools or None,
        description="Agente de generación y revisión de código del ecosistema A(gnO)-KAOS.",
        instructions=[
            "Eres un agente especializado en generación y revisión de código.",
            "Usa git para explorar el repositorio, leer archivos y revisar cambios.",
            "Usa sequential-thinking para razonar sobre problemas complejos.",
            "Genera código con type hints, docstrings y manejo de edge cases.",
            "Sigue las convenciones del proyecto existente.",
            "Responde SIEMPRE en markdown con bloques de código.",
        ],
        markdown=True,
        add_history_to_context=True,
        update_memory_on_run=True,
        search_knowledge=True,
    )


if __name__ == "__main__":
    import uvicorn
    from agno.os import AgentOS

    agent = create_kratos(with_mcp=False)
    os = AgentOS(agents=[agent], enable_mcp_server=True)
    print("A-Kratos AgentOS en http://127.0.0.1:8026")
    uvicorn.run(os.get_app(), host="127.0.0.1", port=8026)
