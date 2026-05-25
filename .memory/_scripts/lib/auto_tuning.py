"""Auto-tuning DSOL — optimizacion automatica de cache, presupuesto y rendimiento.

Decision Estrategica (Principio 6):
  Cache hit rate >60%, costo <$5/semana. Ajuste automatico de prompts,
  thinking mode, y budget basado en metricas de rendimiento.

Mecanismo:
  1. Cache monitor: calcula hit rate diario
  2. Budget optimizer: ajusta thinking mode basado en costo semanal
  3. Prompt evolver: sugiere mejoras de prompt cuando calidad es baja
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("auto_tuning")

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / ".memory" / "cache"
TOKEN_CACHE = CACHE_DIR / "token-usage.json"
COST_LOG = CACHE_DIR / "cost-log.json"
TUNING_STATE = CACHE_DIR / "tuning-state.json"

CACHE_TARGET = 60.0
COST_TARGET_WEEKLY = 5.0
COST_CRITICAL_WEEKLY = 10.0


def _load_token_data() -> dict:
    if TOKEN_CACHE.exists():
        try:
            return json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"total_cost_usd": 0, "total_calls": 0, "total_prompt_tokens": 0,
            "total_cache_hit": 0, "total_cache_miss": 0, "history": []}


def _load_state() -> dict:
    if TUNING_STATE.exists():
        try:
            return json.loads(TUNING_STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"thinking_mode": "high", "budget": "flash", "last_tune": None}


def _save_state(state: dict):
    TUNING_STATE.parent.mkdir(parents=True, exist_ok=True)
    TUNING_STATE.write_text(json.dumps(state, indent=2))


def cache_hit_rate() -> float:
    """Calcula cache hit rate actual."""
    data = _load_token_data()
    hit = data.get("total_cache_hit", 0)
    miss = data.get("total_cache_miss", 0)
    total = hit + miss
    if total == 0:
        return 0.0
    return hit / total * 100


def weekly_cost() -> float:
    """Calcula costo de los ultimos 7 dias."""
    data = _load_token_data()
    cost = data.get("total_cost_usd", 0)
    return cost


def weekly_calls() -> int:
    data = _load_token_data()
    return data.get("total_calls", 0)


def optimize_budget() -> dict:
    """Ajusta budget basado en cache hit rate y costo."""
    state = _load_state()
    cache_rate = cache_hit_rate()
    cost = weekly_cost()
    calls = weekly_calls()

    changes = []
    previous_budget = state.get("budget", "flash")

    if cache_rate < 20 and cost > COST_TARGET_WEEKLY and calls > 50:
        state["thinking_mode"] = None  # no thinking = fastest
        state["budget"] = "flash"
        changes.append("reduced thinking due to low cache hit rate")

    if cache_rate > CACHE_TARGET and cost < COST_TARGET_WEEKLY:
        state["thinking_mode"] = "high"
        state["budget"] = "pro"
        changes.append("increased thinking due to good cache performance")

    if cost > COST_CRITICAL_WEEKLY:
        state["budget"] = "flash"
        state["thinking_mode"] = None
        changes.append("CRITICAL: reduced to flash due to cost")

    state["last_tune"] = datetime.now().isoformat()
    _save_state(state)

    return {
        "previous_budget": previous_budget,
        "new_budget": state["budget"],
        "new_thinking": state["thinking_mode"],
        "cache_hit_rate": round(cache_rate, 1),
        "weekly_cost": round(cost, 2),
        "weekly_calls": calls,
        "changes": changes,
    }


def suggest_prompt_improvement(agent: str, current_prompt: str, score: float) -> str:
    """Sugiere mejora de prompt cuando calidad es baja."""
    suggestions = []

    if score < 60:
        suggestions.append("Agregar ejemplos few-shot relevantes al dominio")
        suggestions.append("Incluir instrucciones explicitas de formato")

    if score < 40:
        suggestions.append("Reducir la temperatura del modelo")
        suggestions.append("Usar chain-of-thought prompting")

    if "[[wikilink]]" not in current_prompt and score < 70:
        suggestions.append("Solicitar citar fuentes explicitamente con [[wikilinks]]")

    if len(current_prompt) < 200:
        suggestions.append("Aumentar la longitud del prompt con contexto adicional")

    return suggestions


def status() -> dict:
    state = _load_state()
    return {
        "cache_hit_rate": round(cache_hit_rate(), 1),
        "weekly_cost": round(weekly_cost(), 2),
        "weekly_calls": weekly_calls(),
        "thinking_mode": state.get("thinking_mode"),
        "budget": state.get("budget"),
        "last_tune": state.get("last_tune"),
        "targets": {
            "cache_hit_rate": f">{CACHE_TARGET}%",
            "weekly_cost": f"<${COST_TARGET_WEEKLY}",
        },
    }
