"""kratos.py — KosmosKratosContract: Adherence Check.

Extraído de kosmos_contracts.py (D3).
K1: Integración con CodeExperience API real con graceful degradation.
"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import (
    _CONTRACTS_DIR,
    AdherenceReport,
)

logger = logging.getLogger(__name__)

# ── Adherence Criteria ──

ADHERENCE_CRITERIA: dict[str, dict[str, Any]] = {
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

    K1: Soporte para API real sobre CodeExperience con graceful degradation.
    """

    def __init__(self, memory_l0: Any = None, use_real_api: bool = True) -> None:
        """Initialize the Kosmos-Kratos contract.

        Args:
            memory_l0: Optional ArchitectureMemoryL0 instance for context.
            use_real_api: If True, use CodeExperience API for adherence checks.
                          Falls back to heuristic parsing if CodeExperience unavailable.
        """
        self._memory_l0 = memory_l0
        self._use_real_api = use_real_api
        self._status: dict[str, Any] = {
            "active": True,
            "last_run": "",
            "last_score": 0.0,
            "total_runs": 0,
            "errors": 0,
        }
        self._contracts_dir = _CONTRACTS_DIR
        self._contracts_dir.mkdir(parents=True, exist_ok=True)

        # K1: Try to import code_memory for real API mode
        self._ce_available = False
        self._code_memory: Any = None
        if self._use_real_api:
            try:
                from lib import code_memory as _ce
                self._code_memory = _ce
                self._ce_available = True
                logger.debug("CodeExperience available for real adherence checks")
            except ImportError:
                self._ce_available = False
                logger.warning(
                    "CodeExperience not available — will use heuristic fallback"
                )

        logger.debug(
            "KosmosKratosContract initialized (use_real_api=%s, ce=%s)",
            self._use_real_api, self._ce_available,
        )

    # ── Public API ──

    def generate_brief(self, adr_text: str, adr_id: str) -> dict[str, Any]:
        """Generate a recommendation brief from ADR text with adherence criteria.

        Extrae recomendaciones del ADR y las asigna criterios de adherencia
        según el tipo de recomendación detectado.

        K1: When use_real_api=True and CodeExperience is available, includes
        evidence from CodeExperience in the brief.

        Args:
            adr_text: Texto del ADR del cual extraer recomendaciones.
            adr_id: Identificador del ADR.

        Returns:
            Dict con keys: adr_id, recommendations (lista de dicts con id,
            description, criteria, adherence_type), timestamp, y opcionalmente
            code_experience_evidence y code_experience_summary.
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

            brief: dict[str, Any] = {
                "adr_id": adr_id,
                "recommendations": enriched,
                "timestamp": datetime.now().isoformat(),
            }

            # K1: Enrich with CodeExperience evidence when available
            if self._ce_available and self._code_memory and recommendations:
                try:
                    ce_evidence = self._gather_code_experience_evidence(recommendations)
                    brief["code_experience_evidence"] = ce_evidence
                    total_matches = sum(e.get("matches", 0) for e in ce_evidence)
                    avg_confidence = (
                        sum(e.get("avg_confidence", 0) for e in ce_evidence) / len(ce_evidence)
                        if ce_evidence else 0
                    )
                    brief["code_experience_summary"] = {
                        "total_related_entries": total_matches,
                        "avg_confidence": round(avg_confidence, 2),
                        "recommendations_with_evidence": sum(
                            1 for e in ce_evidence if e.get("matches", 0) > 0
                        ),
                    }
                    logger.info(
                        "CodeExperience evidence for %s: %d entries, %.0f%% confidence",
                        adr_id, total_matches, avg_confidence * 100,
                    )
                except Exception as exc:
                    logger.debug("CodeExperience enrichment failed (non-blocking): %s", exc)

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
            coverage_by_rec: dict[str, float] = {}
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

    def check_if_implemented(self, recommendation_id: str, codebase_path: str) -> dict[str, Any]:
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
                except OSError:
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

    def real_adherence_check(self, adr_id: str, adr_text: str) -> AdherenceReport:
        """Real adherence check via CodeExperience API.

        K1: En lugar de parsear texto de Kratos con regex, busca en CodeExperience
        entradas relevantes al ADR y computa adherence score basado en evidencia real.

        Para cada recomendación extraída del ADR:
        - Busca en CodeExperience con search(query=rec_text)
        - Si hay entradas con resolution_rate > 0.7 y confidence > 0.5 → implementado
        - Si hay entradas con retrieval_count > 2 y confidence < 0.3 → intentado
        - Si no hay entradas → no implementado

        Args:
            adr_id: Identificador del ADR.
            adr_text: Texto completo del ADR.

        Returns:
            AdherenceReport con adherence_score real basado en CodeExperience.
            Si CodeExperience no está disponible, retorna reporte con score 0
            y deviation indicando que se requiere fallback heurístico.
        """
        try:
            if not self._ce_available or not self._code_memory:
                logger.warning(
                    "CodeExperience not available for real_adherence_check — "
                    "returning empty report"
                )
                return AdherenceReport(
                    adr_id=adr_id,
                    adherence_score=0.0,
                    deviations=["CodeExperience API not available — heuristic check required"],
                    timestamp=datetime.now().isoformat(),
                    adr_title=self._extract_title(adr_text),
                )

            # 1. Extract recommendations from ADR
            recommendations = self._extract_recommendations(adr_text)
            if not recommendations:
                logger.info("No recommendations found in ADR %s — neutral score", adr_id)
                return AdherenceReport(
                    adr_id=adr_id,
                    adherence_score=50.0,
                    timestamp=datetime.now().isoformat(),
                    adr_title=self._extract_title(adr_text),
                )

            # 2. For each recommendation, search CodeExperience
            coverage_by_rec: dict[str, float] = {}
            deviations: list[str] = []
            kratos_decisions: list[str] = []
            implemented_count = 0
            total = len(recommendations)
            ce = self._code_memory

            for i, rec_text in enumerate(recommendations):
                rec_id = f"{adr_id}-REC-{i+1:02d}"

                # Search CodeExperience for this recommendation
                try:
                    results = ce.search(query=rec_text, top_k=5)
                except Exception as exc:
                    logger.debug("CodeExperience search failed for %s: %s", rec_id, exc)
                    results = []

                # Analyze results
                implemented = False
                attempted = False
                best_confidence = 0.0
                best_rate = 0.0

                for r in results:
                    conf = r.get("confidence", 0)
                    rate = r.get("rate", 0)  # resolution_rate
                    retrievals = r.get("retrievals", 0)

                    if conf > best_confidence:
                        best_confidence = conf
                    if rate > best_rate:
                        best_rate = rate

                    # High resolution rate + high confidence → implemented
                    if rate > 0.7 and conf > 0.5:
                        implemented = True
                    # Many retrievals but low confidence → attempted but problematic
                    if retrievals > 2 and conf < 0.3:
                        attempted = True

                if implemented:
                    coverage_by_rec[rec_id] = 100.0
                    implemented_count += 1
                    kratos_decisions.append(
                        f"{rec_id}: Implementado según CodeExperience "
                        f"(confianza: {best_confidence:.2f}, resolución: {best_rate:.0%})"
                    )
                elif attempted:
                    coverage_by_rec[rec_id] = 30.0
                    deviations.append(
                        f"{rec_id}: Intentado pero con problemas persistentes en "
                        f"CodeExperience (confianza: {best_confidence:.2f})"
                    )
                else:
                    coverage_by_rec[rec_id] = 0.0
                    deviations.append(
                        f"{rec_id}: Sin evidencia de implementación en CodeExperience"
                    )

            # 3. Compute adherence score
            adherence_score = (implemented_count / total) * 100.0 if total > 0 else 50.0

            # 4. Build report
            report = AdherenceReport(
                adr_id=adr_id,
                recommendations=[{"description": r} for r in recommendations],
                adherence_score=round(adherence_score, 1),
                coverage_by_rec=coverage_by_rec,
                deviations=deviations,
                kratos_decisions=kratos_decisions,
                timestamp=datetime.now().isoformat(),
                adr_title=self._extract_title(adr_text),
            )

            self._status["last_run"] = datetime.now().isoformat()
            self._status["last_score"] = report.adherence_score
            self._status["total_runs"] += 1
            self._save_report(report)
            logger.info(
                "Real adherence for %s: score=%.1f, implemented=%d/%d, deviations=%d",
                adr_id, report.adherence_score, implemented_count, total, len(deviations),
            )
            return report

        except Exception as exc:
            logger.error("real_adherence_check failed: %s", exc)
            self._status["errors"] += 1
            return AdherenceReport(
                adr_id=adr_id,
                adherence_score=0.0,
                deviations=[f"Error en real_adherence_check: {exc}"],
                timestamp=datetime.now().isoformat(),
                adr_title=self._extract_title(adr_text),
            )

    def status(self) -> dict[str, Any]:
        """Return contract status.

        K1: Includes real_api_available and code_experience_available flags.

        Returns:
            Dict con keys: active, last_run, last_score, total_runs, errors,
            real_api_available, code_experience_available.
        """
        return {
            **self._status,
            "real_api_available": self._use_real_api,
            "code_experience_available": self._ce_available,
        }

    # ── Internal helpers ──

    def _extract_recommendations(self, text: str) -> list[str]:
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

    def _extract_kratos_decisions(self, text: str) -> list[str]:
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

    def _extract_deviations(self, text: str) -> list[str]:
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

    def _save_brief(self, brief: dict[str, Any]) -> None:
        """Persist a recommendation brief."""
        try:
            fname = f"brief-{brief.get('adr_id', 'unknown')}.json"
            path = self._contracts_dir / fname
            path.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to save brief: %s", exc)

    def _save_report(self, report: AdherenceReport) -> None:
        """Persist an adherence report."""
        try:
            fname = f"adherence-{report.adr_id or 'unknown'}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            path = self._contracts_dir / fname
            path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to save adherence report: %s", exc)

    # ── K1 Helpers ──────────────────────────────────────────────

    def _gather_code_experience_evidence(
        self, recommendations: list[str]
    ) -> list[dict[str, Any]]:
        """Search CodeExperience for each recommendation and gather evidence.

        Args:
            recommendations: List of recommendation text strings.

        Returns:
            List of dicts with rec_text, matches, avg_confidence, top_entries keys.
        """
        if not self._code_memory:
            return []

        evidence = []
        for i, rec_text in enumerate(recommendations):
            try:
                results = self._code_memory.search(query=rec_text, top_k=5)
                match_count = len(results)
                avg_confidence = (
                    sum(r.get("confidence", 0) for r in results) / match_count
                    if match_count > 0 else 0
                )
                evidence.append({
                    "index": i,
                    "rec_text": rec_text[:100],
                    "matches": match_count,
                    "avg_confidence": round(avg_confidence, 2),
                    "top_entries": [
                        {
                            "error": r.get("error", "")[:80],
                            "confidence": r.get("confidence", 0),
                            "rate": r.get("rate", 0),
                        }
                        for r in results[:3]
                    ],
                })
            except Exception as exc:
                evidence.append({
                    "index": i,
                    "rec_text": rec_text[:100],
                    "matches": 0,
                    "error": str(exc),
                })
        return evidence
