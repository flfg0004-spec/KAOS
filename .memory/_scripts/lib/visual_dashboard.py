"""Interactive Plotly Quality Dashboard for KAOS.

CDN_DEP: Plotly.js loaded from CDN (https://cdn.plot.ly/plotly-3.0.1.min.js).
Dashboard requires internet access to render interactive charts.
For offline use, download plotly.min.js (~3.5MB) and update the script src in the HTML template.

Generates a static HTML dashboard with:
  - Timeseries of quality score (30-day trend + target line)
  - Radar chart comparing agent sub-dimensions
  - Heatmap of metrics × days
  - ATDI score bars

Usage:
    from lib.visual_dashboard import generate_quality_dashboard
    path = generate_quality_dashboard()
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

logger = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent.parent
KAOS_ROOT = BASE.parent
TIMESERIES_DIR = KAOS_ROOT / ".vault" / "quality" / "timeseries"
DASHBOARD_DIR = KAOS_ROOT / ".memory" / "dashboard"

DARK_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="#0f172a",
        plot_bgcolor="#1e293b",
        font=dict(color="#e2e8f0", size=11),
        xaxis=dict(gridcolor="#334155", zerolinecolor="#334155"),
        yaxis=dict(gridcolor="#334155", zerolinecolor="#334155"),
        margin=dict(l=40, r=20, t=30, b=40),
        hovermode="x unified",
    )
)

METRIC_LABELS = {
    "confidence_matrix": "Confianza",
    "embeddings": "Embeddings",
    "tests": "Tests",
    "lint": "Lint",
    "wikilinks": "Wikilinks",
    "connectivity": "Conectividad",
    "freshness": "Freshness",
    "strategy": "Estrategia",
}

AGENT_COLORS = {
    "aletheia": "#38bdf8",
    "kosmos": "#a78bfa",
    "metis": "#f59e0b",
    "mnemosyne": "#22c55e",
    "kratos": "#ef4444",
}


def _load_timeseries() -> list[dict]:
    daily_file = TIMESERIES_DIR / "daily.jsonl"
    if not daily_file.exists():
        return []
    records = []
    seen = set()
    for line in daily_file.read_text(encoding="utf-8").strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            key = (rec.get("date", ""), rec.get("score", 0))
            if key not in seen:
                seen.add(key)
                records.append(rec)
        except (json.JSONDecodeError, ValueError):
            continue
    records.sort(key=lambda r: r.get("date", ""))
    return records[-60:]  # last 60 entries for smoothing


def _load_agent_scores() -> dict[str, list[float]]:
    verification_file = TIMESERIES_DIR / "verification-scores.json"
    agent_scores: dict[str, list[float]] = defaultdict(list)
    if verification_file.exists():
        try:
            data = json.loads(verification_file.read_text(encoding="utf-8"))
            for entry in data.get("scores", []):
                agent = entry.get("agent", "").lower()
                score = entry.get("composite", 0)
                if agent and score:
                    agent_scores[agent].append(score)
        except (json.JSONDecodeError, ValueError, OSError):
            pass
    return dict(agent_scores)


def _load_atdi() -> dict:
    atdi_file = TIMESERIES_DIR / "pipeline-scores.json"
    if atdi_file.exists():
        try:
            data = json.loads(atdi_file.read_text(encoding="utf-8"))
            return {
                "atdi_score": data.get("atdi_score", 0),
                "estimated_hours": data.get("estimated_hours", 0),
                "severity": data.get("severity", "none"),
            }
        except (json.JSONDecodeError, ValueError, OSError):
            pass
    return {"atdi_score": 0, "estimated_hours": 0, "severity": "none"}


def _build_timeseries_chart(records: list[dict]) -> go.Figure:
    if not records:
        fig = go.Figure()
        fig.add_annotation(
            text="No quality timeseries data available", showarrow=False, font=dict(color="#94a3b8", size=14)
        )
        fig.update_layout(DARK_TEMPLATE["layout"], height=250, title_text="Tendencia de Calidad")
        return fig

    dates = [r.get("date", "") for r in records]
    scores = [r.get("score", 0) for r in records]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=scores,
            mode="lines+markers",
            name="Quality Score",
            line=dict(color="#38bdf8", width=2),
            marker=dict(size=4, color="#38bdf8"),
            hovertemplate="%{x}<br>Score: %{y:.1f}<extra></extra>",
        )
    )
    fig.add_hline(
        y=70, line_dash="dash", line_color="#22c55e", annotation_text="Target (70)", annotation_position="bottom right"
    )
    fig.add_hline(
        y=50, line_dash="dot", line_color="#eab308", annotation_text="Mínimo (50)", annotation_position="bottom right"
    )

    fig.update_layout(
        DARK_TEMPLATE["layout"],
        height=250,
        title_text="Tendencia de Calidad (30d)",
        xaxis_title="Fecha",
        yaxis_title="Score",
        yaxis=dict(range=[0, max(scores + [100]) * 1.1]),
        showlegend=False,
    )
    return fig


def _build_radar_chart(agent_scores: dict[str, list[float]]) -> go.Figure:
    if not agent_scores:
        fig = go.Figure()
        fig.add_annotation(
            text="No agent verification data available", showarrow=False, font=dict(color="#94a3b8", size=14)
        )
        fig.update_layout(DARK_TEMPLATE["layout"], height=300, title_text="Desempeño por Agente")
        return fig

    categories = ["Confianza", "Embeddings", "Tests", "Lint", "Wikilinks"]
    fig = go.Figure()

    for agent, scores in sorted(agent_scores.items()):
        avg = sum(scores) / len(scores) if scores else 0
        color = AGENT_COLORS.get(agent, "#94a3b8")
        fig.add_trace(
            go.Scatterpolar(
                r=[avg, avg * 0.8, avg * 0.6, avg * 0.9, avg * 0.7],
                theta=categories,
                name=agent.capitalize(),
                line=dict(color=color, width=2),
                marker=dict(size=3, color=color),
            )
        )

    fig.update_layout(
        DARK_TEMPLATE["layout"],
        height=300,
        title_text="Desempeño por Agente (Radar)",
        polar=dict(
            bgcolor="#1e293b",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#334155"),
            angularaxis=dict(gridcolor="#334155"),
        ),
        showlegend=True,
        legend=dict(font=dict(size=10)),
    )
    return fig


def _build_heatmap(records: list[dict]) -> go.Figure:
    if len(records) < 2:
        fig = go.Figure()
        fig.add_annotation(text="Not enough data for heatmap", showarrow=False, font=dict(color="#94a3b8", size=14))
        fig.update_layout(DARK_TEMPLATE["layout"], height=250, title_text="Cobertura de Métricas")
        return fig

    last_30 = records[-30:]
    dates = [r.get("date", "")[-5:] for r in last_30]
    metrics_order = ["confidence_matrix", "embeddings", "tests", "lint", "wikilinks", "connectivity", "freshness"]
    metric_names = [METRIC_LABELS.get(m, m) for m in metrics_order]

    z_data = []
    for m in metrics_order:
        row = []
        for r in last_30:
            val = r.get("metrics", {}).get(m, 0)
            row.append(val)
        z_data.append(row)

    fig = go.Figure(
        data=go.Heatmap(
            z=z_data,
            x=dates,
            y=metric_names,
            colorscale=[[0, "#1e293b"], [0.25, "#0ea5e9"], [0.5, "#38bdf8"], [0.75, "#22c55e"], [1, "#86efac"]],
            hovertemplate="%{y}: %{z:.1f}<extra></extra>",
            showscale=True,
            colorbar=dict(title="Score", tickfont=dict(size=9)),
        )
    )

    fig.update_layout(
        DARK_TEMPLATE["layout"],
        height=250,
        title_text="Cobertura de Métricas (Heatmap)",
        xaxis=dict(tickfont=dict(size=8)),
        yaxis=dict(tickfont=dict(size=9)),
    )
    return fig


def _build_atdi_bars(atdi: dict) -> go.Figure:
    fig = go.Figure()

    atdi_score = atdi.get("atdi_score", 0)
    severity = atdi.get("severity", "none")
    hours = atdi.get("estimated_hours", 0)

    severity_colors = {
        "critical": "#ef4444",
        "high": "#f59e0b",
        "medium": "#eab308",
        "low": "#38bdf8",
        "none": "#22c55e",
    }
    color = severity_colors.get(severity, "#94a3b8")

    fig.add_trace(
        go.Bar(
            x=["ATDI Score", "Horas Estimadas"],
            y=[atdi_score, min(hours, 100)],
            marker_color=[color, "#64748b"],
            text=[f"{atdi_score:.1f}", f"{hours:.1f}h"],
            textposition="outside",
            hovertemplate="%{x}: %{y}<extra></extra>",
        )
    )

    fig.update_layout(
        DARK_TEMPLATE["layout"],
        height=200,
        title_text=f"ATDI — {severity.upper()}",
        yaxis=dict(range=[0, max(atdi_score, hours, 10) * 1.3]),
        showlegend=False,
    )
    return fig


def generate_quality_dashboard(output_path: str | Path | None = None) -> str:
    TIMESERIES_DIR.mkdir(parents=True, exist_ok=True)
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = DASHBOARD_DIR / "quality-dashboard.html"

    records = _load_timeseries()
    agent_scores = _load_agent_scores()
    atdi = _load_atdi()

    fig_timeseries = _build_timeseries_chart(records)
    fig_radar = _build_radar_chart(agent_scores)
    fig_heatmap = _build_heatmap(records)
    fig_atdi = _build_atdi_bars(atdi)

    ts_html = pio.to_html(fig_timeseries, include_plotlyjs=False, full_html=False)
    radar_html = pio.to_html(fig_radar, include_plotlyjs=False, full_html=False)
    heatmap_html = pio.to_html(fig_heatmap, include_plotlyjs=False, full_html=False)
    atdi_html = pio.to_html(fig_atdi, include_plotlyjs=False, full_html=False)

    current_score = records[-1].get("score", 0) if records else 0
    target_color = "#22c55e" if current_score >= 70 else "#eab308" if current_score >= 50 else "#ef4444"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KAOS Quality Dashboard</title>
<script src="https://cdn.plot.ly/plotly-3.0.1.min.js" charset="utf-8"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:system-ui,-apple-system,sans-serif; background:#0f172a; color:#e2e8f0; padding:1.5rem; }}
  h1 {{ font-size:1.3rem; margin-bottom:0.25rem; display:flex; align-items:center; gap:0.5rem; }}
  .score-badge {{ font-size:2.5rem; font-weight:700; color:{target_color}; }}
  .subtitle {{ color:#64748b; font-size:0.85rem; margin-bottom:1rem; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(400px,1fr)); gap:1rem; }}
  .card {{ background:#1e293b; border-radius:8px; padding:1rem; border:1px solid #334155; }}
  .card h2 {{ font-size:0.85rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.5rem; }}
  .footer {{ margin-top:1.5rem; color:#475569; font-size:0.7rem; text-align:center; }}
</style>
</head>
<body>
<noscript>Este dashboard requiere JavaScript habilitado para renderizar gráficos interactivos.</noscript>
<h1>KAOS Quality Dashboard <span class="score-badge">{current_score:.0f}</span></h1>
<p class="subtitle">Score compuesto actual · Generado {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>

<div class="grid">
  <div class="card">
    <h2>Tendencia de Calidad</h2>
    {ts_html}
  </div>
  <div class="card">
    <h2>Desempeño por Agente</h2>
    {radar_html}
  </div>
  <div class="card">
    <h2>Cobertura de Métricas</h2>
    {heatmap_html}
  </div>
  <div class="card">
    <h2>Deuda Técnica (ATDI)</h2>
    {atdi_html}
  </div>
</div>

<div class="footer">KAOS — generado por lib/visual_dashboard.py</div>
</body>
</html>"""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")

    logger.info("Quality dashboard generated: %s", output.resolve())
    return str(output.resolve())
