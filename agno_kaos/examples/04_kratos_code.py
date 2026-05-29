"""⚙️ A-Kratos: Revisión y generación de código.

Uso: python agno_kaos/examples/04_kratos_code.py
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from agno_kaos.agents.a_kratos import create_kratos


async def main():
    print("=" * 55)
    print("⚙️ A-Kratos: Revisión y Generación de Código")
    print("=" * 55)
    agent = create_kratos(with_mcp=False)
    response = await agent.arun(
        "Genera una clase `RateLimiter` en Python que implemente "
        "token bucket algorithm con: type hints completos, "
        "docstrings, manejo de edge cases y thread-safety"
    )
    print(f"\n{response.content}\n")
    print("✅ Ejecutado. Para revisar código real: create_kratos(with_mcp=True)")


if __name__ == "__main__":
    asyncio.run(main())
