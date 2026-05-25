"""Strategy engine for Metis — SWOT, OKRs, Risk Matrix, Strategy Report.

Provides structured methodology for strategic analysis:
  - SWOTMatrix: analyze research/aletheia context into strengths, weaknesses, opportunities, threats
  - OKREngine: generate and validate OKRs with baseline + numeric target
  - RiskMatrix: probability x impact risk identification
  - StrategyReport: complete structured strategy output
"""

import re
import json
from datetime import datetime
from pathlib import Path
from collections import Counter

BASE = (Path(__file__).resolve().parent.parent.parent)


def _extract_keywords(text: str, top_n: int = 20) -> list[str]:
    """Extract most frequent significant words from text."""
    words = re.findall(r"\w{4,}", text.lower())
    stop = {"este", "esta", "esto", "para", "como", "entre", "sobre", "tiene",
            "puede", "debe", "muy", "son", "han", "era", "ser", "del", "los",
            "las", "con", "por", "que", "una", "los"}
    filtered = [w for w in words if w not in stop]
    return [w for w, _ in Counter(filtered).most_common(top_n)]


_POSITIVE_WORDS = {
    "ventaja", "fortaleza", "oportunidad", "crecimiento", "innovación",
    "eficiencia", "rápido", "escalable", "robusto", "seguro", "optimizado",
    "líder", "experiencia", "capacidad", "recurso", "talento", "tecnología",
}

_NEGATIVE_WORDS = {
    "debilidad", "amenaza", "riesgo", "limitación", "problema", "error",
    "lento", "obsoleto", "vulnerable", "dependencia", "falta", "carencia",
    "restricción", "barrera", "conflicto", "deuda", "legado",
}


class SWOTMatrix:
    """Analyze research/architecture context into SWOT categories."""

    def __init__(self, research_text: str = "", architecture_text: str = ""):
        self.research = research_text or ""
        self.architecture = architecture_text or ""
        self._analysis = None

    def analyze(self) -> dict:
        """Token-based SWOT analysis using keyword matching."""
        combined = self.research + " " + self.architecture
        tokens = set(re.findall(r"\w{4,}", combined.lower()))
        token_list = _extract_keywords(combined, top_n=30)

        strengths = [w for w in token_list if w in _POSITIVE_WORDS or "ventaj" in w or "fortal" in w]
        opportunities = [w for w in token_list if w in {"oportunidad", "crecimiento", "innovación", "mejora", "potencial"}]

        weaknesses = [w for w in token_list if w in _NEGATIVE_WORDS or "debil" in w or "limit" in w]
        threats = [w for w in token_list if w in {"amenaza", "riesgo", "peligro", "incertidumbre", "competencia"}]

        self._analysis = {
            "strengths": strengths or ["Identificar fortalezas del dominio"],
            "weaknesses": weaknesses or ["Identificar debilidades del dominio"],
            "opportunities": opportunities or ["Identificar oportunidades del dominio"],
            "threats": threats or ["Identificar amenazas del dominio"],
            "key_terms": token_list[:15],
        }
        return self._analysis

    def render(self) -> str:
        if not self._analysis:
            self.analyze()
        a = self._analysis
        lines = [
            "### Matriz FODA\n",
            f"**Fortalezas ({len(a['strengths'])}):** {', '.join(a['strengths'])}",
            f"**Debilidades ({len(a['weaknesses'])}):** {', '.join(a['weaknesses'])}",
            f"**Oportunidades ({len(a['opportunities'])}):** {', '.join(a['opportunities'])}",
            f"**Amenazas ({len(a['threats'])}):** {', '.join(a['threats'])}",
            "",
        ]
        return "\n".join(lines)


class OKREngine:
    """Generate and validate OKRs with baseline + numeric target."""

    def __init__(self):
        self._okrs = []

    def generate(self, objectives: list[str], context: str = "") -> list[dict]:
        """Generate OKR structures from high-level objectives.

        Each OKR gets baseline and target based on context keywords.
        """
        context_tokens = set(re.findall(r"\w{4,}", context.lower())) if context else set()
        okrs = []
        for obj in objectives:
            key_results = []
            obj_lower = obj.lower()

            kr_metrics = ["reducción", "aumento", "mejora", "implementación", "adopción", "cobertura"]
            for metric in kr_metrics:
                if metric in obj_lower or len(key_results) < 2:
                    baseline = self._infer_baseline(metric, context_tokens)
                    key_results.append(
                        f"{metric.capitalize()} de {baseline['baseline']} a {baseline['target']} "
                        f"({baseline['unit']})"
                    )
                if len(key_results) >= 3:
                    break

            if not key_results:
                key_results = [
                    f"Implementar solución con cobertura ≥80%",
                    f"Reducir incidentes en 50%",
                    f"Lograr adopción del equipo ≥70%",
                ]

            okrs.append({
                "objective": obj,
                "key_results": key_results[:3],
                "baseline": "por definir",
                "target": "numérico",
            })

        self._okrs = okrs
        return okrs

    def validate(self, okrs: list[dict]) -> list[str]:
        """Validate OKRs for required fields and numeric targets."""
        errors = []
        for i, okr in enumerate(okrs):
            if not okr.get("objective"):
                errors.append(f"OKR #{i+1}: objective is required")
            if not okr.get("key_results"):
                errors.append(f"OKR #{i+1}: at least one key_result is required")
            else:
                for j, kr in enumerate(okr["key_results"]):
                    if not re.search(r"\d+", kr):
                        errors.append(f"OKR #{i+1}, KR #{j+1}: '{kr[:40]}...' missing numeric target")
        return errors

    def render(self) -> str:
        lines = ["### OKRs\n"]
        for okr in self._okrs:
            lines.append(f"**Objetivo:** {okr['objective']}")
            for kr in okr.get("key_results", []):
                lines.append(f"  - KR: {kr}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _infer_baseline(metric: str, context_tokens: set) -> dict:
        """Infer plausible baseline/target from context."""
        baseline_map = {
            "reducción": {"baseline": "100%", "target": "50%", "unit": "reducción relativa"},
            "aumento": {"baseline": "0", "target": "100", "unit": "unidades"},
            "mejora": {"baseline": "línea base", "target": "+30%", "unit": "porcentaje"},
            "implementación": {"baseline": "0%", "target": "100%", "unit": "cobertura"},
            "adopción": {"baseline": "0%", "target": "80%", "unit": "porcentaje equipo"},
            "cobertura": {"baseline": "0%", "target": "90%", "unit": "porcentaje"},
        }
        return baseline_map.get(metric, {"baseline": "actual", "target": "meta", "unit": "unidades"})


class RiskMatrix:
    """Probability x Impact risk matrix builder."""

    PROBABILITY = {"alta": 3, "media": 2, "baja": 1}
    IMPACT = {"alto": 3, "medio": 2, "bajo": 1}

    def __init__(self):
        self._risks = []

    def identify(self, threats: list[str], context: str = "") -> list[dict]:
        """Build risk entries from threat descriptions."""
        risks = []
        for threat in threats[:8]:
            prob = self._estimate_probability(threat, context)
            impact = self._estimate_impact(threat)
            score = self.PROBABILITY.get(prob, 2) * self.IMPACT.get(impact, 2)
            risks.append({
                "risk": threat,
                "probability": prob,
                "impact": impact,
                "score": score,
                "level": "crítico" if score >= 6 else "alto" if score >= 4 else "medio" if score >= 2 else "bajo",
                "mitigation": self._suggest_mitigation(threat),
            })
        self._risks = risks
        return risks

    def render(self) -> str:
        lines = ["### Matriz de Riesgos\n"]
        if not self._risks:
            lines.append("Sin riesgos identificados.\n")
            return "\n".join(lines)
        lines.append(f"| Riesgo | Probabilidad | Impacto | Score | Nivel | Mitigación |")
        lines.append(f"|--------|-------------|---------|-------|-------|------------|")
        for r in self._risks:
            lines.append(
                f"| {r['risk'][:40]} | {r['probability']} | {r['impact']} | "
                f"{r['score']} | {r['level']} | {r['mitigation'][:40]} |"
            )
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _estimate_probability(threat: str, context: str) -> str:
        threat_lower = threat.lower()
        if any(w in threat_lower for w in {"seguro", "garantizado", "inminente", "actualmente"}):
            return "alta"
        if any(w in threat_lower for w in {"posible", "potencial", "podría", "riesgo"}):
            return "media"
        return "baja"

    @staticmethod
    def _estimate_impact(threat: str) -> str:
        threat_lower = threat.lower()
        if any(w in threat_lower for w in {"crítico", "catastrófico", "severo", "bloqueante"}):
            return "alto"
        if any(w in threat_lower for w in {"significativo", "importante", "considerable"}):
            return "medio"
        return "bajo"

    @staticmethod
    def _suggest_mitigation(threat: str) -> str:
        threat_lower = threat.lower()
        if "dependencia" in threat_lower:
            return "Diversificar proveedores o tecnologías"
        if "competencia" in threat_lower or "mercado" in threat_lower:
            return "Monitoreo continuo y diferenciación"
        if "técnic" in threat_lower or "deuda" in threat_lower:
            return "Plan de refactorización gradual"
        if "seguridad" in threat_lower or "vulnerabilidad" in threat_lower:
            return "Auditoría de seguridad y parches"
        if "adopción" in threat_lower or "cambio" in threat_lower:
            return "Programa de capacitación y acompañamiento"
        return "Definir plan de contingencia específico"


class StrategyReport:
    """Complete strategy report generator — the main integration point for Metis."""

    def __init__(self, topic: str = "", research: str = "", architecture: str = ""):
        self.topic = topic
        self.research = research
        self.architecture = architecture
        self.swot = SWOTMatrix(research, architecture)
        self.okrs = OKREngine()
        self.risks = RiskMatrix()
        self._report = {}

    def generate(self, objectives: list[str] = None) -> dict:
        """Generate a complete strategy report."""
        if objectives is None:
            objectives = [f"Estrategia para {self.topic}"]

        swot_result = self.swot.analyze()
        okr_result = self.okrs.generate(objectives, self.research)
        threat_descriptions = swot_result.get("threats", [])
        if not threat_descriptions:
            threat_descriptions = [f"Riesgos asociados a {self.topic}"]
        risk_result = self.risks.identify(threat_descriptions, self.research)
        validation_errors = self.okrs.validate(okr_result)

        confidence = self._calculate_confidence(swot_result, len(validation_errors))

        self._report = {
            "topic": self.topic,
            "generated_at": datetime.now().isoformat(),
            "swot": swot_result,
            "okrs": okr_result,
            "risks": risk_result,
            "strategy": self._generate_summary(swot_result, okr_result, risk_result),
            "confidence": confidence,
            "warnings": validation_errors[:3] if validation_errors else [],
        }
        return self._report

    def to_json(self) -> str:
        if not self._report:
            self.generate()
        return json.dumps(self._report, indent=2, ensure_ascii=False)

    def render(self) -> str:
        if not self._report:
            self.generate()
        r = self._report
        lines = [
            f"# Estrategia: {r['topic']}",
            f"*Generado: {r['generated_at']}*",
            f"*Confianza: {r['confidence']}*\n",
        ]
        lines.append(self.swot.render())
        lines.append(self.okrs.render())
        lines.append(self.risks.render())

        if r.get("warnings"):
            lines.append("### Advertencias\n")
            for w in r["warnings"]:
                lines.append(f"- ⚠️ {w}")
            lines.append("")

        lines.append(f"**Confianza: {r['confidence']}**")
        return "\n".join(lines)

    @staticmethod
    def _calculate_confidence(swot: dict, warning_count: int) -> str:
        if not swot.get("strengths") or not swot.get("opportunities"):
            return "baja"
        if warning_count > 2:
            return "baja"
        if len(swot.get("strengths", [])) >= 2 and len(swot.get("opportunities", [])) >= 1:
            return "alta"
        return "media"

    @staticmethod
    def _generate_summary(swot: dict, okrs: list, risks: list) -> str:
        parts = [
            f"Análisis FODA identifica {len(swot['strengths'])} fortalezas, "
            f"{len(swot['weaknesses'])} debilidades, {len(swot['opportunities'])} oportunidades, "
            f"y {len(swot['threats'])} amenazas.",
            f"Se proponen {len(okrs)} objetivos estratégicos con OKRs.",
            f"Se identificaron {len(risks)} riesgos con mitigaciones.",
        ]
        return " ".join(parts)
