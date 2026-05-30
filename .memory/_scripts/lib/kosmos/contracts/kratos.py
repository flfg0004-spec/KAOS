"""kratos.py — KosmosKratosContract: Adherence Check.

Extraído de kosmos_contracts.py (D3).
"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .models import (
    AdherenceReport,
    _CONTRACTS_DIR,
)

logger = logging.getLogger(__name__)

# ── Adherence Criteria ──

ADHERENCE_CRITERIA: Dict[str, Dict[str, Any]] = {
    "refactor": {"metric": "coupling", "target": "< 0.4", "description": "Acoplamiento entre módulos menor a 0.4"},
    "migration": {"metric": "migration_rate", "target": "> 80%", "description": "Tasa de migración superior al 80%"},
    "pattern_intro": {"metric": "pattern_usage", "target": "> 1", "description": "Patrón usado en más de 1 lugar"},
    "dependency": {"metric": "dependency_count", "target": "< threshold", "description": "Conteo de dependencias bajo el umbral"},
    "security": {"metric": "vuln_fix_rate", "target": "100%", "description": "Tasa de corrección de vulnerabilidades al 100%"},
}


class KosmosKratosContract:
    """Contrato bidireccional Kosmos ↔ Kratos.

    Kosmos genera recomendaciones arquitectónicas (brief), Kratos las implementa,
    y este contrato verifica qué tanto adhirió el código a las recomendaciones.
    """

    def __init__(self, memory_l0: Any = None) -> None:
        """Initialize the Kosmos-Kratos contract.

        Args:
            memory_l0: Optional ArchitectureMemoryL0 instance for context.
        """
        self._memory_l0 = memory_l0
        self._status: Dict[str, Any] = {
            "active": True,
            "last_run": "",
            "last_score": 0.0,
            "total_runs": 0,
            "errors": 0,
        }
        self._contracts_dir = _CONTRACTS_DIR
        self._contracts_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("KosmosKratosContract initialized")

    # ── Public API ──

    def generate_brief(self, adr_text: str, adr_id: str) -> Dict[str, Any]:
        """Generate a recommendation brief from ADR text with adherence criteria.

        Extrae recomendaciones del ADR y las asigna criterios de adherencia
        según el tipo de recomendación detectado.

        Args:
            adr_text: Texto del ADR del cual extraer recomendaciones.
            adr_id: Identificador del ADR.

        Returns:
            Dict con keys: adr_id, recommendations (lista de dicts con id,
            description, criteria, adherence_type), timestamp.
        """
        try:
            recommendations = self._extract_recommendations(adr_text)
            enriched = []
            for i, rec in enumerate(recommendations):
                rec_id = f"{adr_id}-REC-{i+1:02d}"
                rec_type = self._classify_recommendation(rec)
                criteria = ADHERENCE_CRITERIA.get(rec_type, {
                    "metric": "general_compliance",
                    "target": "> 80%",
                    "description": "Cumplimiento general de la recomendación",
                })
                enriched.append({
                    "id": rec_id,
                    "description": rec,
                    "type": rec_type,
                    "criteria": criteria,
                })

            brief = {
                "adr_id": adr_id,
                "recommendations": enriched,
                "timestamp": datetime.now().isoformat(),
            }

            # Persist brief
            self._save_brief(brief)
            self._status["last_run"] = datetime.now().isoformat()
            logger.info("Generated brief for %s: %d recommendations", adr_id, len(enriched))
            return brief

        except Exception as exc:
            logger.error("generate_brief failed for %s: %s", adr_id, exc)
            self._status["errors"] += 1
            return {
                "adr_id": adr_id,
                "recommendations": [],
                "error": str(exc),
                "timestamp": datetime.now().isoformat(),
            }

    def parse_adherence(self, raw_report: str) -> AdherenceReport:
        """Parse a Kratos adherence report and compute adherence score.

        Analiza el texto de reporte de Kratos buscando evidencia de
        implementación de cada recomendación, y genera un score compuesto.

        Args:
            raw_report: Texto del reporte generado por Kratos (output de código).

        Returns:
            AdherenceReport con scores, desviaciones y decisiones.
        """
        try:
            report_text = raw_report or ""

            # Extract decisions from Kratos output
            decisions = self._extract_kratos_decisions(report_text)

            # Extract deviations (mentions of "cambio", "desviación", "alternative")
            deviations = self._extract_deviations(report_text)

            # Count recommendation patterns vs implementation evidence
            rec_count = len(re.findall(
                r'(?:recommendation|recomendaci[oó]n|implement|implementar|feature|funcionalidad)',
                report_text, re.IGNORECASE
            ))
            impl_evidence = len(re.findall(
                r'(?:implemented|implementado|created|creado|added|agregado|built|construido)',
                report_text, re.IGNORECASE
            ))

            # Score: ratio of implementation evidence to recommendations
            if rec_count > 0:
                base_score = min(100.0, (impl_evidence / max(rec_count, 1)) * 100.0)
            else:
                base_score = 50.0  # neutral if no clear recs

            # Penalize deviations
            deviation_penalty = len(deviations) * 10.0
            adherence_score = max(0.0, min(100.0, base_score - deviation_penalty))

            # Per-rec coverage (heuristic)
            coverage_by_rec: Dict[str, float] = {}
            for rec_match in re.finditer(r'(?:REC-\d+|[Rr]ecommendation\s+\d+)', report_text):
                rec_key = rec_match.group(0)
                surrounding = report_text[
                    max(0, rec_match.start() - 50):
                    rec_match.end() + 100
                ]
                has_evidence = bool(re.search(
                    r'(?:done|implemented|added|created|built|✅|✓|complet)',
                    surrounding, re.IGNORECASE
                ))
                coverage_by_rec[rec_key] = 100.0 if has_evidence else 0.0

            report = AdherenceReport(
                adr_id=self._extract_adr_id(report_text),
                recommendations=[{"description": d} for d in self._extract_recommendations(report_text)],
                adherence_score=round(adherence_score, 1),
                coverage_by_rec=coverage_by_rec,
                deviations=deviations,
                kratos_decisions=decisions,
                timestamp=datetime.now().isoformat(),
                adr_title=self._extract_title(report_text),
            )

            self._status["last_run"] = datetime.now().isoformat()
            self._status["last_score"] = report.adherence_score
            self._status["total_runs"] += 1
            self._save_report(report)
            logger.info("Adherence: score=%.1f, deviations=%d", report.adherence_score, len(deviations))
            return report

        except Exception as exc:
            logger.error("parse_adherence failed: %s", exc)
            self._status["errors"] += 1
            return AdherenceReport(
                adherence_score=0.0,
                deviations=[f"Error parsing adherence: {exc}"],
                timestamp=datetime.now().isoformat(),
            )

    def update_adr_with_adherence(self, adr_path: str, report: AdherenceReport) -> str:
        """Update an ADR markdown file with an 'Adherence' section and score.

        Args:
            adr_path: Path to the ADR markdown file.
            report: AdherenceReport to embed.

        Returns:
            Status string: path written or error.
        """
        try:
            path = Path(adr_path)
            if not path.exists():
                logger.warning("ADR file not found: %s", adr_path)
                return f"ERROR: File not found: {adr_path}"

            adr_text = path.read_text(encoding="utf-8", errors="replace")

            # Build adherence section
            adherence_section = [
                "",
                "## Adherencia Post-Implementación",
                "",
                f"**Score de adherencia**: {report.adherence_score:.1f}/100",
                "",
                "| Recomendación | Score |",
                "|--------------|-------|",
            ]
            for rec_id, score in report.coverage_by_rec.items():
                adherence_section.append(f"| {rec_id} | {score:.0f}/100 |")

            if report.deviations:
                adherence_section.append("")
                adherence_section.append("### Desviaciones Detectadas")
                for dev in report.deviations:
                    adherence_section.append(f"- {dev}")

            if report.kratos_decisions:
                adherence_section.append("")
                adherence_section.append("### Decisiones de Kratos")
                for dec in report.kratos_decisions:
                    adherence_section.append(f"- {dec}")

            adherence_section.append("")

            # Check if adherence section already exists
            if "## Adherencia Post-Implementación" in adr_text:
                # Replace existing section
                adr_text = re.sub(
                    r'## Adherencia Post-Implementación\n.*?(?=\n## |\Z)',
                    '\n'.join(adherence_section),
                    adr_text,
                    flags=re.DOTALL,
                )
            else:
                # Append before the end
                adr_text = adr_text.rstrip() + '\n' + '\n'.join(adherence_section)

            path.write_text(adr_text, encoding="utf-8")
            logger.info("Updated %s with adherence score=%.1f", adr_path, report.adherence_score)
            return f"Updated {adr_path} with adherence score {report.adherence_score:.1f}"

        except Exception as exc:
            logger.error("update_adr_with_adherence failed: %s", exc)
            return f"ERROR: {exc}"

    def check_if_implemented(self, recommendation_id: str, codebase_path: str) -> Dict[str, Any]:
        """Heuristic check if a recommendation was implemented in the codebase.

        Scans Python files for patterns matching the recommendation criteria.

        Args:
            recommendation_id: ID of the recommendation (e.g. "ADR-019-REC-01").
            codebase_path: Root path to scan for implementation evidence.

        Returns:
            Dict con keys: implemented (bool), evidence (list), confidence (float).
        """
        try:
            base_path = Path(codebase_path)
            if not base_path.exists():
                return {"implemented": False, "evidence": [], "confidence": 0.0}

            # Extract keywords from recommendation ID
            keywords = recommendation_id.replace("-", " ").lower().split()
            evidence = []

            # Scan Python files for related patterns
            py_files = list(base_path.rglob("*.py"))[:100]
            for f in py_files:
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                    # Count keyword matches
                    match_count = sum(1 for kw in keywords if kw.lower() in content.lower())
                    if match_count >= 2:
                        rel_path = f.relative_to(base_path) if base_path in f.parents else f
                        evidence.append(str(rel_path))
                except (OSError, IOError):
                    continue

            confidence = min(1.0, len(evidence) / max(len(keywords), 1))
            implemented = len(evidence) > 0 and confidence > 0.3

            return {
                "implemented": implemented,
                "evidence": evidence[:10],
                "confidence": round(confidence, 2),
                "recommendation_id": recommendation_id,
            }

        except Exception as exc:
            logger.error("check_if_implemented failed: %s", exc)
            return {"implemented": False, "evidence": [], "confidence": 0.0, "error": str(exc)}

    def status(self) -> Dict[str, Any]:
        """Return contract status.

        Returns:
            Dict con keys: active, last_run, last_score, total_runs, errors.
        """
        return dict(self._status)

    # ── Internal helpers ──

    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendation statements from ADR text."""
        if not text:
            return []
        recommendations = []

        # Look for sections with recommendations
        rec_section = re.search(
            r'(?:##\s*(?:Recomendacion|Recommendation|Implementaci[oó]n|Implementation|Consecuencias)\s*\n)(.*?)(?=\n##|\Z)',
            text, re.DOTALL | re.IGNORECASE
        )
        if rec_section:
            section_text = rec_section.group(1)
            # Extract list items
            items = re.findall(r'(?:^|\n)\s*[-*\d]+[.)]\s*(.*)', section_text)
            recommendations.extend(item.strip() for item in items if len(item.strip()) > 20)

        # Also look for bold recommendations
        bold_recs = re.findall(r'\*\*(.*?)\*\*\s*[:：]\s*(.*?)(?:\.|$)', text)
        for bold, desc in bold_recs:
            combined = f"{bold}: {desc}".strip()
            if len(combined) > 20 and combined not in recommendations:
                recommendations.append(combined)

        return recommendations[:10]

    def _classify_recommendation(self, rec_text: str) -> str:
        """Classify a recommendation text into an adherence type."""
        rec_lower = rec_text.lower()
        if any(w in rec_lower for w in ["refactor", "refactorizar", "reestructurar", "modularizar"]):
            return "refactor"
        if any(w in rec_lower for w in ["migrar", "migración", "migration", "portar"]):
            return "migration"
        if any(w in rec_lower for w in ["patrón", "pattern", "introducir", "adoptar", "implementar"]):
            return "pattern_intro"
        if any(w in rec_lower for w in ["dependencia", "dependency", "librería", "library", "paquete"]):
            return "dependency"
        if any(w in rec_lower for w in ["seguridad", "security", "vuln", "vulnerabilidad", "auth"]):
            return "security"
        return "refactor"  # default

    def _extract_kratos_decisions(self, text: str) -> List[str]:
        """Extract decisions Kratos made during implementation."""
        if not text:
            return []
        decisions = []

        # Look for decision patterns
        patterns = [
            r'(?:Decid[íi]|Decided|Opt[ée]|Eligi[óo]|Chose)\s*:?\s*([^.\n]+)',
            r'(?:Se\s+decidi[óo]|We\s+decided)\s*:?\s*([^.\n]+)',
            r'(?:alternativa|alternative)\s*:?\s*([^.\n]+)',
        ]
        for pat in patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            decisions.extend(m.strip() for m in matches if len(m.strip()) > 10)

        return decisions[:5]

    def _extract_deviations(self, text: str) -> List[str]:
        """Extract deviations or changes from the original plan."""
        if not text:
            return []
        deviations = []
        patterns = [
            r'(?:desviaci[oó]n|deviation|cambio|change|modificaci[oó]n)\s*:?\s*([^.\n]+)',
            r'(?:no\s+se\s+(?:implement[oó]|sigui[óo]|respet[óo]))\s*:?\s*([^.\n]+)',
            r'(?:different\s+approach|enfoque\s+diferente)\s*:?\s*([^.\n]+)',
        ]
        for pat in patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            deviations.extend(m.strip() for m in matches if len(m.strip()) > 10)

        return deviations[:5]

    def _extract_adr_id(self, text: str) -> str:
        """Extract ADR ID from text."""
        match = re.search(r'(ADR-\d+)', text or "")
        return match.group(1) if match else ""

    def _extract_title(self, text: str) -> str:
        """Extract ADR title from text."""
        match = re.search(r'^#\s+(.+)$', text or "", re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _save_brief(self, brief: Dict[str, Any]) -> None:
        """Persist a recommendation brief."""
        try:
            fname = f"brief-{brief.get('adr_id', 'unknown')}.json"
            path = self._contracts_dir / fname
            path.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
        except (OSError, IOError) as exc:
            logger.warning("Failed to save brief: %s", exc)

    def _save_report(self, report: AdherenceReport) -> None:
        """Persist an adherence report."""
        try:
            fname = f"adherence-{report.adr_id or 'unknown'}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            path = self._contracts_dir / fname
            path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        except (OSError, IOError) as exc:
            logger.warning("Failed to save adherence report: %s", exc)
