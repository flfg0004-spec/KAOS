import json as _json
from datetime import datetime

from lib.agent_tools import (
    PLAN_PATH,
    detect_complexity,
    detect_subtasks,
    llm_or_executor_call,
    load_context,
    notify_step,
    save_context,
    slugify,
)
from lib.config import LLM_DIRECT_ENABLED
from lib.feature_flags import is_enabled


def planner_node(state: dict) -> dict:
    if is_enabled("kratos_new_executor"):
        return _planner_node_v2(state)
    return _planner_node_impl(state)


def _planner_node_impl(state: dict) -> dict:
    topic = state.get("topic", "")
    profile = state.get("profile", "standard")
    slug = slugify(topic)

    if LLM_DIRECT_ENABLED:
        notify_step(state, "Planner", "in_progress")
        plan_prompt = (
            f"Descompón esta tarea en subtasks: {topic}\n\n"
            f"Perfil: {profile}\n"
            f"Responde SOLO con JSON:\n"
            f'{{"subtasks":[{{"id":"research|architecture|strategy|code|test|docs","name":"..."}}],'
            f'"complexity":"simple|moderada|alta","has_code":true|false}}'
        )
        raw = llm_or_executor_call("planner", plan_prompt)
        try:
            plan_data = _json.loads(raw.strip().strip("```json").strip("```").strip())
        except Exception:
            plan_data = {}
        subtasks = plan_data.get("subtasks", detect_subtasks(topic))
        complexity = plan_data.get("complexity", detect_complexity(topic))
        has_code = plan_data.get("has_code", any(s["id"] in ("code", "test") for s in subtasks))
        notify_step(state, "Planner", "completed")
    else:
        subtasks = detect_subtasks(topic)
        complexity = detect_complexity(topic)
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

    PLAN_PATH.write_text(_json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    ctx = load_context()
    ctx["agents"] = []
    ctx["context_summary"] = {"planner": plan}
    ctx["cross_agent"] = {"plan": plan}
    save_context(ctx)

    return {
        **state,
        "plan": plan,
        "has_code_subtasks": has_code,
        "iteration": 0,
    }


def _planner_node_v2(state: dict) -> dict:
    return _planner_node_impl(state)
