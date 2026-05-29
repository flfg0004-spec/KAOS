"""StrategyTeam: Metis + Aletheia para análisis estratégico con investigación.

Mode: route — enruta según necesidad de investigación vs análisis.
"""

from agno.agent import Agent
from agno.team import Team, TeamMode

from agno_kaos import default_model
from agno_kaos.agents.a_metis import create_metis
from agno_kaos.agents.a_aletheia import create_aletheia


def create_strategy_team(
    model_id: str = "deepseek-v4-flash",
    with_mcp: bool = False,
    metis: Agent | None = None,
    aletheia: Agent | None = None,
) -> Team:
    metis = metis or create_metis(with_mcp=with_mcp)
    aletheia = aletheia or create_aletheia(with_mcp=with_mcp)

    return Team(
        name="StrategyTeam",
        description="Equipo de estrategia: investiga tendencias y genera planes estratégicos.",
        mode=TeamMode.route,
        members=[metis, aletheia],
        model=default_model(model_id),
        instructions=[
            "Eres un equipo de estrategia de alto nivel.",
            "Aletheia investiga tendencias, competidores y datos de mercado.",
            "Metis analiza la información y genera planes estratégicos (OKRs, roadmaps).",
            "Para investigación de mercado → asigna a Aletheia.",
            "Para planeación estratégica → asigna a Metis.",
            "Para informes completos → ambos trabajan en secuencia.",
        ],
        markdown=True,
        show_members_responses=True,
        add_history_to_context=True,
        search_knowledge=True,
    )
