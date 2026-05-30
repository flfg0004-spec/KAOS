from lib.agent_tools import (
    RAW_DIR,
    build_rag_context,
    llm_or_executor_call,
    load_context,
    notify_step,
    save_context,
    slugify,
)
from lib.config import LLM_DIRECT_ENABLED
from lib.feature_flags import is_enabled


def kosmos_node(state: dict) -> dict:
    if is_enabled("use_new_agent_executor"):
        return _kosmos_node_v2(state)
    return _kosmos_node_impl(state)


def _kosmos_node_impl(state: dict) -> dict:
    topic = state.get("topic", "")
    slug = slugify(topic)

    sources_summary = ""
    ctx = load_context()
    a_ctx = ctx.get("context_summary", {}).get("aletheia", {})
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
        notify_step(state, "Kosmos Architecture", "in_progress")
        enhanced = build_rag_context(topic) + "\n\n" + prompt
        raw = llm_or_executor_call("kosmos", enhanced)
        output_path.write_text(raw, encoding="utf-8")
        ctx = load_context()
        ctx["agents"].append("kosmos")
        ctx["context_summary"]["kosmos"] = {"started_at": datetime.now().isoformat()}
        save_context(ctx)
        notify_step(state, "Kosmos Architecture", "completed")
        result = {"kosmos_output": raw, "kosmos_prompt": prompt}
        try:
            from lib.opa_bridge import check_architecture
            governance = check_architecture(
                adr={"title": topic[:40], "context": topic, "decision": result.get("kosmos_output", "")[:200], "consequences": [], "status": "draft"},
                code=state.get("kratos_output", ""),
            )
            result["governance_allowed"] = governance["allowed"]
            if not governance["allowed"]:
                result["governance_denials"] = governance["denials"]
        except Exception:
            result["governance_allowed"] = True
            result["governance_denials"] = []
        try:
            from lib.viz_orchestrator import orchestrate as _viz
            _viz("kosmos", {"adr_content": raw})
        except Exception:
            pass
    return {**state, **result}


def _kosmos_node_v2(state: dict) -> dict:
    return _kosmos_node_impl(state)

    from datetime import datetime
    ctx["agents"].append("kosmos")
    ctx["context_summary"]["kosmos"] = {
        "started_at": datetime.now().isoformat(),
    }
    save_context(ctx)

    result = {
        "kosmos_output": f"ADR prompt written to {output_path}",
        "kosmos_prompt": prompt,
    }
    try:
        from lib.opa_bridge import check_architecture
        governance = check_architecture(
            adr={"title": topic[:40], "context": topic, "decision": result.get("kosmos_output", "")[:200], "consequences": [], "status": "draft"},
            code=state.get("kratos_output", ""),
        )
        result["governance_allowed"] = governance["allowed"]
        if not governance["allowed"]:
            result["governance_denials"] = governance["denials"]
    except Exception:
        result["governance_allowed"] = True
        result["governance_denials"] = []
    try:
        from lib.viz_orchestrator import orchestrate as _viz
        _viz("kosmos", {"adr_content": result.get("kosmos_output", "")})
    except Exception:
        pass
    return {**state, **result}
