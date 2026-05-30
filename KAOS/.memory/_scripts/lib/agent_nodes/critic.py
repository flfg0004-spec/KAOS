"""Critic node — evaluates pipeline output quality and generates feedback.

Extracted from orchestrator.py for consistency (all other nodes live in
agent_nodes/). Uses the same helper pattern as sibling nodes.
"""
import json
import logging
import re

from lib.config import HERMES_ENABLED, LLM_DIRECT_ENABLED
from lib.hermes_bridge import pipeline_notify
from lib.llm import agent_llm_call
from lib.quality.agent import record as verify_record

_CRITIC_THRESHOLD = 40


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


def _notify(step: str, status: str, state: dict):
    """Notify via Hermes bridge if enabled."""
    if HERMES_ENABLED:
        pipeline_notify(state, step, status)


def _generate_suggestions(scores: dict, outputs: dict) -> dict[str, list[str]]:
    """Generate structured improvement suggestions per agent based on scores."""
    suggestions = {}
    for agent, text in outputs.items():
        agent_sugs = []
        text = text or ""
        if agent in scores and scores.get(agent, 100) < _CRITIC_THRESHOLD:
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


def _kratos_feedback_loop(kratos_output: str, critic_score: float):
    """Feed Kratos output quality back into CodeExperience bandit."""
    try:
        from lib.code_memory import feedback, search
        experiences = search(kratos_output[:200], top_k=3)
        for exp in experiences:
            success = critic_score >= 60
            fb = feedback(exp["hash"], success=success)
            if fb.get("status") == "updated":
                logger = logging.getLogger("critic")
                logger.debug("Feedback loop: %s -> %s (score=%d, success=%s)",
                             exp["hash"], fb.get("new_confidence"), critic_score, success)
    except Exception:
        pass


def critic_node(state: dict) -> dict:
    """Evaluate pipeline output quality and generate improvement feedback.

    Skips kratos — already evaluated by reflexion_node (avoids redundant LLM calls).
    Evaluates aletheia, kosmos, metis, mnemosyne outputs.
    """
    _notify("Critic Quality", "in_progress", state)
    iteration = state.get("iteration", 0)
    score_history = state.get("score_history", [])

    # Skip kratos — already evaluated by reflexion_node
    outputs = {
        "aletheia": state.get("aletheia_output", ""),
        "kosmos": state.get("kosmos_output", ""),
        "metis": state.get("metis_output", ""),
        "mnemosyne": state.get("mnemosyne_output", ""),
    }

    if LLM_DIRECT_ENABLED:
        eval_prompt = "Evalua estas salidas de pipeline (0-100 cada una). Sugiere 1-2 mejoras especificas por agente:\n\n"
        for agent, text in outputs.items():
            truncated = text[:1000] if text else "(empty)"
            eval_prompt += f"## {agent}\n{truncated}\n---\n"
        eval_prompt += (
            '\nResponde SOLO con JSON:\n'
            '{"scores":{"aletheia":0,"kosmos":0,"metis":0,"mnemosyne":0},'
            '"avg_score":0,"feedback":"...",'
            '"suggestions":{"aletheia":["mejora1","mejora2"],"kosmos":[...]}}'
        )
        raw = agent_llm_call("critic", eval_prompt)
        try:
            parsed = json.loads(raw.strip().strip("```json").strip("```").strip())
            scores = parsed.get("scores", {})
            avg_score = parsed.get("avg_score", 0)
            feedback_text = parsed.get("feedback", "No feedback")
            suggestions = parsed.get("suggestions", {})
        except Exception:
            scores = {a: _score_output(t)["score"] for a, t in outputs.items()}
            avg_score = int(sum(scores.values()) / max(1, len(scores)))
            feedback_text = "LLM parse error, used heuristic fallback"
            suggestions = _generate_suggestions(scores, outputs)
    else:
        scores = {agent: _score_output(text)["score"] for agent, text in outputs.items()}
        avg_score = int(sum(scores.values()) / max(1, len(scores)))
        feedback_parts = []
        for agent, s in scores.items():
            if s < _CRITIC_THRESHOLD:
                missing = []
                if not _score_output(outputs[agent])["has_structure"]:
                    missing.append("estructura")
                if not _score_output(outputs[agent])["has_content"]:
                    missing.append("contenido sustancial")
                feedback_parts.append(f"{agent}: {s}/100 - falta {', '.join(missing)}")
        feedback_text = "; ".join(feedback_parts) if feedback_parts else "Calidad aceptable"
        suggestions = _generate_suggestions(scores, outputs)

    _notify("Critic Quality", "completed", state)

    # Feedback loop: Kratos output quality -> CodeExperience bandit
    kratos_out = state.get("kratos_output", "")
    if kratos_out:
        _kratos_feedback_loop(kratos_out, state.get("reflexion_score", 0) * 10)

    # Persist quality scores via kosmos_quality engine
    try:
        verify_record(
            agent="critic",
            output=str(feedback_text),
            topic=state.get("topic", ""),
        )
    except Exception:
        pass

    return {
        **state,
        "critic_score": avg_score if isinstance(avg_score, int) else int(avg_score),
        "critic_feedback": feedback_text,
        "critic_suggestions": suggestions,
        "score_history": score_history + [avg_score],
        "iteration": iteration + 1,
    }
