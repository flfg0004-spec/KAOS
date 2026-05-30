"""KosmosV2 Contracts — Subpackage con contratos bidireccionales.

Contiene 4 contratos independientes + orchestrator:
1. KosmosKratosContract  — Adherence check post-código
2. KosmosMetisContract   — OKR-ADR synchronization
3. KosmosMnemosyneContract — Curation quality
4. KosmosAletheiaContract  — Factual grounding
"""

from .models import (
    AdherenceReport,
    OKRValidationResult,
    ADRImpactNotification,
    CurationFeedback,
    FactualVerification,
)

from .kratos import KosmosKratosContract, ADHERENCE_CRITERIA
from .metis import KosmosMetisContract
from .mnemosyne import KosmosMnemosyneContract
from .aletheia import KosmosAletheiaContract
from .orchestrator import ContractOrchestrator

__all__ = [
    "AdherenceReport",
    "OKRValidationResult",
    "ADRImpactNotification",
    "CurationFeedback",
    "FactualVerification",
    "KosmosKratosContract",
    "KosmosMetisContract",
    "KosmosMnemosyneContract",
    "KosmosAletheiaContract",
    "ContractOrchestrator",
    "ADHERENCE_CRITERIA",
]
