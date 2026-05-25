"""LangGraph Orchestrator — DAG with deep routing + HITL + parallel fan-out."""
import os, re, json, sqlite3
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Send
from typing import TypedDict, Optional

from lib.config import VAULT_ROOT, LLM_DIRECT_ENABLED, HERMES_ENABLED
from lib.llm import agent_llm_call, SYSTEM_PROMPTS
from lib.agent_executor import planner_node, aletheia_node, kosmos_node, metis_node, kratos_node, mnemosyne_node
from lib.hermes_bridge import pipeline_notify

DB_PATH = VAULT_ROOT / "cache" / "langgraph.db"
HITL_PATH = VAULT_ROOT / "_pipeline" / "hitl.json"
EVAL_PATH = VAULT_ROOT / "_pipeline" / "evaluation.json"

# Deshabilitar LangSmith si no hay API key
if not os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

CODE_KEYWORDS = ["code", "codigo", "implement", "program", "function", "class",
                 "bug", "error", "test", "refactor", "debug", "pull request", "pr",
                 "algorithm", "api", "script", "library", "package", "module"]

HITL_TIMEOUT_MINUTES = 60

def _hitl_enabled(profile: str = "desarrollo") -> bool:
    """HITL solo para perfil produccion. Desarrollo/exploracion usan auto-aprobar."""
    return profile == "produccion"

def _has_code_keywords(topic: str) -> bool:
    tl = topic.lower()
    return any(kw in tl for kw in CODE_KEYWORDS)

class KAOSState(TypedDict):
    topic: str
    profile: Optional[str] = "standard"
    plan: Optional[dict] = None
    has_code_subtasks: bool = False
    aletheia_output: Optional[str] = None
    aletheia_prompt: Optional[str] = None
    kosmos_output: Optional[str] = None
    kosmos_prompt: Optional[str] = None
    metis_output: Optional[str] = None
    metis_prompt: Optional[str] = None
    kratos_output: Optional[str] = None
    kratos_prompt: Optional[str] = None
    mnemosyne_output: Optional[str] = None
    mnemosyne_prompt: Optional[str] = None
    mnemosyne_gaps: Optional[list] = None
    needs_gap_check: bool = False
    kratos_decision: Optional[str] = None
    critic_score: float = 0
    critic_feedback: Optional[str] = None
    iteration: int = 0
    error: Optional[str] = None
    retries: int = 0
    hitl_approved: Optional[bool] = None
    evaluation: Optional[dict] = None
    evaluation_score: Optional[float] = None

def interrupt_human(prompt: str, context: dict = None) -> bool:
    """Human-in-the-Loop: pause pipeline and wait for approval.
    
    Writes a request to hitl.json. External process (Hermes/TUI) reads it
    and writes response. Pipeline polls until response or timeout.
    
    Args:
        prompt: Question to show the human
        context: Optional dict with extra info (diff, files, etc.)
    
    Returns:
        True if approved, False if rejected
    """
    import time, datetime
    
    request = {
        "id": datetime.datetime.now().strftime("HITL-%Y%m%d-%H%M%S"),
        "prompt": prompt,
        "context": context or {},
        "status": "pending",
        "created_at": datetime.datetime.now().isoformat(),
        "response": None
    }
    HITL_PATH.write_text(json.dumps(request, indent=2))
    
    # Poll for response (up to HITL_TIMEOUT_MINUTES)
    start = time.time()
    while (time.time() - start) < HITL_TIMEOUT_MINUTES * 60:
        time.sleep(5)
        if HITL_PATH.exists():
            try:
                data = json.loads(HITL_PATH.read_text())
                if data.get("status") == "responded":
                    approved = data.get("response") == "approved"
                    # Reset for next use
                    HITL_PATH.write_text(json.dumps({"status": "idle"}))
                    return approved
            except Exception:
                pass
    
    # Timeout: auto-reject for safety
    HITL_PATH.write_text(json.dumps({"status": "timeout", "response": "denied"}))
    return False

def route_after_strategy(state: KAOSState) -> str:
    """Route to Kratos if plan includes code subtasks."""
    has_code = state.get("has_code_subtasks", False) or _has_code_keywords(state.get("topic", ""))
    if has_code:
        return "kratos"
    return "mnemosyne"

def route_after_aletheia(state: KAOSState) -> str:
    """Route to Mnemosyne gap check if needed, else Kosmos."""
    if state.get("needs_gap_check", False):
        return "mnemosyne_gap_check"
    return "kosmos"

def _cross_validator_node(state: KAOSState) -> dict:
    """Cross-validate output with Gemini Flash (solo perfil produccion)."""
    profile = state.get("profile", "desarrollo")
    if profile != "produccion":
        return {**state, "cross_val_score": 100, "cross_val_passed": True}

    output = state.get("metis_output", "") or state.get("aletheia_output", "")
    if not output:
        return {**state, "cross_val_score": 0, "cross_val_passed": False}

    try:
        from lib.cross_validator import validate_content
        result = validate_content(output, profile=profile)
        state["cross_val_score"] = result.get("avg_score", 0)
        state["cross_val_passed"] = result.get("avg_score", 0) >= 60
        state["cross_val_report"] = result
    except Exception:
        state["cross_val_score"] = 0
        state["cross_val_passed"] = False
    return state


def route_after_cross_val(state: KAOSState) -> str:
    """Route after cross-validation: kratos if passed, mnemosyne if failed."""
    if state.get("cross_val_passed", True):
        return "kratos"
    return "mnemosyne"


def route_after_kratos(state: KAOSState) -> str:
    """Deep routing with HITL approval for code changes."""
    decision = state.get("kratos_decision", "needs_curation")
    
    # HITL: ask human before applying Kratos changes (solo perfil produccion)
    profile = state.get("profile", "desarrollo")
    if _hitl_enabled(profile) and (decision == "needs_curation" or decision == "complete"):
        kratos_output = state.get("kratos_output", "")
        if kratos_output and len(kratos_output) > 50:
            approved = interrupt_human(
                prompt="Kratos proposes code changes. Approve?",
                context={"diff_length": len(kratos_output), "topic": state.get("topic", "")}
            )
            if not approved:
                return "mnemosyne"
    
    if decision == "complete":
        return "mnemosyne"
    elif decision == "error":
        return "mnemosyne"
    return "mnemosyne"

def route_parallel_split(state: KAOSState) -> str:
    """Split: research+código en paralelo o secuencial."""
    topic = state.get("topic", "")
    if _has_code_keywords(topic):
        return "parallel"
    return "sequential"

def _evaluator_node(state: KAOSState) -> dict:
    _notify("Kosmos Evaluator", "in_progress", state)
    try:
        from lib.kosmos_evaluator import evaluate_system
        result = evaluate_system(state=state)
        _notify("Kosmos Evaluator", "completed", state)
        return {**state, "evaluation": result, "evaluation_score": result.get("composite", 0)}
    except Exception as e:
        _notify("Kosmos Evaluator", "failed", state)
        return {**state, "evaluation": {"error": str(e)}, "evaluation_score": 0}

def _parallel_validate_node(state: KAOSState) -> dict:
    """Parallel validation node — lightweight code review alongside Kratos."""
    _notify("Parallel Validation", "in_progress", state)
    topic = state.get("topic", "")
    kratos_raw = state.get("kratos_output", "")
    validation = "ok"
    if kratos_raw and len(kratos_raw) < 100:
        validation = "warning: output too short"
    _notify("Parallel Validation", "completed", state)
    return {**state, "parallel_validation": validation}

def _gap_check_node(state: KAOSState) -> dict:
    """Mnemosyne gap check: query existing knowledge gaps for the topic."""
    _notify("Mnemosyne Gap Check", "in_progress", state)
    topic = state.get("topic", "")
    gaps = []
    try:
        from lib.pipeline import get_cross_context
        ctx = get_cross_context("mnemosyne")
        if ctx:
            gaps = ctx.get("aletheia_research_context", {}).get("gaps_detected", [])
    except Exception:
        pass
    _notify("Mnemosyne Gap Check", "completed", state)
    return {**state, "mnemosyne_gaps": gaps, "needs_gap_check": False}

def route_parallel_fanout(state: KAOSState) -> list[Send]:
    """Fan-out from metis: send to kratos + parallel validation simultaneously."""
    return [
        Send("kratos", state),
        Send("parallel_validate", {**state, "topic": state.get("topic", "")}),
    ]

MAX_ITERATIONS = 2
CRITIC_THRESHOLD = 40
NODE_TIMEOUT = 300  # seconds per node

def _score_output(text: str) -> dict:
    """Evaluate a single text output for quality."""
    text = text or ""
    lines = text.strip().split("\n")
    length_score = min(1.0, len(lines) / 20)
    has_content = len(text) > 200
    has_structure = bool(re.search(r'(?m)^#{1,3}\s', text))
    has_recommendations = any(w in text.lower() for w in ["recomend", "conclus", "resumen", "summary"])
    completeness = sum([has_content, has_structure, has_recommendations]) / 3
    score = int((length_score * 0.3 + completeness * 0.7) * 100)
    return {"score": min(score, 100), "has_content": has_content, "has_structure": has_structure}

def _notify(step: str, status: str, state: KAOSState):
    if HERMES_ENABLED:
        pipeline_notify(state, step, status)

def _generate_suggestions(scores: dict, outputs: dict) -> dict[str, list[str]]:
    """Generate structured improvement suggestions per agent based on scores."""
    suggestions = {}
    for agent, text in outputs.items():
        agent_sugs = []
        text = text or ""
        if agent in scores and scores.get(agent, 100) < CRITIC_THRESHOLD:
            score_info = _score_output(text)
            if not score_info["has_structure"]:
                agent_sugs.append(f"Agregar estructura clara con secciones (## titulos) en {agent}")
            if not score_info["has_content"]:
                agent_sugs.append(f"Incluir contenido mas sustancial en {agent} (min 200 caracteres)")
            if agent == "aletheia":
                agent_sugs.append("Incluir referencias a fuentes externas con [[wikilinks]]")
            elif agent == "kosmos":
                agent_sugs.append("Agregar diagrama de arquitectura o ADR estructurado")
            elif agent == "kratos":
                agent_sugs.append("Incluir ejemplos de codigo completos con explicacion")
            elif agent == "mnemosyne":
                agent_sugs.append("Verificar wikilinks, cobertura y consistencia del vault")
        if agent_sugs:
            suggestions[agent] = agent_sugs[:3]
    return suggestions


def critic_node(state: KAOSState) -> dict:
    _notify("Critic Quality", "in_progress", state)
    iteration = state.get("iteration", 0)
    score_history = state.get("score_history", [])
    
    outputs = {
        "aletheia": state.get("aletheia_output", ""),
        "kosmos": state.get("kosmos_output", ""),
        "metis": state.get("metis_output", ""),
        "kratos": state.get("kratos_output", ""),
        "mnemosyne": state.get("mnemosyne_output", ""),
    }
    
    if LLM_DIRECT_ENABLED:
        eval_prompt = "Evalúa estas salidas de pipeline (0-100 cada una). Sugiere 1-2 mejoras específicas por agente:\n\n"
        for agent, text in outputs.items():
            truncated = text[:1000] if text else "(empty)"
            eval_prompt += f"## {agent}\n{truncated}\n---\n"
        eval_prompt += (
            '\nResponde SOLO con JSON:\n'
            '{"scores":{"aletheia":0,"kosmos":0,"metis":0,"kratos":0,"mnemosyne":0},'
            '"avg_score":0,"feedback":"...",'
            '"suggestions":{"aletheia":["mejora1","mejora2"],"kosmos":[...]}}'
        )
        raw = agent_llm_call("critic", eval_prompt)
        import json as _json
        try:
            parsed = _json.loads(raw.strip().strip("```json").strip("```").strip())
            scores = parsed.get("scores", {})
            avg_score = parsed.get("avg_score", 0)
            feedback = parsed.get("feedback", "No feedback")
            suggestions = parsed.get("suggestions", {})
        except Exception:
            scores = {a: _score_output(t)["score"] for a, t in outputs.items()}
            avg_score = int(sum(scores.values()) / max(1, len(scores)))
            feedback = "LLM parse error, used heuristic fallback"
            suggestions = _generate_suggestions(scores, outputs)
    else:
        scores = {agent: _score_output(text)["score"] for agent, text in outputs.items()}
        avg_score = int(sum(scores.values()) / max(1, len(scores)))
        feedback_parts = []
        for agent, s in scores.items():
            if s < CRITIC_THRESHOLD:
                missing = []
                if not _score_output(outputs[agent])["has_structure"]:
                    missing.append("estructura")
                if not _score_output(outputs[agent])["has_content"]:
                    missing.append("contenido sustancial")
                feedback_parts.append(f"{agent}: {s}/100 - falta {', '.join(missing)}")
        feedback = "; ".join(feedback_parts) if feedback_parts else "Calidad aceptable"
        suggestions = _generate_suggestions(scores, outputs)
    
    _notify("Critic Quality", "completed", state)
    return {
        **state,
        "critic_score": avg_score if isinstance(avg_score, int) else int(avg_score),
        "critic_feedback": feedback,
        "critic_suggestions": suggestions,
        "score_history": score_history + [avg_score],
        "iteration": iteration + 1,
    }


def route_after_critic(state: KAOSState) -> str:
    """Route: refine if quality low + iterations remain, else advance.
    
    Skip critic loop for non-code tasks (no kratos_output).
    Abort loop if score hasn't improved from previous iteration.
    """
    iteration = state.get("iteration", 0)
    score = state.get("critic_score", 0)
    kratos_out = state.get("kratos_output", "")
    score_history = state.get("score_history", [])
    
    if not kratos_out:
        return "advance"
    
    # Abort loop if no improvement from previous iteration
    if len(score_history) >= 2 and score_history[-2] >= score:
        return "advance"
    
    if score < CRITIC_THRESHOLD and iteration < MAX_ITERATIONS:
        return "refine"
    return "advance"

def build_graph(with_parallel: bool = False):
    """Build LangGraph DAG.
    
    Args:
        with_parallel: Enable parallel Aletheia+Kratos execution
    """
    # Pre-carga de modelos pesados al inicio del pipeline
    try:
        from lib.vectorstore import warmup_model
        warmup_model()
    except Exception:
        pass

    builder = StateGraph(KAOSState)
    
    builder.add_node("planner", planner_node)
    builder.add_node("aletheia", aletheia_node)
    builder.add_node("kosmos", kosmos_node)
    builder.add_node("metis", metis_node)
    builder.add_node("kratos", kratos_node)
    builder.add_node("mnemosyne", mnemosyne_node)
    builder.add_node("critic", critic_node)
    builder.add_node("kosmos_evaluator", _evaluator_node)
    builder.add_node("parallel_validate", _parallel_validate_node)
    builder.add_node("mnemosyne_gap_check", _gap_check_node)
    builder.add_node("cross_validator", _cross_validator_node)
    
    builder.set_entry_point("planner")
    
    builder.add_edge("planner", "aletheia")
    builder.add_conditional_edges(
        "aletheia",
        route_after_aletheia,
        {"mnemosyne_gap_check": "mnemosyne_gap_check", "kosmos": "kosmos"}
    )
    builder.add_edge("mnemosyne_gap_check", "kosmos")
    builder.add_edge("kosmos", "metis")
    
    # After metis: cross-validation for production, then route to kratos/mnemosyne
    builder.add_edge("metis", "cross_validator")
    builder.add_conditional_edges(
        "cross_validator",
        route_after_cross_val,
        {"kratos": "kratos", "mnemosyne": "mnemosyne"}
    )
    
    if with_parallel:
        # Also start parallel validation alongside cross_validator
        builder.add_conditional_edges(
            "metis",
            route_parallel_fanout,
            ["kratos", "parallel_validate"],
        )
    
    # Deep routing: Kratos evaluates if its output is complete
    builder.add_conditional_edges(
        "kratos",
        route_after_kratos,
        {"mnemosyne": "mnemosyne"}
    )

    if with_parallel:
        # Parallel join: wait for kratos + parallel_validate before mnemosyne
        builder.add_edge("parallel_validate", "mnemosyne")
    
    builder.add_edge("mnemosyne", "critic")
    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {"refine": "aletheia", "advance": "kosmos_evaluator"}
    )
    builder.add_edge("kosmos_evaluator", END)
    
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    return builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    g = build_graph(with_parallel=False)
    g2 = build_graph(with_parallel=True)
    print(f"Sequential graph: {list(g.nodes.keys())}")
    print(f"Parallel graph:   {list(g2.nodes.keys())}")
    print(f"LangSmith: {bool(os.environ.get('LANGCHAIN_API_KEY'))}")
    
    # Test routing
    state = KAOSState(topic="implementar API REST con JWT")
    print(f"\nCode topic → {route_after_strategy(state)} ✓")
    
    state["kratos_decision"] = "complete"
    print(f"Kratos complete → {route_after_kratos(state)} ✓")
    
    state["kratos_decision"] = "needs_curation"
    print(f"Kratos needs_curation → {route_after_kratos(state)} ✓")
