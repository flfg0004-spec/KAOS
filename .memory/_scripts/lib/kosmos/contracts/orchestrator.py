"""orchestrator.py — ContractOrchestrator: Orquestador de los 4 contratos.

Extraído de kosmos_contracts.py (D3).
"""
import logging
from datetime import datetime
from typing import Any

from .aletheia import KosmosAletheiaContract
from .kratos import KosmosKratosContract
from .metis import KosmosMetisContract
from .mnemosyne import KosmosMnemosyneContract

logger = logging.getLogger(__name__)


class ContractOrchestrator:
    """Orquestador de todos los contratos post-ADR.

    Ejecuta los 4 contratos según disponibilidad de cada agente:
    - KosmosKratosContract: si hay output de Kratos
    - KosmosMetisContract: si hay OKRs definidos
    - KosmosMnemosyneContract: siempre (curación)
    - KosmosAletheiaContract: si hay claims factuales detectados

    Graceful degradation: si un contrato falla, continua con los demás.
    """

    def __init__(self, memory_l0: Any = None, aletheia_real: bool = True, state: dict = None,
                 kratos_real: bool = True) -> None:
        """Initialize the Contract Orchestrator.

        G4: aletheia_real flag enables real Aletheia calls with fallback.
        G5: state dict for pipeline context (corrective actions feedback).
        K1: kratos_real flag enables real Kratos adherence via CodeExperience.

        Args:
            memory_l0: Optional ArchitectureMemoryL0 for context.
            aletheia_real: If True, KosmosAletheiaContract uses real Aletheia.
            state: Optional pipeline state dict for context.
            kratos_real: If True, KosmosKratosContract uses real CodeExperience API.
        """
        self._memory_l0 = memory_l0
        self._state = state or {}
        self._kratos_contract = KosmosKratosContract(memory_l0=memory_l0, use_real_api=kratos_real)
        self._metis_contract = KosmosMetisContract(memory_l0=memory_l0)
        self._mnemosyne_contract = KosmosMnemosyneContract()
        self._aletheia_contract = KosmosAletheiaContract(real_mode=aletheia_real)
        self._results: dict[str, Any] = {
            "kratos": None,
            "metis": None,
            "mnemosyne": None,
            "aletheia": None,
        }
        self._run_timestamp = ""
        logger.info("ContractOrchestrator initialized with all 4 contracts")

    # ── Public API ──

    def get_corrective_actions(self) -> list[dict[str, Any]]:
        """G5: Generate corrective actions from contract results.

        Si un contrato reporta score bajo, genera una acción correctiva
        que el pipeline puede ejecutar (re-ADR, re-análisis, etc.).

        Returns:
            List of corrective action dicts with: type, severity, message, source, score.
        """
        actions: list[dict[str, Any]] = []
        contracts = self._results.get("contracts", {})

        # Kratos: adherence < 70% → corrective ADR needed
        kratos_result = contracts.get("kratos", {})
        kratos_score = kratos_result.get("adherence_score", 100) if isinstance(kratos_result, dict) else 100
        if kratos_score < 70:
            actions.append({
                "type": "adr_revision",
                "severity": "alta",
                "message": f"Kratos adherence {kratos_score}/100 < 70% — ADR revision recommended",
                "source": "kratos",
                "score": kratos_score,
            })

        # Also check kratos_adherence (alternative key used in run_all_contracts)
        kratos_adherence = contracts.get("kratos_adherence", {})
        if isinstance(kratos_adherence, dict):
            kratos_adh_score = kratos_adherence.get("score", 100)
            if kratos_adh_score < 70:
                actions.append({
                    "type": "adr_revision",
                    "severity": "alta",
                    "message": f"Kratos adherence {kratos_adh_score}/100 < 70% — ADR revision recommended",
                    "source": "kratos",
                    "score": kratos_adh_score,
                })

        # Aletheia: factual confidence < 0.5 → re-verify claims
        aletheia_result = contracts.get("aletheia", {})
        if isinstance(aletheia_result, dict):
            verifications = aletheia_result.get("verifications", [])
            low_conf = [v for v in verifications if v.get("confidence", 1) < 0.5]
            if low_conf:
                actions.append({
                    "type": "factual_review",
                    "severity": "media",
                    "message": f"{len(low_conf)} factual claims with confidence < 0.5 — re-verify needed",
                    "source": "aletheia",
                    "score": min(v.get("confidence", 1) for v in low_conf),
                })

        # Mnemosyne: curation score < 70 → request re-curation
        mnemosyne_result = contracts.get("mnemosyne", {})
        if isinstance(mnemosyne_result, dict):
            quality_check = mnemosyne_result.get("quality_check", {})
            if isinstance(quality_check, dict):
                curation_score = quality_check.get("score", 100)
            else:
                curation_score = mnemosyne_result.get("curation_score", 100)
            if curation_score < 70:
                actions.append({
                    "type": "re_curation",
                    "severity": "media",
                    "message": f"Mnemosyne curation {curation_score}/100 < 70% — re-curation needed",
                    "source": "mnemosyne",
                    "score": curation_score,
                })

        return actions

    def run_all_contracts(self, adr_text: str, adr_id: str, state: dict[str, Any]) -> dict[str, Any]:
        """Execute all relevant contracts post-ADR.

        Examina el estado del pipeline y ejecuta los contratos necesarios:
        - Kratos contract: si state tiene output de código (kratos_output)
        - Metis contract: si state tiene OKRs (metis_to_kratos.okrs)
        - Mnemosyne contract: siempre (curación del ADR)
        - Aletheia contract: si se detectan claims factuales en el ADR

        Args:
            adr_text: Texto del ADR generado.
            adr_id: ID del ADR.
            state: Dict con el estado completo del pipeline.

        Returns:
            Dict con resultados de cada contrato ejecutado.
        """
        self._run_timestamp = datetime.now().isoformat()
        results: dict[str, Any] = {
            "orchestration_timestamp": self._run_timestamp,
            "adr_id": adr_id,
            "contracts": {},
        }

        # ── 1. KosmosKratosContract: adherence check (K1: real API + heuristic fallback) ──
        kratos_output = state.get("kratos_output", "") or ""
        has_kratos_output = kratos_output and len(kratos_output) > 100
        if has_kratos_output or adr_text:
            logger.info("▶️ Running KosmosKratosContract...")
            try:
                brief = self._kratos_contract.generate_brief(adr_text, adr_id)
                results["contracts"]["kratos_brief"] = {
                    "status": "completed",
                    "recommendations": len(brief.get("recommendations", [])),
                }

                # K1: try real CodeExperience API first
                adherence = None
                if hasattr(self._kratos_contract, 'real_adherence_check') and adr_text:
                    try:
                        adherence = self._kratos_contract.real_adherence_check(adr_id, adr_text)
                        logger.info("K1: Real adherence via CodeExperience: score=%s",
                                    adherence.adherence_score if hasattr(adherence, 'adherence_score') else 'N/A')
                    except Exception as exc:
                        logger.info("K1: CodeExperience fallback to heuristic: %s", exc)

                # Fallback: heuristic parse of kratos output
                if adherence is None and has_kratos_output:
                    adherence = self._kratos_contract.parse_adherence(kratos_output)

                if adherence is not None:
                    results["contracts"]["kratos_adherence"] = {
                        "status": "completed",
                        "score": adherence.adherence_score if hasattr(adherence, 'adherence_score') else 0,
                        "deviations": len(adherence.deviations) if hasattr(adherence, 'deviations') else 0,
                        "report": adherence.to_dict() if hasattr(adherence, 'to_dict') else {},
                        "source": "code_experience" if adherence is not None and hasattr(adherence, 'adherence_score') else "heuristic",
                    }

                    adr_path = state.get("adr", {}).get("filepath", "")
                    if adr_path:
                        update_result = self._kratos_contract.update_adr_with_adherence(adr_path, adherence)
                        results["contracts"]["kratos_adherence_update"] = update_result

            except Exception as exc:
                logger.warning("KosmosKratosContract failed (non-blocking): %s", exc)
                results["contracts"]["kratos"] = {"status": "error", "error": str(exc)}
        else:
            results["contracts"]["kratos"] = {
                "status": "skipped",
                "reason": "No Kratos output or ADR text available",
            }

        # ── 2. KosmosMetisContract: si hay OKRs ──
        cross_agent = state.get("cross_agent", {}) or state.get("context_summary", {}).get("cross_agent", {})
        metis_data = cross_agent.get("metis_to_kratos", {}) if isinstance(cross_agent, dict) else {}
        if not isinstance(metis_data, dict):
            metis_data = {}
        metis_okrs = metis_data.get("okrs", [])
        if isinstance(metis_okrs, list) and len(metis_okrs) > 0:
            logger.info("▶️ Running KosmosMetisContract (%d OKRs)...", len(metis_okrs))
            try:
                # Validate each OKR
                okr_validations = []
                for okr in metis_okrs:
                    okr_text = okr.get("objective", "") if isinstance(okr, dict) else str(okr)
                    if okr_text:
                        validation = self._metis_contract.validate_okr(okr_text)
                        okr_validations.append(validation.to_dict())

                # Notify ADR impact on OKRs
                existing_okr_texts = [
                    okr.get("objective", "") if isinstance(okr, dict) else str(okr)
                    for okr in metis_okrs
                ]
                impact = self._metis_contract.notify_adr_impact(adr_text, existing_okr_texts)

                results["contracts"]["metis"] = {
                    "status": "completed",
                    "okr_validations": okr_validations,
                    "adr_impact": impact.to_dict(),
                }
            except Exception as exc:
                logger.warning("KosmosMetisContract failed (non-blocking): %s", exc)
                results["contracts"]["metis"] = {"status": "error", "error": str(exc)}
        else:
            results["contracts"]["metis"] = {
                "status": "skipped",
                "reason": "No OKRs available in cross_agent context",
            }

        # ── 3. KosmosMnemosyneContract: siempre ──
        logger.info("▶️ Running KosmosMnemosyneContract...")
        try:
            adr_path = state.get("adr", {}).get("filepath", "")
            if adr_path:
                curation_result = self._mnemosyne_contract.request_curation(adr_path)
                quality_check = self._mnemosyne_contract.check_curation_quality(adr_path)
                results["contracts"]["mnemosyne"] = {
                    "status": "completed",
                    "curation_request": curation_result,
                    "quality_check": quality_check,
                }
            else:
                # Even without a file path, do a quality check on the text
                quality_check = self._mnemosyne_contract.check_curation_quality(
                    state.get("adr", {}).get("filepath", ""),
                    min_score=70.0,
                )
                results["contracts"]["mnemosyne"] = {
                    "status": "partial",
                    "note": "No ADR file path — quality check limited",
                    "quality_check": quality_check,
                }
        except Exception as exc:
            logger.warning("KosmosMnemosyneContract failed (non-blocking): %s", exc)
            results["contracts"]["mnemosyne"] = {"status": "error", "error": str(exc)}

        # ── 4. KosmosAletheiaContract: si hay claims factuales ──
        logger.info("▶️ Scanning for factual claims in ADR...")
        try:
            claims = self._aletheia_contract.detect_uncertain_claims(adr_text)
            if claims:
                logger.info("▶️ Running KosmosAletheiaContract (%d claims)...", len(claims))
                verifications = []
                for claim in claims[:5]:  # limit to top 5 claims
                    verification = self._aletheia_contract.real_request_verification(claim)
                    verifications.append(verification.to_dict())

                results["contracts"]["aletheia"] = {
                    "status": "completed",
                    "claims_detected": len(claims),
                    "claims_verified": len(verifications),
                    "verifications": verifications,
                }
            else:
                results["contracts"]["aletheia"] = {
                    "status": "skipped",
                    "reason": "No uncertain claims detected in ADR",
                }
        except Exception as exc:
            logger.warning("KosmosAletheiaContract failed (non-blocking): %s", exc)
            results["contracts"]["aletheia"] = {"status": "error", "error": str(exc)}

        # Store results
        self._results = results

        # G5: Generate corrective actions from contract results
        try:
            actions = self.get_corrective_actions()
            results["corrective_actions"] = actions
            if actions:
                logger.info("G5: %d corrective actions generated", len(actions))
        except Exception as exc:
            logger.warning("G5: get_corrective_actions failed (non-blocking): %s", exc)
            results["corrective_actions"] = []

        logger.info(
            "Contract orchestration complete: %d contracts executed, %d corrective actions",
            len([c for c in results["contracts"].values() if c.get("status") == "completed"]),
            len(results.get("corrective_actions", [])),
        )
        return results

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all contract results.

        Returns:
            Dict con keys: timestamp, adr_id, contract_statuses, summary_text.
        """
        contracts = self._results.get("contracts", {})
        statuses = {}
        for name, result in contracts.items():
            if isinstance(result, dict):
                statuses[name] = result.get("status", "unknown")
            else:
                statuses[name] = "unknown"

        completed = sum(1 for s in statuses.values() if s == "completed")
        skipped = sum(1 for s in statuses.values() if s == "skipped")
        errors = sum(1 for s in statuses.values() if s == "error")

        # G5: Include corrective actions in summary
        corrective_actions = self._results.get("corrective_actions", [])
        corrective_count = len(corrective_actions)

        summary_text = (
            f"Contracts: {completed} completed, {skipped} skipped, "
            f"{errors} errors, {corrective_count} corrective actions"
        )

        return {
            "timestamp": self._run_timestamp,
            "adr_id": self._results.get("adr_id", ""),
            "contract_statuses": statuses,
            "completed": completed,
            "skipped": skipped,
            "errors": errors,
            "corrective_actions": corrective_count,
            "summary_text": summary_text,
        }

    def get_contract_statuses(self) -> dict[str, dict[str, Any]]:
        """Get status of each individual contract.

        Returns:
            Dict con keys: kratos, metis, mnemosyne, aletheia, cada uno con
            status propio.
        """
        return {
            "kratos": self._kratos_contract.status(),
            "metis": self._metis_contract.status(),
            "mnemosyne": self._mnemosyne_contract.status(),
            "aletheia": self._aletheia_contract.status(),
        }
