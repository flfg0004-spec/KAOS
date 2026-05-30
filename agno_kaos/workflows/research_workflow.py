"""ResearchWorkflow: Pipeline multi-paso de investigación.

1. Aletheia investiga el tema
2. Kosmos analiza la estructura
3. Metis sintetiza en un plan estratégico

Cada paso tiene timeout de 30s para evitar hangs.
"""

import asyncio
import logging
from dataclasses import dataclass, field

from agno.workflow import Workflow

from agno_kaos.agents.a_aletheia import create_aletheia
from agno_kaos.agents.a_kosmos import create_kosmos
from agno_kaos.agents.a_metis import create_metis

logger = logging.getLogger("agno_kaos.workflow")
_STEP_TIMEOUT = 30


@dataclass
class _StepResult:
    """Reemplazo mínimo de RunResponse para evitar type() dinámico."""
    content: str = ""


def _error_step(msg: str):
    return _StepResult(content=msg)


async def _safe_step(coro, step_name: str, topic: str):
    try:
        result = await asyncio.wait_for(coro, timeout=_STEP_TIMEOUT)
        return result
    except asyncio.TimeoutError:
        logger.error("Workflow step '%s' timed out after %ss (topic: %s)", step_name, _STEP_TIMEOUT, topic[:80])
        return _error_step(f"[ERROR] Step '{step_name}' timed out after {_STEP_TIMEOUT}s")
    except Exception as e:
        logger.error("Workflow step '%s' failed: %s (topic: %s)", step_name, e, topic[:80])
        return _error_step(f"[ERROR] Step '{step_name}' failed: {e}")


def create_research_workflow(model_id: str = "deepseek-v4-flash", with_mcp: bool = False) -> Workflow:
    aletheia = create_aletheia(with_mcp=with_mcp)
    kosmos = create_kosmos(with_mcp=with_mcp)
    metis = create_metis(with_mcp=with_mcp)

    async def run_workflow(ctx, topic: str) -> dict:
        paso1 = await _safe_step(
            aletheia.arun(f"Investiga a fondo: {topic}"),
            "research", topic,
        )
        paso2 = await _safe_step(
            kosmos.arun(f"Analiza la siguiente investigación:\n\n{paso1.content}"),
            "analyze", topic,
        )
        paso3 = await _safe_step(
            metis.arun(
                f"Basado en esta investigación y análisis, genera un plan estratégico:\n\n"
                f"## Investigación\n{paso1.content}\n\n"
                f"## Análisis\n{paso2.content}"
            ),
            "strategize", topic,
        )
        return {
            "research": paso1.content if hasattr(paso1, "content") else str(paso1),
            "analysis": paso2.content if hasattr(paso2, "content") else str(paso2),
            "strategy": paso3.content if hasattr(paso3, "content") else str(paso3),
        }

    return Workflow(
        name="ResearchWorkflow",
        description="Pipeline completo de investigación: Aletheia busca → Kosmos analiza → Metis estratégia",
        steps=[run_workflow],
    )
