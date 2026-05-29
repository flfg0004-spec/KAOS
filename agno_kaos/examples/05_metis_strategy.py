"""🧠 A-Metis: Plan estratégico con OKRs y roadmaps.

Uso: python agno_kaos/examples/05_metis_strategy.py
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from agno_kaos.agents.a_metis import create_metis


async def main():
    print("=" * 55)
    print("🧠 A-Metis: Plan Estratégico con OKRs")
    print("=" * 55)
    agent = create_metis(with_mcp=False)
    response = await agent.arun(
        "Genera un plan estratégico para el equipo KAOS con OKRs "
        "para el próximo trimestre. Contexto: score 8.3/10, "
        "5 agentes funcionales, dashboard web, 19 tests. "
        "Incluye: 3 OKRs con KRs, roadmaps y métricas de éxito"
    )
    print(f"\n{response.content}\n")
    print("✅ Ejecutado. Para análisis estratégico real: create_metis(with_mcp=True)")


if __name__ == "__main__":
    asyncio.run(main())
