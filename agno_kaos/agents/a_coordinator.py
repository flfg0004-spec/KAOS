"""A-Coordinator: Enrutador inteligente que conecta consultas al LangGraph DAG.

Cuando AGNO_ENABLED=true, las consultas se enrutan al DAG real de KAOS.
Cuando AGNO_ENABLED=false, funciona como clasificador de texto standalone.
"""
import os
import logging

from agno.agent import Agent
from agno_kaos import default_model

logger = logging.getLogger("agno_kaos.coordinator")

_AGNO_ENABLED = os.environ.get("AGNO_ENABLED", "false").lower() == "true"


def create_coordinator(model_id: str = "deepseek-v4-flash") -> Agent:
    instructions = [
        "Eres el punto de entrada del sistema multi-agente A(gnO)-KAOS.",
        "Analiza cada consulta y clasifícala en UNA de estas categorías:",
        "",
        "  RESEARCH — necesita búsqueda de información actualizada, noticias, papers",
        "  ARCHITECTURE — necesita análisis de código, dependencias, diagramas",
        "  STRATEGY — necesita OKRs, roadmaps, análisis competitivo",
        "  CODE — necesita generación, revisión o debugging de código",
        "  GENERAL — preguntas simples que puedes responder directamente",
        "",
        "Responde SIEMPRE en markdown.",
    ]

    if _AGNO_ENABLED:
        instructions.extend([
            "",
            "IMPORTANTE: Estás conectado al pipeline LangGraph de KAOS.",
            "Las consultas de investigación, código o estrategia se ejecutarán",
            "en el DAG completo con agentes especializados.",
        ])

    return Agent(
        name="A-Coordinator",
        model=default_model(model_id),
        description="Coordinador inteligente que clasifica y enruta consultas al equipo especializado.",
        instructions=instructions,
        markdown=True,
        add_history_to_context=True,
        search_knowledge=True,
    )
