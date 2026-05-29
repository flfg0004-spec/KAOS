"""Smoke test: verifica que todo el paquete importe correctamente."""
from pathlib import Path


def test_import_package():
    from agno_kaos import default_model, load_config, get_ports, get_db, get_auth_config
    assert callable(default_model)
    cfg = load_config()
    assert "agentos" in cfg
    assert get_ports()["escadron"] == 8030


def test_import_agents():
    from agno_kaos.agents.a_aletheia import create_aletheia
    from agno_kaos.agents.a_kosmos import create_kosmos
    from agno_kaos.agents.a_kratos import create_kratos
    from agno_kaos.agents.a_metis import create_metis
    from agno_kaos.agents.apilot import create_pilot
    from agno_kaos.agents.a_coordinator import create_coordinator
    for fn in [create_aletheia, create_kosmos, create_kratos, create_metis, create_pilot, create_coordinator]:
        assert callable(fn)


def test_import_teams():
    from agno_kaos.teams.research_team import create_research_team
    from agno_kaos.teams.code_team import create_code_team
    from agno_kaos.teams.strategy_team import create_strategy_team
    for fn in [create_research_team, create_code_team, create_strategy_team]:
        assert callable(fn)


def test_import_workflow():
    from agno_kaos.workflows.research_workflow import create_research_workflow
    assert callable(create_research_workflow)


def test_mcp_utils():
    from agno_kaos.mcp_utils import safe_mcp_tools, _command_exists, _resolve_path
    assert callable(safe_mcp_tools)


def test_config_yaml():
    from agno_kaos import load_config
    cfg = load_config()
    assert cfg["agentos"]["name"] == "A(gnO)-KAOS Escuadrón A"
    assert cfg["agentos"]["version"] == "3.0.0"
    assert "ports" in cfg
    assert "database" in cfg


def test_resolve_db_path():
    from agno_kaos import _resolve_db_path
    p1 = _resolve_db_path(None, Path("/default/db.db"))
    assert p1 == Path("/default/db.db").resolve()
    p2 = _resolve_db_path("/abs/path.db", Path("/default/db.db"))
    assert p2 == Path("/abs/path.db")
