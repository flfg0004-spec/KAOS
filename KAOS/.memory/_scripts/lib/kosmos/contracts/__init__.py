"""KosmosV2 Contracts — Subpackage con contratos bidireccionales.

Contiene 4 contratos independientes + orchestrator:
1. KosmosKratosContract  — Adherence check post-código
2. KosmosMetisContract   — OKR-ADR synchronization
3. KosmosMnemosyneContract — Curation quality
4. KosmosAletheiaContract  — Factual grounding
"""

from .aletheia import KosmosAletheiaContract
from .kratos import ADHERENCE_CRITERIA, KosmosKratosContract
from .metis import KosmosMetisContract
from .mnemosyne import KosmosMnemosyneContract
from .models import (
    AdherenceReport,
    ADRImpactNotification,
    CurationFeedback,
    FactualVerification,
    OKRValidationResult,
)
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
