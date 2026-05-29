"""🎮 A-Pilot: Asistente general consultando el vault del ecosistema.

Uso: python agno_kaos/examples/01_pilot_vault.py
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from agno_kaos.agents.apilot import create_pilot


async def main():
    print("=" * 55)
    print("🎮 A-Pilot: Consulta al Vault del Ecosistema")
    print("=" * 55)
    agent = create_pilot(with_mcp=False)
    response = await agent.arun(
        "¿Cuál es la arquitectura del ecosistema A(gnO)-KAOS? "
        "Describe los componentes principales: agentes, equipos, "
        "workflows, gateway MCP y cómo se relacionan."
    )
    print(f"\n{response.content}\n")
    print("✅ Ejecutado. Para usar con MCP real: create_pilot(with_mcp=True)")


if __name__ == "__main__":
    asyncio.run(main())
