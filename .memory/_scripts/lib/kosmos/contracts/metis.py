"""metis.py — KosmosMetisContract: OKR-ADR Synchronization.

Extraído de kosmos_contracts.py (D3).
"""
import logging
import re
from datetime import datetime
from typing import Any, Dict, List

from .models import (
    OKRValidationResult,
    ADRImpactNotification,
)

logger = logging.getLogger(__name__)


class KosmosMetisContract:
    """Contrato bidireccional Kosmos ↔ Metis.

    Kosmos valida la viabilidad arquitectónica de los OKRs de Metis y notifica
    el impacto de nuevos ADRs sobre los OKRs existentes.
    """

    def __init__(self, memory_l0: Any = None) -> None:
        """Initialize the Kosmos-Metis contract.

        Args:
            memory_l0: Optional ArchitectureMemoryL0 instance for ADR lookups.
        """
        self._memory_l0 = memory_l0
        self._status: Dict[str, Any] = {
            "active": True,
            "last_run": "",
            "last_score": 0.0,
            "total_runs": 0,
            "errors": 0,
        }
        logger.debug("KosmosMetisContract initialized")

    # ── Public API ──

    def validate_okr(self, okr_text: str, memory_l0: Any = None) -> OKRValidationResult:
        """Validate architectural viability of an OKR.

        Consulta L0 (y L1 si está disponible) para evaluar si el OKR es
        viable desde el punto de vista arquitectónico.

        Args:
            okr_text: Texto del OKR a validar.
            memory_l0: Optional ArchitectureMemoryL0 for ADR search.

        Returns:
            OKRValidationResult con score, riesgos, y recomendaciones.
        """
        try:
            mem = memory_l0 or self._memory_l0
            okr_id = self._extract_okr_id(okr_text)
            risks: List[str] = []
            aligned_adrs: List[str] = []
            impact_on_krs: Dict[str, str] = {}
            recommendations: List[str] = []

            # Extract key results from OKR text
            krs = self._extract_key_results(okr_text)
            for kr in krs:
                impact_on_krs[kr] = "needs_review"

            # Check against L0 memory if available
            if mem is not None:
                try:
                    # Search for related ADRs
                    related = mem.search(okr_text, limit=5)
                    for r in related:
                        ref_id = re.search(r'(ADR-\d+)', r.get("title", ""))
                        if ref_id:
                            aligned_adrs.append(ref_id.group(1))

                    # Check if there are ADRs that contradict the OKR
                    stats = mem.get_stats()
                    if stats.get("total_adrs", 0) > 0:
                        for i in range(1, min(stats["total_adrs"] + 1, 20)):
                            adr = mem.get_adr(i)
                            if adr:
                                adr_text = (adr.get("title", "") + " " + adr.get("content", "")).lower()
                                okr_lower = okr_text.lower()
                                # Simple contradiction detection
                                if "no" in adr_text and any(kw in okr_lower for kw in
                                    ["migrar", "cambiar", "reemplazar", "remover", "eliminar"]):
                                    risks.append(f"ADR existente '{adr['title'][:50]}' podría contradecir este OKR")
                except Exception as e:
                    logger.warning("L0 search failed during OKR validation: %s", e)

            # Heuristic viability scoring
            risk_count = len(risks)
            aligned_count = len(aligned_adrs)

            # More aligned ADRs = higher viability
            alignment_score = min(40, aligned_count * 15)
            # Risks reduce viability
            risk_penalty = min(50, risk_count * 20)
            # Base score
            viability_score = max(0, min(100, 60 + alignment_score - risk_penalty))

            # Generate recommendations
            if risk_count > 2:
                recommendations.append("Revisar OKRs con alto riesgo arquitectónico — considerar dividir en sub-OKRs")
            if aligned_count == 0:
                recommendations.append("No se encontraron ADRs alineados — considerar crear ADR de fundamentación primero")
            if viability_score < 50:
                recommendations.append("Viabilidad arquitectónica baja — consultar con Kosmos antes de proceder")
            else:
                recommendations.append("OKR arquitectónicamente viable — proceder con planificación detallada")

            result = OKRValidationResult(
                okr_id=okr_id,
                viable=viability_score >= 50,
                viability_score=round(viability_score, 1),
                aligned_adrs=aligned_adrs,
                risks=risks,
                recommendations=recommendations,
                impact_on_krs=impact_on_krs,
            )

            self._status["last_run"] = datetime.now().isoformat()
            self._status["last_score"] = result.viability_score
            self._status["total_runs"] += 1
            logger.info("OKR '%s': viability=%.1f, risks=%d", okr_id, viability_score, risk_count)
            return result

        except Exception as exc:
            logger.error("validate_okr failed: %s", exc)
            self._status["errors"] += 1
            return OKRValidationResult(
                okr_id=self._extract_okr_id(okr_text),
                viable=False,
                viability_score=0.0,
                risks=[f"Error en validación: {exc}"],
            )

    def notify_adr_impact(self, adr_text: str, existing_okrs: List[str]) -> ADRImpactNotification:
        """Analyze impact of a new ADR on existing OKRs.

        Examina el ADR y lo compara con los OKRs existentes para determinar
        qué objetivos estratégicos se ven afectados.

        Args:
            adr_text: Texto del nuevo ADR.
            existing_okrs: Lista de textos de OKRs existentes.

        Returns:
            ADRImpactNotification con OKRs afectados y resumen.
        """
        try:
            adr_lower = adr_text.lower()
            adr_id = ""
            id_match = re.search(r'(ADR-\d+)', adr_text)
            if id_match:
                adr_id = id_match.group(1)

            title_match = re.search(r'^#\s+(.+)$', adr_text, re.MULTILINE)
            adr_title = title_match.group(1).strip() if title_match else ""

            affected_okrs: List[str] = []
            kr_status: Dict[str, str] = {}
            impact_details: List[str] = []

            # Extract key topics from ADR
            adr_topics = set(re.findall(r'\b\w{4,}\b', adr_lower))
            adr_decision = re.search(
                r'##\s*Decisi[oó]n\s*\n(.*?)(?:\n##|\Z)',
                adr_text, re.DOTALL | re.IGNORECASE
            )
            decision_text = adr_decision.group(1).lower() if adr_decision else ""

            for okr_text in existing_okrs:
                okr_lower = okr_text.lower()
                okr_topics = set(re.findall(r'\b\w{4,}\b', okr_lower))

                # Topic overlap
                overlap = adr_topics & okr_topics
                if len(overlap) >= 3:
                    affected_okrs.append(okr_text[:80])
                    # Determine KR status
                    if any(w in decision_text for w in ["aprobar", "implementar", "adoptar", "migrar"]):
                        kr_status[okr_text[:60]] = "confirmed"
                        impact_details.append(f"ADR refuerza OKR '{okr_text[:50]}'")
                    elif any(w in decision_text for w in ["rechazar", "descartar", "no implementar"]):
                        kr_status[okr_text[:60]] = "needs_new_adr"
                        impact_details.append(f"ADR podría retrasar OKR '{okr_text[:50]}'")
                    else:
                        kr_status[okr_text[:60]] = "partial"
                        impact_details.append(f"ADR impacta parcialmente OKR '{okr_text[:50]}'")

            # Build summary
            summary_parts = [f"ADR {adr_id}: {adr_title}"]
            if affected_okrs:
                summary_parts.append(f"Afecta {len(affected_okrs)} OKRs")
            else:
                summary_parts.append("No afecta OKRs existentes directamente")
            summary = " — ".join(summary_parts)

            notification = ADRImpactNotification(
                adr_id=adr_id,
                adr_title=adr_title,
                affected_okrs=affected_okrs,
                kr_status=kr_status,
                summary=summary,
            )

            self._status["last_run"] = datetime.now().isoformat()
            self._status["total_runs"] += 1
            logger.info("ADR impact: %d OKRs affected", len(affected_okrs))
            return notification

        except Exception as exc:
            logger.error("notify_adr_impact failed: %s", exc)
            self._status["errors"] += 1
            return ADRImpactNotification(
                adr_id="",
                summary=f"Error analyzing impact: {exc}",
            )

    def sync_with_strategy(self, strategy_text: str) -> Dict[str, Any]:
        """Sync ADRs with current strategy, detecting gaps and contradictions.

        Args:
            strategy_text: Texto de la estrategia actual (Metis output).

        Returns:
            Dict con keys: gaps (list), contradictions (list),
            aligned (list), recommendations (list).
        """
        try:
            result: Dict[str, Any] = {
                "gaps": [],
                "contradictions": [],
                "aligned": [],
                "recommendations": [],
            }

            # Extract strategic objectives from strategy text
            objectives = re.findall(
                r'(?:Objetivo|Objective|OKR)\s*:?\s*([^.\n]+)',
                strategy_text, re.IGNORECASE
            )
            key_results = re.findall(
                r'(?:KR|Key\s*Result)\s*:?\s*([^.\n]+)',
                strategy_text, re.IGNORECASE
            )

            # If L0 available, check alignment
            if self._memory_l0 is not None:
                try:
                    stats = self._memory_l0.get_stats()
                    total_adrs = stats.get("total_adrs", 0)

                    if total_adrs == 0:
                        result["gaps"].append("No hay ADRs en L0 — la estrategia carece de fundamentación arquitectónica")

                    # Check each objective against ADRs
                    for obj in objectives:
                        hits = self._memory_l0.search(obj, limit=2)
                        if hits:
                            result["aligned"].append(f"'{obj[:50]}' respaldado por {len(hits)} ADRs")
                        else:
                            result["gaps"].append(f"Objetivo '{obj[:50]}' sin ADRs de soporte")

                    # Check for contradictions
                    # (heuristic: strategy says one thing, existing ADRs say another)
                    for kr in key_results:
                        kr_lower = kr.lower()
                        if any(w in kr_lower for w in ["migrar", "cambiar", "reemplazar", "eliminar"]):
                            # Check if there are ADRs that say "no" to this
                            hits = self._memory_l0.search(kr, limit=3)
                            for hit in hits:
                                adr = self._memory_l0.get_adr(hit["id"])
                                if adr and "no" in adr.get("content", "").lower()[:500]:
                                    result["contradictions"].append(
                                        f"KR '{kr[:50]}' puede contradecir ADR #{hit['id']}"
                                    )
                except Exception as e:
                    logger.warning("L0 sync failed: %s", e)

            # Generate recommendations
            if result["gaps"]:
                result["recommendations"].append(
                    "Crear ADRs para cubrir objetivos estratégicos sin soporte arquitectónico"
                )
            if result["contradictions"]:
                result["recommendations"].append(
                    "Revisar contradicciones entre estrategia y ADRs existentes antes de implementar"
                )
            if not result["gaps"] and not result["contradictions"]:
                result["recommendations"].append(
                    "Estrategia alineada con arquitectura actual — mantener sincronización"
                )

            self._status["last_run"] = datetime.now().isoformat()
            self._status["total_runs"] += 1
            logger.info("Strategy sync: %d gaps, %d contradictions", len(result["gaps"]), len(result["contradictions"]))
            return result

        except Exception as exc:
            logger.error("sync_with_strategy failed: %s", exc)
            self._status["errors"] += 1
            return {"gaps": [], "contradictions": [], "aligned": [], "recommendations": [f"Error: {exc}"]}

    def status(self) -> Dict[str, Any]:
        """Return contract status."""
        return dict(self._status)

    # ── Internal helpers ──

    def _extract_okr_id(self, text: str) -> str:
        """Extract OKR ID from text."""
        match = re.search(r'(OKR-\d+)', text or "")
        if match:
            return match.group(1)
        # Generate from first objective-like line
        lines = text.strip().split("\n") if text else []
        if lines:
            return f"OKR-{abs(hash(lines[0])) % 1000:03d}"
        return "OKR-000"

    def _extract_key_results(self, text: str) -> List[str]:
        """Extract Key Results from OKR text."""
        if not text:
            return []
        krs = []
        # Find list items after "Key Results" or "KR"
        kr_section = re.search(
            r'(?:Key\s*Results|KR|KRs)\s*:?\s*\n(.*?)(?:\n\n|\Z)',
            text, re.DOTALL | re.IGNORECASE
        )
        if kr_section:
            items = re.findall(r'(?:^|\n)\s*[-*\d]+[.)]\s*(.*)', kr_section.group(1))
            krs.extend(item.strip() for item in items if item.strip())
        # Fallback: look for any bullet points that mention metrics
        if not krs:
            items = re.findall(r'(?:^|\n)\s*[-*\d]+[.)]\s*(.*(?:%|\d+|reducir|aumentar|mejorar).*)', text)
            krs.extend(item.strip() for item in items if item.strip())
        return krs[:5]
