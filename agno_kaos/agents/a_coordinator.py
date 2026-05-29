"""A-Coordinator: Agente enrutador que clasifica consultas y delega al equipo correcto.

Mode: route — analiza la consulta y enruta al agente/equipo especializado.
"""

from agno.agent import Agent

from agno_kaos import default_model


def create_coordinator(model_id: str = "deepseek-v4-flash") -> Agent:
    return Agent(
        name="A-Coordinator",
        model=default_model(model_id),
        description="Coordinador inteligente que clasifica y enruta consultas al equipo especializado.",
        instructions=[
            "Eres el punto de entrada del sistema multi-agente A(gnO)-KAOS.",
            "Analiza cada consulta y determina qué tipo de trabajo se necesita:",
            "",
            "  - INVESTIGACIÓN → necesita búsqueda de información actualizada",
            "    → Responde: 'research: <consulta>'",
            "",
            "  - ARQUITECTURA/CÓDIGO → necesita análisis, revisión o generación de código",
            "    → Responde: 'code: <consulta>'",
            "",
            "  - ESTRATEGIA/PLANEACIÓN → necesita OKRs, roadmaps, análisis competitivo",
            "    → Responde: 'strategy: <consulta>'",
            "",
            "  - GENERAL → preguntas simples que puedes responder directamente",
            "    → Responde directamente",
            "",
            "Responde SIEMPRE en markdown.",
            "Sé conciso en el análisis pero completo en la respuesta.",
        ],
        markdown=True,
        add_history_to_context=True,
    )
