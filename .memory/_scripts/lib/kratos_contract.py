"""Formal contract schemas for Kosmos↔Kratos cross-agent communication.

TypedDicts define the exact shape of cross-agent data structures.
Validated by KosmosKratosContract and consumed by Kratos type guards.
"""

from typing import TypedDict

from lib.kratos_telemetry import KratosTelemetry


class MetisToKratos(TypedDict, total=False):
    """Shape of cross_agent['metis_to_kratos'] — produced by Metis, consumed by Kratos."""
    strategy_summary: str
    okrs: list[dict]
    risks: list[dict]
    confidence: str
    priority: str
    initiatives: list[dict]
    kr_assignment: dict
    execution_plan: dict
    # --- nuevos campos Kratos 2.0 ---
    execution_strategy: str          # "waterfall" | "iterative" | "agile"
    risk_profile: str                # "conservative" | "balanced" | "aggressive"
    quality_targets: dict            # {"min_composite": 7.0, "required_gates": ["syntax", "lint"]}
    evolve_permission: bool          # permite auto-evolución del código
    language_targets: list[str]      # ["python", "rust", "typescript"]


class AletheiaToKratos(TypedDict, total=False):
    """Shape of cross_agent['aletheia_to_kratos'] — produced by Aletheia."""
    code_context: str
    research_context: str
    sources: list[str]


class KratosOutput(TypedDict, total=False):
    """Shape of kratos_node() return value.

    kratos_decision can be KratosDecision (enum) or str for backward compat.
    telemetry is populated when use_kratos_telemetry feature flag is active.
    """
    kratos_output: str
    kratos_prompt: str
    kratos_decision: str  # can be KratosDecision or str for backward compat
    governance_allowed: bool
    governance_denials: list[str]
    telemetry: KratosTelemetry | None


def validate_metis_to_kratos(data) -> dict:
    """Validate and coerce metis_to_kratos data to contract. Never raises."""
    if not isinstance(data, dict):
        return {"strategy_summary": "", "okrs": [], "risks": [],
                "confidence": "media", "priority": "high", "initiatives": [],
                "kr_assignment": {}, "execution_plan": {},
                "execution_strategy": "iterative", "risk_profile": "balanced",
                "quality_targets": {}, "evolve_permission": False,
                "language_targets": []}
    return data


def validate_aletheia_to_kratos(data) -> dict:
    """Validate and coerce aletheia_to_kratos data to contract. Never raises."""
    if not isinstance(data, dict):
        return {"code_context": "", "research_context": "", "sources": []}
    return data
