"""Kosmos Self-Evaluation — measures architectural analysis quality across 5 dimensions."""

import logging
import re

_LOG = logging.getLogger(__name__)


def _check_architectural_structure(text: str) -> dict:
    patterns = {
        "components": r"(?:component|module|service|sistema|system|entidad|entity)",
        "relationships": r"(?:relacion|relation|dependenc|conexion|connect|interface|api)",
        "context": r"(?:contexto|context|entorno|environment|boundary|limite|frontera)",
        "layers": r"(?:capa|layer|nivel|tier|nodo|node)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_technical_depth(text: str) -> dict:
    patterns = {
        "coupling": r"(?:acoplam|coupling|tight|loose|desacopl)",
        "scalability": r"(?:escalab|scalab|horizontal|vertical|throughput|rendimient)",
        "security": r"(?:seguridad|security|autentic|auth|permiso|permisos|token|ssl|tls)",
        "performance": r"(?:performance|rendimiento|latencia|latency|velocidad|speed|optimiz)",
        "availability": r"(?:disponibilidad|availability|failover|redundan|ha\b)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_recommendations(text: str) -> dict:
    patterns = {
        "recommendations": r"(?:recomend|recommend|sugerenc|suggest|propongo|proposal)",
        "risks": r"(?:riesgo|risk|peligro|danger|threat|amenaza)", 
        "actions": r"(?:acción|action|implementar|implement|cambiar|change|migrar|migrate)",
        "priorities": r"(?:prioridad|priority|critic|urgente|critical|importante)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_coverage(text: str) -> dict:
    sections = [
        r"^##\s*Contexto",
        r"^##\s*Decisi",
        r"^##\s*Opciones",
        r"^##\s*Alternativas",
        r"^##\s*Consecuencias",
        r"^##\s*Recomend",
        r"^##\s*Diagram",
        r"^##\s*Análisis",
        r"^##\s*Arquitectura",
        r"^##\s*Referencias",
        r"^##\s*Conclusi",
        r"^##\s*Resumen",
        r"^#\s",
    ]
    found = []
    for pat in sections:
        matches = re.findall(pat, text, re.MULTILINE | re.IGNORECASE)
        found.extend(matches)
    return {"section_count": len(found), "sections": found}


def _check_consistency(text: str) -> dict:
    contradiction_pairs = [
        (r"\bmicroservicio", r"\bmonolito"),
        (r"\bsql\b", r"\bnosql\b"),
        (r"\brest\b", r"\bgraphql\b"),
        (r"\bsíncrono", r"\basíncrono"),
    ]
    contradictions = 0
    for a, b in contradiction_pairs:
        has_a = bool(re.search(a, text, re.IGNORECASE))
        has_b = bool(re.search(b, text, re.IGNORECASE))
        if has_a and has_b:
            contradictions += 1
    terms = re.findall(r"\b(?:recomendamos|decidimos|optamos|elegimos|proponemos)\b", text, re.IGNORECASE)
    return {
        "contradiction_pairs": contradictions,
        "decision_terms": len(terms),
    }


def kosmos_self_eval(agent: str, output: dict) -> dict:
    output = output or {}
    content = output.get("content", "")
    analysis = output.get("analysis", "")
    recommendations = output.get("recommendations", "")
    diagrams = output.get("diagrams", [])
    evaluation = output.get("evaluation", {})

    text = content or analysis or ""
    if not text:
        return {
            "agent": agent,
            "score": 0.0,
            "dimensions": {
                "claridad_arquitectonica": {"score": 0.0, "justificacion": "No content provided"},
                "profundidad_tecnica": {"score": 0.0, "justificacion": "No content provided"},
                "accionabilidad": {"score": 0.0, "justificacion": "No content provided"},
                "completitud": {"score": 0.0, "justificacion": "No content provided"},
                "consistencia": {"score": 0.0, "justificacion": "No content provided"},
            },
        }

    structure = _check_architectural_structure(text)
    tech_depth = _check_technical_depth(text)
    rec_info = _check_recommendations(text)
    coverage = _check_coverage(text)
    consistency = _check_consistency(text)

    total_rel = sum(structure.values())
    claridad_arquitectonica = min(1.0, 0.3 + 0.1 * min(total_rel, 7))
    if coverage["section_count"] >= 3:
        claridad_arquitectonica = min(1.0, claridad_arquitectonica + 0.2)

    tech_total = sum(tech_depth.values())
    profundidad_tecnica = min(1.0, 0.2 + 0.1 * min(tech_total, 8))
    if tech_depth.get("coupling", 0) > 0:
        profundidad_tecnica = min(1.0, profundidad_tecnica + 0.1)
    if tech_depth.get("scalability", 0) > 0:
        profundidad_tecnica = min(1.0, profundidad_tecnica + 0.1)
    if tech_depth.get("security", 0) > 0:
        profundidad_tecnica = min(1.0, profundidad_tecnica + 0.1)

    rec_total = sum(rec_info.values())
    accionabilidad = min(1.0, 0.2 + 0.1 * min(rec_total, 8))
    if rec_info.get("recommendations", 0) > 1:
        accionabilidad = min(1.0, accionabilidad + 0.2)
    if rec_info.get("risks", 0) > 0:
        accionabilidad = min(1.0, accionabilidad + 0.1)
    if recommendations:
        accionabilidad = min(1.0, accionabilidad + 0.1)
    if diagrams:
        accionabilidad = min(1.0, accionabilidad + 0.1)

    completitud = 0.3
    if coverage["section_count"] >= 2:
        completitud = 0.5
    if coverage["section_count"] >= 4:
        completitud = 0.7
    if coverage["section_count"] >= 6:
        completitud = 0.9
    if coverage["section_count"] >= 8:
        completitud = 1.0
    if evaluation and evaluation.get("passed"):
        completitud = min(1.0, completitud + 0.1)
    text_len = len(text)
    if text_len > 1500:
        completitud = min(1.0, completitud + 0.05)

    conflict_score = consistency.get("contradiction_pairs", 0)
    consistencia = 1.0
    if conflict_score > 0:
        consistencia = max(0.0, 1.0 - 0.2 * conflict_score)
    if consistency.get("decision_terms", 0) > 2:
        consistencia = min(1.0, consistencia + 0.1)

    score = round((claridad_arquitectonica + profundidad_tecnica + accionabilidad + completitud + consistencia) / 5, 2)

    return {
        "agent": agent,
        "score": score,
        "dimensions": {
            "claridad_arquitectonica": {
                "score": claridad_arquitectonica,
                "justificacion": (
                    f"{total_rel} architectural signals "
                    f"(components={structure.get('components', 0)}, "
                    f"relationships={structure.get('relationships', 0)})"
                ),
            },
            "profundidad_tecnica": {
                "score": profundidad_tecnica,
                "justificacion": (
                    f"coupling={tech_depth.get('coupling', 0)}, "
                    f"scalability={tech_depth.get('scalability', 0)}, "
                    f"security={tech_depth.get('security', 0)}"
                ),
            },
            "accionabilidad": {
                "score": accionabilidad,
                "justificacion": (
                    f"recommendations={rec_info.get('recommendations', 0)}, "
                    f"risks={rec_info.get('risks', 0)}, "
                    f"actions={rec_info.get('actions', 0)}, "
                    f"diagrams={len(diagrams)}"
                ),
            },
            "completitud": {
                "score": completitud,
                "justificacion": (
                    f"{coverage['section_count']} sections, "
                    f"{text_len} chars, "
                    f"eval_passed={bool(evaluation and evaluation.get('passed'))}"
                ),
            },
            "consistencia": {
                "score": consistencia,
                "justificacion": (
                    f"{conflict_score} potential contradictions, "
                    f"{consistency.get('decision_terms', 0)} decision terms"
                ),
            },
        },
    }
