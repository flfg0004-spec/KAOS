"""Health Score Dashboard — Daily metrics.

Produces .vault/quality/dashboard.md with current health scores.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

QUALITY_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".vault" / "quality"


def build_dashboard() -> float:
    """Build health dashboard and return overall health score (0-100)."""
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)

    metrics = _collect_metrics()
    score = _compute_health_score(metrics)
    _write_dashboard(metrics, score)
    return score


def _collect_metrics() -> dict:
    metrics: dict[str, float] = {
        "vault_quality": _get_vault_quality(),
        "pipeline_success": _get_pipeline_success(),
        "bridge_token_savings": _get_bridge_savings(),
    }
    metrics["timestamp"] = datetime.now().isoformat()
    return metrics


def _get_latest_scores(limit: int = 10) -> list[dict]:
    try:
        from lib.quality.store import history
        return history(limit=limit)
    except Exception:
        return []


def _get_vault_quality() -> float:
    scores = _get_latest_scores(limit=10)
    if scores:
        return sum(s["score"] for s in scores) / len(scores)
    return 0.0


def _get_pipeline_success() -> float:
    try:
        p = Path(__file__).resolve().parent.parent.parent.parent / "cache" / "aletheia_scores.db"
        if not p.exists():
            return 0.0
        import sqlite3
        conn = sqlite3.connect(str(p))
        row = conn.execute("SELECT COUNT(*), SUM(valid) FROM scores").fetchone()
        conn.close()
        if row and row[0] and row[0] > 0:
            return (row[1] / row[0]) * 100
    except Exception:
        pass
    return 0.0


def _get_bridge_savings() -> float:
    try:
        from lib.bridge.ab_test import ABTest
        ab = ABTest()
        sessions = ab.sessions()
        prog = [s for s in sessions if s.variant == "progressive"]
        full = [s for s in sessions if s.variant == "full"]
        if prog and full:
            avg_prog = sum(s.schema_tokens for s in prog) / len(prog)
            avg_full = sum(s.schema_tokens for s in full) / len(full)
            if avg_full > 0:
                return (1 - avg_prog / avg_full) * 100
    except Exception:
        pass
    return 0.0


def _compute_health_score(metrics: dict) -> float:
    weights = {
        "vault_quality": 0.30,
        "pipeline_success": 0.30,
        "bridge_token_savings": 0.40,
    }
    score = 0.0
    for key, weight in weights.items():
        value = metrics.get(key, 0.0)
        score += weight * min(value, 100)
    return round(score, 1)


def _write_dashboard(metrics: dict, score: float) -> None:
    ts = metrics.get("timestamp", datetime.now().isoformat())
    lines = [
        f"# Health Dashboard",
        f"**Generated**: {ts}",
        f"**Overall Score**: {score}/100",
        "",
        "| Metric | Value | Threshold | Status |",
        "|--------|-------|-----------|--------|",
    ]
    checks = {
        "vault_quality": (80, "≥"),
        "pipeline_success": (90, "≥"),
        "bridge_token_savings": (40, "≥"),
    }
    for key, (threshold, op) in checks.items():
        val = metrics.get(key, 0.0)
        status = "✅" if (op == "≥" and val >= threshold) else "❌"
        lines.append(f"| {key} | {val:.1f} | {op} {threshold} | {status} |")

    dashboard_path = QUALITY_DIR / "dashboard.md"
    dashboard_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Dashboard written to %s (score: %.1f)", dashboard_path, score)


if __name__ == "__main__":
    score = build_dashboard()
    print(f"Health score: {score}/100")
