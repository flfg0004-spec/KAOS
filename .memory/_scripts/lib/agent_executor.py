"""Agent Executor — real node functions for LangGraph DAG.

Each function:
  1. Builds agent prompt from accumulated state
  2. Writes input files for the agent
  3. Updates context.json for cross-agent memory
  4. Returns augmented KAOSState
"""
import json
import logging
import re
import subprocess
import tempfile
from datetime import datetime
from functools import lru_cache

logger = logging.getLogger("agent_executor")

from lib.config import EXECUTOR_ENABLED, EXECUTOR_TIMEOUT, HERMES_ENABLED, LLM_DIRECT_ENABLED, RAG_ENABLED, VAULT_ROOT
from lib.hermes_bridge import pipeline_notify
from lib.rag_injector import inject_context

RAW_DIR = VAULT_ROOT / "_pipeline" / "raw"
CONTEXT_PATH = VAULT_ROOT / "_pipeline" / "context.json"
PLAN_PATH = VAULT_ROOT / "_pipeline" / "plan.json"

RAW_DIR.mkdir(parents=True, exist_ok=True)

_ctx_cache: dict | None = None
_ctx_dirty: bool = False

AGENT_SLUGS = {
    "aletheia": "raw",
    "kosmos": "schema",
    "metis": "wiki",
    "kratos": "code",
    "mnemosyne": "wiki",
}

COMPLEXITY_KEYWORDS = {
    "alta": ["microservicio", "distribuido", "escalable", "cluster", "kubernetes",
             "orquestacion", "eventos", "cqrs", "event-sourcing", "multi-tenant",
             "alta disponibilidad", "ha", "failover", "replicacion"],
    "moderada": ["api", "rest", "graphql", "base de datos", "autenticacion", "jwt",
                 "oauth", "cache", "cola", "middleware", "testing", "ci/cd"],
    "simple": ["script", "funcion", "componente", "vista", "formulario",
               "pagina", "endpoint", "consulta", "archivo"],
}

SUBTASK_PATTERNS = [
    ("research", "investigacion", "research", "analisis", "requerimientos", "estudio", "explorar"),
    ("architecture", "arquitectura", "adr", "c4", "diseno", "disenar", "estructura",
     "patron", "patrones", "microservicio", "distribuido", "escalable"),
    ("strategy", "estrategia", "roadmap", "okr", "plan", "planeacion", "hoja de ruta"),
    ("code", "implementacion", "codigo", "programar", "desarrollar", "implementa",
     "implementar", "construir", "crear", "hacer", "api", "rest", "endpoint",
     "funcion", "clase", "modulo", "script", "algoritmo"),
    ("test", "test", "testing", "pruebas", "unit", "integracion"),
    ("docs", "documentacion", "docs", "wiki", "readme", "manual"),
]


def _slugify(text: str) -> str:
    slug = re.sub(r'[^a-z0-9\s-]', '', text.lower())
    return re.sub(r'\s+', '-', slug)[:60]


def _load_context() -> dict:
    global _ctx_cache
    if _ctx_cache is not None:
        return _ctx_cache
    if CONTEXT_PATH.exists():
        try:
            _ctx_cache = json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
            return _ctx_cache
        except Exception:
            pass
    _ctx_cache = {"agents": [], "context_summary": {}, "cross_agent": {}}
    return _ctx_cache


def _save_context(ctx: dict) -> None:
    global _ctx_cache, _ctx_dirty
    _ctx_cache = ctx
    _ctx_dirty = True


def _flush_context() -> None:
    global _ctx_dirty
    if _ctx_cache is not None and _ctx_dirty:
        CONTEXT_PATH.write_text(json.dumps(_ctx_cache, indent=2, ensure_ascii=False), encoding="utf-8")
        _ctx_dirty = False


def _reset_context_cache() -> None:
    global _ctx_cache, _ctx_dirty
    _ctx_cache = None
    _ctx_dirty = False


def _detect_subtasks(topic: str) -> list[dict]:
    """Detect subtasks from topic text."""
    tl = topic.lower()
    detected = []
    for task_id, name, *keywords in SUBTASK_PATTERNS:
        if any(kw in tl for kw in [name] + keywords):
            detected.append({"id": task_id, "name": name, "enabled": True})
    if not detected:
        detected = [{"id": "research", "name": "research", "enabled": True}]
    return detected


def _detect_complexity(topic: str) -> str:
    """Detect complexity level from topic."""
    tl = topic.lower()
    weights = {"alta": 0, "moderada": 0, "simple": 0}
    for level, keywords in COMPLEXITY_KEYWORDS.items():
        weights[level] = sum(1 for kw in keywords if kw in tl)
    return max(weights, key=weights.get)


def _executor_call(prompt: str, agent_name: str, model_override: str = "") -> str:
    """Invoke opencode CLI subprocess as the agent executor."""
    try:
        if len(prompt) > 7000:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False, encoding="utf-8"
            ) as f:
                f.write(prompt)
                tmp = f.name
            result = subprocess.run(
                ["opencode", "-p", tmp],
                capture_output=True, text=True, timeout=EXECUTOR_TIMEOUT
            )
        else:
            result = subprocess.run(
                ["opencode", "-p", prompt],
                capture_output=True, text=True, timeout=EXECUTOR_TIMEOUT
            )
        output = result.stdout.strip()
        if output:
            return output
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    from lib.llm import agent_llm_call
    return agent_llm_call(agent_name, prompt, model_override=model_override)

def _llm_or_executor_call(agent_name: str, prompt: str, model_override: str = "", step_type: str = None) -> str:
    """Route: executor → LLM, with optional model override and step type."""
    if EXECUTOR_ENABLED:
        return _executor_call(prompt, agent_name, model_override)
    kwargs = {}
    if model_override:
        kwargs["model_override"] = model_override
    if step_type:
        kwargs["step_type"] = step_type
    return _call_with_langfuse(agent_name, prompt, **kwargs)


def _call_with_langfuse(agent_name: str, prompt: str, trace_id: str = "", **kwargs):
    """Execute LLM call with Langfuse tracing."""
    from lib.llm import agent_llm_call
    
    try:
        handler = getattr(__import__('lib.orchestrator', fromlist=['_LANGFUSE_HANDLER']), '_LANGFUSE_HANDLER', None)
        if handler:
            return agent_llm_call(agent_name, prompt, langfuse_handler=handler, **kwargs)
    except Exception:
        logger.warning("Langfuse handler not available, proceeding without tracing")
    return agent_llm_call(agent_name, prompt, **kwargs)


@lru_cache(maxsize=50)
def _cached_rag(topic: str) -> str:
    return inject_context(topic)

def _build_rag_context(topic: str) -> str:
    if not RAG_ENABLED:
        return ""
    try:
        return _cached_rag(topic)
    except Exception:
        logger.warning("RAG context injection failed, proceeding without RAG context")
        return ""

def _notify_step(state, agent_name: str, status: str = "in_progress"):
    if HERMES_ENABLED:
        pipeline_notify(state, agent_name, status)

def planner_node(state: dict) -> dict:
    topic = state.get("topic", "")
    profile = state.get("profile", "standard")
    slug = _slugify(topic)

    if LLM_DIRECT_ENABLED:
        _notify_step(state, "Planner", "in_progress")
        plan_prompt = (
            f"Descompón esta tarea en subtasks: {topic}\n\n"
            f"Perfil: {profile}\n"
            f"Responde SOLO con JSON:\n"
            f'{{"subtasks":[{{"id":"research|architecture|strategy|code|test|docs","name":"..."}}],'
            f'"complexity":"simple|moderada|alta","has_code":true|false}}'
        )
        raw = _llm_or_executor_call("planner", plan_prompt)
        import json as _json
        try:
            plan_data = _json.loads(raw.strip().strip("```json").strip("```").strip())
        except Exception:
            plan_data = {}
        subtasks = plan_data.get("subtasks", _detect_subtasks(topic))
        complexity = plan_data.get("complexity", _detect_complexity(topic))
        has_code = plan_data.get("has_code", any(s["id"] in ("code", "test") for s in subtasks))
        _notify_step(state, "Planner", "completed")
    else:
        subtasks = _detect_subtasks(topic)
        complexity = _detect_complexity(topic)
        has_code = any(s["id"] in ("code", "test") for s in subtasks)

    parallelizable = len(subtasks) > 1
    plan = {
        "topic": topic,
        "slug": slug,
        "profile": profile,
        "complexity": complexity,
        "subtasks": subtasks,
        "has_code": has_code,
        "parallelizable": parallelizable,
        "estimated_steps": len(subtasks) + 2,
        "created_at": datetime.now().isoformat(),
        "status": "planned",
    }

    PLAN_PATH.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    ctx = _load_context()
    ctx["agents"] = []
    ctx["context_summary"] = {"planner": plan}
    ctx["cross_agent"] = {"plan": plan}
    _save_context(ctx)

    return {
        **state,
        "plan": plan,
        "has_code_subtasks": has_code,
        "iteration": 0,
    }


def aletheia_node(state: dict) -> dict:
    topic = state.get("topic", "")
    slug = _slugify(topic)
    profile = state.get("profile", "standard")
    plan = state.get("plan", {})
    subtask_ids = [s["id"] for s in plan.get("subtasks", [])]
    focus = "implementación" if "code" in subtask_ids else "investigación general"

    # Quality Loop: inject critic feedback + suggestions from previous iteration
    iteration = state.get("iteration", 0)
    critic_feedback = state.get("critic_feedback", "")
    critic_suggestions = state.get("critic_suggestions", {})
    quality_hint = ""
    if iteration > 0:
        parts = [f"Puntaje anterior: {state.get('critic_score', 0)}/100"]
        if critic_feedback:
            parts.append(f"Feedback: {critic_feedback}")
        # Add structured suggestions for this agent if available
        agent_sugs = critic_suggestions.get("aletheia", []) or critic_suggestions.get("kosmos", [])
        my_sugs = critic_suggestions.get("aletheia", [])
        if my_sugs:
            parts.append("Sugerencias de mejora:")
            for s in my_sugs:
                parts.append(f"- {s}")
        if parts:
            quality_hint = "\n\n## Feedback de Iteración Anterior\n" + "\n".join(parts) + "\n"

    # Gap-driven re-research: inject gaps from BCG evaluation
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
    )
    
    output_path = RAW_DIR / f"{slug}.md"
    output_path.write_text(prompt, encoding="utf-8")

    if LLM_DIRECT_ENABLED:
        _notify_step(state, "Aletheia Research", "in_progress")
        enhanced = _build_rag_context(topic) + "\n\n" + prompt
        raw = _llm_or_executor_call("aletheia", enhanced)
        output_path.write_text(raw, encoding="utf-8")
        ctx = _load_context()
        ctx["agents"].append("aletheia")
        ctx["context_summary"]["aletheia"] = {
            "topic": topic, "profile": profile,
            "started_at": datetime.now().isoformat(),
        }
        ctx["cross_agent"]["aletheia_question"] = topic
        _save_context(ctx)
        sources = re.findall(r'(?:fuente|source|ref)\s*:?\s*(https?://\S+)', raw, re.IGNORECASE)
        ctx["context_summary"]["aletheia"]["sources_used"] = sources
        _save_context(ctx)
        _notify_step(state, "Aletheia Research", "completed")
        # Increment gap_iteration for gap-driven re-research routing
        new_gap_iter = gap_iteration + 1 if gap_iteration > 0 else gap_iteration
        return {
            **state, "aletheia_output": raw, "aletheia_prompt": prompt,
            "gap_iteration": new_gap_iter,
            "aletheia_pending_gaps": [],
        }
    
    ctx = _load_context()
    ctx["agents"].append("aletheia")
    ctx["context_summary"]["aletheia"] = {
        "topic": topic,
        "profile": profile,
        "started_at": datetime.now().isoformat(),
    }
    ctx["cross_agent"]["aletheia_question"] = topic
    _save_context(ctx)
    
    new_gap_iter = gap_iteration + 1 if gap_iteration > 0 else gap_iteration
    return {
        **state,
        "aletheia_output": f"Prompt written to {output_path}",
        "aletheia_prompt": prompt,
        "gap_iteration": new_gap_iter,
        "aletheia_pending_gaps": [],
    }

def kosmos_node(state: dict) -> dict:
    """KosmosV2 pipeline node — delegada a kosmos/agent_node.py (D5)."""
    from lib.kosmos.agent_node import kosmos_node as _impl
    return _impl(state)

def _extract_json_from_output(text: str) -> dict:
    """Try to extract JSON object from agent output."""
    import json as _json
    # Try direct parse first
    try:
        return _json.loads(text)
    except Exception:
        pass
    # Try between ```json markers
    m = __import__("re").search(r'```(?:json)?\s*\n?(.*?)```', text, __import__("re").DOTALL)
    if m:
        try:
            return _json.loads(m.group(1).strip())
        except Exception:
            pass
    return {}


def metis_node(state: dict) -> dict:
    topic = state.get("topic", "")
    slug = _slugify(topic)
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
        _notify_step(state, "Metis Strategy + Devil's Advocate", "in_progress")
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
        combined = _llm_or_executor_call("metis", combined_prompt, step_type="analysis")
        output_path.write_text(combined, encoding="utf-8")

        parsed = _extract_json_from_output(combined)
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

        # ── Extract knowledge gaps from Devil's Advocate critique ──
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

        # ── Decompose OKRs into initiatives ──
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
                logger.warning("strategy_tools not available, skipping initiative/KR planning")

        ctx = _load_context()
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
        _save_context(ctx)
        _notify_step(state, "Metis Strategy", "completed")
        return {**state, "metis_output": final_output, "metis_prompt": prompt}
    
    ctx = _load_context()
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
    _save_context(ctx)
    
    return {
        **state,
        "metis_output": f"Strategy prompt written to {output_path}",
        "metis_prompt": prompt,
    }

# Backward-compatible re-exports (canonical implementations live in agent_nodes/)

def kratos_node(state: dict) -> dict:
    """Delegates to canonical kratos_node in agent_nodes/kratos.py."""
    from lib.agent_nodes.kratos import kratos_node as _kratos_node
    return _kratos_node(state)


def mnemosyne_node(state: dict) -> dict:
    """Delegates to the unified curation pipeline (lib/curation_pipeline.py).

    Runs 5 phases: discover → score → synthesize → lint → report.
    Controlled by feature flags use_knowledge_scorer and use_knowledge_synthesis.
    Falls back to LLM prompt if pipeline is unavailable.
    """
    try:
        from lib.curation_pipeline import mnemosyne_curation_node
        return mnemosyne_curation_node(state)
    except ImportError as e:
        logger.warning("Curation pipeline not available, falling back to LLM prompt: %s", e)
    except Exception as e:
        logger.error("Curation pipeline failed, falling back to LLM prompt: %s", e)
    topic = state.get("topic", "")
    slug = _slugify(topic)
    prompt = (
        f"# Pipeline: Curación\n\n"
        f"## Tema\n{topic}\n\n"
        f"## Salidas a Curar\n\n"
        f"1. Investigación: raw/{slug}.md\n"
    )
    output_path = RAW_DIR / f"{slug}-curation.md"
    output_path.write_text(prompt, encoding="utf-8")
    if LLM_DIRECT_ENABLED:
        _notify_step(state, "Mnemosyne Curation", "in_progress")
        raw = _llm_or_executor_call("mnemosyne", prompt)
        output_path.write_text(raw, encoding="utf-8")
        ctx = _load_context()
        ctx["agents"].append("mnemosyne")
        ctx["context_summary"]["mnemosyne"] = {"started_at": datetime.now().isoformat()}
        _save_context(ctx)
        _notify_step(state, "Mnemosyne Curation", "completed")
        return {**state, "mnemosyne_output": raw, "mnemosyne_prompt": prompt}
    ctx = _load_context()
    ctx["agents"].append("mnemosyne")
    ctx["context_summary"]["mnemosyne"] = {"started_at": datetime.now().isoformat()}
    _save_context(ctx)
    return {
        **state,
        "mnemosyne_output": f"Curation prompt written to {output_path}",
        "mnemosyne_prompt": prompt,
    }
    _save_context(ctx)
    
    return {
        **state,
        "mnemosyne_output": f"Curation prompt written to {output_path}",
        "mnemosyne_prompt": prompt,
    }


def bcg_evaluator_node(state: dict) -> dict:
    """BCG Evaluation of strategy output — 8 dimensions + OKR checklist.

    Evaluate metis_output using the BCG rubric. Stores scores in state.
    Also evaluates OKRs if present in cross_agent context.
    """
    metis_output = state.get("metis_output", "") or ""
    if not metis_output:
        return {**state, "bcg_score": 0, "bcg_passed": False, "bcg_details": {}}

    try:
        from lib.bcg_evaluator import evaluate_okrs, evaluate_strategy
        bcg = evaluate_strategy(metis_output)

        okr_result = {}
        try:
            ctx = _load_context()
            metis_data = ctx.get("cross_agent", {}).get("metis_to_kratos", {})
            if not isinstance(metis_data, dict):
                metis_data = {}
            okrs = metis_data.get("okrs", [])
            if okrs:
                okr_result = evaluate_okrs(okrs)
        except Exception:
            logger.warning("OKR evaluation failed, proceeding without OKR quality assessment")
            okr_result = {}

        # Track to strategy analytics timeseries
        try:
            from lib.strategy_analytics import track_bcg as _track
            _track({**state, "bcg_score": bcg.get("total_score_10", 0),
                     "bcg_passed": bcg.get("passed", False),
                     "bcg_details": bcg,
                     "okr_quality": okr_result})
        except Exception:
            logger.warning("strategy_analytics tracking failed, skipping")

        # Detect knowledge gaps from critique context
        try:
            ctx = _load_context()
            metis_feedback = ctx.get("cross_agent", {}).get("metis_to_aletheia", {})
            gaps = metis_feedback.get("gaps_identified", [])
        except Exception:
            logger.warning("Failed to extract knowledge gaps from context")
            gaps = []

        return {
            **state,
            "bcg_score": bcg.get("total_score_10", 0),
            "bcg_passed": bcg.get("passed", False),
            "bcg_details": bcg,
            "okr_quality": okr_result,
            "aletheia_pending_gaps": gaps,
        }
    except Exception as e:
        return {**state, "bcg_score": 0, "bcg_passed": False, "bcg_details": {"error": str(e)}}
