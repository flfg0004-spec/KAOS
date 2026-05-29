"""Sandbox 02: AgentOS mínimo con MCP server habilitado.

Expone un agente agno como MCP server vía AgentOS.
Uso: python agno_kaos/sandbox/02_agentos.py
"""

from pathlib import Path
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS

from agno_kaos import AGNO_DB_PATH, default_model

AGNO_DB = SqliteDb(db_file=str(AGNO_DB_PATH.with_name("agno_sandbox.db")))

pilot = Agent(
    name="SandboxPilot",
    model=default_model("deepseek-v4-flash"),
    db=AGNO_DB,
    instructions="Eres un asistente útil. Responde de forma clara y concisa.",
    markdown=True,
    add_history_to_context=True,
    update_memory_on_run=True,
)

os = AgentOS(
    agents=[pilot],
    enable_mcp_server=True,
)

app = os.get_app()

if __name__ == "__main__":
    import uvicorn

    print("AgentOS corriendo en http://127.0.0.1:8021 (MCP en /mcp)")
    uvicorn.run(app, host="127.0.0.1", port=8021)
