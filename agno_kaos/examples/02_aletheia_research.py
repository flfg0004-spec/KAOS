"""🔍 A-Aletheia: Investigación web y síntesis de información.

Uso: python agno_kaos/examples/02_aletheia_research.py
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from agno_kaos.agents.a_aletheia import create_aletheia


async def main():
    print("=" * 55)
    print("🔍 A-Aletheia: Investigación Profunda")
    print("=" * 55)
    agent = create_aletheia(with_mcp=False)
    response = await agent.arun(
        "Investiga sobre el protocolo MCP (Model Context Protocol). "
        "Proporciona un resumen ejecutivo con: "
        "1) ¿Qué es MCP? 2) ¿Cómo funciona? 3) Beneficios clave "
        "4) Cómo se aplica en KAOS para conectar agentes con herramientas"
    )
    print(f"\n{response.content}\n")
    print("✅ Ejecutado. Para búsqueda web real: create_aletheia(with_mcp=True)")


if __name__ == "__main__":
    asyncio.run(main())
