"""Golden dataset for Aletheia Router — 50 labeled queries for profile validation.
Each entry: (query, expected_profile, difficulty)
"""
GOLDEN_DATASET = [
    # ── FLASH (10 queries) ──
    ("¿Qué es el aprendizaje automático?", "flash", "facil"),
    ("¿Quién escribió Cien años de soledad?", "flash", "facil"),
    ("Resume el teorema de Pitágoras", "flash", "facil"),
    ("Define qué es una API REST", "flash", "facil"),
    ("¿Cuándo comenzó la Segunda Guerra Mundial?", "flash", "facil"),
    ("¿Cuánto cuesta un iPhone 15?", "flash", "facil"),
    ("Busca rápido el significado de 'ontología'", "flash", "facil"),
    ("Dame una definición de machine learning", "flash", "facil"),
    ("Fact-check: ¿el Everest es la montaña más alta?", "flash", "facil"),
    ("¿Dónde está la sede de la ONU?", "flash", "facil"),

    # ── STANDARD (10 queries) ──
    ("Análisis de la situación política en América Latina 2026", "standard", "media"),
    ("Tendencias de inteligencia artificial en la industria financiera", "standard", "media"),
    ("Comparativa entre metodologías ágiles y tradicionales", "standard", "media"),
    ("Impacto del cambio climático en la agricultura del sur global", "standard", "media"),
    ("Panorama actual del comercio electrónico en mercados emergentes", "standard", "media"),
    ("Historia de la filosofía occidental: principales corrientes", "standard", "media"),
    ("Aplicaciones de blockchain en la cadena de suministro", "standard", "media"),
    ("Análisis de la brecha digital en zonas rurales", "standard", "media"),
    ("Evolución del concepto de privacidad en la era digital", "standard", "media"),
    ("Revisión bibliográfica sobre psicología cognitiva y aprendizaje", "deep", "alta"),

    # ── DEEP (10 queries) ──
    ("Estado del arte en transformers para procesamiento de lenguaje natural", "deep", "alta"),
    ("Análisis exhaustivo de la evolución de los modelos de lenguaje", "deep", "alta"),
    ("Revisión sistemática de la literatura sobre computación cuántica", "deep", "alta"),
    ("Estado actual de la investigación en fusión nuclear", "deep", "alta"),
    ("Meta-análisis sobre efectividad de terapias cognitivo-conductuales", "deep", "alta"),
    ("Investigación profunda sobre los fundamentos de la teoría de cuerdas", "deep", "alta"),
    ("Análisis crítico de la metodología Scrum en equipos distribuidos", "deep", "alta"),
    ("Estudio detallado de la ética en inteligencia artificial autónoma", "deep", "alta"),
    ("Revisión exhaustiva del impacto de la pandemia en la salud mental", "deep", "alta"),
    ("Investigación a fondo sobre arquitecturas de microservicios", "deep", "alta"),

    # ── MASSIVE (5 queries) ──
    ("Crawl todo el sitio web del proyecto GNU y extrae su documentación completa", "massive", "alta"),
    ("Dataset completo de artículos académicos sobre cambio climático 2020-2026", "massive", "alta"),
    ("Recopila todas las referencias bibliográficas de la filosofía estoica", "massive", "alta"),
    ("Extrae todos los papers publicados sobre transformers en 2025", "massive", "alta"),
    ("Base de datos de todas las APIs públicas de machine learning", "massive", "alta"),

    # ── ESTRATÉGICO (10 queries) ──
    ("Estrategia de mercado para lanzar un SaaS de IA en Latinoamérica 2026", "estrategico", "alta"),
    ("Análisis FODA del mercado de vehículos eléctricos en Europa 2026", "estrategico", "alta"),
    ("Recomendación de inversión en tecnologías de energía renovable", "estrategico", "alta"),
    ("Plan estratégico para la transformación digital de una PYME industrial", "estrategico", "alta"),
    ("Análisis de impacto de regulaciones GDPR en plataformas de IA", "estrategico", "alta"),
    ("Estudio de factibilidad para un centro de datos sostenible", "estrategico", "alta"),
    ("Evaluación de riesgos y oportunidades en el mercado fintech 2026", "estrategico", "alta"),
    ("Roadmap de innovación tecnológica para el sector salud en 2027", "estrategico", "alta"),
    ("Análisis competitivo del mercado de asistentes virtuales empresariales", "estrategico", "alta"),
    ("Proyección de escenarios para la adopción de IA generativa 2026-2030", "estrategico", "alta"),

    # ── BORDERLINE (5 queries para probar casos ambiguos) ──
    ("Hola", "standard", "borderline"),
    ("Prueba", "standard", "borderline"),
    ("Estrategia", "estrategico", "borderline"),
    ("", "standard", "borderline"),
    ("Análisis", "standard", "borderline"),
]


def run_golden_validation():
    """Run the golden dataset against the router and return accuracy stats."""
    import sys
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
    from aletheia_router import classify_query

    results = {"correct": 0, "total": 0, "by_profile": {}, "by_difficulty": {}}
    for query, expected, difficulty in GOLDEN_DATASET:
        profile, confidence, _ = classify_query(query)
        is_correct = profile == expected
        results["total"] += 1
        if is_correct:
            results["correct"] += 1
        results["by_profile"].setdefault(expected, {"correct": 0, "total": 0})
        results["by_profile"][expected]["total"] += 1
        if is_correct:
            results["by_profile"][expected]["correct"] += 1
        results["by_difficulty"].setdefault(difficulty, {"correct": 0, "total": 0})
        results["by_difficulty"][difficulty]["total"] += 1
        if is_correct:
            results["by_difficulty"][difficulty]["correct"] += 1
    results["accuracy"] = round(results["correct"] / max(results["total"], 1) * 100, 1)
    return results


if __name__ == "__main__":
    import json
    r = run_golden_validation()
    print(json.dumps(r, indent=2))
    print(f"\nAccuracy: {r['accuracy']}% ({r['correct']}/{r['total']})")
