"""Verification Hook — event-driven quality scoring post-output.

Decision ADR-012 (P7) + Estrategia (Principio 2):
  La calidad debe estar disenada en la arquitectura, no delegada a la
  disciplina de los agentes. Este hook se ejecuta post-output de cada
  agente y persiste el score en timeseries.

Mecanismo:
  - Cualquier nodo puede llamar record() al finalizar
  - El score se persiste en .vault/quality/timeseries/
  - No bloquea el pipeline principal (fire-and-forget)
  - Si score < 60, genera alerta en bridge/signals/
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("verification_hook")

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
TIMESERIES_DIR = VAULT_ROOT / ".vault" / "quality" / "timeseries"
SIGNALS_DIR = VAULT_ROOT / ".memory" / "bridge" / "signals"

TIMESERIES_FILE = TIMESERIES_DIR / "verification-scores.json"
SCORE_THRESHOLD_WARN = 80
SCORE_THRESHOLD_CRIT = 60


def _dimension_score(text: str, agent: str) -> dict:
    """Score heuristico en 5 dimensiones.
    
    Returns dict con scores 0-100 para cada dimension.
    """
    text = text or ""
    lines = text.strip().split("\n")
    words = text.split()

    veracidad = 80  # default alto (no podemos verificar hechos sin LLM)
    if not text:
        veracidad = 0

    coherencia = min(100, len(lines) * 5 + 20)
    if not text:
        coherencia = 0

    has_titles = bool(__import__("re").search(r"(?m)^#{1,3}\s", text))
    has_lists = "  - " in text or "* " in text
    completitud = 0
    if has_titles:
        completitud += 40
    if has_lists:
        completitud += 20
    if text and len(text) > 200:
        completitud += 40

    has_wikilinks = "[[" in text and "]]" in text
    reproducibilidad = 60
    if has_wikilinks:
        reproducibilidad += 30
    if len(text) > 50:
        reproducibilidad += 10

    utilidad = min(100, len(words) // 2 + 20)
    if not text:
        utilidad = 0

    return {
        "veracidad": veracidad,
        "coherencia": coherencia,
        "completitud": completitud,
        "reproducibilidad": reproducibilidad,
        "utilidad": utilidad,
    }


def _composite(dims: dict) -> float:
    """Score compuesto: promedio simple de 5 dimensiones."""
    return sum(dims.values()) / max(1, len(dims))


def record(agent: str, output: str, topic: str = "", pipeline_id: str = "") -> dict:
    """Evalua calidad del output de un agente y persiste.

    Args:
        agent: Nombre del agente (aletheia, kosmos, etc.)
        output: Texto generado por el agente
        topic: Topico de la tarea (opcional)
        pipeline_id: ID del pipeline (opcional)

    Returns:
        dict con scores
    """
    dims = _dimension_score(output, agent)
    composite = _composite(dims)
    timestamp = datetime.now().isoformat()

    entry = {
        "agent": agent,
        "topic": topic[:80] if topic else "",
        "pipeline_id": pipeline_id,
        "timestamp": timestamp,
        "composite": round(composite, 1),
        **{k: round(v, 1) for k, v in dims.items()},
    }

    TIMESERIES_DIR.mkdir(parents=True, exist_ok=True)
    if TIMESERIES_FILE.exists():
        try:
            data = json.loads(TIMESERIES_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {"scores": []}
    else:
        data = {"scores": []}

    data["scores"].append(entry)
    data["scores"] = data["scores"][-10000:]
    TIMESERIES_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    logger.info(f"[VERIFY] {agent}: composite={composite:.1f}/100")

    if composite < SCORE_THRESHOLD_CRIT:
        SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
        signal = {
            "type": "quality_critical",
            "agent": agent,
            "score": composite,
            "timestamp": timestamp,
        }
        (SIGNALS_DIR / f"quality-crit-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json").write_text(
            json.dumps(signal, indent=2)
        )
        logger.warning(f"[ALERT] Quality CRITICAL for {agent}: {composite:.1f}")
    elif composite < SCORE_THRESHOLD_WARN:
        logger.info(f"[WARN] Quality below threshold for {agent}: {composite:.1f}")

    return entry


def latest(agent: str = "", limit: int = 10) -> list:
    """Obtiene los ultimos scores registrados."""
    if not TIMESERIES_FILE.exists():
        return []
    try:
        data = json.loads(TIMESERIES_FILE.read_text(encoding="utf-8"))
        scores = data.get("scores", [])
        if agent:
            scores = [s for s in scores if s.get("agent") == agent]
        return scores[-limit:]
    except Exception:
        return []


def summary() -> dict:
    """Resumen de calidad: promedio por agente, tendencia."""
    if not TIMESERIES_FILE.exists():
        return {"agents": {}, "global_avg": 0, "total_records": 0}
    try:
        data = json.loads(TIMESERIES_FILE.read_text(encoding="utf-8"))
        scores = data.get("scores", [])
        if not scores:
            return {"agents": {}, "global_avg": 0, "total_records": 0}

        agents = {}
        for s in scores:
            a = s.get("agent", "unknown")
            if a not in agents:
                agents[a] = []
            agents[a].append(s.get("composite", 0))

        avgs = {a: round(sum(v) / len(v), 1) for a, v in agents.items()}
        global_avg = round(sum(s.get("composite", 0) for s in scores) / len(scores), 1)

        last_7 = [s.get("composite", 0) for s in scores[-7:]]
        trend = "up" if len(last_7) >= 2 and last_7[-1] > last_7[0] else "down" if len(last_7) >= 2 else "stable"

        return {
            "agents": avgs,
            "global_avg": global_avg,
            "trend": trend,
            "total_records": len(scores),
        }
    except Exception:
        return {"error": "Could not parse scores"}
