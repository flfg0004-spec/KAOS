"""Strategy Analytics — BCG score tracking, OKR health trends, strategy dashboard data.

Tracks strategy quality metrics over time for visibility and improvement.
"""

import json
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
TIMESERIES_DIR = BASE.parent / ".vault" / "quality" / "timeseries"


def track_bcg(state: dict) -> None:
    """Save BCG and OKR scores to strategy timeseries.

    Called from bcg_evaluator_node in the pipeline.
    """
    bcg_details = state.get("bcg_details", {})
    okr_quality = state.get("okr_quality", {})

    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "topic": state.get("topic", ""),
        "bcg_score": state.get("bcg_score", 0),
        "bcg_passed": state.get("bcg_passed", False),
        "okr_health": okr_quality.get("score_100", 0),
        "okr_passed": okr_quality.get("passed", False),
        "okr_count": okr_quality.get("total_okrs", 0),
        "dimension_scores": {
            dim: bcg_details.get("dimensions", {}).get(dim, {}).get("score", 0)
            for dim in ["structure", "ambiguity_handling", "narrowing", "rigor",
                         "breaking_obviousness", "synthesis", "independence", "achievement"]
        },
    }

    TIMESERIES_DIR.mkdir(parents=True, exist_ok=True)
    strategy_file = TIMESERIES_DIR / "strategy.jsonl"
    with open(strategy_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_trend(days: int = 30) -> dict:
    """Get BCG score trend over the last N days.

    Returns:
        dict with scores, direction, delta, data_points
    """
    strategy_file = TIMESERIES_DIR / "strategy.jsonl"
    if not strategy_file.exists():
        return {"scores": [], "direction": "stable", "delta": 0, "data_points": 0}

    entries = []
    with open(strategy_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass

    cutoff = datetime.now().timestamp() - (days * 86400)
    recent = [
        e for e in entries
        if datetime.fromisoformat(e.get("timestamp", "2000-01-01")).timestamp() >= cutoff
    ]

    if len(recent) < 2:
        return {
            "scores": [{"date": e.get("date"), "bcg": e.get("bcg_score"), "okr": e.get("okr_health")} for e in recent],
            "direction": "stable",
            "delta": 0,
            "data_points": len(recent),
        }

    first_bcg = recent[0].get("bcg_score", 0)
    last_bcg = recent[-1].get("bcg_score", 0)
    delta = round(last_bcg - first_bcg, 1)

    if delta > 0.5:
        direction = "improving"
    elif delta < -0.5:
        direction = "declining"
    else:
        direction = "stable"

    return {
        "scores": [
            {"date": e.get("date"), "bcg": e.get("bcg_score"), "okr": e.get("okr_health")}
            for e in recent
        ],
        "direction": direction,
        "delta": delta,
        "first_bcg": first_bcg,
        "last_bcg": last_bcg,
        "avg_bcg": round(sum(e.get("bcg_score", 0) for e in recent) / len(recent), 1),
        "avg_okr": round(sum(e.get("okr_health", 0) for e in recent) / len(recent), 1),
        "data_points": len(recent),
    }


def get_summary() -> dict:
    """Get a summary of strategy health for dashboard.

    Returns:
        dict with latest scores, trend, and recommendations
    """
    trend = get_trend(days=30)
    strategy_file = TIMESERIES_DIR / "strategy.jsonl"
    total_sessions = 0
    if strategy_file.exists():
        with open(strategy_file) as f:
            total_sessions = sum(1 for _ in f)

    return {
        "total_sessions": total_sessions,
        "latest_bcg": trend.get("last_bcg", 0) if trend.get("data_points", 0) > 0 else 0,
        "latest_okr": trend.get("avg_okr", 0) if trend.get("data_points", 0) > 0 else 0,
        "avg_bcg_30d": trend.get("avg_bcg", 0),
        "trend": trend.get("direction", "stable"),
        "delta_30d": trend.get("delta", 0),
        "data_points_30d": trend.get("data_points", 0),
        "recommendation": _recommendation(trend),
    }


def _recommendation(trend: dict) -> str:
    if trend.get("data_points", 0) == 0:
        return "Sin datos de estrategia. Ejecuta pipelines con Metis para generar métricas."
    last_bcg = trend.get("last_bcg", 0)
    direction = trend.get("direction", "stable")
    if last_bcg < 7.0:
        return "BCG score bajo. Revisar calidad de outputs estratégicos."
    if direction == "declining":
        return "BCG score en declive. Revisar cambios recientes en metodología."
    if last_bcg >= 8.0:
        return "Salud estratégica buena. Mantener metodología actual."
    return "Salud estratégica estable. Monitorear tendencia."
