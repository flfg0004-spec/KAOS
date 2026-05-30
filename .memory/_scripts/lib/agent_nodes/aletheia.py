import os
import logging
import re
from datetime import datetime

logger = logging.getLogger("aletheia")

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

try:
    from aletheia_router import PROFILES, classify_query
    _HAS_ROUTER = True
except ImportError:
    logger.debug("aletheia_router not available, using fallback")
    _HAS_ROUTER = False
    PROFILES = {}

try:
    from lib.gap_query import query_gaps
    _HAS_GAPS = True
except ImportError:
    logger.debug("lib.gap_query not available")
    _HAS_GAPS = False


def _scope_phase(state: dict) -> dict:
    topic = state.get("topic", "")
    if not topic:
        return state

    profile = state.get("profile", "")
    if not profile or profile == "desarrollo":
        if _HAS_ROUTER:
            profile, confidence, _ = classify_query(topic)
            state["profile"] = profile
            state["profile_confidence"] = confidence
        else:
            profile = "standard"
            state["profile"] = profile

    profile_cfg = PROFILES.get(profile, {})

    # 1. Research brief
    brief = {
        "topic": topic,
        "profile": profile,
        "sub_questions": _generate_sub_questions(topic, profile),
        "tools": profile_cfg.get("tools", []),
        "output_format": profile_cfg.get("output_format", "markdown"),
        "estimated_duration": profile_cfg.get("duration", "30-60 min"),
        "generated_at": datetime.now().isoformat(),
    }
    state["research_brief"] = brief

    # 2. Pre-consult Mnemosyne gaps
    if _HAS_GAPS and not os.environ.get("KAOS_TESTING") == "1":
        try:
            gaps = query_gaps(topic)
            state["gaps_pre"] = gaps
            if gaps.get("existing_concepts"):
                state["existing_concepts"] = [c["name"] for c in gaps["existing_concepts"][:5]]
            if gaps.get("gaps_detected"):
                state["aletheia_pending_gaps"] = [g["reason"][:100] for g in gaps["gaps_detected"][:3]]
        except Exception as e:
            logger.warning("Gap query failed: %s", e)

    # 3. Pre-consult vault context
    if os.environ.get("KAOS_TESTING") != "1":
        try:
            vault_context = build_rag_context(topic)
            state["vault_context"] = vault_context
        except Exception as e:
            state["vault_context"] = ""
            logger.warning("Vault context failed: %s", e)
        state["vault_context"] = ""

    return state


def _generate_sub_questions(topic: str, profile: str) -> list:
    base = [
        f"¿Cuál es el estado actual de {topic}?",
        f"¿Cuáles son las fuentes principales sobre {topic}?",
    ]
    if profile in ("deep", "massive", "estrategico"):
        return [
            f"¿Cuál es el estado del arte en {topic}?",
            f"¿Qué controversias o debates existen sobre {topic}?",
            "¿Cuáles son las fuentes primarias y secundarias?",
            f"¿Qué tendencias futuras se identifican en {topic}?",
            f"¿Qué implicaciones prácticas tiene {topic}?",
        ]
    if profile == "flash":
        return [f"¿Cuál es la respuesta concisa sobre {topic}?"]
    return base


def aletheia_node(state: dict) -> dict:
    state = _scope_phase(state)
    return _aletheia_node_impl(state)


def _aletheia_node_impl(state: dict) -> dict:
    topic = state.get("topic", "")
    slug = slugify(topic)
    profile = state.get("profile", "")
    if not profile or profile == "desarrollo":
        if _HAS_ROUTER and topic:
            profile, confidence, _ = classify_query(topic)
        else:
            profile = "standard"
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

    # Scope phase data
    brief = state.get("research_brief", {})
    brief_section = ""
    if brief:
        sq = brief.get("sub_questions", [])
        if sq:
            sq_lines = "\n".join(f"{i+1}. {q}" for i, q in enumerate(sq))
            brief_section = f"\n## Sub-preguntas a Investigar\n{sq_lines}\n"

    existing = state.get("existing_concepts", [])
    existing_section = ""
    if existing:
        existing_section = "\n## Conceptos Existentes en el Vault\n" + "\n".join(f"- {c}" for c in existing) + "\n"

    prompt = (
        f"# Pipeline: Investigación\n\n"
        f"## Tema\n{topic}\n\n"
        f"## Perfil: {profile}\n"
        f"## Complejidad: {plan.get('complexity', 'desconocida')}\n"
        f"## Enfoque: {focus}\n"
        f"{brief_section}"
        f"{existing_section}"
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
        state = _synthesis_phase(state, raw)
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
        except Exception as e:
            logger.debug("Viz orchestrate skipped: %s", e)
        if state.get("aletheia_pending_gaps"):
            from lib.quality.agent import record_gap_feedback
            pending = state["aletheia_pending_gaps"]
            confirmed = sum(1 for g in pending if g.lower() in raw.lower())
            rejected = len(pending) - confirmed
            record_gap_feedback(topic, len(pending), confirmed, rejected)
        return {
            **state, "aletheia_output": raw, "aletheia_prompt": prompt,
            "gap_iteration": gap_iteration + 1,
            "aletheia_pending_gaps": [],
            "synthesis": state.get("synthesis", {}),
            "confidence_matrix": state.get("confidence_matrix", {}),
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
    except Exception as e:
        logger.debug("Viz orchestrate skipped: %s", e)

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
        "synthesis": state.get("synthesis", {}),
        "confidence_matrix": state.get("confidence_matrix", {}),
    }


REQUIRED_SECTIONS = [
    "resumen ejecutivo",
    "hallazgos",
    "fuentes",
    "conclusiones",
    "recomendaciones",
]


def _synthesis_phase(state: dict, raw: str) -> dict:
    sections = _parse_sections(raw)
    confidence_matrix = _build_confidence_matrix(raw)
    faithfulness = _faithfulness_check(raw)

    # Build structured output
    structured = {
        "sections_found": list(sections.keys()),
        "sections_missing": [s for s in REQUIRED_SECTIONS if s not in sections],
        "confidence_matrix": confidence_matrix,
        "faithfulness": faithfulness,
        "sources_count": len(re.findall(r'https?://[^\s\)\]>\"\']+', raw)),
        "has_wikilinks": "[[" in raw,
        "total_length": len(raw.strip()),
    }
    state["synthesis"] = structured
    state["confidence_matrix"] = confidence_matrix

    try:
        from lib.quality.agent import record as qa_record
        qa_record("aletheia", raw, topic=state.get("topic", ""), pipeline_id=state.get("pipeline_id", ""), task_prompt=state.get("topic", ""))
    except Exception as e:
        logger.warning("Quality record failed: %s", e)

    return state


def _parse_sections(raw: str) -> dict:
    sections = {}
    current_section = None
    current_lines = []
    for line in raw.split("\n"):
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = line[3:].strip().lower()
            current_lines = []
        else:
            current_lines.append(line)
    if current_section:
        sections[current_section] = "\n".join(current_lines).strip()
    return sections


def _build_confidence_matrix(raw: str) -> dict:
    has_urls = bool(re.findall(r'https?://[^\s\)\]>\"\']+', raw))
    has_wikilinks = "[[" in raw
    has_sections = sum(1 for s in REQUIRED_SECTIONS if s in raw.lower())
    length_ok = len(raw.strip()) > 500

    confidence = "alta" if (has_urls and has_wikilinks and has_sections >= 4 and length_ok) else \
                 "media" if (has_urls and has_sections >= 3) else \
                 "baja"
    return {
        "overall": confidence,
        "signals": {
            "has_urls": has_urls,
            "has_wikilinks": has_wikilinks,
            "sections_present": has_sections,
            "length_ok": length_ok,
        }
    }


def _faithfulness_check(raw: str) -> dict:
    claims = re.findall(r'(?:(?:Afirmación|Claim|Hallazgo|Finding)[^.]*\.)', raw)
    claims_with_source = 0
    for claim in claims:
        if re.findall(r'https?://[^\s\)\]>\"\']+', claim) or "[[" in claim:
            claims_with_source += 1
    words = raw.split()
    urls = re.findall(r'https?://[^\s\)\]>\"\']+', raw)
    source_density = round(len(urls) / (len(words) / 500), 2) if len(words) > 100 else 0
    evidential_verbs = r'\b(demuestra|confirma|sugiere|indica|prueba|evidencia|concluye|establece|muestra|revela)\b'
    sentences = re.split(r'[.!?]+', raw)
    claims_without_source = 0
    for s in sentences:
        s = s.strip()
        if len(s) > 20 and re.search(evidential_verbs, s, re.IGNORECASE):
            if not re.findall(r'https?://[^\s\)\]>\"\']+', s):
                claims_without_source += 1
    return {
        "total_claims": len(claims),
        "claims_with_source": claims_with_source,
        "faithfulness_score": round(claims_with_source / max(len(claims), 1), 2),
        "source_density": source_density,
        "claims_without_source": claims_without_source,
    }

