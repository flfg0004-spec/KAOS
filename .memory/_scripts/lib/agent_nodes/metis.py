import re
from datetime import datetime

from lib.agent_tools import (
    RAW_DIR,
    extract_json_from_output,
    llm_or_executor_call,
    load_context,
    notify_step,
    save_context,
    slugify,
)
from lib.config import LLM_DIRECT_ENABLED
from lib.feature_flags import is_enabled


def metis_node(state: dict) -> dict:
    if is_enabled("use_new_agent_executor"):
        return _metis_node_v2(state)
    return _metis_node_impl(state)


def _metis_node_impl(state: dict) -> dict:
    topic = state.get("topic", "")
    slug = slugify(topic)
    aletheia_out = state.get("aletheia_output", "") or ""
    kosmos_out = state.get("kosmos_output", "") or ""

    prompt = (
        f"# Pipeline: Estrategia\n\n"
        f"## Tema\n{topic}\n\n"
        f"## Contexto de Investigación\n"
        f"{aletheia_out[:2000]}\n\n"
        f"## Contexto Arquitectónico\n"
        f"{kosmos_out[:2000]}\n\n"
        f"## Metodología\n\n"
        f"### 1. Diagnóstico Estratégico (FODA)\n"
        f"- Fortalezas, Oportunidades, Debilidades, Amenazas\n"
        f"- Basado en la investigación y el análisis arquitectónico\n\n"
        f"### 2. Formulación de Objetivos y OKRs\n"
        f"- 2-3 objetivos estratégicos con baseline y target numérico\n"
        f"- Key Results medibles por objetivo\n\n"
        f"### 3. Roadmap 3 Horizontes\n"
        f"- H1 (táctico, 0-3 meses): acciones inmediatas\n"
        f"- H2 (estratégico, 3-6 meses): capacidades a desarrollar\n"
        f"- H3 (visión, 6-12 meses): transformación\n\n"
        f"### 4. Evaluación de Riesgos\n"
        f"- Matriz: probabilidad x impacto\n"
        f"- Mitigaciones explícitas por cada riesgo\n\n"
        f"### 5. Recomendaciones Priorizadas\n"
        f"- Impacto vs esfuerzo\n"
        f"- Quick wins identificados\n\n"
        f"## Formato de Salida\n"
        f"Responde SOLO con JSON:\n"
        f'{{"strategy": "...", '
        f'"okrs": [{{"objective": "...", "key_results": ["..."]}}], '
        f'"risks": [{{"risk": "...", "probability": "alta|media|baja", '
        f'"impact": "alto|medio|bajo", "mitigation": "..."}}], '
        f'"confidence": "alta|media|baja"}}\n'
    )

    output_path = RAW_DIR / f"{slug}-strategy.md"
    output_path.write_text(prompt, encoding="utf-8")

    if LLM_DIRECT_ENABLED:
        notify_step(state, "Metis Strategy + Devil's Advocate", "in_progress")
        combined_prompt = (
            f"{prompt}\n\n"
            f"## Auto-Crítica y Refinamiento\n"
            f"Después de generar la estrategia, haz lo siguiente:\n"
            f"1. **Auto-crítica (Devil's Advocate)**: Cuestiona tu propia estrategia.\n"
            f"   - Supuestos débiles o no verificados\n"
            f"   - Perspectivas alternativas no consideradas\n"
            f"   - Riesgos no mencionados\n"
            f"   - Sesgos de confirmación\n"
            f"   - Qué falta para que sea ejecutable\n"
            f"2. **Refina**: Incorpora la crítica en una versión mejorada.\n\n"
            f"## Formato de Salida\n"
            f"Responde con JSON con esta estructura EXACTA:\n"
            f'{{\n'
            f'  "critique": "tu analisis Devil_s Advocate...",\n'
            f'  "strategy": "versión refinada de la estrategia...",\n'
            f'  "okrs": [{{"objective": "...", "key_results": ["..."]}}],\n'
            f'  "risks": [{{"risk": "...", "probability": "alta|media|baja", "impact": "alto|medio|bajo", "mitigation": "..."}}],\n'
            f'  "confidence": "alta|media|baja"\n'
            f'}}\n'
            f'Usa \\n para saltos de línea dentro de strings.'
        )
        combined = llm_or_executor_call("metis", combined_prompt, step_type="analysis")
        output_path.write_text(combined, encoding="utf-8")

        parsed = extract_json_from_output(combined)
        raw_strategy = parsed.get("strategy", "") if isinstance(parsed, dict) else combined
        okrs = parsed.get("okrs", []) if isinstance(parsed, dict) else []
        risks = parsed.get("risks", []) if isinstance(parsed, dict) else []
        confidence = parsed.get("confidence", "media") if isinstance(parsed, dict) else "media"
        critique = parsed.get("critique", "") if isinstance(parsed, dict) else ""
        final_output = raw_strategy if raw_strategy else combined

        critique_path = RAW_DIR / f"{slug}-critique.md"
        critique_path.write_text(critique, encoding="utf-8")
        refined_path = RAW_DIR / f"{slug}-strategy-refined.md"
        refined_path.write_text(final_output, encoding="utf-8")

        gaps_identified = []
        critique_lower = critique.lower()
        gap_patterns = [
            r"(?:gap|falta|missing|falta|carece|debilidad)\s*:?\s*([^\n.]+)",
            r"(?:no se consideró|no se mencionó|no se analizó|not considered|not analyzed)\s*:?\s*([^\n.]+)",
            r"(?:supuesto débil|weak assumption)\s*:?\s*([^\n.]+)",
        ]
        for pat in gap_patterns:
            matches = re.findall(pat, critique_lower)
            gaps_identified.extend(m.strip() for m in matches if len(m.strip()) > 10)
        gaps_identified = list(set(gaps_identified))[:5]

        initiatives = []
        kr_assignment = {}
        execution_plan = {}
        if okrs:
            try:
                from lib.strategy_tools import assign_krs, build_execution_plan, scope_initiatives
                initiatives = scope_initiatives(okrs, topic)
                kr_assignment = assign_krs(okrs, initiatives)
                execution_plan = build_execution_plan(okrs, initiatives, kr_assignment)
            except Exception:
                pass

        ctx = load_context()
        ctx["agents"].append("metis")
        ctx["context_summary"]["metis"] = {"started_at": datetime.now().isoformat()}
        ctx["cross_agent"]["metis_to_kratos"] = {
            "strategy_summary": final_output[:500],
            "okrs": okrs,
            "risks": risks,
            "confidence": confidence,
            "priority": "high",
            "initiatives": initiatives,
            "kr_assignment": kr_assignment,
            "execution_plan": execution_plan,
        }
        ctx["cross_agent"]["metis_to_aletheia"] = {
            "strategy_summary": final_output[:500],
            "confidence": confidence,
            "gaps_identified": gaps_identified,
            "generated_at": datetime.now().isoformat(),
        }
        save_context(ctx)
        notify_step(state, "Metis Strategy", "completed")
        try:
            from lib.viz_orchestrator import orchestrate as _viz
            _viz("metis", {"domain_clusters": final_output})
        except Exception:
            pass
        return {**state, "metis_output": final_output, "metis_prompt": prompt}

    ctx = load_context()
    ctx["agents"].append("metis")
    ctx["context_summary"]["metis"] = {
        "started_at": datetime.now().isoformat(),
    }
    ctx["cross_agent"]["metis_to_kratos"] = {
        "strategy_summary": topic,
        "okrs": [],
        "risks": [],
        "confidence": "media",
        "priority": "high",
    }
    ctx["cross_agent"]["metis_to_aletheia"] = {
        "strategy_summary": topic,
        "confidence": "media",
        "gaps_identified": [],
        "generated_at": datetime.now().isoformat(),
    }
    save_context(ctx)

    try:
        from lib.viz_orchestrator import orchestrate as _viz
        _viz("metis", {"domain_clusters": topic})
    except Exception:
        pass

    return {
        **state,
        "metis_output": f"Strategy prompt written to {output_path}",
        "metis_prompt": prompt,
    }


def _metis_node_v2(state: dict) -> dict:
    return _metis_node_impl(state)
