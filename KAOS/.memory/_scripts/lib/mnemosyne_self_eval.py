"""Mnemosyne Self-Evaluation — measures knowledge curation quality across 5 dimensions."""

import logging
import re

_LOG = logging.getLogger(__name__)


def _check_calidad_fuentes(text: str) -> dict:
    patterns = {
        "fuente": r"(?:fuente|source|source|reference|referencia)",
        "citation": r"(?:citation|cita|doi|doi|link|url|enlace)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_organizacion(text: str) -> dict:
    patterns = {
        "categoria": r"(?:categor|categor|tag|wikilink|wikilink)",
        "estructura": r"(?:index|índice|estructura|structure|taxonomy|taxonomía)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_completitud(text: str) -> dict:
    patterns = {
        "seccion": r"(?:seccion|section|section|overview|visión general)",
        "cobertura": r"(?:summary|resumen|coverage|cobertura|todo|pendiente)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_consistencia_interna(text: str) -> dict:
    patterns = {
        "contradiccion": r"(?:contradiccion|contradiction|conflict|conflicto|duplicado|duplicate)",
        "version": r"(?:version|versión|inconsisten|inconsistency)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_utilidad(text: str) -> dict:
    patterns = {
        "util": r"(?:util|useful|actionable|procesable|relevance|relevante)",
        "aplicacion": r"(?:practical|práctico|aplicable|insight|perspectiva)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def mnemosyne_self_eval(agent: str, output: dict) -> dict:
    output = output or {}
    content = output.get("content", "") or ""
    sources = output.get("sources", "") or ""
    tags = output.get("tags", "") or ""
    structure = output.get("structure", "") or ""
    summary = output.get("summary", "") or ""

    text = content + " " + sources + " " + tags + " " + structure + " " + summary

    if not text.strip():
        return {
            "agent": agent,
            "score": 0.0,
            "dimensions": {
                "calidad_fuentes": {"score": 0.0, "justificacion": "No content provided"},
                "organizacion": {"score": 0.0, "justificacion": "No content provided"},
                "completitud": {"score": 0.0, "justificacion": "No content provided"},
                "consistencia_interna": {"score": 0.0, "justificacion": "No content provided"},
                "utilidad": {"score": 0.0, "justificacion": "No content provided"},
            },
        }

    fuentes = _check_calidad_fuentes(text)
    organizacion = _check_organizacion(text)
    completitud = _check_completitud(text)
    consistencia = _check_consistencia_interna(text)
    utilidad = _check_utilidad(text)

    total_fuentes = sum(fuentes.values())
    calidad_fuentes = min(1.0, 0.2 + 0.1 * min(total_fuentes, 8))
    if fuentes.get("fuente", 0) > 1:
        calidad_fuentes = min(1.0, calidad_fuentes + 0.2)
    if fuentes.get("citation", 0) > 0:
        calidad_fuentes = min(1.0, calidad_fuentes + 0.2)

    total_org = sum(organizacion.values())
    organizacion_score = min(1.0, 0.2 + 0.1 * min(total_org, 6))
    if organizacion.get("categoria", 0) > 0:
        organizacion_score = min(1.0, organizacion_score + 0.2)
    if organizacion.get("estructura", 0) > 0:
        organizacion_score = min(1.0, organizacion_score + 0.2)

    total_comp = sum(completitud.values())
    completitud_score = min(1.0, 0.2 + 0.1 * min(total_comp, 6))
    if completitud.get("seccion", 0) > 0:
        completitud_score = min(1.0, completitud_score + 0.2)
    if completitud.get("cobertura", 0) > 0:
        completitud_score = min(1.0, completitud_score + 0.2)

    total_cons = sum(consistencia.values())
    consistencia_interna = min(1.0, 0.2 + 0.1 * min(total_cons, 6))
    if consistencia.get("contradiccion", 0) > 0:
        consistencia_interna = min(1.0, consistencia_interna + 0.2)
    if consistencia.get("version", 0) > 0:
        consistencia_interna = min(1.0, consistencia_interna + 0.2)
    if consistencia.get("contradiccion", 0) > 2:
        consistencia_interna = max(0.3, consistencia_interna - 0.2)

    total_util = sum(utilidad.values())
    utilidad_score = min(1.0, 0.2 + 0.1 * min(total_util, 6))
    if utilidad.get("util", 0) > 0:
        utilidad_score = min(1.0, utilidad_score + 0.2)
    if utilidad.get("aplicacion", 0) > 0:
        utilidad_score = min(1.0, utilidad_score + 0.2)

    score = round((calidad_fuentes + organizacion_score + completitud_score + consistencia_interna + utilidad_score) / 5, 2)

    return {
        "agent": agent,
        "score": score,
        "dimensions": {
            "calidad_fuentes": {
                "score": calidad_fuentes,
                "justificacion": (
                    f"fuente={fuentes.get('fuente', 0)}, "
                    f"citation={fuentes.get('citation', 0)}"
                ),
            },
            "organizacion": {
                "score": organizacion_score,
                "justificacion": (
                    f"categoria={organizacion.get('categoria', 0)}, "
                    f"estructura={organizacion.get('estructura', 0)}"
                ),
            },
            "completitud": {
                "score": completitud_score,
                "justificacion": (
                    f"seccion={completitud.get('seccion', 0)}, "
                    f"cobertura={completitud.get('cobertura', 0)}"
                ),
            },
            "consistencia_interna": {
                "score": consistencia_interna,
                "justificacion": (
                    f"contradiccion={consistencia.get('contradiccion', 0)}, "
                    f"version={consistencia.get('version', 0)}"
                ),
            },
            "utilidad": {
                "score": utilidad_score,
                "justificacion": (
                    f"util={utilidad.get('util', 0)}, "
                    f"aplicacion={utilidad.get('aplicacion', 0)}"
                ),
            },
        },
    }
