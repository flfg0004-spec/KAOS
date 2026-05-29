"""CodeTeam: Kratos + Kosmos para revisiones y generación de código.

Mode: route — enruta según el tipo de tarea (revisión → Kosmos, generación → Kratos).
"""

from agno.agent import Agent
from agno.team import Team, TeamMode

from agno_kaos import default_model
from agno_kaos.agents.a_kratos import create_kratos
from agno_kaos.agents.a_kosmos import create_kosmos


def create_code_team(
    model_id: str = "deepseek-v4-flash",
    with_mcp: bool = False,
    kratos: Agent | None = None,
    kosmos: Agent | None = None,
) -> Team:
    kratos = kratos or create_kratos(with_mcp=with_mcp)
    kosmos = kosmos or create_kosmos(with_mcp=with_mcp)

    return Team(
        name="CodeTeam",
        description="Equipo de código: genera, revisa y analiza código.",
        mode=TeamMode.route,
        members=[kratos, kosmos],
        model=default_model(model_id),
        instructions=[
            "Eres un equipo de desarrollo de software.",
            "Kratos genera y modifica código según los requerimientos.",
            "Kosmos revisa la arquitectura y calidad del código.",
            "Para generación de código nuevo → asigna a Kratos.",
            "Para revisión de arquitectura o calidad → asigna a Kosmos.",
            "Para tareas mixtas → Kratos genera, Kosmos revisa.",
        ],
        markdown=True,
        show_members_responses=True,
        add_history_to_context=True,
        search_knowledge=True,
    )
