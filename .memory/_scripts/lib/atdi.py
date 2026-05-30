"""ATDI (Architecture Technical Debt Index) — quantifies architectural debt."""

import logging

logger = logging.getLogger("atdi")

SEVERITY_WEIGHTS = {"critical": 5, "high": 4, "medium": 3, "low": 2, "cosmetic": 1}


def calculate(smell_counts: dict, total_components: int = 1, affected_components: int = 0) -> dict:
    if not smell_counts:
        return {"atdi_score": 0, "estimated_hours": 0, "severity": "none", "component_impact": 0}
    weighted_sum = sum(SEVERITY_WEIGHTS.get(k, 1) * v for k, v in smell_counts.items())
    total_smells = sum(smell_counts.values())
    avg_severity = weighted_sum / max(1, total_smells)
    impact_radius = affected_components / max(1, total_components)
    avg_hours_per_smell = avg_severity * 2
    estimated_hours = total_smells * avg_hours_per_smell * (1 + impact_radius)
    atdi_score = weighted_sum * (1 + impact_radius)
    atdi_score = min(100, atdi_score * 5)
    severity_label = "none"
    if atdi_score > 60:
        severity_label = "critical"
    elif atdi_score > 30:
        severity_label = "high"
    elif atdi_score > 15:
        severity_label = "medium"
    elif atdi_score > 5:
        severity_label = "low"
    return {
        "atdi_score": round(atdi_score, 1),
        "estimated_hours": round(estimated_hours, 1),
        "severity": severity_label,
        "total_smells": total_smells,
        "avg_severity": round(avg_severity, 2),
        "component_impact": round(impact_radius * 100, 1),
        "smell_breakdown": smell_counts,
    }


def from_smell_pipeline(smell_result: dict, total_components: int = 1, affected_components: int = 0) -> dict:
    severity_counts = smell_result.get("severity_breakdown", {})
    return calculate(severity_counts, total_components, affected_components)
