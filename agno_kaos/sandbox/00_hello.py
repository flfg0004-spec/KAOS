"""Sandbox 00: Agente mínimo agno con OpenCode GO.

Uso: python agno_kaos/sandbox/00_hello.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from agno.agent import Agent

from agno_kaos import default_model

agent = Agent(
    name="HelloAgent",
    model=default_model(),
    description="Eres un asistente útil.",
    instructions="Responde de forma amable y concisa.",
    markdown=True,
)
agent.print_response("¿Quién eres y qué puedes hacer?", stream=True)
