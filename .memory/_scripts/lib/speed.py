"""Speed metrics for the dual system (Gemini Flash + DeepSeek)."""

import json
import re
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
BRIDGE_REPORTS = BASE / "bridge" / "reports"
CONTEXT_PATH = BASE / "_pipeline" / "context.json"
QUALITY_DIR = BASE.parent / ".vault" / "quality"


def _load_context() -> dict:
    if CONTEXT_PATH.exists():
        try:
            return json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _count_flash_calls(hours: int = 24) -> list[Path]:
    cutoff = datetime.now().timestamp() - (hours * 3600)
    if not BRIDGE_REPORTS.exists():
        return []
    return [f for f in sorted(BRIDGE_REPORTS.glob("response-*.md"), reverse=True)
            if f.stat().st_mtime >= cutoff]


def _flash_to_production_ratio(reports: list[Path]) -> float:
    if not reports:
        return 0.0
    ctx = _load_context()
    has_flash = ctx.get("cross_agent", {}).get("flash_exploration") is not None
    return 100.0 if has_flash else 0.0


def _avg_time_to_commit(reports: list[Path]) -> float | None:
    if len(reports) < 2:
        return None
    timestamps = [r.stat().st_mtime for r in reports[:10]]
    gaps = [timestamps[i] - timestamps[i + 1] for i in range(len(timestamps) - 1)]
    avg_min = (sum(gaps) / len(gaps)) / 60
    return round(avg_min, 1)


def report() -> str:
    """Generate speed metrics report."""
    reports_24h = _count_flash_calls(24)
    reports_1h = _count_flash_calls(1)
    ctx = _load_context()
    flash_ctx = ctx.get("cross_agent", {}).get("flash_exploration")
    avg_commit = _avg_time_to_commit(reports_24h)

    lines = [
        "# Speed Report — Sistema DUAL",
        f"*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Últimas 24h",
        f"- Llamadas Flash: {len(reports_24h)}",
        f"- Flash→Production: {'✅' if flash_ctx else '⏳'} {'vinculado' if flash_ctx else 'pendiente'}",
        f"- Time-to-commit promedio: {avg_commit if avg_commit else 'N/A'} min",
        "",
        "## Última hora",
        f"- Iteraciones: {len(reports_1h)}",
        "",
        "## Reportes Recientes",
    ]
    for r in reports_24h[:5]:
        mtime = datetime.fromtimestamp(r.stat().st_mtime).strftime("%H:%M")
        size = r.stat().st_size
        lines.append(f"- `{r.name}` ({mtime}, {size}B)")

    lines.append("")
    lines.append("---")
    lines.append(f"**Total bridge reports**: {len(list(BRIDGE_REPORTS.glob('*.md'))) if BRIDGE_REPORTS.exists() else 0}")

    report_path = QUALITY_DIR / "speed-report.md"
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")

    return "\n".join(lines)
