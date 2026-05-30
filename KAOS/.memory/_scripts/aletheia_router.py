#!/usr/bin/env python3
"""
aletheia_router.py — Router Dinámico de Perfiles para Aletheia.

Clasifica queries de investigación según perfil (flash/standard/deep/estrategico)
usando clasificador heurístico con fallback a agy-bridge si está disponible.

Uso:
    py -3 .memory/_scripts/aletheia_router.py "Mi consulta de investigación aquí"
    # Output: {"profile": "deep", "confidence": 0.85, "reason": "query compleja con análisis profundo"}

    py -3 .memory/_scripts/aletheia_router.py "Mi consulta" --json
    # Output JSON con metadata adicional
"""

import argparse
import json
import re
import sys

# ─── Config ───────────────────────────────────────────────────────────────────
PROFILES = {
    "flash": {
        "label": "flash",
        "steps": 5,
        "temperature": 0.1,
        "tools": ["exa-search_*", "vault_*"],
        "thinking": False,
        "output_format": "json",
        "duration": "5-10 min",
        "description": "Consulta rápida, fact-checking, preguntas simples",
    },
    "standard": {
        "label": "standard",
        "steps": 10,
        "temperature": 0.2,
        "tools": ["exa-search_*", "scholar-search_*", "searxng_*", "rss-reader_*", "vault_*"],
        "thinking": True,
        "output_format": "markdown",
        "duration": "30-60 min",
        "description": "Investigación multi-fuente estándar",
    },
    "deep": {
        "label": "deep",
        "steps": 15,
        "temperature": 0.3,
        "tools": [
            "searxng_*",
            "crawl4ai_*",
            "exa-search_*",
            "scholar-search_*",
            "vault_*",
            "txtai_*",
        ],
        "thinking": True,
        "output_format": "report_with_sources",
        "duration": "1-2 hrs",
        "description": "Investigación profunda con múltiples fuentes y validación",
    },
    "massive": {
        "label": "massive",
        "steps": 20,
        "temperature": 0.2,
        "tools": [
            "crawl4ai_*",
            "searxng_*",
            "txtai_*",
            "vault_*",
            "knowledge-graph_*",
        ],
        "thinking": True,
        "output_format": "full_report",
        "duration": "4+ hrs",
        "description": "Ingesta masiva de datos con crawl total",
    },
    "estrategico": {
        "label": "estrategico",
        "steps": 18,
        "temperature": 0.1,
        "tools": [
            "searxng_*",
            "crawl4ai_*",
            "exa-search_*",
            "scholar-search_*",
            "vault_*",
            "txtai_*",
            "knowledge-graph_*",
        ],
        "thinking": True,
        "output_format": "report_with_adr",
        "duration": "3+ hrs",
        "description": "Investigación para decisiones críticas con ADR y gap feedback",
    },
}


# ─── Clasificador Heurístico ──────────────────────────────────────────────────


def classify_query(query: str) -> tuple[str, float, str]:
    """
    Clasifica una query de investigación en un perfil.

    Returns:
        tuple: (profile_name: str, confidence: float, reason: str)
    """
    query_lower = query.lower()
    word_count = len(query.split())

    # === Patrones de perfil ESTRATÉGICO ===
    strategic_patterns = [
        r"\bestrategi(a|as)\b",
        r"\bdecis(ión|ones|on)\b",
        r"\brecomendaci(o|ó)n\b",
        r"\bkaos\b",
        r"\broadmap\b",
        r"\banálisis\s*(?:foda|dafo|pestel?|porter)\b",
        r"\bplan\s*(?:estratégico|de\s*acción)\b",
        r"\b(?:mercado|competencia|industria)\s*(?:análisis|tendencia)\b",
        r"\banálisis\s*(?:competitivo|de\s*impacto)\b",
        r"\binversi(o|ó)n\b",
        r"\b(?:costo|costo\-beneficio|roi)\b",
        r"\b(?:oportunidades?|riesgos?)\b",
        r"\b(?:regulaci(o|ó)n|normativa)\b",
        r"\bfactibilidad\b",
        r"\b(?:largo\s*plazo|futuro|proyecci(o|ó)n)\b",
        r"\bmercado\s*(?:potencial|objetivo|meta)\b",
    ]
    strategic_score = sum(1 for p in strategic_patterns if re.search(p, query_lower))

    # === Patrones de perfil DEEP ===
    deep_patterns = [
        r"\binvestigaci(o|ó)n\s*(?:a\s*fondo|profunda|exhaustiva)\b",
        r"\b(?:investiga|analiza)\s*(?:a\s*fondo|en\s*profundidad|exhaustivamente)\b",
        r"\banálisis\s*(?:profundo|exhaustivo|detallado|crítico)\b",
        r"\bestado\s*(?:del\s*arte|actual)\b",
        r"\bestudio\s+detallado\b",
        r"\bcomparativ(a|as?)\s*(?:exhaustiva|detallada)\b",
        r"\brevisi(o|ó)n\s*(?:sistemática|exhaustiva|bibliográfica)\b",
        r"\b(?:tendencia|evoluci(o|ó)n)\s*(?:actual|futura)\b",
        r"\bliteratura\s*(?:científica|académica|revisi(o|ó)n)\b",
        r"\b(?:sistemático|meta\-análisis|revisi(o|ó)n\s*bibliográfica)\b",
        r"\b(?:tecnología|innovaci(o|ó)n|vanguardia)\s*(?:emergente|disruptiva)\b",
        r"\bprofundiz(a|ar)\b",
        r"\b(?:metodología|framework|paradigma)\b",
        r"\btesis\b",
        r"\bargumento\b",
        r"\bevidencia\b",
    ]
    deep_score = sum(1 for p in deep_patterns if re.search(p, query_lower))

    # === Patrones de perfil FLASH ===
    flash_patterns = [
        r"^[¿?]?(?:qué|quién|cuándo|dónde|cuál|cómo)\s+(?:es|era|fue|son|está|están|comenzó|empezó|surgió|ocurre)\b",
        r"\bresume\b",
        r"\b(?:busca|encuentra)\s*(?:rápido|rápidamente)\b",
        r"\bdefine\b",
        r"\b(?:significa|significado)\b",
        r"\b(?:fact\-check|verifica|chequea|confirm(a|ar))\b",
        r"\b(?:fecha|año|día|hora)\s*(?:de|del)\b",
        r"\b(?:precio|cuánto\s*(?:cuesta|vale|es))\b",
        r"\b(?:simple|rápido|breve|corto|corta)\b",
        r"^\b(?:dame|necesito|quiero)\s*(?:una\s*)?(?:idea|definición|explicación)\b",
    ]
    flash_score = sum(1 for p in flash_patterns if re.search(p, query_lower))

    # === Patrones perfil MASSIVE (por longitud o crawl explícito) ===
    massive_patterns = [
        r"\bcrawl\b",
        r"\bmasiv(o|a)\b",
        r"\btodo\s*(?:lo\s*)?(?:relacionado|sobre)\b",
        r"\b(?:dataset|corpus|base\s*de\s*datos)\b",
        r"\b(?:extrae|recolecta|recopila)\s*tod[oa]s?\b",
    ]
    massive_score = sum(1 for p in massive_patterns if re.search(p, query_lower))

    # === Heurística de longitud ===
    length_factor = min(word_count / 150, 1.0)  # 0..1, satura en 150 palabras

    # === Pesos por perfil ===
    scores = {
        "flash": flash_score * 2.0 + (1.0 - length_factor) if flash_score > 0 else 0,
        "standard": 1.0 + max(0, length_factor * 0.5),  # baseline
        "deep": deep_score * 2.5 + length_factor * 2.0,
        "massive": massive_score * 3.0 + (1.5 if word_count > 200 else 0) + (1.0 if word_count > 300 else 0),
        "estrategico": strategic_score * 3.0 + length_factor * 1.5,
    }

    # === Ajustes por longitud ===
    if word_count <= 10 and flash_score > 0:
        scores["flash"] += 5.0  # Boost fuerte para consultas muy cortas
    if word_count >= 80:
        scores["deep"] += 2.0
    if word_count >= 150:
        scores["deep"] += 1.5
    if word_count >= 200:
        scores["massive"] += 3.0

    # === Ajustes por palabras clave específicas ===
    if any(kw in query_lower for kw in ["estrategia", "decisión", "recomendación"]):
        scores["estrategico"] += 2.0
    if "impacto" in query_lower and any(kw in query_lower for kw in ["mercado", "inversión", "negocio", "competencia", "costo", "roi", "estrategia"]):
        scores["estrategico"] += 2.0
    if any(kw in query_lower for kw in ["qué es", "quién es", "resume", "busca rápido"]):
        scores["flash"] += 3.0
    if any(kw in query_lower for kw in ["investiga a fondo", "análisis profundo", "estado del arte"]):
        scores["deep"] += 4.0
    if any(kw in query_lower for kw in ["crawl", "todo sobre", "masivo"]):
        scores["massive"] += 4.0

    # === Selección ===
    best_profile = max(scores, key=scores.get)
    best_score = scores[best_profile]
    second_best = sorted(scores.values())[-2] if len(scores) > 1 else 0

    # Calcular confianza: tan cerca del segundo mejor, menos confianza
    if best_score == 0:
        confidence = 0.5
        best_profile = "standard"
        reason = "query genérica sin patrones detectados → perfil default"
    else:
        margin = best_score - second_best
        confidence = min(0.5 + margin * 0.1, 0.99)
        if best_profile == "flash":
            reason = f"pregunta directa/dato concreto (score flash={best_score:.1f})"
        elif best_profile == "standard":
            reason = f"consulta de profundidad media (score={best_score:.1f})"
        elif best_profile == "deep":
            reason = f"investigación compleja con análisis profundo (score deep={best_score:.1f})"
        elif best_profile == "massive":
            reason = f"necesidad de crawl masivo (score massive={best_score:.1f})"
        elif best_profile == "estrategico":
            reason = f"decisión estratégica con análisis de impacto (score={best_score:.1f})"

    return best_profile, round(confidence, 2), reason


# ─── CLI ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Router Dinámico de Perfiles para Aletheia",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            '  py -3 .memory/_scripts/aletheia_router.py "¿Qué es el aprendizaje profundo?"\n'
            '  py -3 .memory/_scripts/aletheia_router.py "Investigación detallada sobre cambio climático" --json\n'
            '  py -3 .memory/_scripts/aletheia_router.py "Estrategia de mercado para IA en 2026" --profile-only\n'
        ),
    )
    parser.add_argument("query", nargs="?", help="Consulta de investigación a clasificar")
    parser.add_argument("--json", action="store_true", help="Output completo en JSON")
    parser.add_argument("--profile-only", action="store_true", help="Output solo nombre del perfil")
    parser.add_argument("--list-profiles", action="store_true", help="Listar perfiles disponibles")
    parser.add_argument("--stdin", action="store_true", help="Leer query desde stdin")

    args = parser.parse_args()

    # List profiles mode
    if args.list_profiles:
        print(json.dumps(PROFILES, indent=2, ensure_ascii=False))
        return

    # Get query
    query = args.query
    if (args.stdin or not query) and not sys.stdin.isatty():
        query = sys.stdin.read().strip()

    if not query:
        parser.print_help()
        sys.exit(1)

    # Classify
    profile, confidence, reason = classify_query(query)
    profile_info = PROFILES.get(profile, {})

    # Output
    result = {
        "profile": profile,
        "confidence": confidence,
        "reason": reason,
        "details": profile_info,
    }

    if args.profile_only:
        print(profile)
    elif args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
