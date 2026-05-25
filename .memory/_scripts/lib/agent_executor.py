"""Agent Executor — real node functions for LangGraph DAG.

Each function:
  1. Builds agent prompt from accumulated state
  2. Writes input files for the agent
  3. Updates context.json for cross-agent memory
  4. Returns augmented KAOSState
"""
import json, re, os, subprocess, tempfile
from datetime import datetime
from pathlib import Path

from lib.config import LLM_DIRECT_ENABLED, EXECUTOR_ENABLED, RAG_ENABLED, HERMES_ENABLED, EXECUTOR_TIMEOUT
from lib.llm import agent_llm_call
from lib.rag_injector import inject_context
from lib.hermes_bridge import pipeline_notify

_RAG_CACHE: dict[str, str] = {}  # topic → RAG context

ROOT = Path(__file__).resolve().parent.parent.parent
VAULT = ROOT
RAW_DIR = VAULT / "_pipeline" / "raw"
CONTEXT_PATH = VAULT / "_pipeline" / "context.json"
PLAN_PATH = VAULT / "_pipeline" / "plan.json"

RAW_DIR.mkdir(parents=True, exist_ok=True)

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
    if CONTEXT_PATH.exists():
        try:
            return json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"agents": [], "context_summary": {}, "cross_agent": {}}


def _save_context(ctx: dict) -> None:
    CONTEXT_PATH.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding="utf-8")


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


def _executor_call(prompt: str, agent_name: str) -> str:
    """Invoke opencode CLI subprocess as the agent executor.

    Writes prompt to tempfile (avoids Windows CLI arg limit of 8191 chars),
    runs `opencode -p`, captures stdout. Falls back to LLM on error or timeout.
    """
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
    return agent_llm_call(agent_name, prompt)

def _llm_or_executor_call(agent_name: str, prompt: str) -> str:
    """Route: executor → LLM, according to feature flags."""
    if EXECUTOR_ENABLED:
        return _executor_call(prompt, agent_name)
    return agent_llm_call(agent_name, prompt)

def _build_rag_context(topic: str) -> str:
    if not RAG_ENABLED:
        return ""
    if topic in _RAG_CACHE:
        return _RAG_CACHE[topic]
    ctx = inject_context(topic)
    _RAG_CACHE[topic] = ctx
    return ctx

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

    prompt = (
        f"# Pipeline: Investigación\n\n"
        f"## Tema\n{topic}\n\n"
        f"## Perfil: {profile}\n"
        f"## Complejidad: {plan.get('complexity', 'desconocida')}\n"
        f"## Enfoque: {focus}\n"
        f"{quality_hint}"
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
        return {
            **state, "aletheia_output": raw, "aletheia_prompt": prompt,
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
    
    return {
        **state,
        "aletheia_output": f"Prompt written to {output_path}",
        "aletheia_prompt": prompt,
    }

def kosmos_node(state: dict) -> dict:
    topic = state.get("topic", "")
    slug = _slugify(topic)
    aletheia_output = state.get("aletheia_output", "")
    
    sources_summary = ""
    ctx = _load_context()
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
        _notify_step(state, "Kosmos Architecture", "in_progress")
        enhanced = _build_rag_context(topic) + "\n\n" + prompt
        raw = _llm_or_executor_call("kosmos", enhanced)
        output_path.write_text(raw, encoding="utf-8")
        ctx = _load_context()
        ctx["agents"].append("kosmos")
        ctx["context_summary"]["kosmos"] = {"started_at": datetime.now().isoformat()}
        _save_context(ctx)
        _notify_step(state, "Kosmos Architecture", "completed")
        return {**state, "kosmos_output": raw, "kosmos_prompt": prompt}
    
    ctx["agents"].append("kosmos")
    ctx["context_summary"]["kosmos"] = {
        "started_at": datetime.now().isoformat(),
    }
    _save_context(ctx)
    
    return {
        **state,
        "kosmos_output": f"ADR prompt written to {output_path}",
        "kosmos_prompt": prompt,
    }

def metis_node(state: dict) -> dict:
    topic = state.get("topic", "")
    slug = _slugify(topic)
    
    prompt = (
        f"# Pipeline: Estrategia\n\n"
        f"## Tema\n{topic}\n\n"
        f"Sintetiza la investigación y el análisis arquitectónico "
        f"en un plan estratégico accionable.\n\n"
        f"Produce:\n"
        f"1. Resumen estratégico\n"
        f"2. OKRs y roadmap\n"
        f"3. Recomendaciones priorizadas\n"
        f"4. Riesgos y mitigaciones\n"
    )
    
    output_path = RAW_DIR / f"{slug}-strategy.md"
    output_path.write_text(prompt, encoding="utf-8")

    if LLM_DIRECT_ENABLED:
        _notify_step(state, "Metis Strategy", "in_progress")
        raw = _llm_or_executor_call("metis", prompt)
        output_path.write_text(raw, encoding="utf-8")
        ctx = _load_context()
        ctx["agents"].append("metis")
        ctx["context_summary"]["metis"] = {"started_at": datetime.now().isoformat()}
        ctx["cross_agent"]["metis_to_kratos"] = {"strategy_summary": raw[:500], "priority": "high"}
        _save_context(ctx)
        _notify_step(state, "Metis Strategy", "completed")
        return {**state, "metis_output": raw, "metis_prompt": prompt}
    
    ctx = _load_context()
    ctx["agents"].append("metis")
    ctx["context_summary"]["metis"] = {
        "started_at": datetime.now().isoformat(),
    }
    ctx["cross_agent"]["metis_to_kratos"] = {
        "strategy_summary": topic,
        "priority": "high",
    }
    _save_context(ctx)
    
    return {
        **state,
        "metis_output": f"Strategy prompt written to {output_path}",
        "metis_prompt": prompt,
    }

def kratos_node(state: dict) -> dict:
    topic = state.get("topic", "")
    slug = _slugify(topic)
    
    ctx = _load_context()
    strategy = ctx.get("cross_agent", {}).get("metis_to_kratos", {})
    code_context = ctx.get("cross_agent", {}).get("aletheia_to_kratos", {})
    
    strategy_summary = strategy.get("strategy_summary", topic)
    
    prompt = (
        f"# Pipeline: Implementación\n\n"
        f"## Tarea\n{topic}\n\n"
        f"## Contexto Estratégico\n{strategy_summary}\n\n"
        f"## Especificación Técnica\n\n"
        f"Implementa el código necesario según la estrategia definida.\n"
        f"1. Revisa el contexto de código existente\n"
        f"2. Escribe o modifica archivos\n"
        f"3. Incluye tests\n"
        f"4. Documenta cambios\n"
    )
    
    output_path = RAW_DIR / f"{slug}-code.md"
    output_path.write_text(prompt, encoding="utf-8")

    if LLM_DIRECT_ENABLED:
        _notify_step(state, "Kratos Implementation", "in_progress")
        raw = _llm_or_executor_call("kratos", prompt)
        output_path.write_text(raw, encoding="utf-8")
        ctx = _load_context()
        ctx["agents"].append("kratos")
        ctx["context_summary"]["kratos"] = {"started_at": datetime.now().isoformat()}
        ctx["cross_agent"]["kratos_decision"] = "complete" if len(raw) > 500 else "needs_curation"
        _save_context(ctx)
        _notify_step(state, "Kratos Implementation", "completed")
        return {
            **state, "kratos_output": raw, "kratos_prompt": prompt,
            "kratos_decision": ctx["cross_agent"]["kratos_decision"],
        }
    
    ctx["agents"].append("kratos")
    ctx["context_summary"]["kratos"] = {
        "started_at": datetime.now().isoformat(),
    }
    ctx["cross_agent"]["kratos_decision"] = "needs_curation"
    _save_context(ctx)
    
    return {
        **state,
        "kratos_output": f"Code prompt written to {output_path}",
        "kratos_prompt": prompt,
        "kratos_decision": "needs_curation",
    }

def mnemosyne_node(state: dict) -> dict:
    topic = state.get("topic", "")
    slug = _slugify(topic)
    
    ctx = _load_context()
    kratos_decision = ctx.get("cross_agent", {}).get("kratos_decision", "needs_curation")
    
    prompt = (
        f"# Pipeline: Curación\n\n"
        f"## Tema\n{topic}\n\n"
        f"## Salidas a Curar\n\n"
        f"1. Investigación: raw/{slug}.md\n"
    )
    if kratos_decision != "skip":
        prompt += f"2. Código: code/{slug}.md\n"
    prompt += (
        f"\n## Tarea\n\n"
        f"1. Revisa calidad y consistencia de todas las salidas\n"
        f"2. Actualiza wikilinks y referencias cruzadas\n"
        f"3. Actualiza el índice de conocimiento\n"
        f"4. Reporta calidad y gaps\n"
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
    
    ctx["agents"].append("mnemosyne")
    ctx["context_summary"]["mnemosyne"] = {
        "started_at": datetime.now().isoformat(),
    }
    _save_context(ctx)
    
    return {
        **state,
        "mnemosyne_output": f"Curation prompt written to {output_path}",
        "mnemosyne_prompt": prompt,
    }
