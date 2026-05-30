"""BCG Self-Evaluation — measures evaluation quality across 5 dimensions."""

import logging
import re

_LOG = logging.getLogger(__name__)


def _check_objetividad(text: str) -> dict:
    patterns = {
        "metric": r"(?:metric|métrica|score|puntuación|evidence|evidencia)",
        "data": r"(?:data|datos|medicion|medición|cuantitativo|quantitative)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_claridad_evaluacion(text: str) -> dict:
    patterns = {
        "criterio": r"(?:criterio|criterion|standard|estándar|benchmark|benchmark)",
        "comparacion": r"(?:baseline|línea base|comparacion|comparison|referencia)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_retroalimentacion(text: str) -> dict:
    patterns = {
        "feedback": r"(?:feedback|retroaliment|improvement|mejora|oportunidad|opportunity)",
        "gap": r"(?:gap|brecha|déficit|deficit)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_consistencia(text: str) -> dict:
    patterns = {
        "coherente": r"(?:consistente|consistent|coherente|coherent|aligned|alinead)",
        "match": r"(?:match|correspond|correspondencia|equivalen)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_accionabilidad(text: str) -> dict:
    patterns = {
        "action_item": r"(?:action item|next step|próximo paso|recomendacion|recommendation)",
        "fix": r"(?:fix|solucion|resolve|resolver|reparar)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def bcg_self_eval(agent: str, output: dict) -> dict:
    output = output or {}
    content = output.get("content", "") or ""
    criteria = output.get("criteria", "") or ""
    feedback = output.get("feedback", "") or ""
    scores = output.get("scores", "") or ""
    actions = output.get("actions", "") or ""

    text = content + " " + criteria + " " + feedback + " " + scores + " " + actions

    if not text.strip():
        return {
            "agent": agent,
            "score": 0.0,
            "dimensions": {
                "objetividad": {"score": 0.0, "justificacion": "No content provided"},
                "claridad_evaluacion": {"score": 0.0, "justificacion": "No content provided"},
                "retroalimentacion": {"score": 0.0, "justificacion": "No content provided"},
                "consistencia": {"score": 0.0, "justificacion": "No content provided"},
                "accionabilidad": {"score": 0.0, "justificacion": "No content provided"},
            },
        }

    objetividad = _check_objetividad(text)
    claridad_eval = _check_claridad_evaluacion(text)
    retro = _check_retroalimentacion(text)
    consistencia = _check_consistencia(text)
    accion = _check_accionabilidad(text)

    total_obj = sum(objetividad.values())
    objetividad_score = min(1.0, 0.2 + 0.1 * min(total_obj, 8))
    if objetividad.get("metric", 0) > 1:
        objetividad_score = min(1.0, objetividad_score + 0.2)
    if objetividad.get("data", 0) > 0:
        objetividad_score = min(1.0, objetividad_score + 0.2)

    total_clar = sum(claridad_eval.values())
    claridad_evaluacion = min(1.0, 0.2 + 0.1 * min(total_clar, 6))
    if claridad_eval.get("criterio", 0) > 0:
        claridad_evaluacion = min(1.0, claridad_evaluacion + 0.2)
    if claridad_eval.get("comparacion", 0) > 0:
        claridad_evaluacion = min(1.0, claridad_evaluacion + 0.2)

    total_retro = sum(retro.values())
    retroalimentacion = min(1.0, 0.2 + 0.1 * min(total_retro, 6))
    if retro.get("feedback", 0) > 0:
        retroalimentacion = min(1.0, retroalimentacion + 0.2)
    if retro.get("gap", 0) > 0:
        retroalimentacion = min(1.0, retroalimentacion + 0.2)

    total_cons = sum(consistencia.values())
    consistencia_score = min(1.0, 0.3 + 0.1 * min(total_cons, 6))
    if consistencia.get("coherente", 0) > 0:
        consistencia_score = min(1.0, consistencia_score + 0.2)
    if consistencia.get("match", 0) > 0:
        consistencia_score = min(1.0, consistencia_score + 0.15)

    total_acc = sum(accion.values())
    accionabilidad_score = min(1.0, 0.2 + 0.1 * min(total_acc, 6))
    if accion.get("action_item", 0) > 0:
        accionabilidad_score = min(1.0, accionabilidad_score + 0.2)
    if accion.get("fix", 0) > 0:
        accionabilidad_score = min(1.0, accionabilidad_score + 0.2)

    score = round((objetividad_score + claridad_evaluacion + retroalimentacion + consistencia_score + accionabilidad_score) / 5, 2)

    return {
        "agent": agent,
        "score": score,
        "dimensions": {
            "objetividad": {
                "score": objetividad_score,
                "justificacion": (
                    f"metric={objetividad.get('metric', 0)}, "
                    f"data={objetividad.get('data', 0)}"
                ),
            },
            "claridad_evaluacion": {
                "score": claridad_evaluacion,
                "justificacion": (
                    f"criterio={claridad_eval.get('criterio', 0)}, "
                    f"comparacion={claridad_eval.get('comparacion', 0)}"
                ),
            },
            "retroalimentacion": {
                "score": retroalimentacion,
                "justificacion": (
                    f"feedback={retro.get('feedback', 0)}, "
                    f"gap={retro.get('gap', 0)}"
                ),
            },
            "consistencia": {
                "score": consistencia_score,
                "justificacion": (
                    f"coherente={consistencia.get('coherente', 0)}, "
                    f"match={consistencia.get('match', 0)}"
                ),
            },
            "accionabilidad": {
                "score": accionabilidad_score,
                "justificacion": (
                    f"action_item={accion.get('action_item', 0)}, "
                    f"fix={accion.get('fix', 0)}"
                ),
            },
        },
    }
