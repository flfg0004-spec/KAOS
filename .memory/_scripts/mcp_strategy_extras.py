#!/usr/bin/env python3
"""Extended strategy MCP server — SWOT, BMC, Planning, Goal Health.

Provides the tools from business-design-mcp and agent-planner-mcp 
that are not available as installable packages.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None

BASE = Path(__file__).resolve().parent.parent.parent


def _extract_keywords(text: str, top_n: int = 20) -> list[str]:
    from collections import Counter
    words = re.findall(r"\w{4,}", text.lower())
    stop = {"este", "esta", "esto", "para", "como", "entre", "sobre", "tiene",
            "puede", "debe", "muy", "son", "han", "era", "ser", "del", "los",
            "las", "con", "por", "que", "una"}
    filtered = [w for w in words if w not in stop]
    return [w for w, _ in Counter(filtered).most_common(top_n)]


def create_swot_analysis(context: str, industry: str = "") -> dict:
    """Perform SWOT analysis based on context and industry."""
    keywords = _extract_keywords(context, top_n=25)
    tech_words = {"escalabilidad", "rendimiento", "seguridad", "arquitectura", "api",
                  "microservicios", "nube", "datos", "automatización", "ia"}
    biz_words = {"mercado", "competencia", "cliente", "ingreso", "crecimiento",
                 "costo", "eficiencia", "recurso", "talento"}

    strengths = [w for w in keywords if w in tech_words | biz_words][:5]
    weaknesses = [w for w in keywords if w in {"deuda", "limitación", "error", "lento", "riesgo"}][:4]
    opportunities = [w for w in keywords if w in {"oportunidad", "crecimiento", "mejora", "innovación", "mercado", "tendencia"}][:4]
    threats = [w for w in keywords if w in {"amenaza", "competencia", "riesgo", "regulación", "cambio"}][:3]

    return {
        "framework": "SWOT",
        "industry": industry or "general",
        "matrix": {
            "strengths": strengths or ["Análisis detallado requerido"],
            "weaknesses": weaknesses or ["Análisis detallado requerido"],
            "opportunities": opportunities or ["Análisis detallado requerido"],
            "threats": threats or ["Análisis detallado requerido"],
        },
        "insights": [
            f"Fortalezas clave: {', '.join(strengths[:3])}" if strengths else "Identificar fortalezas",
            f"Oportunidades: {', '.join(opportunities[:2])}" if opportunities else "Explorar oportunidades",
        ],
        "next_steps": [
            "Validar cada fortaleza con datos cuantitativos",
            "Priorizar debilidades por impacto",
            "Crear plan de mitigación para amenazas",
        ],
        "confidence": "Media",
    }


def create_business_model_canvas(product: str, target_market: str, value_prop: str) -> dict:
    """Generate a Business Model Canvas for a product/service."""
    return {
        "framework": "Business Model Canvas",
        "canvas": {
            "value_proposition": value_prop,
            "customer_segments": [target_market],
            "channels": ["Por definir"],
            "customer_relationships": ["Por definir"],
            "revenue_streams": ["Por definir"],
            "key_resources": ["Equipo", "Tecnología"],
            "key_activities": [f"Desarrollar {product}"],
            "key_partners": ["Por definir"],
            "cost_structure": ["Por definir"],
        },
        "coherence_assessment": "Requiere revisión con datos reales",
        "critical_gaps": [
            "Canales de distribución no definidos",
            "Estructura de costos incompleta",
        ],
        "next_steps": [
            "Validar propuesta de valor con clientes potenciales",
            "Definir canales de distribución",
            "Estimar estructura de costos",
        ],
        "confidence": "Baja",
    }


def create_plan(objective: str, context: str = "", constraints: str = "") -> dict:
    """Create a structured plan from an objective with dependency graph."""
    steps = [
        f"1. Investigar y analizar {objective}",
        f"2. Diseñar solución para {objective}",
        f"3. Implementar componentes de {objective}",
        "4. Validar y probar resultados",
        "5. Iterar basado en feedback",
    ]
    return {
        "framework": "Structured Plan",
        "objective": objective,
        "steps": steps,
        "dependencies": {s: [steps[i-1]] for i, s in enumerate(steps) if i > 0},
        "critical_path": steps[:3],
        "estimated_effort": "Por determinar",
        "next_steps": [steps[0]] if steps else [],
        "confidence": "Media",
    }


def analyze_impact(change: str, plan_summary: str) -> dict:
    """Analyze impact of a change on an existing plan."""
    return {
        "framework": "Impact Analysis",
        "change": change,
        "affected_areas": ["Cronograma", "Recursos", "Alcance"],
        "severity": "Media",
        "mitigation": "Revisar plan y ajustar dependencias",
        "recommendation": "Evaluar trade-offs antes de proceder",
        "confidence": "Media",
    }


def check_goals_health(okrs: list[dict]) -> dict:
    """Check health of OKRs against quality criteria."""
    checks = []
    for i, okr in enumerate(okrs):
        objective = okr.get("objective", "")
        krs = okr.get("key_results", [])
        has_numeric = any(bool(re.search(r"\d+", kr)) for kr in krs)
        check = {
            "okr_index": i,
            "objective": objective[:60],
            "has_krs": len(krs) > 0,
            "has_numeric_targets": has_numeric,
            "is_specific": len(objective) > 20,
            "health": "good" if (len(krs) > 0 and has_numeric) else "needs_improvement",
        }
        checks.append(check)

    healthy = sum(1 for c in checks if c["health"] == "good")
    return {
        "framework": "OKR Health Check",
        "total_okrs": len(okrs),
        "healthy": healthy,
        "needs_improvement": len(okrs) - healthy,
        "checks": checks,
        "recommendation": "Revisar OKRs sin targets numéricos" if healthy < len(okrs) else "OKRs saludables",
        "confidence": "Alta",
    }


def main():
    if FastMCP is None:
        print("ERROR: fastmcp not installed. Run: pip install fastmcp", file=sys.stderr)
        sys.exit(1)

    mcp = FastMCP("strategy-extras")

    mcp.tool()(create_swot_analysis)
    mcp.tool()(create_business_model_canvas)
    mcp.tool()(create_plan)
    mcp.tool()(analyze_impact)
    mcp.tool()(check_goals_health)

    mcp.run()


if __name__ == "__main__":
    main()
