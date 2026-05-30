#!/usr/bin/env python3
"""Weekly score report for Aletheia quality metrics."""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.aletheia_score_store import history, average, trend
from lib.quality.agent import summary as kq_summary, latest as kq_latest

RAW_DIR = Path(__file__).resolve().parent.parent / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

def generate():
    lines = []
    lines.append(f"# Reporte Semanal de Calidad — Aletheia")
    lines.append(f"**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    avg_score = average(days=7)
    recent = history(limit=10)
    lines.append("## Score Store (validate_aletheia_output)")
    lines.append(f"- Promedio últimos 7 días: **{avg_score:.3f}**")
    lines.append(f"- Total registros recientes: {len(recent)}")
    lines.append("")

    if recent:
        lines.append("| # | Fecha | Tema | Score | Válido |")
        lines.append("|---|-------|------|-------|--------|")
        for i, r in enumerate(recent[:5], 1):
            lines.append(f"| {i} | {r['timestamp'][:10]} | {r['topic'][:40]} | {r['score']} | {r['valid']} |")
        lines.append("")

    t = trend(days=14)
    if t and len(t) >= 2:
        lines.append(f"## Tendencia (14 días)")
        lines.append(f"- Puntos de datos: {len(t)}")
        lines.append(f"- Primer score: {t[0].get('avg_score', 0)}")
        lines.append(f"- Último score: {t[-1].get('avg_score', 0)}")
        delta = round(t[-1].get('avg_score', 0) - t[0].get('avg_score', 0), 3)
        direction = "↑" if delta > 0.01 else ("↓" if delta < -0.01 else "→")
        lines.append(f"- Delta: {delta} {direction}")
        lines.append("")

    qs = kq_summary()
    lines.append("## Kosmos Quality Engine")
    lines.append(f"- Total evaluaciones: {qs.get('total', 0)}")
    lines.append(f"- Promedio composite: **{qs.get('avg_composite', 0)}/100**")
    lines.append(f"- Métricas reales (DeepEval): {qs.get('real_metrics', False)}")
    if qs.get("agents"):
        lines.append("### Por agente:")
        for agent, data in qs["agents"].items():
            lines.append(f"- {agent}: avg {data['avg_composite']}/100 ({data['count']} registros)")
    lines.append("")

    latest_entries = kq_latest(5)
    if latest_entries:
        lines.append("### Últimas evaluaciones:")
        lines.append("| Fecha | Agente | Composite | Real |")
        lines.append("|-------|--------|-----------|------|")
        for e in latest_entries:
            lines.append(f"| {e.get('timestamp', '')[:16]} | {e.get('agent', '')} | {e.get('composite', 0)} | {e.get('real_metrics', False)} |")
        lines.append("")

    report = "\n".join(lines)
    out_path = RAW_DIR / f"aletheia-quality-report-{datetime.now().strftime('%Y%m%d')}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"Reporte generado: {out_path}")
    return report

if __name__ == "__main__":
    generate()
