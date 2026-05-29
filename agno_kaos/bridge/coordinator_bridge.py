"""Coordinator Bridge: conecta el A-Coordinator con el LangGraph DAG real.

Cuando AGNO_ENABLED=true, el Coordinator invoca el DAG de KAOS
en lugar de responder con texto clasificado.
"""
import os
import logging

logger = logging.getLogger("agno_kaos.bridge")

_DAG_AVAILABLE = False
_DAG = None


def _get_dag():
    global _DAG, _DAG_AVAILABLE
    if _DAG is not None:
        return _DAG
    try:
        from lib.orchestrator import build_graph, KAOSState
        _DAG = build_graph(with_parallel=False)
        _DAG_AVAILABLE = True
        return _DAG
    except Exception as e:
        logger.warning("DAG not available: %s", e)
        _DAG_AVAILABLE = False
        return None


def run_dag(topic: str, profile: str = "standard") -> dict:
    """Ejecuta el LangGraph DAG completo para un topic.

    Args:
        topic: Tema a procesar.
        profile: Perfil de ejecución (standard, deep, produccion).

    Returns:
        Dict con los resultados de cada nodo del DAG.
    """
    dag = _get_dag()
    if dag is None:
        return {"error": "DAG not available", "topic": topic}

    try:
        initial_state = {
            "topic": topic,
            "profile": profile,
            "plan": {},
            "iteration": 0,
        }
        result = dag.invoke(initial_state)
        return dict(result) if isinstance(result, dict) else {"result": str(result)}
    except Exception as e:
        logger.error("DAG execution failed: %s", e)
        return {"error": str(e), "topic": topic}


def coordinator_route(query: str) -> str:
    """Clasifica una consulta y determina la ruta en el DAG.

    Returns:
        "research" | "code" | "strategy" | "general"
    """
    q = query.lower()
    research_kw = ["investiga", "busca", "encuentra", "research", "paper", "noticia", "tendencia", "que es"]
    code_kw = ["codigo", "code", "implementa", "programa", "bug", "test", "refactor", "api", "funcion"]
    strategy_kw = ["estrategia", "strategy", "plan", "okr", "roadmap", "competitivo", "mercado"]

    for kw in research_kw:
        if kw in q:
            return "research"
    for kw in code_kw:
        if kw in q:
            return "code"
    for kw in strategy_kw:
        if kw in q:
            return "strategy"
    return "general"
