"""Metis Self-Evaluation — measures strategic planning quality across 5 dimensions."""

import logging
import re

_LOG = logging.getLogger(__name__)


def _check_claridad_estrategica(text: str) -> dict:
    patterns = {
        "estrategia": r"(?:estrategia|strategy|objetivo|objective|goal|goal)",
        "okr": r"(?:okr|roadmap|roadmap|plan|plan|vision|vision)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_accionabilidad(text: str) -> dict:
    patterns = {
        "accion": r"(?:accion|action|implement|implement|deliverable|deliverable)",
        "next_step": r"(?:next step|próximo paso|timeline|cronograma)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_analisis_competitivo(text: str) -> dict:
    patterns = {
        "competencia": r"(?:compet|compet|mercado|market|market)",
        "analisis": r"(?:foda|foda|swot|competitive|brecha|gap)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_cobertura_riesgos(text: str) -> dict:
    patterns = {
        "riesgo": r"(?:riesgo|risk|risk|threat|amenaza)",
        "mitigacion": r"(?:mitigacion|mitigation|contingency|contingencia|blocker|bloqueo)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_recomendaciones(text: str) -> dict:
    patterns = {
        "recomendacion": r"(?:recomend|recommend|suggest|suger|propose|propone)",
        "prioridad": r"(?:priority|prioridad|impact|impacto|effort|esfuerzo)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def metis_self_eval(agent: str, output: dict) -> dict:
    output = output or {}
    content = output.get("content", "") or ""
    analysis = output.get("analysis", "") or ""
    recommendations = output.get("recommendations", "") or ""
    risks = output.get("risks", "") or ""
    action_items = output.get("action_items", "") or ""

    text = content + " " + analysis + " " + recommendations + " " + risks + " " + action_items

    if not text.strip():
        return {
            "agent": agent,
            "score": 0.0,
            "dimensions": {
                "claridad_estrategica": {"score": 0.0, "justificacion": "No content provided"},
                "accionabilidad": {"score": 0.0, "justificacion": "No content provided"},
                "analisis_competitivo": {"score": 0.0, "justificacion": "No content provided"},
                "cobertura_riesgos": {"score": 0.0, "justificacion": "No content provided"},
                "recomendaciones": {"score": 0.0, "justificacion": "No content provided"},
            },
        }

    claridad = _check_claridad_estrategica(text)
    accion = _check_accionabilidad(text)
    competitivo = _check_analisis_competitivo(text)
    riesgos = _check_cobertura_riesgos(text)
    recom = _check_recomendaciones(text)

    total_claridad = sum(claridad.values())
    claridad_estrategica = min(1.0, 0.2 + 0.1 * min(total_claridad, 8))
    if claridad.get("estrategia", 0) > 1:
        claridad_estrategica = min(1.0, claridad_estrategica + 0.2)
    if claridad.get("okr", 0) > 0:
        claridad_estrategica = min(1.0, claridad_estrategica + 0.2)

    total_accion = sum(accion.values())
    accionabilidad = min(1.0, 0.2 + 0.1 * min(total_accion, 6))
    if accion.get("accion", 0) > 0:
        accionabilidad = min(1.0, accionabilidad + 0.2)
    if accion.get("next_step", 0) > 0:
        accionabilidad = min(1.0, accionabilidad + 0.2)

    total_comp = sum(competitivo.values())
    analisis_competitivo = min(1.0, 0.2 + 0.1 * min(total_comp, 6))
    if competitivo.get("competencia", 0) > 0:
        analisis_competitivo = min(1.0, analisis_competitivo + 0.2)
    if competitivo.get("analisis", 0) > 0:
        analisis_competitivo = min(1.0, analisis_competitivo + 0.2)

    total_riesgos = sum(riesgos.values())
    cobertura_riesgos = min(1.0, 0.2 + 0.1 * min(total_riesgos, 6))
    if riesgos.get("riesgo", 0) > 0:
        cobertura_riesgos = min(1.0, cobertura_riesgos + 0.2)
    if riesgos.get("mitigacion", 0) > 0:
        cobertura_riesgos = min(1.0, cobertura_riesgos + 0.2)

    total_recom = sum(recom.values())
    recomendaciones = min(1.0, 0.2 + 0.1 * min(total_recom, 6))
    if recom.get("recomendacion", 0) > 0:
        recomendaciones = min(1.0, recomendaciones + 0.2)
    if recom.get("prioridad", 0) > 0:
        recomendaciones = min(1.0, recomendaciones + 0.2)

    score = round((claridad_estrategica + accionabilidad + analisis_competitivo + cobertura_riesgos + recomendaciones) / 5, 2)

    return {
        "agent": agent,
        "score": score,
        "dimensions": {
            "claridad_estrategica": {
                "score": claridad_estrategica,
                "justificacion": (
                    f"estrategia={claridad.get('estrategia', 0)}, "
                    f"okr={claridad.get('okr', 0)}"
                ),
            },
            "accionabilidad": {
                "score": accionabilidad,
                "justificacion": (
                    f"accion={accion.get('accion', 0)}, "
                    f"next_step={accion.get('next_step', 0)}"
                ),
            },
            "analisis_competitivo": {
                "score": analisis_competitivo,
                "justificacion": (
                    f"competencia={competitivo.get('competencia', 0)}, "
                    f"analisis={competitivo.get('analisis', 0)}"
                ),
            },
            "cobertura_riesgos": {
                "score": cobertura_riesgos,
                "justificacion": (
                    f"riesgo={riesgos.get('riesgo', 0)}, "
                    f"mitigacion={riesgos.get('mitigacion', 0)}"
                ),
            },
            "recomendaciones": {
                "score": recomendaciones,
                "justificacion": (
                    f"recomendacion={recom.get('recomendacion', 0)}, "
                    f"prioridad={recom.get('prioridad', 0)}"
                ),
            },
        },
    }
