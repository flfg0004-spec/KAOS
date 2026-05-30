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

    # ── SIMULATION MODE (5 queries) ──
    ("Pipeline de simulación RAG con aletheia y kratos", "standard", "media"),
    ("Simular pipeline de arquitectura con kosmos y metis", "standard", "media"),
    ("Demo de pipeline multi-agente con 5 agentes en simulación", "standard", "alta"),
    ("Prueba de simulación de pipeline cancelado en ejecución", "standard", "media"),
    ("Test de simulación con timeout recovery automático", "standard", "media"),

    # ── PIPELINE 10+ NODES (5 queries) ──
    ("Pipeline completo de calidad con aletheia kratos kosmos metis mnemosyne kronos", "standard", "alta"),
    ("Orquestación de 12 agentes para análisis de código legacy", "standard", "alta"),
    ("Pipeline de investigación masiva con 15 nodos de búsqueda y síntesis", "massive", "alta"),
    ("Cadena de verificación cruzada con 10 agentes de revisión", "standard", "alta"),
    ("Pipeline jerárquico de estrategia con análisis, ADR y síntesis", "estrategico", "alta"),

    # ── CANCELACIÓN EN EJECUCIÓN (5 queries) ──
    ("Cancelar pipeline de búsqueda después del primer agente", "standard", "media"),
    ("Detener análisis profundo a mitad del proceso de investigación", "deep", "media"),
    ("Cancelar despliegue de pipeline multi-agente por cambio de prioridad", "standard", "media"),
    ("Abortar síntesis de documentos por timeout del modelo principal", "standard", "media"),
    ("Interrumpir pipeline de curación por conflicto de fuentes", "standard", "media"),

    # ── TIMEOUT RECOVERY (5 queries) ──
    ("Recuperar pipeline después de timeout del modelo go-kimi-latest", "standard", "alta"),
    ("Reintentar nodo fallido con fallback a go-flash tras timeout", "standard", "media"),
    ("Pipeline con timeout de 5 segundos por nodo y retry exponencial", "standard", "media"),
    ("Recuperación automática tras fallo de 3 nodos concurrentes", "standard", "alta"),
    ("Timeout en agente de investigación con fallback a modelo más rápido", "flash", "media"),

    # ── PRIORITY SORTING (5 queries) ──
    ("Pipeline crítico de seguridad que debe ejecutarse primero", "standard", "media"),
    ("Tarea de baja prioridad para análisis de métricas semanales", "standard", "facil"),
    ("Pipeline de alta prioridad para parche de seguridad urgente", "standard", "facil"),
    ("Ordenar 20 pipelines por prioridad crítica alta normal baja", "standard", "alta"),
    ("Pipeline normal de mantenimiento con dependencias de otros pipelines", "standard", "media"),

    # ── CROSS_CHECK + VERIFY (5 queries) ──
    ("Verificación cruzada de resultados entre aletheia y kosmos", "standard", "alta"),
    ("Validación de hechos con múltiples fuentes independientes", "standard", "media"),
    ("Doble verificación de referencias bibliográficas en paper de IA", "standard", "alta"),
    ("Cross-check de datos financieros entre 3 fuentes distintas", "standard", "alta"),
    ("Verificación de consistencia en pipeline multi-agente completo", "standard", "alta"),

    # ── FALLBACK CHAIN ROUTING (5 queries) ──
    ("Ruteo automático a go-gemini-flash por ser tarea de lint rápido", "flash", "facil"),
    ("Fallback de go-pro a go-mimo cuando el modelo principal está saturado", "standard", "media"),
    ("Router con cadena de 6 modelos para máxima resiliencia", "standard", "alta"),
    ("Enrutamiento de tarea factual directamente a go-pro con thinking high", "standard", "alta"),
    ("Selección de modelo según costo: preferir go-mimo para tareas extractivas", "estrategico", "media"),

    # ── EDGE CASES (5 queries) ──
    ("", "standard", "borderline"),
    ("a", "standard", "borderline"),
    ("ñ", "standard", "borderline"),
    ("12345", "standard", "borderline"),
    ("¿?", "standard", "borderline"),

    # ── MULTI-AGENT PIPELINES (5 queries) ──
    ("Pipeline de 4 agentes: aletheia investiga, kratos implementa, kosmos revisa, metis estratégia", "standard", "alta"),
    ("Flujo de trabajo agente-especialista con 3 niveles de revisión", "standard", "media"),
    ("Orquestación de agentes para generación de documentación técnica completa", "standard", "media"),
    ("Pipeline colaborativo entre aletheia y mnemosyne para curación de conocimiento", "standard", "media"),
    ("Sistema multi-agente con routing dinámico según carga de trabajo", "standard", "alta"),

    # ── ERROR RECOVERY (5 queries) ──
    ("Pipeline con reintento automático tras error de conexión", "standard", "media"),
    ("Recuperación de pipeline tras corrupción de estado en nodo intermedio", "standard", "alta"),
    ("Manejo de error en agente con escalado a modelo de respaldo", "standard", "media"),
    ("Pipeline degradado: continuar con agentes restantes si uno falla", "standard", "media"),
    ("Re-ejecución inteligente solo de nodos fallidos en pipeline completo", "standard", "alta"),
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
