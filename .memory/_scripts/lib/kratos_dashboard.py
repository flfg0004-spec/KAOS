"""Kratos Telemetry Dashboard — enhanced CLI dashboard."""

import logging

from lib.kratos_telemetry import telemetry_summary
from lib.feature_flags import is_enabled

logger = logging.getLogger(__name__)


def render_dashboard() -> str:
    """Render telemetry data as a CLI dashboard string."""
    data = telemetry_summary()

    lines = []
    lines.append("=" * 56)
    lines.append("  KRATOS TELEMETRY DASHBOARD")
    lines.append("=" * 56)

    total = data.get("total", 0)
    lines.append(f"  Total invocations : {total}")
    lines.append(f"  Avg quality score : {data.get('avg_quality_score', 0.0)}")
    lines.append(f"  Avg duration (ms) : {data.get('avg_duration_ms', 0.0)}")

    # Health score
    if total > 0:
        qs = data.get("avg_quality_score", 0.0)
        dur = data.get("avg_duration_ms", 0.0)
        health = min(100, (qs / 10) * 50 + max(0, 50 - (dur / 100)))
        lines.append(f"  Health score      : {health:.1f}/100")
    lines.append("")

    by_decision = data.get("by_decision", {})
    if by_decision:
        lines.append("  ── By Decision ──")
        for decision, count in sorted(by_decision.items()):
            lines.append(f"    {decision:20s}: {count}")
        lines.append("")

    by_language = data.get("by_language", {})
    if by_language:
        lines.append("  ── By Language ──")
        for lang, count in sorted(by_language.items()):
            lines.append(f"    {lang:20s}: {count}")
        lines.append("")

    # Active flags section
    kratos_flags = [
        "use_kratos_telemetry", "use_real_coverage", "use_parallel_gates",
        "use_early_exit", "use_real_mypy", "use_circuit_breaker",
        "use_rust_gates", "use_ts_gates", "use_go_gates",
    ]
    active = [f for f in kratos_flags if is_enabled(f)]
    if active:
        lines.append("  ── Active Flags ──")
        for flag in active:
            lines.append(f"    {flag}")
        lines.append("")

    recent = data.get("recent", [])
    if recent:
        lines.append(f"  ── Recent ({len(recent)} entries) ──")
        for entry in recent[-5:]:
            ts = entry.get("timestamp", "?")[:19]
            dec = entry.get("decision", "?")
            qs = entry.get("quality_score", "?")
            lines.append(f"    {ts}  {dec:15s}  q={qs}")

    lines.append("=" * 56)
    return "\n".join(lines)


def show_dashboard() -> None:
    """Print the dashboard to stdout, respecting the use_kratos_dashboard flag."""
    if not is_enabled("use_kratos_dashboard"):
        print("[Dashboard disabled — set use_kratos_dashboard=true]")
        return
    print(render_dashboard())
