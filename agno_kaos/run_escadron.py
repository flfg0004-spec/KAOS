"""Run Escuadrón A — AgentOS producción (Postgres, scheduler, RBAC, tracing).

Uso: python agno_kaos/run_escadron.py
"""

from pathlib import Path

import uvicorn
from agno.os import AgentOS

from agno_kaos import get_auth_config, get_db, get_ports, load_config

_SCRIPTS = Path(__file__).resolve().parent.parent
from agno_kaos.agents.a_aletheia import create_aletheia
from agno_kaos.agents.a_kosmos import create_kosmos
from agno_kaos.agents.a_kratos import create_kratos
from agno_kaos.agents.a_metis import create_metis
from agno_kaos.agents.a_coordinator import create_coordinator
from agno_kaos.app import app as base_app
from agno_kaos.teams.code_team import create_code_team
from agno_kaos.teams.research_team import create_research_team
from agno_kaos.teams.strategy_team import create_strategy_team
from agno_kaos.workflows.research_workflow import create_research_workflow

PORTS = get_ports()
PORT = PORTS.get("escadron", 8030)
AGENTOS_CFG = load_config().get("agentos", {})

# Database (Postgres con SQLite fallback)
db = get_db()

# Agents individuales (paths absolutos)
aletheia = create_aletheia(db_path=_SCRIPTS / "agno_kaos" / "a_aletheia.db", with_mcp=True)
kosmos = create_kosmos(db_path=_SCRIPTS / "agno_kaos" / "a_kosmos.db", with_mcp=True)
metis = create_metis(db_path=_SCRIPTS / "agno_kaos" / "a_metis.db", with_mcp=True)
kratos = create_kratos(db_path=_SCRIPTS / "agno_kaos" / "a_kratos.db", with_mcp=True)
coordinator = create_coordinator()

# Teams multi-agente
research_team = create_research_team(with_mcp=True)
code_team = create_code_team(with_mcp=True)
strategy_team = create_strategy_team(with_mcp=True)

# Workflows multi-paso
research_workflow = create_research_workflow(with_mcp=True)

# Auth config
auth_config = get_auth_config()

os = AgentOS(
    agents=[coordinator, aletheia, kosmos, metis, kratos],
    teams=[research_team, code_team, strategy_team],
    workflows=[research_workflow],
    db=db,
    enable_mcp_server=AGENTOS_CFG.get("enable_mcp_server", True),
    base_app=base_app,
    on_route_conflict="preserve_base_app",
    tracing=AGENTOS_CFG.get("tracing", True),
    authorization=auth_config is not None,
    authorization_config=auth_config,
    scheduler=AGENTOS_CFG.get("scheduler", False),
    scheduler_poll_interval=AGENTOS_CFG.get("scheduler_poll_interval", 15),
)

app = os.get_app()

features = []
if db.__class__.__name__ == "PostgresDb":
    features.append("Postgres")
else:
    features.append("SQLite")
if auth_config:
    features.append("RBAC")
if getattr(os, "_scheduler_enabled", False):
    features.append("Scheduler")
if AGENTOS_CFG.get("tracing"):
    features.append("Tracing")

print("=" * 55)
print("  Escuadrón A — A(gnO)-KAOS AgentOS v3")
print("=" * 55)
print(f"  Landing:     http://127.0.0.1:{PORT}/")
print(f"  Swagger UI:  http://127.0.0.1:{PORT}/docs")
print(f"  Agents:      http://127.0.0.1:{PORT}/agents")
print(f"  Teams:       http://127.0.0.1:{PORT}/teams")
print(f"  Workflows:   http://127.0.0.1:{PORT}/workflows")
print(f"  Health:      http://127.0.0.1:{PORT}/health")
print(f"  MCP:         http://127.0.0.1:{PORT}/mcp")
print(f"  Features:    {', '.join(features)}")
print("=" * 55)

uvicorn.run(app, host="127.0.0.1", port=PORT)
