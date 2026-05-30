"""Knowledge levels and tier management for Knowledge Scorer.

Tiers map 0-100 scores to 6 quality levels:
  RAW (0-20) → ROUGH (21-40) → DRAFT (41-60) → REVIEW (61-75) → CURATED (76-90) → CANONICAL (91-100)
"""

from typing import Optional

TIERS: dict[str, tuple[int, int, str]] = {
    "RAW": (0, 20, "Sin procesar, necesita síntesis completa"),
    "ROUGH": (21, 40, "Borrador, necesita refinamiento mayor"),
    "DRAFT": (41, 60, "Estructura básica, necesita wikilinks + calidad"),
    "REVIEW": (61, 75, "Bueno, necesita revisión menor"),
    "CURATED": (76, 90, "Curado, listo para consumo"),
    "CANONICAL": (91, 100, "Conocimiento canónico, referencia definitiva"),
}

TIER_ORDER: list[str] = ["RAW", "ROUGH", "DRAFT", "REVIEW", "CURATED", "CANONICAL"]


def assign_level(score: float) -> str:
    """Retorna nombre del tier para un score 0-100."""
    for ot, (low, high, _) in TIERS.items():
        if low <= score <= high:
            return ot
    return "RAW"


def needs_synthesis(score: float) -> bool:
    """True si score < 60 (threshold REVIEW)."""
    return score < 60


def get_tier_info(tier: str) -> dict:
    """Retorna información completa del tier."""
    if tier not in TIERS:
        raise ValueError(f"Unknown tier: {tier}. Valid: {', '.join(TIERS)}")
    low, high, desc = TIERS[tier]
    return {
        "name": tier,
        "min_score": low,
        "max_score": high,
        "description": desc,
        "requires_synthesis": needs_synthesis((low + high) / 2.0),
        "requires_hitl": tier == "CANONICAL",
    }


def can_promote(current_score: float, previous_score: Optional[float] = None) -> dict:
    """Retorna si puede promocionar de tier y a cuál.

    Si previous_score es None, solo evalúa score actual.
    Previene degradaciones bruscas (>20 pts drop).
    """
    current_tier = assign_level(current_score)
    result = {
        "can_promote": False,
        "current_tier": current_tier,
        "target_tier": current_tier,
        "blocked_by": None,
    }

    if previous_score is not None:
        drop = previous_score - current_score
        if drop > 20:
            result["blocked_by"] = f"Score drop too large: {drop:.1f} pts (max 20)"
            return result

    idx = TIER_ORDER.index(current_tier) if current_tier in TIER_ORDER else -1
    if idx < len(TIER_ORDER) - 1:
        target = TIER_ORDER[idx + 1]
        target_min = TIERS[target][0]
        if current_score >= target_min:
            result["can_promote"] = True
            result["target_tier"] = target

    return result


def get_promotion_path(current_tier: str) -> list[str]:
    """Retorna los siguientes tiers para llegar a CANONICAL."""
    if current_tier not in TIER_ORDER:
        return []
    idx = TIER_ORDER.index(current_tier)
    return TIER_ORDER[idx + 1:]
