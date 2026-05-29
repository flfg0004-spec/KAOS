"""ResearchTeam: Aletheia + Kosmos coordinados para investigación multi-paso.

Mode: coordinate — un agente coordinador orquesta la investigación.
"""

from agno.agent import Agent
from agno.team import Team, TeamMode

from agno_kaos import default_model
from agno_kaos.agents.a_aletheia import create_aletheia
from agno_kaos.agents.a_kosmos import create_kosmos


def create_research_team(
    model_id: str = "deepseek-v4-flash",
    with_mcp: bool = False,
    aletheia: Agent | None = None,
    kosmos: Agent | None = None,
) -> Team:
    aletheia = aletheia or create_aletheia(with_mcp=with_mcp)
    kosmos = kosmos or create_kosmos(with_mcp=with_mcp)

    return Team(
        name="ResearchTeam",
        description="Equipo de investigación: busca información, analiza estructura, sintetiza resultados.",
        mode=TeamMode.coordinate,
        members=[aletheia, kosmos],
        model=default_model(model_id),
        instructions=[
            "Eres un equipo de investigación de alto rendimiento.",
            "Aletheia se encarga de la búsqueda y recopilación de información.",
            "Kosmos analiza la estructura y relaciones de la información encontrada.",
            "Sintetiza los hallazgos en un reporte coherente y bien estructurado.",
            "Incluye fuentes, referencias y análisis en cada respuesta.",
        ],
        markdown=True,
        show_members_responses=True,
        add_history_to_context=True,
        search_knowledge=True,
    )
