"""🏗️ A-Kosmos: Análisis de arquitectura y estructura del código.

Uso: python agno_kaos/examples/03_kosmos_architecture.py
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from agno_kaos.agents.a_kosmos import create_kosmos


async def main():
    print("=" * 55)
    print("🏗️ A-Kosmos: Análisis de Arquitectura")
    print("=" * 55)
    agent = create_kosmos(with_mcp=False)
    response = await agent.arun(
        "Analiza la estructura del paquete agno_kaos/. "
        "Describe: 1) Organización de módulos 2) Patrones de diseño "
        "3) Cómo se relacionan los componentes 4) Recomendaciones "
        "de mejora arquitectónica"
    )
    print(f"\n{response.content}\n")
    print("✅ Ejecutado. Para análisis con depwire/structurizr: create_kosmos(with_mcp=True)")


if __name__ == "__main__":
    asyncio.run(main())
