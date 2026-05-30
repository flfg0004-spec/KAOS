"""Run Escuadrón A — AgentOS producción (Postgres, scheduler, RBAC, tracing, Telegram).

Uso: python agno_kaos/run_escadron.py
"""
import logging
import os
from pathlib import Path

import uvicorn
from agno.os import AgentOS

from agno_kaos import get_auth_config, get_db, get_ports, load_config

logger = logging.getLogger("agno_kaos")

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

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

PORTS = get_ports()
PORT = PORTS.get("escadron", 8030)
AGENTOS_CFG = load_config().get("agentos", {})

db = get_db()

aletheia = create_aletheia(db_path=_SCRIPTS / "agno_kaos" / "a_aletheia.db", with_mcp=False)
kosmos = create_kosmos(db_path=_SCRIPTS / "agno_kaos" / "a_kosmos.db", with_mcp=False)
metis = create_metis(db_path=_SCRIPTS / "agno_kaos" / "a_metis.db", with_mcp=False)
kratos = create_kratos(db_path=_SCRIPTS / "agno_kaos" / "a_kratos.db", with_mcp=False)
coordinator = create_coordinator()

research_team = create_research_team(with_mcp=False, aletheia=aletheia, kosmos=kosmos)
code_team = create_code_team(with_mcp=False, kratos=kratos, kosmos=kosmos)
strategy_team = create_strategy_team(with_mcp=False, metis=metis, aletheia=aletheia)

research_workflow = create_research_workflow(with_mcp=False)

auth_config = get_auth_config()

# Telegram interface (opcional, requiere TELEGRAM_BOT_TOKEN en .env)
telegram_interfaces = []
telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if telegram_token:
    try:
        from agno.os.interfaces.telegram import Telegram

        telegram_interfaces.append(
            Telegram(
                agent=coordinator,
                token=telegram_token,
                commands=[
                    {"command": "investigate", "description": "Investiga un tema"},
                    {"command": "analyze", "description": "Analiza arquitectura"},
                    {"command": "strategize", "description": "Plan estratégico"},
                    {"command": "code", "description": "Genera o revisa código"},
                    {"command": "status", "description": "Estado del sistema"},
                ],
            )
        )
        logger.info("Telegram interface enabled")
    except ImportError as e:
        logger.warning("Telegram interface not available: %s", e)

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
    interfaces=telegram_interfaces or None,
)

app = os.get_app()

features = []
if db.__class__.__name__ == "PostgresDb":
    features.append("Postgres")
else:
    features.append("SQLite")
if auth_config:
    features.append("RBAC")
else:
    features.append("NoAuth")
if getattr(os, "_scheduler_enabled", False):
    features.append("Scheduler")
if AGENTOS_CFG.get("tracing"):
    features.append("Tracing")
if telegram_interfaces:
    features.append("Telegram")

logger.info("Sec mode: %s", load_config().get("security", {}).get("mode", "disabled"))
logger.info("=" * 55)
logger.info("  Escuadrón A — A(gnO)-KAOS AgentOS v3")
logger.info("=" * 55)
logger.info("  Landing:     http://127.0.0.1:%d/", PORT)
logger.info("  Swagger UI:  http://127.0.0.1:%d/docs", PORT)
logger.info("  Agents:      http://127.0.0.1:%d/agents", PORT)
logger.info("  Teams:       http://127.0.0.1:%d/teams", PORT)
logger.info("  Workflows:   http://127.0.0.1:%d/workflows", PORT)
logger.info("  Health:      http://127.0.0.1:%d/health", PORT)
logger.info("  MCP:         http://127.0.0.1:%d/mcp", PORT)
logger.info("  Features:    %s", ", ".join(features))
logger.info("=" * 55)

uvicorn.run(app, host="127.0.0.1", port=PORT)
