"""models.py — Dataclasses y constantes de ruta compartidas.

Extraído de kosmos_contracts.py (D3).
"""
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Paths ──
# Ajuste: desde contracts/models.py subimos 3 niveles hasta lib/
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent  # lib/
_MEMORY_DIR = _SCRIPTS_DIR.parent.parent  # .memory/
_VAULT_ROOT = _MEMORY_DIR.parent  # KAOS/
_CONTRACTS_DIR = _MEMORY_DIR / "cache" / "kosmos" / "contracts"
_ADRS_DIR = _MEMORY_DIR / "schema"
_EVALUATION_DIR = _MEMORY_DIR / "cache" / "kosmos"
_WIKI_ENTITIES_DIR = _MEMORY_DIR / "wiki" / "entities"


# ── Dataclasses ──


@dataclass
class AdherenceReport:
    """Reporte de adherencia de Kratos a recomendaciones arquitectónicas.

    Attributes:
        adr_id: ID del ADR que generó las recomendaciones.
        recommendations: Lista de recomendaciones emitidas.
        adherence_score: Score compuesto de adherencia (0-100).
        coverage_by_rec: Score por cada recomendación individual.
        deviations: Desviaciones encontradas entre lo recomendado y lo implementado.
        kratos_decisions: Decisiones que tomó Kratos durante la implementación.
        timestamp: ISO timestamp del reporte.
        adr_title: Título del ADR asociado.
    """
    adr_id: str = ""
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    adherence_score: float = 0.0
    coverage_by_rec: dict[str, float] = field(default_factory=dict)
    deviations: list[str] = field(default_factory=list)
    kratos_decisions: list[str] = field(default_factory=list)
    timestamp: str = ""
    adr_title: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        status = "✅" if self.adherence_score >= 80 else "⚠️" if self.adherence_score >= 50 else "❌"
        return (
            f"{status} Adherence: score={self.adherence_score:.1f}/100, "
            f"recs={len(self.recommendations)}, deviations={len(self.deviations)}"
        )


@dataclass
class OKRValidationResult:
    """Resultado de validación de un OKR contra la arquitectura actual.

    Attributes:
        okr_id: Identificador del OKR validado.
        viable: Si el OKR es arquitectónicamente viable.
        viability_score: Score de viabilidad (0-100).
        aligned_adrs: Lista de ADRs relevantes para el OKR.
        risks: Riesgos arquitectónicos identificados.
        recommendations: Recomendaciones para Metis.
        impact_on_krs: Dict con impacto sobre cada Key Result.
    """
    okr_id: str = ""
    viable: bool = False
    viability_score: float = 0.0
    aligned_adrs: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    impact_on_krs: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ADRImpactNotification:
    """Notificación de impacto de un nuevo ADR sobre OKRs existentes.

    Attributes:
        adr_id: ID del ADR que impacta.
        adr_title: Título del ADR.
        affected_okrs: OKRs afectados por el ADR.
        kr_status: Estado de cada KR (confirmed, partial, needs_new_adr).
        summary: Resumen ejecutivo para Metis.
    """
    adr_id: str = ""
    adr_title: str = ""
    affected_okrs: list[str] = field(default_factory=list)
    kr_status: dict[str, str] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CurationFeedback:
    """Feedback de Mnemosyne sobre la curación de un ADR.

    Attributes:
        adr_id: ID del ADR curado.
        curation_score: Score de calidad de curación (0-100).
        wikilinks_added: Número de wikilinks añadidos.
        tags_added: Tags nuevos añadidos durante la curación.
        issues_found: Problemas encontrados durante la curación.
        passed: Si la curación pasa el threshold de calidad.
        timestamp: ISO timestamp.
    """
    adr_id: str = ""
    curation_score: float = 0.0
    wikilinks_added: int = 0
    tags_added: list[str] = field(default_factory=list)
    issues_found: list[str] = field(default_factory=list)
    passed: bool = False
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        status = "✅" if self.passed else "❌"
        return f"{status} Curation: score={self.curation_score:.1f}/100, wikilinks={self.wikilinks_added}, issues={len(self.issues_found)}"


@dataclass
class FactualVerification:
    """Resultado de verificación factual de un claim arquitectónico.

    Attributes:
        query: Claim o consulta verificada.
        claims: Lista de claims extraídos y verificados.
        sources: Fuentes encontradas que respaldan o contradicen.
        confidence: Nivel de confianza (0-1).
        verified: Si el claim pudo ser verificado.
        contradictions: Contradicciones encontradas.
        timestamp: ISO timestamp.
    """
    query: str = ""
    claims: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0
    verified: bool = False
    contradictions: list[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        status = "✅" if self.verified else "⚠️" if self.confidence > 0.3 else "❌"
        return f"{status} FactCheck: confidence={self.confidence:.2f}, claims={len(self.claims)}, sources={len(self.sources)}"
