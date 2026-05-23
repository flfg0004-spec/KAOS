"""Dashboard Builder — agrega resultados históricos del pipeline CI."""
import json
from pathlib import Path
from datetime import datetime, timedelta

TS_FILE = Path(__file__).resolve().parent.parent / ".vault" / "quality" / "timeseries" / "pipeline-scores.json"
DASHBOARD_FILE = Path(__file__).resolve().parent.parent / ".vault" / "quality" / "pipeline-dashboard.md"


def load_timeseries() -> list[dict]:
    if TS_FILE.exists():
        try:
            data = json.loads(TS_FILE.read_text(encoding="utf-8"))
            return data.get("scores", [])
        except Exception:
            return []
    return []


def compute_trend(scores: list[dict], window: int = 5) -> dict:
    if len(scores) < 2:
        avg = scores[0].get("composite", 0) if scores else 0
        return {"direction": "stable", "delta": 0, "avg_composite": avg}
    recent = scores[-window:] if len(scores) > window else scores
    avg = sum(s.get("composite", 0) for s in recent) / len(recent)
    prev_avg = sum(s.get("composite", 0) for s in scores[:-window]) / max(1, len(scores[:-window]))
    delta = round(avg - prev_avg, 1)
    direction = "up" if delta > 3 else ("down" if delta < -3 else "stable")
    return {"direction": direction, "delta": delta, "avg_composite": round(avg, 1)}


def build_dashboard(scores: list[dict]) -> str:
    trend = compute_trend(scores)
    latest = scores[-1] if scores else {}
    icon = {"up": "📈", "down": "📉", "stable": "➡️"}.get(trend["direction"], "➡️")
    direction_label = {"up": "mejorando", "down": "degradando", "stable": "estable"}.get(trend["direction"], "estable")

    lines = [
        "# Pipeline Dashboard",
        f"*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Resumen",
        f"| Métrica | Valor | Tendencia |",
        f"|---------|-------|-----------|",
        f"| Último Composite | {latest.get('composite', 'N/A')}/100 | {icon} {direction_label} ({trend['delta']:+}) |",
        f"| Último System Health | {latest.get('system_health', 'N/A')}/100 | |",
        f"| Último Critic Score | {latest.get('critic_score', 'N/A')}/100 | |",
        f"| Total ejecuciones | {len(scores)} | |",
        f"| Promedio histórico | {trend['avg_composite']}/100 | |",
        "",
        "## Histórico",
        "| Fecha | Composite | Health | Critic | Duración | Topic |",
        "|-------|-----------|--------|--------|----------|-------|",
    ]
    for s in reversed(scores[-30:]):
        lines.append(
            f"| {s.get('date', '?')} | {s.get('composite', '?')} | "
            f"{s.get('system_health', '?')} | {s.get('critic_score', '?')} | "
            f"{s.get('duration_s', '?')}s | {s.get('topic', '?')[:40]} |"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    scores = load_timeseries()
    dashboard = build_dashboard(scores)
    DASHBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_FILE.write_text(dashboard, encoding="utf-8")
    print(f"Dashboard written: {DASHBOARD_FILE}")
    print(f"Total entries: {len(scores)}")
    if scores:
        print(f"Latest: composite={scores[-1].get('composite')}")
