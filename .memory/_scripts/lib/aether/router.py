"""Router — model resolution and fallback chain with adaptive multi-priority routing."""

import logging

from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER
from lib.aether.config import (
    AGENT_DEFAULT_TASK,
    AGENT_TASK_MODEL,
    COST_CAPS,
    ETHER_BUDGET_ENFORCEMENT,
    ETHER_CONTEXT_ROUTING,
    ETHER_KIMI_ENABLED,
    ETHER_MULTIMODAL_ENABLED,
    MODEL_FALLBACK_CHAIN,
    QUALITY_ROUTING_ENABLED,
    ModelTaskRule,
    TASK_MODEL_MAP,
)

_LOG = logging.getLogger(__name__)
_QUALITY_THRESHOLD = 5.0  # mínimo score 0-10 para considerar un modelo confiable


def resolve_model(
    task_type=None, agent="", model_override=None, prompt_size=0, has_images=False, budget_remaining=None
):
    """Resuelve qué modelo OCGo usar con routing adaptativo multi-priority.

    Pipeline: override > multimodal > base(priority) > quality_rerank > budget_downgrade > cb_fallback > return

    Args:
        task_type: Categoría de tarea
        agent: Nombre del agente
        model_override: Override explícito de modelo
        prompt_size: Tamaño del prompt en tokens (0 = desconocido)
        has_images: Si el prompt contiene imágenes/video
        budget_remaining: Budget semanal restante en USD (None = sin verificar)

    Returns: {"model": str, "thinking": str|None, "tier": str, "resolved_by": str}
    """
    # 1. Override explícito
    if model_override and model_override.startswith("go-"):
        return {"model": model_override, "thinking": None, "tier": "override", "resolved_by": "explicit"}

    # 2. Obtener candidatos base
    candidates = _get_candidates(task_type, agent)
    if not candidates:
        return {"model": "go-flash", "thinking": None, "tier": "flash", "resolved_by": "absolute_default"}

    # 3. Multimodal preference: si hay imágenes, priorizar modelos con soporte multimodal
    if has_images and ETHER_MULTIMODAL_ENABLED:
        candidates = _prefer_multimodal(candidates)

    # 4. Routing por contenido multimodal (Kimi legacy)
    if has_images and ETHER_MULTIMODAL_ENABLED and ETHER_KIMI_ENABLED and _is_kimi_available(task_type, agent):
        kimi_rule = _get_kimi_rule()
        return {**kimi_rule, "resolved_by": "multimodal_routing"}

    # 5. Tomar primer candidato disponible (por prioridad)
    chosen = _pick_first_available(candidates)
    if not chosen:
        return {"model": "go-flash", "thinking": None, "tier": "flash", "resolved_by": "no_candidate_available"}

    # 6. Quality-aware rerank (si hay datos históricos)
    reranked = _rerank_by_quality(candidates, task_type or "general")
    if reranked and reranked[0] != chosen and _ETHER_CIRCUIT_BREAKER.is_available(reranked[0].model):
        chosen = reranked[0]

    # 7. Long-context routing (prompts largos -> Kimi)
    if prompt_size > 100000 and ETHER_CONTEXT_ROUTING and ETHER_KIMI_ENABLED:
        if chosen.model != "go-kimi-latest" and _is_kimi_available(task_type, agent):
            if _kimi_budget_ok(budget_remaining):
                kimi_rule = _get_kimi_rule()
                return {**kimi_rule, "resolved_by": f"long_context_routing({prompt_size}tokens)"}

    # 8. Budget-aware downgrade
    final_model = _apply_budget_downgrade(chosen.model, budget_remaining)
    tier = _model_to_tier(final_model)

    # 9. Quality feedback: skip models with consistently low scores
    if QUALITY_ROUTING_ENABLED:
        qf_model = _apply_quality_feedback(final_model, task_type or "general", agent)
        if qf_model != final_model:
            _LOG.info("QUALITY_FEEDBACK: skip %s (score < threshold), fallback to %s", final_model, qf_model)
            return {
                "model": qf_model,
                "thinking": None,
                "tier": _model_to_tier(qf_model),
                "resolved_by": f"quality_feedback_from_{final_model}",
            }

    # 10. CB-aware fallback
    if not _ETHER_CIRCUIT_BREAKER.is_available(final_model):
        fallback = _resolve_fallback(task_type, agent)
        return {**fallback, "resolved_by": f"cb_fallback_from_{final_model}"}

    return {
        "model": final_model,
        "thinking": chosen.thinking,
        "tier": tier,
        "resolved_by": f"multi_priority_routing({chosen.model})" if final_model != chosen.model else "multi_priority_routing",
    }


def _get_candidates(task_type, agent):
    """Obtiene lista de candidatos ModelTaskRule ordenados por prioridad."""
    if task_type and task_type in TASK_MODEL_MAP:
        return TASK_MODEL_MAP[task_type]

    default_task = AGENT_DEFAULT_TASK.get(agent) or AGENT_TASK_MODEL.get(agent, {}).get("default_task", "general")
    if default_task in TASK_MODEL_MAP:
        return TASK_MODEL_MAP[default_task]

    if "general" in TASK_MODEL_MAP:
        return TASK_MODEL_MAP["general"]

    return []


def _pick_first_available(candidates: list[ModelTaskRule]) -> ModelTaskRule | None:
    """Toma el primer candidato disponible según CB."""
    for c in candidates:
        if _ETHER_CIRCUIT_BREAKER.is_available(c.model):
            return c
    return None


def _prefer_multimodal(candidates: list[ModelTaskRule]) -> list[ModelTaskRule]:
    """Reordena candidatos priorizando los que soportan multimodal."""
    mimo = [c for c in candidates if c.supports_multimodal]
    if not mimo:
        return candidates
    return mimo + [c for c in candidates if not c.supports_multimodal]


_QS_INSTANCE = None


def _get_qs():
    global _QS_INSTANCE
    if _QS_INSTANCE is None:
        from lib.aether.quality_store import QualityStore

        _QS_INSTANCE = QualityStore()
    return _QS_INSTANCE


def _rerank_by_quality(candidates: list[ModelTaskRule], task_type: str) -> list[ModelTaskRule]:
    """Reordena candidatos por QualityStore si hay datos históricos."""
    try:
        qs = _get_qs()
        scored = []
        scores_by_model = qs.get_task_scores(task_type)  # dict[model, {avg_score, samples, ...}]
        for c in candidates:
            model_data = scores_by_model.get(c.model, {}) if scores_by_model else {}
            avg = model_data.get("avg_score", 5)
            scored.append((c, avg))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored]
    except Exception:
        return candidates


def _apply_budget_downgrade(model_key: str, budget_remaining: float | None) -> str:
    """Downgrade de modelo si budget escaso."""
    if budget_remaining is None or not ETHER_BUDGET_ENFORCEMENT:
        return model_key
    if budget_remaining < 0.01:
        return "go-flash"
    if budget_remaining < 0.05 and model_key in ("go-kimi-latest", "go-pro"):
        return "go-flash"
    return model_key


def _apply_quality_feedback(model_key: str, task_type: str, agent: str) -> str:
    """Skip models with consistently low quality scores via fallback chain."""
    try:
        qs = _get_qs()
        score = qs.get_model_score(model_key, task_type)
        if score >= _QUALITY_THRESHOLD:
            return model_key

        # Score bajo — probar fallback chain
        chain = MODEL_FALLBACK_CHAIN.get(model_key, [model_key])
        for fb in chain:
            if fb == model_key:
                continue
            fb_score = qs.get_model_score(fb, task_type)
            if fb_score >= _QUALITY_THRESHOLD:
                _LOG.info("QUALITY_FEEDBACK: %s score=%.2f < %.1f → switch to %s (score=%.2f)",
                          model_key, score, _QUALITY_THRESHOLD, fb, fb_score)
                return fb

        # Ninguno pasa el threshold — mantener original
        return model_key
    except Exception:
        return model_key


def _model_to_tier(model: str) -> str:
    if model == "go-kimi-latest":
        return "kimi"
    if model == "go-pro":
        return "pro"
    if model == "go-mimo":
        return "mimo"
    return "flash"


def _base_resolve(task_type, agent):
    """Resolución base legacy: mantiene compatibilidad con código que usa TASK_MODEL_MAP como dict."""
    candidates = _get_candidates(task_type, agent)
    chosen = _pick_first_available(candidates)
    if chosen:
        return {"model": chosen.model, "thinking": chosen.thinking, "tier": _model_to_tier(chosen.model)}
    return {"model": "go-flash", "thinking": None, "tier": "flash", "resolved_by": "absolute_default"}


def _resolve_fallback(task_type, agent):
    """Fallback chain cuando el modelo primario no está disponible."""
    candidates = _get_candidates(task_type, agent)
    primary_model = candidates[0].model if candidates else "go-flash"
    chain = MODEL_FALLBACK_CHAIN.get(primary_model, [primary_model])
    for fb_model in chain:
        if fb_model != primary_model and _ETHER_CIRCUIT_BREAKER.is_available(fb_model):
            return {
                "model": fb_model,
                "thinking": None,
                "tier": _model_to_tier(fb_model),
                "resolved_by": f"fallback_from_{primary_model}",
            }
    return {"model": "go-flash", "thinking": None, "tier": "flash", "resolved_by": "last_resort_fallback"}


def _is_kimi_available(task_type, agent):
    if not ETHER_KIMI_ENABLED:
        return False
    return _ETHER_CIRCUIT_BREAKER.is_available("go-kimi-latest")


def _get_kimi_rule():
    return {"model": "go-kimi-latest", "thinking": None, "tier": "kimi"}


def _kimi_fallback(task_type, agent):
    fallback_order = ["go-pro", "go-flash"]
    for fb in fallback_order:
        if _ETHER_CIRCUIT_BREAKER.is_available(fb):
            return {"model": fb, "thinking": None, "tier": "pro" if fb == "go-pro" else "flash"}
    return {"model": "go-flash", "thinking": None, "tier": "flash", "resolved_by": "kimi_fallback_last_resort"}


def _cheapest_fallback(task_type, agent):
    for model in ["go-flash", "go-pro"]:
        if _ETHER_CIRCUIT_BREAKER.is_available(model):
            return {"model": model, "thinking": None, "tier": "flash" if model == "go-flash" else "pro"}
    return None


def _kimi_budget_ok(budget_remaining):
    if budget_remaining is None:
        return True
    kimi_cap = COST_CAPS.get("kimi", {}).get("weekly_usd", 1.0)
    return budget_remaining > kimi_cap * 0.2
