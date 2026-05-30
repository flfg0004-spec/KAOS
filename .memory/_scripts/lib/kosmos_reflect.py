"""kosmos_reflect.py — Ciclo de Reflexión de KosmosV2 (Post-ADR).

Checklist de 10 puntos para auto-crítica post-ADR. Cada punto tiene un peso
específico y evalúa un aspecto concreto de la calidad del ADR. Al final se
obtiene un score compuesto 0-100 y un plan de mejora.

Registro persistente en ``.memory/cache/kosmos/reflections.json``.
"""

import json
import logging
import math
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default paths
REFLECTIONS_DIR = Path(__file__).resolve().parent.parent.parent / "cache" / "kosmos"
REFLECTIONS_FILE = REFLECTIONS_DIR / "reflections.json"

# ── Checklist: 10 items with weight (total = 100) and detection patterns ──

CHECKLIST: list[dict[str, Any]] = [
    {
        "id": "frontmatter",
        "label": "Frontmatter YAML completo",
        "weight": 5,
        "description": "El ADR tiene frontmatter YAML (--- ... ---) con id, title, status, date, tags",
        "patterns": [
            r'^---\s*\n',
            r'id:\s*',
            r'title:\s*',
            r'status:\s*',
            r'date:\s*',
        ],
    },
    {
        "id": "contexto_problemas",
        "label": "Contexto con ≥3 problemas",
        "weight": 10,
        "description": "El contexto incluye al menos 3 problemas, motivaciones o drivers",
        "min_count": 3,
        "patterns": [
            r'(?:problema|issue|desafío|challenge|necesidad|need|motivaci[óo]n|reason|driver|pain\s*point)',
        ],
    },
    {
        "id": "opciones_multiples",
        "label": "≥3 opciones consideradas",
        "weight": 15,
        "description": "Se consideraron al menos 3 opciones o alternativas",
        "min_count": 3,
        "patterns": [
            r'(?:^|\n)\s*(?:#+|[-\*])\s*(?:Opcion|Option|Alternativa|Alternative)',
            r'(?:^|\n)\s*\d+[.)]\s+',
            r'(?:^|\n)\s*[-*]\s+\*\*',
        ],
        "section_keywords": ["opcion", "option", "alternativa", "alternative"],
    },
    {
        "id": "decision_justificada",
        "label": "Decisión con justificación explícita",
        "weight": 10,
        "description": "La decisión tiene justificación explícita con razones",
        "patterns": [
            r'^##\s*(?:Decisi[oó]n|Decision)',
            r'(?:decidim[oó]s|decided|optamos|elegimos|se\s+decidi[oó])',
            r'(?:porque|because|ya que|since|dado que|debido a)',
            r'(?:basado en|based on|fundamentado en)',
        ],
    },
    {
        "id": "consecuencias_ambas",
        "label": "Consecuencias positivas Y negativas",
        "weight": 10,
        "description": "Las consecuencias incluyen tanto aspectos positivos como negativos",
        "patterns": [
            r'^##\s*(?:Consecuencias|Consequences|Impacto)',
            r'(?:positiv[oa]|positive|beneficio|benefit|ventaja)',
            r'(?:negativ[oa]|negative|desventaja|drawback|riesgo|risk|contra)',
        ],
        "both_required": True,
    },
    {
        "id": "diagrama_presente",
        "label": "Diagrama presente y legible",
        "weight": 15,
        "description": "El diagrama está presente y es legible (Mermaid, Excalidraw, o ASCII)",
        "patterns": [
            r'```mermaid',
            r'```plantuml',
            r'```puml',
            r'^##\s*Diagram',
            r'(?:graph\s+(?:TD|LR|RL|BT))',
            r'(?:subgraph\s+\w+)',
            r'┌[─]+┐',   # ASCII box-drawing
            r'\+[-+]+\+',
        ],
    },
    {
        "id": "referencias_correctas",
        "label": "Referencias a ADRs existentes correctas",
        "weight": 10,
        "description": "Las referencias a ADRs existentes son correctas y verificables",
        "patterns": [
            r'ADR-\d+',
            r'\[\[ADR-',
            r'(?:referencia|reference|ver|see)\s*(?:ADR|adr)',
        ],
    },
    {
        "id": "l0_consultada",
        "label": "L0 consultada para contexto histórico",
        "weight": 10,
        "description": "Se consultó L0 para contexto histórico (referencias a ADRs previos)",
        "patterns": [
            r'ADR-\d+',
            r'\[\[\w+',  # wikilinks
            r'(?:basado en|basándose en|building on|tomando como referencia)',
            r'(?:previamente|anteriormente|previously|históricamente)',
            r'(?:véase|see also|ver también|relacionado|related)',
        ],
    },
    {
        "id": "metricas_cuantificables",
        "label": "Métricas o scores cuantificables",
        "weight": 10,
        "description": "Incluye métricas o scores cuantificables (números, porcentajes)",
        "patterns": [
            r'\d+%',
            r'\d+\.?\d*\s*(?:ms|s|gb|mb|kb|hz|rps|tps|qps)',
            r'(?:score|puntaje|métrica|metric|kpi|indicador)',
            r'(?:precisión|accuracy|latencia|throughput|cobertura|coverage)',
            r'(?:disminuci[oó]n|reducción|reduction|increase|aumento)\s+(?:del|de|of)\s+\d+',
        ],
    },
    {
        "id": "feedback_loop",
        "label": "Feedback loop con al menos un agente",
        "weight": 5,
        "description": "Se ejecutó feedback loop con al menos un agente",
        "patterns": [
            r'(?:feedback|retroalimentación|review|revisión|iteración)',
            r'(?:critic|crítica|evaluación|evaluation|assessment)',
            r'(?:aprobado por|approved by|validado por|validated by)',
            r'(?:agente|agent)\s*(?:involucrado|involved|consultado|consulted)',
            r'(?:revisado por|reviewed by|checked by)',
        ],
    },
]

# Pattern used to extract checkboxes from ADR sections
_RE_SECTION = re.compile(r'^##\s+(.+)$', re.MULTILINE)
_RE_LIST_ITEM = re.compile(r'^\s*[-*\d]+[.)]\s+(.*)$', re.MULTILINE)
_RE_BOLD = re.compile(r'\*\*(.+?)\*\*')


@dataclass
class ReflectionReport:
    """Reporte de reflexión para un ADR.

    Attributes:
        checklist_scores: Score por cada item del checklist (0-100).
        total_score: Score total ponderado (0-100).
        gaps: Items con score < 70%.
        improvement_plan: 3 acciones concretas de mejora.
        timestamp: ISO timestamp.
        adr_title: Título del ADR evaluado.
        pattern_matches: Patrones recurrentes detectados.
    """
    checklist_scores: dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0
    gaps: list[str] = field(default_factory=list)
    improvement_plan: list[str] = field(default_factory=list)
    timestamp: str = ""
    adr_title: str = ""
    pattern_matches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dict."""
        return asdict(self)

    def summary(self) -> str:
        """Return a human-readable summary."""
        status = "✅" if self.total_score >= 70 else "⚠️" if self.total_score >= 40 else "❌"
        return (
            f"{status} Reflection: score={self.total_score:.1f}/100, "
            f"gaps={len(self.gaps)}, plan={len(self.improvement_plan)} items"
        )


class ReflectionEngine:
    """Motor de reflexión para ADRs de KosmosV2.

    Evalúa un ADR contra un checklist de 10 puntos, genera planes de mejora,
    y mantiene un registro histórico de reflexiones para detectar tendencias.
    """

    def __init__(self, memory: Any = None) -> None:
        """Initialize the Reflection Engine.

        Args:
            memory: Optional ArchitectureMemoryL0 instance for cross-referencing.
        """
        self._memory = memory
        self._reflections_file = REFLECTIONS_FILE
        self._reflections_file.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("ReflectionEngine initialized")

    def evaluate_adr(self, adr_text: str) -> ReflectionReport:
        """Evaluate an ADR text against the 10-point checklist.

        Args:
            adr_text: The full ADR markdown text to evaluate.

        Returns:
            ReflectionReport with scores, gaps, and improvement plan.
        """
        if not adr_text or not adr_text.strip():
            return ReflectionReport(
                total_score=0.0,
                gaps=["empty ADR text"],
                improvement_plan=["Write ADR content first"],
                timestamp=datetime.now().isoformat(),
                adr_title="(empty)",
            )

        text_lower = adr_text.lower()
        scores: dict[str, float] = {}
        gaps: list[str] = []
        all_patterns: list[str] = []

        for item in CHECKLIST:
            item_id = item["id"]
            weight = item["weight"]
            patterns = item.get("patterns", [])
            min_count = item.get("min_count", 1)
            section_keywords = item.get("section_keywords", [])
            both_required = item.get("both_required", False)

            # Count pattern hits
            hits = 0
            for pat in patterns:
                matches = re.findall(pat, adr_text, re.MULTILINE | re.IGNORECASE)
                hits += len(matches)

            # Check for section keyword presence
            has_section_keyword = False
            if section_keywords:
                for kw in section_keywords:
                    if re.search(rf'^##\s*\w*{kw}\w*', adr_text, re.MULTILINE | re.IGNORECASE):
                        has_section_keyword = True
                        hits += 2  # bonus for having the section
                        break

            # Calculate score for this item
            if both_required:
                # Need both positive and negative patterns to match
                has_positive = bool(
                    re.search(r'(?:positiv[oa]|positive|beneficio|benefit|ventaja)', text_lower)
                )
                has_negative = bool(
                    re.search(r'(?:negativ[oa]|negative|desventaja|drawback|riesgo|risk|contra)', text_lower)
                )
                if has_positive and has_negative:
                    item_score = 100.0
                elif has_positive or has_negative:
                    item_score = 50.0
                else:
                    item_score = 0.0
            elif min_count > 1:
                # Need at least min_count items
                item_score = min(100.0, (hits / min_count) * 100.0)
            else:
                # Binary: found at least one pattern?
                max_possible_weight = min(hits, 3)  # cap at 3 pattern matches
                item_score = min(100.0, max_possible_weight * 40.0)  # each match = 40 pts up to 100

            # Ensure minimum for section existence
            if has_section_keyword and item_score < 50:
                item_score = max(item_score, 50.0)

            scores[item_id] = round(item_score, 1)

            # Record patterns found for trend analysis
            if hits > 0:
                all_patterns.append(f"{item_id}:{hits}")

            # Detect gap (score < 70%)
            if item_score < 70.0:
                gaps.append(f"{item['label']} ({item_score:.0f}/100)")

        # Weighted total
        total_weight = sum(item["weight"] for item in CHECKLIST)
        weighted_score = sum(
            scores[item["id"]] * (item["weight"] / total_weight)
            for item in CHECKLIST
        )
        total_score = round(weighted_score, 1)

        # Extract ADR title
        title_match = re.search(r'^#\s+(.+)$', adr_text, re.MULTILINE)
        adr_title = title_match.group(1).strip() if title_match else "(untitled)"

        # Generate improvement plan (3 items)
        sorted_gaps = sorted(gaps, key=lambda g: self._extract_score(g), reverse=True)
        improvement_plan = self.generate_improvement_plan(
            ReflectionReport(
                checklist_scores=scores,
                total_score=total_score,
                gaps=[g.split(" (")[0] for g in sorted_gaps[:5]],
            )
        )

        report = ReflectionReport(
            checklist_scores=scores,
            total_score=total_score,
            gaps=gaps,
            improvement_plan=improvement_plan,
            timestamp=datetime.now().isoformat(),
            adr_title=adr_title,
            pattern_matches=all_patterns[:10],
        )

        # Save reflection persistently
        self._save_reflection(report)

        logger.info(
            "Reflection for '%s': score=%s/100, gaps=%d",
            adr_title[:50], total_score, len(gaps)
        )

        return report

    @staticmethod
    def _extract_score(gap_text: str) -> float:
        """Extract numeric score from a gap string like 'label (45/100)'."""
        m = re.search(r'\((\d+(?:\.\d+)?)/100\)', gap_text)
        return float(m.group(1)) if m else 0.0

    def generate_improvement_plan(
        self, reflection: ReflectionReport
    ) -> list[str]:
        """Generate 3 concrete improvement actions from a reflection report.

        Args:
            reflection: The ReflectionReport to act on.

        Returns:
            List of 3 improvement action strings.
        """
        gaps = reflection.gaps
        scores = reflection.checklist_scores

        if not gaps:
            return ["Mantener calidad actual — revisar en próxima iteración",
                    "Documentar lecciones aprendidas para otros ADRs",
                    "Automatizar verificación de checklist"]

        plan: list[str] = []
        gap_lower = [g.lower() for g in gaps]

        # Map gaps to concrete improvements
        improvement_map: dict[str, list[str]] = {
            "frontmatter": [
                "Agregar frontmatter YAML (id, title, status, date, tags) al inicio del ADR",
                "Verificar que el frontmatter tenga todos los campos requeridos",
            ],
            "contexto": [
                "Expandir la sección de Contexto con al menos 3 problemas o drivers concretos",
                "Incluir contexto histórico y limitaciones del sistema actual",
            ],
            "opciones": [
                "Documentar al menos 3 opciones consideradas con pros/cons cada una",
                "Explicar por qué las opciones descartadas no fueron seleccionadas",
            ],
            "decision": [
                "Añadir justificación explícita de la decisión con criterios objetivos",
                "Vincular la decisión a los problemas identificados en el Contexto",
            ],
            "consecuencias": [
                "Incluir consecuencias tanto positivas como negativas de la decisión",
                "Cuantificar el impacto esperado cuando sea posible",
            ],
            "diagrama": [
                "Agregar diagrama arquitectónico (Mermaid, PlantUML, o ASCII art)",
                "Asegurar que el diagrama sea legible y muestre relaciones clave",
            ],
            "referencias": [
                "Verificar referencias a ADRs existentes en la base L0",
                "Agregar wikilinks [[ADR-XXX]] para referencias cruzadas",
            ],
            "l0": [
                "Consultar memoria L0 para contexto histórico de decisiones previas",
                "Referenciar ADRs relacionados que impactan esta decisión",
            ],
            "metricas": [
                "Incluir métricas cuantificables (tiempos, scores, porcentajes)",
                "Agregar tabla comparativa con datos numéricos cuando aplique",
            ],
            "feedback": [
                "Solicitar revisión de al menos un agente (Kratos, Aletheia, Metis)",
                "Incorporar feedback del ciclo de crítica antes de finalizar",
            ],
        }

        for gap in gap_lower:
            for key, suggestions in improvement_map.items():
                if key in gap:
                    plan.extend(suggestions)
                    break

        # If no specific matches, add generic improvements
        if not plan:
            plan = [
                "Revisar estructura general del ADR contra la plantilla estándar",
                "Asegurar cobertura de todos los puntos del checklist de 10 ítems",
                "Solicitar revisión de pares antes de finalizar el ADR",
            ]

        # Trim to 3 items
        return plan[:3]

    def run_weekly_review(self) -> dict[str, Any]:
        """Run a weekly review: aggregate reflections, detect patterns, generate plan.

        Reads all stored reflections and produces a weekly summary with
        trend analysis and recommendations.

        Returns:
            Dict with keys: total_adrs, avg_score, trend (up/down/stable),
            common_gaps, recommendations, period.
        """
        reflections = self._load_all_reflections()
        if not reflections:
            return {
                "total_adrs": 0,
                "avg_score": 0.0,
                "trend": "no_data",
                "common_gaps": [],
                "recommendations": ["No hay reflexiones para analizar aún"],
                "period": "N/A",
            }

        scores = [r.get("total_score", 0) for r in reflections]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Trend: compare last 3 vs previous
        recent = scores[-3:] if len(scores) >= 3 else scores
        older = scores[:-3] if len(scores) > 3 else scores
        recent_avg = sum(recent) / len(recent) if recent else 0.0
        older_avg = sum(older) / len(older) if older else 0.0

        if recent_avg > older_avg + 5:
            trend = "upward 📈"
        elif recent_avg < older_avg - 5:
            trend = "downward 📉"
        else:
            trend = "stable 📊"

        # Most common gaps
        gap_counter: dict[str, int] = defaultdict(int)
        for r in reflections:
            for gap in r.get("gaps", []):
                gap_counter[gap] += 1
        common_gaps = sorted(gap_counter.items(), key=lambda x: -x[1])[:5]

        # Recommendations based on common gaps
        recommendations = []
        for gap, count in common_gaps:
            if count >= len(reflections) * 0.5:
                recommendations.append(
                    f"Alta incidencia de '{gap}' ({count}/{len(reflections)} ADRs) — "
                    f"considerar incluir en template estándar"
                )

        if not recommendations:
            recommendations = ["Sin patrones críticos detectados. Mantener calidad actual."]

        return {
            "total_adrs": len(reflections),
            "avg_score": round(avg_score, 1),
            "trend": trend,
            "common_gaps": [{"gap": g, "count": c} for g, c in common_gaps],
            "recommendations": recommendations,
            "period": f"{reflections[0].get('timestamp', '?')[:10]} → {reflections[-1].get('timestamp', '?')[:10]}",
        }

    def get_trend(self) -> dict[str, Any]:
        """Get reflection score trends over time.

        Returns:
            Dict with keys: scores (list of {date, score}), trend_line,
            volatility, last_improvement.
        """
        reflections = self._load_all_reflections()
        if not reflections:
            return {"scores": [], "trend_line": "no_data", "volatility": 0.0, "last_improvement": ""}

        timeline = [
            {"date": r.get("timestamp", "")[:10], "score": r.get("total_score", 0)}
            for r in reflections
        ]

        scores = [t["score"] for t in timeline]
        mean = sum(scores) / len(scores) if scores else 0
        variance = sum((s - mean) ** 2 for s in scores) / len(scores) if scores else 0
        volatility = round(math.sqrt(variance), 1) if scores else 0.0

        # Last improvement
        last_improvement = ""
        for i in range(len(scores) - 1, 0, -1):
            if scores[i] > scores[i - 1]:
                last_improvement = timeline[i]["date"]
                break

        return {
            "scores": timeline,
            "trend_line": "up" if len(scores) > 1 and scores[-1] > scores[0] else "down" if len(scores) > 1 else "flat",
            "volatility": volatility,
            "last_improvement": last_improvement or "N/A",
        }

    # ── Persistence ──

    def _save_reflection(self, report: ReflectionReport) -> None:
        """Persist a reflection report to the reflections JSON file.

        Args:
            report: The ReflectionReport to save.
        """
        entry = report.to_dict()
        reflections = self._load_all_reflections()
        reflections.append(entry)

        # Cap at 1000 entries
        if len(reflections) > 1000:
            reflections = reflections[-1000:]

        try:
            self._reflections_file.write_text(
                json.dumps(reflections, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Failed to save reflection: %s", exc)

    def _load_all_reflections(self) -> list[dict[str, Any]]:
        """Load all stored reflections from the JSON file.

        Returns:
            List of reflection dicts.
        """
        if not self._reflections_file.exists():
            return []
        try:
            data = json.loads(self._reflections_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            return []
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load reflections: %s", exc)
            return []


# ── Quick test ──
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sample_adr = """# ADR-020: Sistema de Reflexión Automática

---
id: ADR-020
title: Sistema de Reflexión Automática
status: proposed
date: 2026-05-29
tags: [reflection, quality, adr]
---

## Contexto

Actualmente tenemos 3 problemas principales:
1. No hay autoevaluación post-ADR
2. La calidad depende del agente que escribe
3. No hay mejora continua basada en datos

## Opciones Consideradas

1. **Reflection Engine**: Automático, basado en reglas
2. **LLM-as-Judge**: Más flexible pero más lento y costoso
3. **Humano-in-the-loop**: Máxima calidad pero no escalable

## Decisión

Implementar Reflection Engine basado en reglas por su velocidad y
determinismo, ya que necesitamos feedback inmediato sin depender de
LLM externo.

## Consecuencias

- Positivas: Feedback inmediato, 100% determinista, sin costo API
- Negativas: Menos flexible que un LLM, requiere mantenimiento de reglas

## Diagrama

```mermaid
graph TD
    A[ADR] --> B[Reflection Engine]
    B --> C{Score > 70%?}
    C -->|Sí| D[Aprobado]
    C -->|No| E[Plan de mejora]
```

## Referencias

- [[ADR-001-sistema-memoria]]
- [[ADR-002-sistema-scores]]
"""

    engine = ReflectionEngine()
    report = engine.evaluate_adr(sample_adr)
    print(report.summary())
    print(f"\nTitle: {report.adr_title}")
    print(f"Gaps ({len(report.gaps)}):")
    for g in report.gaps[:5]:
        print(f"  - {g}")
    print("\nImprovement plan:")
    for i, p in enumerate(report.improvement_plan, 1):
        print(f"  {i}. {p}")

    # Test weekly review
    review = engine.run_weekly_review()
    print(f"\nWeekly review: {review['total_adrs']} ADRs, avg={review['avg_score']}, trend={review['trend']}")

    # Test trend
    trend = engine.get_trend()
    print(f"Trend: {trend['trend_line']}, volatility={trend['volatility']}")

    print("\nReflectionEngine: OK")
