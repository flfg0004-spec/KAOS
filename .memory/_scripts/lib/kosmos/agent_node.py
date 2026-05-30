"""kosmos/agent_node.py — KosmosV2 pipeline node for LangGraph orchestrator (D5).

Extraído de agent_executor.py para mantener el monolito más manejable.
Usa imports lazy de agent_executor para las funciones helper compartidas.
"""

import logging
from datetime import datetime
from typing import Any, Dict

_log = logging.getLogger(__name__)


def kosmos_node(state: dict) -> dict:
    """KosmosV2 pipeline node — 8-node architecture analysis with memory, contracts, and fallback.

    Uses KosmosPipelineV2 for full pipeline execution when LLM_DIRECT_ENABLED,
    with graceful fallback to v1 prompt-gen mode when tools are unavailable.

    Args:
        state: LangGraph state dict with at least 'topic' key.

    Returns:
        Updated state dict with kosmos_output, kosmos_prompt, and evaluation results.
    """
    from lib.agent_executor import (
        _slugify, _load_context, _save_context,
        LLM_DIRECT_ENABLED, RAW_DIR,
        _notify_step, _build_rag_context, _llm_or_executor_call,
    )

    topic = state.get("topic", "")
    slug = _slugify(topic)

    ctx = _load_context()
    a_ctx = ctx.get("context_summary", {}).get("aletheia", {})

    pipeline_result = None
    memory = None
    try:
        from lib.kosmos_memory import ArchitectureMemoryL0
        from lib.kosmos.pipeline import KosmosPipelineV2
        from lib.kosmos_evaluator_v2 import DimensionalEvaluator
        from lib.kosmos_reflect import ReflectionEngine

        memory = ArchitectureMemoryL0()
        if LLM_DIRECT_ENABLED:
            memory.index_all_adrs()

        pipeline = KosmosPipelineV2(state, memory=memory)
        pipeline_result = pipeline.run_all()
        _log.info("KosmosV2 pipeline completed: %d nodes, %d errors",
                   len(pipeline_result.get("node_results", {})),
                   len(pipeline_result.get("errors", {})))
    except Exception as exc:
        _log.warning("KosmosV2 pipeline failed, falling back to v1: %s", exc)
        pipeline_result = None

    if pipeline_result and pipeline_result.get("node_results"):
        pipeline.state["pipeline_status"] = pipeline_result
        state["pipeline_status"] = pipeline_result
        adr_text = pipeline.state.get("kosmos_adr", "")
        diagrams = pipeline.state.get("kosmos_diagrams", [])
        errors = pipeline_result.get("errors", {})

        # G2: Extract evaluation from pipeline state
        eval_v2 = pipeline.state.get("kosmos_eval_v2", {})
        if eval_v2 and eval_v2.get("scores"):
            state["kosmos_eval_v2"] = eval_v2
            _log.info("G2: Using pipeline-computed evaluation")
        else:
            evaluator = DimensionalEvaluator(profile=state.get("profile", "desarrollo"))
            eval_result = evaluator.evaluate(adr_text or topic)
            state["kosmos_eval_v2"] = {
                "scores": eval_result.scores,
                "weighted_score": eval_result.weighted_score,
                "passed": eval_result.passed,
                "profile": eval_result.profile_used,
            }

        # G2: Extract reflection from pipeline state
        reflection = pipeline.state.get("kosmos_reflection", {})
        if reflection and reflection.get("total_score") is not None:
            state["kosmos_reflection"] = reflection
        elif adr_text:
            try:
                reflector = ReflectionEngine(memory=memory)
                r = reflector.evaluate_adr(adr_text)
                state["kosmos_reflection"] = {
                    "total_score": r.total_score,
                    "gaps": r.gaps,
                    "improvement_plan": r.improvement_plan,
                }
            except Exception as exc_ref:
                _log.warning("Reflection fallback failed: %s", exc_ref)

        # Fase 2: Execute contracts
        contracts_result = {}
        try:
            from lib.kosmos.contracts import ContractOrchestrator
            from lib.kosmos_memory import ArchitectureMemoryL1
            orch = ContractOrchestrator(memory_l0=memory, kratos_real=True)
            adr_id = pipeline.state.get("adr", {}).get("adr_id", f"ADR-XXX-{slug}")
            contracts_result = orch.run_all_contracts(adr_text or "", adr_id, pipeline.state)
            state["kosmos_contracts"] = contracts_result
            _log.info("Contracts executed: %d/%d completed",
                       len(contracts_result.get("contracts", {})),
                       len(contracts_result.get("contracts", {})))
        except Exception as exc_c:
            _log.warning("Contract orchestration failed (non-blocking): %s", exc_c)

        # L1 txtai indexing
        try:
            l1 = ArchitectureMemoryL1(memory_l0=memory)
            if adr_text:
                l1_result = pipeline.sync_with_txtai(adr_text, adr_id)
                state["kosmos_l1_indexed"] = l1_result.get("indexed", False)
        except Exception as exc_l1:
            _log.warning("L1 txtai indexing failed (non-blocking): %s", exc_l1)

        kosmos_output = adr_text or f"Pipeline ejecutado. Diagramas: {len(diagrams)}. Errores: {len(errors)}"
        state["kosmos_output"] = kosmos_output
        state["kosmos_diagrams"] = diagrams
        state["kosmos_prompt"] = f"KosmosV2 pipeline ejecutado con {len(pipeline_result.get('node_results', {}))} nodos"

        output_path = RAW_DIR / f"{slug}-adr.md"
        output_path.write_text(kosmos_output or "Pipeline ejecutado sin ADR.", encoding="utf-8")

        eval_score = state.get("kosmos_eval_v2", {}).get("weighted_score")
        ctx["agents"].append("kosmos")
        ctx["context_summary"]["kosmos"] = {
            "started_at": datetime.now().isoformat(),
            "pipeline_version": "v2-full",
            "nodes_executed": len(pipeline_result.get("node_results", {})),
            "errors": len(errors),
            "eval_score": eval_score,
            "contracts": {
                name: st for name, st in contracts_result.get("contracts", {}).items()
            } if contracts_result else {},
        }
        _save_context(ctx)
        if memory:
            memory.close()
        return state

    # Fallback: v1 prompt-gen mode
    sources_summary = ""
    if a_ctx.get("sources_used"):
        sources_summary = "\n".join(f"- {s}" for s in a_ctx["sources_used"])

    prompt = (
        f"# Pipeline: Arquitectura\n\n"
        f"## Tema\n{topic}\n\n"
        f"## Contexto de Investigación\n"
        f"{sources_summary if sources_summary else 'Sin fuentes documentadas aún.'}\n\n"
        f"Analiza la arquitectura del sistema descrito en el tema.\n"
        f"Produce:\n"
        f"1. ADR (Architecture Decision Record)\n"
        f"2. Diagramas C4 (contexto y contenedor)\n"
        f"3. Recomendaciones arquitectónicas\n"
    )

    output_path = RAW_DIR / f"{slug}-adr.md"
    output_path.write_text(prompt, encoding="utf-8")

    if LLM_DIRECT_ENABLED:
        _notify_step(state, "Kosmos Architecture", "in_progress")
        enhanced = _build_rag_context(topic) + "\n\n" + prompt
        raw = _llm_or_executor_call("kosmos", enhanced)
        output_path.write_text(raw, encoding="utf-8")
        ctx = _load_context()
        ctx["agents"].append("kosmos")
        ctx["context_summary"]["kosmos"] = {"started_at": datetime.now().isoformat(), "pipeline_version": "v1"}
        _save_context(ctx)
        _notify_step(state, "Kosmos Architecture", "completed")
        if memory:
            memory.close()
        return {**state, "kosmos_output": raw, "kosmos_prompt": prompt}

    ctx["agents"].append("kosmos")
    ctx["context_summary"]["kosmos"] = {
        "started_at": datetime.now().isoformat(),
        "pipeline_version": "v1-fallback",
    }
    _save_context(ctx)
    if memory:
        memory.close()
    return {
        **state,
        "kosmos_output": f"ADR prompt written to {output_path}",
        "kosmos_prompt": prompt,
    }
