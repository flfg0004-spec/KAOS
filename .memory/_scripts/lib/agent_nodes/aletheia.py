import re
from datetime import datetime

from lib.config import LLM_DIRECT_ENABLED
from lib.agent_tools import (
    slugify, load_context, save_context,
    llm_or_executor_call, build_rag_context, notify_step,
    RAW_DIR,
)
def aletheia_node(state: dict) -> dict:
    return _aletheia_node_impl(state)


def _aletheia_node_impl(state: dict) -> dict:
    topic = state.get("topic", "")
    slug = slugify(topic)
    profile = state.get("profile", "standard")
    plan = state.get("plan", {})
    subtask_ids = [s["id"] for s in plan.get("subtasks", [])]
    focus = "implementación" if "code" in subtask_ids else "investigación general"

    iteration = state.get("iteration", 0)
    critic_feedback = state.get("critic_feedback", "")
    critic_suggestions = state.get("critic_suggestions", {})
    quality_hint = ""
    if iteration > 0:
        parts = [f"Puntaje anterior: {state.get('critic_score', 0)}/100"]
        if critic_feedback:
            parts.append(f"Feedback: {critic_feedback}")
        agent_sugs = critic_suggestions.get("aletheia", []) or critic_suggestions.get("kosmos", [])
        my_sugs = critic_suggestions.get("aletheia", [])
        if my_sugs:
            parts.append("Sugerencias de mejora:")
            for s in my_sugs:
                parts.append(f"- {s}")
        if parts:
            quality_hint = "\n\n## Feedback de Iteración Anterior\n" + "\n".join(parts) + "\n"

    gaps_section = ""
    gap_iteration = state.get("gap_iteration", 0)
    pending_gaps = state.get("aletheia_pending_gaps", [])
    if gap_iteration > 0 and pending_gaps:
        gap_lines = "\n".join(f"- {g}" for g in pending_gaps[:5])
        gaps_section = (
            f"\n## Gaps de Conocimiento a Investigar (Iteración {gap_iteration})\n"
            f"{gap_lines}\n\n"
            f"Enfoca tu investigación en cubrir estos gaps específicos.\n"
        )

    prompt = (
        f"# Pipeline: Investigación\n\n"
        f"## Tema\n{topic}\n\n"
        f"## Perfil: {profile}\n"
        f"## Complejidad: {plan.get('complexity', 'desconocida')}\n"
        f"## Enfoque: {focus}\n"
        f"{quality_hint}"
        f"{gaps_section}"
        f"Investiga a fondo el tema. Busca fuentes, evidencia, análisis.\n"
        f"Produce un informe detallado en markdown con:\n"
        f"1. Resumen ejecutivo\n"
        f"2. Hallazgos clave (con fuentes)\n"
        f"3. Análisis detallado\n"
        f"4. Conclusiones y recomendaciones\n"
        f"5. El informe debe estar escrito en español.\n"
    )

    output_path = RAW_DIR / f"{slug}.md"
    output_path.write_text(prompt, encoding="utf-8")

    if LLM_DIRECT_ENABLED:
        notify_step(state, "Aletheia Research", "in_progress")
        enhanced = build_rag_context(topic) + "\n\n" + prompt
        try:
            raw = llm_or_executor_call("aletheia", enhanced)
        except Exception as e:
            raw = f"# Error en investigación: {e}\n\nFallo en todos los providers."
        if not raw or len(raw.strip()) < 100:
            raw = f"# ⚠️ Investigación incompleta: {topic}\n\nEl modelo no produjo contenido suficiente."
        output_path.write_text(raw, encoding="utf-8")
        ctx = load_context()
        ctx["agents"].append("aletheia")
        ctx["context_summary"]["aletheia"] = {
            "topic": topic, "profile": profile,
            "started_at": datetime.now().isoformat(),
        }
        ctx["cross_agent"]["aletheia_question"] = topic
        save_context(ctx)
        sources = list(set(re.findall(r'https?://[^\s\)\]>\"\']+', raw)))
        ctx["context_summary"]["aletheia"]["sources_used"] = sources
        save_context(ctx)
        notify_step(state, "Aletheia Research", "completed")
        try:
            from lib.viz_orchestrator import orchestrate as _viz
            _viz("aletheia", {"research_tree": raw})
        except Exception:
            pass
        if state.get("aletheia_pending_gaps"):
            from lib.quality import record_gap_feedback
            pending = state["aletheia_pending_gaps"]
            confirmed = sum(1 for g in pending if g.lower() in raw.lower())
            rejected = len(pending) - confirmed
            record_gap_feedback(topic, len(pending), confirmed, rejected)
        return {
            **state, "aletheia_output": raw, "aletheia_prompt": prompt,
            "gap_iteration": gap_iteration + 1,
            "aletheia_pending_gaps": [],
        }

    ctx = load_context()
    ctx["agents"].append("aletheia")
    ctx["context_summary"]["aletheia"] = {
        "topic": topic,
        "profile": profile,
        "started_at": datetime.now().isoformat(),
    }
    ctx["cross_agent"]["aletheia_question"] = topic
    save_context(ctx)

    try:
        from lib.viz_orchestrator import orchestrate as _viz
        _viz("aletheia", {"research_tree": topic})
    except Exception:
        pass

    if state.get("aletheia_pending_gaps"):
        from lib.quality import record_gap_feedback
        pending = state["aletheia_pending_gaps"]
        confirmed = sum(1 for g in pending if g.lower() in prompt.lower())
        rejected = len(pending) - confirmed
        record_gap_feedback(topic, len(pending), confirmed, rejected)

    return {
        **state,
        "aletheia_output": f"Prompt written to {output_path}",
        "aletheia_prompt": prompt,
        "gap_iteration": gap_iteration + 1,
        "aletheia_pending_gaps": [],
    }



