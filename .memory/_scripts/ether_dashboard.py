#!/usr/bin/env python3
"""Aether Dashboard — generador de dashboard de estado en JSON.

Uso:
    python .memory/_scripts/ether_dashboard.py

Genera:
    .memory/cache/aether-dashboard.json  (dashboard completo)
"""

import json
import logging
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

# Asegurar path de import
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER
from lib.aether.config import COST_CAPS
from lib.aether.quality_store import QualityStore
from lib.aether.tracker import EtherTracker

_KAOS_ROOT = _SCRIPT_DIR.parent  # .memory → KAOS root
_CACHE_DIR = _KAOS_ROOT / "cache"
_DASHBOARD_PATH = _CACHE_DIR / "ether-dashboard.json"

logging.basicConfig(level=logging.WARNING)
_LOG = logging.getLogger("ether_dashboard")


# ── Recolectores ──────────────────────────────────────────────


def collect_routing_data() -> dict:
    """Recolecta datos de ruteo desde EtherTracker.

    Returns:
        dict con total_calls, by_tier, by_model, by_task_type,
        by_agent, resolved_by_breakdown, fallback_rate.
    """
    tracker = EtherTracker()
    stats = tracker.get_stats()
    model_bd = tracker.get_model_breakdown()
    tier_bd = tracker.get_model_tier_breakdown()
    sessions = tracker.get_recent_sessions(10_000)

    total_calls = stats.get("total_calls", 0)

    # by_model
    by_model = {}
    for model, data in model_bd.items():
        by_model[model] = data["calls"]

    # by_tier
    by_tier = {}
    for tier, data in tier_bd.items():
        by_tier[tier] = data["calls"]

    # by_task_type
    by_task_type: dict[str, int] = {}
    by_agent: dict[str, int] = {}
    for s in sessions:
        tt = s.get("task", "unknown")
        by_task_type[tt] = by_task_type.get(tt, 0) + 1

        ag = s.get("agent", "unknown")
        by_agent[ag] = by_agent.get(ag, 0) + 1

    # resolved_by_breakdown (no se persiste directamente en tracker,
    # inferimos de los modelos/tiers)
    resolved_by: dict[str, int] = {
        "task_type_map": 0,
        "multimodal": 0,
        "quality_upgrade": 0,
        "agent_default": 0,
        "absolute_default": 0,
        "fallback": 0,
    }
    # No podemos saber exactamente el resolved_by de cada sesión histórica
    # sin persistirlo. Usamos heurística: si es flash y había mejores opciones.
    # Por ahora dejamos conteo simple.
    for model, cnt in by_model.items():
        # Heurística: mimo en code_simple → calidad, kimi → multimodal/task_type
        if "kimi" in model:
            resolved_by["task_type_map"] = resolved_by.get("task_type_map", 0) + cnt
        elif "mimo" in model:
            resolved_by["quality_upgrade"] = resolved_by.get("quality_upgrade", 0) + cnt
        elif "pro" in model:
            resolved_by["task_type_map"] = resolved_by.get("task_type_map", 0) + cnt
        else:
            resolved_by["absolute_default"] = resolved_by.get("absolute_default", 0) + cnt

    fallback_rate = round(resolved_by.get("fallback", 0) / max(total_calls, 1), 4)

    return {
        "total_calls": total_calls,
        "by_tier": by_tier,
        "by_model": by_model,
        "by_task_type": by_task_type,
        "by_agent": by_agent,
        "resolved_by_breakdown": resolved_by,
        "fallback_rate": fallback_rate,
    }


def collect_cost_data() -> dict:
    """Recolecta datos de costo desde EtherTracker y config.

    Returns:
        dict con total_usd, by_tier, by_model, weekly_total,
        budget_status, cost_per_call_avg.
    """
    tracker = EtherTracker()
    stats = tracker.get_stats()
    model_bd = tracker.get_model_breakdown()
    tier_bd = tracker.get_model_tier_breakdown()

    total_usd = stats.get("total_cost_usd", 0.0)
    total_calls = stats.get("total_calls", 0)

    # by_model
    by_model = {}
    for model, data in model_bd.items():
        by_model[model] = round(data["cost_usd"], 6)

    # by_tier
    by_tier = {}
    for tier, data in tier_bd.items():
        by_tier[tier] = round(data["cost_usd"], 6)

    # Weekly total
    daily = stats.get("daily_breakdown", {})
    weekly_total = sum(d["cost_usd"] for d in daily.values())

    # Budget status
    budget_status = {}
    for tier, cap in COST_CAPS.items():
        tier_cost = by_tier.get(tier, 0.0)
        weekly_cap = cap.get("weekly_usd", 1.0)
        budget_status[tier] = {
            "used": round(tier_cost, 6),
            "cap": weekly_cap,
            "pct": round(tier_cost / weekly_cap * 100, 1) if weekly_cap > 0 else 0,
        }

    cost_per_call_avg = round(total_usd / max(total_calls, 1), 6)

    return {
        "total_usd": round(total_usd, 6),
        "by_tier": by_tier,
        "by_model": by_model,
        "weekly_total": round(weekly_total, 6),
        "budget_status": budget_status,
        "cost_per_call_avg": cost_per_call_avg,
    }


def collect_performance_data() -> dict:
    """Recolecta métricas de latencia desde EtherTracker.

    Returns:
        dict con avg_latency_ms, p50/p95/p99, by_model.
    """
    tracker = EtherTracker()
    sessions = tracker.get_recent_sessions(10_000)

    latencies = []
    by_model_lat: dict[str, list[float]] = defaultdict(list)

    for s in sessions:
        lat = s.get("latency_ms", 0)
        if lat > 0:
            latencies.append(lat)
            model = s.get("model", "unknown")
            by_model_lat[model].append(lat)

    if not latencies:
        return {
            "avg_latency_ms": 0.0,
            "p50_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "p99_latency_ms": 0.0,
            "by_model": {},
        }

    latencies.sort()
    n = len(latencies)

    def percentile(data, p):
        k = max(0, min(len(data) - 1, int(len(data) * p / 100)))
        return round(data[k], 2)

    by_model_summary = {}
    for model, vals in by_model_lat.items():
        vals.sort()
        by_model_summary[model] = {
            "avg": round(sum(vals) / len(vals), 2),
            "p95": percentile(vals, 95),
            "samples": len(vals),
        }

    return {
        "avg_latency_ms": round(sum(latencies) / n, 2),
        "p50_latency_ms": percentile(latencies, 50),
        "p95_latency_ms": percentile(latencies, 95),
        "p99_latency_ms": percentile(latencies, 99),
        "by_model": by_model_summary,
    }


def collect_quality_data() -> dict:
    """Recolecta métricas de calidad desde QualityStore.

    Returns:
        dict con avg_score, samples, by_model, by_task_type,
        worst_model, best_model.
    """
    try:
        qs = QualityStore()
        summary = qs.get_summary()
    except Exception as e:
        _LOG.warning("collect_quality_data: %s", e)
        return {
            "avg_score": 0.0,
            "samples": 0,
            "by_model": {},
            "by_task_type": {},
            "worst_model": None,
            "best_model": None,
        }

    per_model = summary.get("per_model", {})
    per_task = summary.get("per_task_type", {})
    global_avg = summary.get("global_avg", 0.0)
    total = summary.get("total_entries", 0)

    # Modelos con datos
    sorted_models = sorted(
        per_model.items(),
        key=lambda x: x[1].get("avg_score", 0),
    )
    worst_model = None
    best_model = None
    if sorted_models:
        worst = sorted_models[0]
        best = sorted_models[-1]
        worst_model = {"model": worst[0], "score": worst[1]["avg_score"]}
        best_model = {"model": best[0], "score": best[1]["avg_score"]}

    return {
        "avg_score": global_avg,
        "samples": total,
        "by_model": per_model,
        "by_task_type": per_task,
        "worst_model": worst_model,
        "best_model": best_model,
    }


def collect_cb_data() -> dict:
    """Recolecta estado del Circuit Breaker.

    Returns:
        dict con open_count, by_model, total_failures.
    """
    cb = _ETHER_CIRCUIT_BREAKER
    status = cb.get_status()

    open_count = 0
    by_model = {}
    total_failures = 0

    for model, s in status.items():
        state = s.get("state", "closed")
        by_model[model] = state
        if state == "open":
            open_count += 1
        total_failures += s.get("failures", 0)

    return {
        "open_count": open_count,
        "by_model": by_model,
        "total_failures": total_failures,
    }


# ── Alertas ────────────────────────────────────────────────────


def check_alerts(data: dict) -> list[dict]:
    """Genera alertas basadas en umbrales del dashboard.

    Umbrales:
    - 🔴 critical: CB abierto para >1 modelos
    - 🟡 warning: Budget >80% usado en algún tier
    - 🟡 warning: Quality score < 6.0 para algún modelo con >10 samples
    - 🟡 warning: Fallback rate > 5%
    - 🟢 info: MiMo routing activo (>0 calls a MiMo)

    Args:
        data: Dashboard completo.

    Returns:
        Lista de dicts con severity, component, message, timestamp.
    """
    alerts = []
    now = datetime.now(UTC).isoformat()

    # CB abierto para >1 modelos
    cb_data = data.get("circuit_breaker", {})
    if cb_data.get("open_count", 0) > 1:
        open_models = [m for m, s in cb_data.get("by_model", {}).items() if s == "open"]
        alerts.append(
            {
                "severity": "critical",
                "component": "circuit_breaker",
                "message": f"Circuit breaker open for {len(open_models)} models: {', '.join(open_models)}",
                "timestamp": now,
            }
        )

    # Budget >80%
    budget_status = data.get("cost_summary", {}).get("budget_status", {})
    for tier, info in budget_status.items():
        pct = info.get("pct", 0)
        if pct > 80:
            severity = "critical" if pct > 95 else "warning"
            alerts.append(
                {
                    "severity": severity,
                    "component": f"budget_{tier}",
                    "message": f"Budget {tier}: {pct:.1f}% used (${info.get('used', 0):.4f}/${info.get('cap', 0):.4f})",
                    "timestamp": now,
                }
            )

    # Quality score bajo
    quality = data.get("quality", {})
    for model, info in quality.get("by_model", {}).items():
        samples = info.get("samples", 0)
        score = info.get("avg_score", 10.0)
        if samples >= 10 and score < 6.0:
            alerts.append(
                {
                    "severity": "warning",
                    "component": f"quality_{model}",
                    "message": f"Quality score {score} for {model} ({samples} samples) — below threshold 6.0",
                    "timestamp": now,
                }
            )

    # Fallback rate
    fallback_rate = data.get("routing_summary", {}).get("fallback_rate", 0)
    if fallback_rate > 0.05:
        alerts.append(
            {
                "severity": "warning",
                "component": "routing",
                "message": f"Fallback rate {fallback_rate:.1%} exceeds 5% threshold",
                "timestamp": now,
            }
        )

    # MiMo activo
    mimo_calls = data.get("routing_summary", {}).get("by_tier", {}).get("mimo", 0)
    if mimo_calls > 0:
        alerts.append(
            {
                "severity": "info",
                "component": "mimo_routing",
                "message": f"MiMo routing active — {mimo_calls} calls routed to MiMo",
                "timestamp": now,
            }
        )

    return alerts


# ── Dashboard Generator ────────────────────────────────────────


def generate_dashboard() -> dict:
    """Genera el dashboard completo de ETHER v2.

    Recolecta datos de routing, costo, performance, calidad y
    circuit breaker, verifica alertas y persiste a JSON.

    Returns:
        dict con el dashboard completo.
    """
    routing = collect_routing_data()
    cost = collect_cost_data()
    perf = collect_performance_data()
    quality = collect_quality_data()
    cb = collect_cb_data()

    dashboard = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": "v2",
        "routing_summary": routing,
        "cost_summary": cost,
        "performance": perf,
        "quality": quality,
        "circuit_breaker": cb,
        "alerts": [],
    }

    dashboard["alerts"] = check_alerts(dashboard)

    # Persistir
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        tmp = _DASHBOARD_PATH.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(dashboard, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(_DASHBOARD_PATH)
        _LOG.info("Dashboard saved to %s", _DASHBOARD_PATH)
    except Exception as e:
        _LOG.warning("Failed to save dashboard: %s", e)

    return dashboard


def print_summary(dashboard: dict):
    """Imprime un resumen del dashboard en consola.

    Args:
        dashboard: Dict del dashboard.
    """
    r = dashboard.get("routing_summary", {})
    c = dashboard.get("cost_summary", {})
    p = dashboard.get("performance", {})
    q = dashboard.get("quality", {})
    cb = dashboard.get("circuit_breaker", {})
    alerts = dashboard.get("alerts", [])

    print("\n" + "=" * 60)
    print("  ETHER v2 — Dashboard Summary")
    print("=" * 60)
    print(f"  Generated: {dashboard.get('generated_at', '?')}")
    print()

    # Routing
    print("  ── Routing ──")
    print(f"  Total calls:     {r.get('total_calls', 0)}")
    print(f"  By tier:         {dict(r.get('by_tier', {}))}")
    print(f"  Fallback rate:   {r.get('fallback_rate', 0):.1%}")
    print()

    # Cost
    print("  ── Cost ──")
    print(f"  Total (USD):     ${c.get('total_usd', 0):.6f}")
    print(f"  Weekly:          ${c.get('weekly_total', 0):.6f}")
    print(f"  Avg/call:        ${c.get('cost_per_call_avg', 0):.6f}")
    for tier, info in c.get("budget_status", {}).items():
        icon = "🟢" if info["pct"] < 80 else "🟡" if info["pct"] < 95 else "🔴"
        print(f"  {icon} {tier}: ${info['used']:.4f}/{info['cap']:.4f} ({info['pct']:.1f}%)")
    print()

    # Performance
    print("  ── Performance ──")
    print(f"  Avg latency:     {p.get('avg_latency_ms', 0):.0f}ms")
    print(
        f"  P50/P95/P99:     {p.get('p50_latency_ms', 0):.0f}ms / "
        f"{p.get('p95_latency_ms', 0):.0f}ms / {p.get('p99_latency_ms', 0):.0f}ms"
    )
    print()

    # Quality
    print("  ── Quality ──")
    print(f"  Global avg:      {q.get('avg_score', 0):.2f}/10")
    print(f"  Samples:         {q.get('samples', 0)}")
    best = q.get("best_model")
    worst = q.get("worst_model")
    if best:
        print(f"  Best model:      {best['model']} ({best['score']:.2f})")
    if worst:
        print(f"  Worst model:     {worst['model']} ({worst['score']:.2f})")
    print()

    # Circuit Breaker
    print("  ── Circuit Breaker ──")
    print(f"  Open count:      {cb.get('open_count', 0)}")
    print(f"  Total failures:  {cb.get('total_failures', 0)}")
    for model, state in cb.get("by_model", {}).items():
        icon = "✅" if state == "closed" else "⚠️" if state == "half-open" else "🔴"
        print(f"  {icon} {model}: {state}")
    print()

    # Alertas
    if alerts:
        print("  ── Alerts ──")
        for a in alerts:
            icon = {"critical": "🔴", "warning": "🟡", "info": "🟢"}.get(a["severity"], "⚪")
            print(f"  {icon} [{a['severity'].upper()}] {a['component']}: {a['message']}")
        print()
    else:
        print("  ✅ No alerts\n")

    print(f"  Dashboard saved: {_DASHBOARD_PATH}")
    print("=" * 60 + "\n")


def main():
    """Entry point: generate + print dashboard."""
    dashboard = generate_dashboard()
    print_summary(dashboard)
    return 0


if __name__ == "__main__":
    sys.exit(main())

