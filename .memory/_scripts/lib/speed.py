"""Speed metrics for the dual system (Gemini Flash + DeepSeek)."""

import json
import re
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
BRIDGE_REPORTS = BASE / "bridge" / "reports"
CONTEXT_PATH = BASE / "_pipeline" / "context.json"
PIPELINE_DIR = BASE / "_pipeline"
QUALITY_DIR = BASE.parent / ".vault" / "quality"
TIMESERIES_DIR = QUALITY_DIR / "timeseries"
FLASH_PROD_FILE = TIMESERIES_DIR / "flash-production.json"


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
    """Calculate ratio of pipelines that used flash context vs total pipelines."""
    if not FLASH_PROD_FILE.exists():
        return 0.0
    try:
        data = json.loads(FLASH_PROD_FILE.read_text(encoding="utf-8"))
        links = data.get("links", [])
        if not links:
            return 0.0
        recent = [l for l in links if l.get("pipeline_id", "").startswith("P-")]
        return round(len(recent) / max(len(links), 1) * 100, 1)
    except Exception:
        return 0.0


def _avg_time_to_commit(reports: list[Path]) -> float | None:
    if len(reports) < 2:
        return None
    timestamps = [r.stat().st_mtime for r in reports[:10]]
    gaps = [timestamps[i] - timestamps[i + 1] for i in range(len(timestamps) - 1)]
    avg_min = (sum(gaps) / len(gaps)) / 60
    return round(avg_min, 1)


def _pipeline_benchmarks() -> dict:
    """Return pipeline duration data from timeseries."""
    bench = {"exploracion": [], "desarrollo": [], "produccion": [], "standard": [], "flash": [], "deep": [], "massive": []}
    durations_file = TIMESERIES_DIR / "pipeline-durations.json"
    if durations_file.exists():
        try:
            data = json.loads(durations_file.read_text(encoding="utf-8"))
            for entry in data.get("entries", []):
                profile = entry.get("profile", "desarrollo")
                dur = entry.get("duration_s", 0)
                if profile in bench and dur > 0:
                    bench[profile].append(dur)
        except Exception:
            pass
    return bench


def report() -> str:
    """Generate speed metrics report."""
    reports_24h = _count_flash_calls(24)
    reports_1h = _count_flash_calls(1)
    ratio = _flash_to_production_ratio(reports_24h)
    avg_commit = _avg_time_to_commit(reports_24h)
    benchmarks = _pipeline_benchmarks()

    lines = [
        "# Speed Report — Sistema DUAL",
        f"*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Últimas 24h",
        f"- Llamadas Flash: {len(reports_24h)}",
        f"- Flash→Production ratio: {ratio}%",
        f"- Time-to-commit promedio: {avg_commit if avg_commit else 'N/A'} min",
        "",
        "## Última hora",
        f"- Iteraciones: {len(reports_1h)}",
        "",
        "## Benchmarks por Perfil",
    ]
    for profile, durations in benchmarks.items():
        if durations:
            avg_dur = sum(durations) / len(durations)
            lines.append(f"- **{profile}**: {avg_dur:.0f}s avg ({len(durations)} ejecuciones)")
        else:
            lines.append(f"- **{profile}**: sin datos")

    lines.extend([
        "",
        "## Reportes Recientes",
    ])
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
