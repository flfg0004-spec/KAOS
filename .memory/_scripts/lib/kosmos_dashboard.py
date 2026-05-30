"""kosmos_dashboard.py — Dashboard arquitectónico de KosmosV2 (Fase 3).

Genera un dashboard HTML autónomo con:
- Health score ring gauge + tendencia 30 días
- ATDI score + breakdown por severidad
- Architecture smells por categoría
- Últimos ADRs con scores de reflexión
- Estado de contratos (Kratos, Metis, Mnemosyne, Aletheia)
- Routing DSOL actual por nodo
- Alertas activas

Sin dependencias externas — inline SVG, sin CDN.
"""

from __future__ import annotations

import html
import json
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_SCRIPTS_DIR = Path(__file__).resolve().parent  # lib/
_MEMORY_DIR = _SCRIPTS_DIR.parent.parent  # .memory/
_CACHE_DIR = _MEMORY_DIR / "cache"
_DASHBOARD_DIR = _MEMORY_DIR / "dashboard"
_PIPELINE_DIR = _MEMORY_DIR / "_pipeline"

# Colors
KOSMOS_ACCENT = "#7B68EE"
BG_DARK = "#0f172a"
BG_CARD = "#1e293b"
BORDER = "#334155"
TEXT_PRIMARY = "#e2e8f0"
TEXT_SECONDARY = "#94a3b8"

SEVERITY_COLORS = {
    "critical": "#ef4444",
    "high": "#f97316",
    "medium": "#eab308",
    "low": "#64748b",
    "none": "#22c55e",
}


# ── KosmosDashboard ──

class KosmosDashboard:
    """Dashboard arquitectónico autónomo de KosmosV2.

    Recolecta métricas del monitor, L0, contratos, pipeline y DSOL,
    y genera un HTML autónomo (sin CDN) con visualizaciones inline SVG.

    Uso:
        dashboard = KosmosDashboard()
        path = dashboard.generate()
        # or
        dashboard.serve(port=9090)
    """

    def __init__(
        self,
        monitor: Any = None,
        memory_l0: Any = None,
    ) -> None:
        """Initialize KosmosDashboard.

        Args:
            monitor: Optional ArchitectureMonitor instance.
            memory_l0: Optional ArchitectureMemoryL0 instance.
        """
        self._monitor = monitor
        self._memory_l0 = memory_l0
        self._dashboard_dir = _DASHBOARD_DIR
        self._dashboard_dir.mkdir(parents=True, exist_ok=True)
        logger.info("KosmosDashboard initialized")

    # ── Public API ──

    def collect_metrics(self) -> dict[str, Any]:
        """Recolecta TODAS las métricas para el dashboard.

        Returns:
            Dict completo con todas las métricas.
        """
        metrics: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "kosmos": {},
            "adrs": [],
            "contracts": {},
            "pipeline": {},
            "routing": {},
            "alerts": [],
        }

        # 1. Monitor metrics
        try:
            if self._monitor is not None:
                # Use monitor's internal methods
                try:
                    full = self._monitor.full_scan()
                    metrics["kosmos"] = asdict(full)
                except Exception:
                    quick = self._monitor.quick_scan()
                    metrics["kosmos"] = asdict(quick)
                metrics["alerts"] = self._monitor.get_alerts()
                metrics["trend"] = self._monitor.get_trend(days=30)
            else:
                # Try to create monitor on the fly
                try:
                    from lib.kosmos_monitor import ArchitectureMonitor

                    mon = ArchitectureMonitor()
                    quick = mon.quick_scan()
                    metrics["kosmos"] = asdict(quick)
                    metrics["alerts"] = mon.get_alerts()
                    metrics["trend"] = mon.get_trend(days=30)
                except Exception as exc:
                    logger.warning("Monitor metrics unavailable: %s", exc)
                    metrics["kosmos"] = {"health_score": 0, "atdi_score": 0}
        except Exception as exc:
            logger.warning("Could not collect monitor metrics: %s", exc)

        # 2. L0 ADR stats
        metrics["adrs"] = self._collect_adr_metrics()

        # 3. Contract status (F2)
        metrics["contracts"] = self._collect_contract_metrics()

        # 4. Pipeline status
        metrics["pipeline"] = self._collect_pipeline_metrics()

        # 5. DSOL routing table
        metrics["routing"] = self._collect_routing_metrics()

        logger.debug(
            "Metrics collected: health=%.1f, atdi=%.1f, adrs=%d, alerts=%d",
            metrics["kosmos"].get("health_score", 0),
            metrics["kosmos"].get("atdi_score", 0),
            len(metrics["adrs"]),
            len(metrics["alerts"]),
        )
        return metrics

    def render_html(self, metrics: dict[str, Any] | None = None) -> str:
        """Genera HTML autónomo del dashboard.

        Args:
            metrics: Dict de métricas (si None, ejecuta collect_metrics).

        Returns:
            String HTML completo (sin dependencias externas).
        """
        if metrics is None:
            metrics = self.collect_metrics()

        km = metrics.get("kosmos", {})
        alerts = metrics.get("alerts", [])
        trend = metrics.get("trend", {})
        adrs = metrics.get("adrs", [])
        contracts = metrics.get("contracts", {})
        pipeline = metrics.get("pipeline", {})
        routing = metrics.get("routing", {})

        hs = km.get("health_score", 0)
        atdi = km.get("atdi_score", 0)
        atdi_sev = km.get("atdi_severity", "none")
        smells = km.get("smell_count", 0)
        sb = km.get("smell_breakdown", {})
        debt = km.get("debt_estimate_hours", 0)
        trend_str = km.get("trend", "stable")

        # ── Build inline SVGs ──

        # Health score ring gauge
        ring_health = self._ring_gauge_svg(
            value=hs, max_val=100,
            color="#22c55e" if hs >= 70 else ("#eab308" if hs >= 40 else "#ef4444"),
            label="Health Score",
        )

        # ATDI ring gauge
        ring_atdi = self._ring_gauge_svg(
            value=atdi, max_val=100,
            color="#22c55e" if atdi < 15 else ("#eab308" if atdi < 60 else "#ef4444"),
            label=f"ATDI · {atdi_sev}",
        )

        # Trend sparkline (health scores)
        trend_spark = self._sparkline_svg(
            values=trend.get("health_scores", []),
            label="Health Trend (30d)",
            width=200, height=50,
        )

        # ATDI trend sparkline
        atdi_spark = self._sparkline_svg(
            values=trend.get("atdi_scores", []),
            label="ATDI Trend (30d)",
            width=200, height=50,
            invert=True,
        )

        # Smell breakdown bars
        smell_bars = self._smell_bars_html(sb)

        # ── Alert badges ──
        alert_html = ""
        if alerts:
            for a in alerts:
                sc = SEVERITY_COLORS.get(a.get("severity", "low"), "#64748b")
                msg = html.escape(str(a.get("message", "")))
                alert_html += f'<div class="alert-item" style="border-left-color:{sc};">⚠️ {msg}</div>'

        # ── ADR table ──
        adr_rows = ""
        for adr in adrs[:10]:
            score = adr.get("reflection_score", "—")
            status = adr.get("status", "?")
            status_color = "#22c55e" if status == "accepted" else ("#eab308" if status == "proposed" else "#64748b")
            adr_id = html.escape(str(adr.get("id", "?")))
            adr_title = html.escape(str(adr.get("title", "?")[:40]))
            adr_rows += f"""
            <tr>
              <td>{adr_id}</td>
              <td>{adr_title}</td>
              <td><span style="color:{status_color};">●</span> {status}</td>
              <td>{score}</td>
            </tr>"""

        # ── Contracts status ──
        contract_rows = ""
        contract_list = contracts.get("contracts", {})
        if isinstance(contract_list, dict):
            for cname, cstatus in contract_list.items():
                if isinstance(cstatus, dict):
                    st = cstatus.get("status", "unknown")
                else:
                    st = str(cstatus)
                indicator = "🟢" if st in ("completed", "passed", "ok") else ("🟡" if st in ("pending", "running") else "🔴")
                safe_name = html.escape(str(cname))
                contract_rows += f'<tr><td>{safe_name}</td><td>{indicator} {st}</td></tr>'
        if not contract_rows:
            contract_rows = '<tr><td colspan="2" style="color:#64748b;">No contract data</td></tr>'

        # ── Pipeline status ──
        pipeline_status = html.escape(str(pipeline.get("status", "N/A")))
        pipeline_last_run = html.escape(str(pipeline.get("last_run", "N/A")))
        pipeline_info = f"""
        <div class="row"><span class="label">Status</span><span>{pipeline_status}</span></div>
        <div class="row"><span class="label">Nodes</span><span>{pipeline.get("nodes_executed", 0)}/{pipeline.get("total_nodes", 8)}</span></div>
        <div class="row"><span class="label">Errors</span><span style="color:{'#ef4444' if pipeline.get('nodes_with_errors', 0) > 0 else '#22c55e'};">{pipeline.get('nodes_with_errors', 0)}</span></div>
        <div class="row"><span class="label">Last run</span><span>{pipeline_last_run}</span></div>
        """

        # ── Routing table ──
        routing_rows = ""
        for node, route in routing.items():
            if isinstance(route, dict):
                model = route.get("model", "?")
                reason = route.get("reason", "")[:30]
                safe_node = html.escape(str(node))
                safe_reason = html.escape(str(reason))
                routing_rows += f'<tr><td>{safe_node}</td><td>{model}</td><td style="font-size:0.75rem;color:#64748b;">{safe_reason}</td></tr>'

        # ── Assemble HTML ──
        dashboard_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🏛️ KosmosV2 — Architecture Dashboard</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:system-ui,-apple-system,sans-serif; background:{BG_DARK}; color:{TEXT_PRIMARY}; padding:1.5rem; }}
  h1 {{ font-size:1.4rem; color:{KOSMOS_ACCENT}; margin-bottom:0.5rem; display:flex; align-items:center; gap:0.5rem; }}
  .subtitle {{ color:{TEXT_SECONDARY}; font-size:0.85rem; margin-bottom:1rem; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:1rem; margin:1rem 0; }}
  .card {{ background:{BG_CARD}; border-radius:10px; padding:1.25rem; border:1px solid {BORDER}; }}
  .card h2 {{ font-size:0.85rem; color:{TEXT_SECONDARY}; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.75rem; }}
  .card-title {{ font-size:0.95rem; color:{KOSMOS_ACCENT}; font-weight:600; margin-bottom:0.75rem; }}
  .metric {{ font-size:2rem; font-weight:700; color:#38bdf8; }}
  .row {{ display:flex; justify-content:space-between; padding:0.3rem 0; font-size:0.85rem; border-bottom:1px solid #1a2332; }}
  .row:last-child {{ border-bottom:none; }}
  .label {{ color:{TEXT_SECONDARY}; }}
  .bar {{ height:6px; background:{BORDER}; border-radius:3px; margin:0.25rem 0 0.5rem 0; overflow:hidden; }}
  .bar-fill {{ height:100%; border-radius:3px; transition:width 0.3s; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.8rem; }}
  th {{ text-align:left; color:{TEXT_SECONDARY}; padding:0.4rem 0.25rem; border-bottom:1px solid {BORDER}; font-weight:500; }}
  td {{ padding:0.3rem 0.25rem; border-bottom:1px solid #1a2332; }}
  .alert-item {{ padding:0.5rem; margin:0.25rem 0; background:#1a2332; border-left:3px solid; border-radius:4px; font-size:0.8rem; }}
  .ring-gauges {{ display:flex; flex-wrap:wrap; gap:0.75rem; justify-content:center; }}
  .ring-wrapper {{ text-align:center; }}
  .ring-label {{ font-size:0.7rem; color:{TEXT_SECONDARY}; margin-top:0.25rem; }}
  .footer {{ margin-top:2rem; color:#475569; font-size:0.75rem; text-align:center; border-top:1px solid {BORDER}; padding-top:1rem; }}
  .badge {{ display:inline-block; padding:0.15rem 0.5rem; border-radius:4px; font-size:0.7rem; font-weight:500; }}
  .badge.green {{ background:#166534; color:#86efac; }}
  .badge.yellow {{ background:#854d0e; color:#fde047; }}
  .badge.red {{ background:#7f1d1d; color:#fca5a5; }}
  .badge.purple {{ background:#4c1d95; color:#c4b5fd; }}
  .deltas {{ font-size:0.75rem; margin-top:0.5rem; }}
  .delta-up {{ color:#22c55e; }}
  .delta-down {{ color:#ef4444; }}
</style>
</head>
<body>
<h1>🏛️ KosmosV2 — Architecture Dashboard</h1>
<p class="subtitle">{metrics.get("timestamp", "")} · Kosmos Phase 3 Autonomy</p>

<!-- Alert Banner -->
{ f'<div style="margin-bottom:1rem;">{alert_html}</div>' if alert_html else "" }

<!-- Ring Gauges Row -->
<div class="card" style="margin-bottom:1rem;">
  <div class="ring-gauges">
    {ring_health}
    {ring_atdi}
    <div class="ring-wrapper" style="width:90px;">
      <svg width="90" height="90" viewBox="0 0 90 90">
        <circle cx="45" cy="45" r="36" fill="none" stroke="#334155" stroke-width="6"/>
        <text x="45" y="40" text-anchor="middle" fill="{TEXT_PRIMARY}" font-size="24" font-weight="bold">{smells}</text>
        <text x="45" y="55" text-anchor="middle" fill="{TEXT_SECONDARY}" font-size="9">smells</text>
      </svg>
      <div class="ring-label">Total Smells</div>
    </div>
    <div class="ring-wrapper" style="width:90px;">
      <svg width="90" height="90" viewBox="0 0 90 90">
        <circle cx="45" cy="45" r="36" fill="none" stroke="#334155" stroke-width="6"/>
        <text x="45" y="40" text-anchor="middle" fill="{TEXT_PRIMARY}" font-size="24" font-weight="bold">{debt:.0f}</text>
        <text x="45" y="55" text-anchor="middle" fill="{TEXT_SECONDARY}" font-size="9">hours</text>
      </svg>
      <div class="ring-label">Deuda Est.</div>
    </div>
  </div>
</div>

<!-- Main Grid -->
<div class="grid">

  <!-- Smell Breakdown -->
  <div class="card">
    <h2>🧹 Smell Breakdown</h2>
    {smell_bars}
    <div class="deltas">
      Trend: <span class="{'delta-up' if trend_str == 'improving' else 'delta-down' if trend_str == 'declining' else ''}">
        {'📈 ' + trend_str if trend_str == 'improving' else '📉 ' + trend_str if trend_str == 'declining' else '➡️ ' + trend_str}
      </span>
      { f'<br/>Delta: <span class="{'delta-up' if km.get("deltas",{}).get("smell_count",0) < 0 else 'delta-down'}">{km.get("deltas",{}).get("smell_count",0):+d}</span>' if km.get("deltas",{}).get("smell_count") is not None else "" }
    </div>
  </div>

  <!-- Health Trend -->
  <div class="card">
    <h2>📊 Health Score Trend (30d)</h2>
    <div style="text-align:center;">
      {trend_spark}
    </div>
    <div style="margin-top:0.5rem;">
      <div class="row"><span class="label">Trend</span><span>{trend.get("health_trend", "N/A")}</span></div>
      <div class="row"><span class="label">Current</span><span>{hs:.1f}/100</span></div>
    </div>
  </div>

  <!-- ATDI Trend -->
  <div class="card">
    <h2>📉 ATDI Trend (30d)</h2>
    <div style="text-align:center;">
      {atdi_spark}
    </div>
    <div style="margin-top:0.5rem;">
      <div class="row"><span class="label">Trend</span><span>{trend.get("atdi_trend", "N/A")}</span></div>
      <div class="row"><span class="label">Current</span><span>{atdi:.1f}/100</span></div>
    </div>
  </div>

  <!-- ADRs Recientes -->
  <div class="card">
    <h2>📜 ADRs Recientes</h2>
    <table>
      <tr><th>ID</th><th>Título</th><th>Status</th><th>Score</th></tr>
      {adr_rows if adr_rows else '<tr><td colspan="4" style="color:#64748b;text-align:center;padding:1rem;">No hay ADRs disponibles</td></tr>'}
    </table>
  </div>

  <!-- Contract Status -->
  <div class="card">
    <h2>🔗 Contract Status (F2)</h2>
    <table>
      <tr><th>Contract</th><th>Status</th></tr>
      {contract_rows}
    </table>
  </div>

  <!-- Pipeline Status -->
  <div class="card">
    <h2>⚙️ Pipeline Status</h2>
    {pipeline_info}
  </div>

  <!-- Routing DSOL -->
  <div class="card">
    <h2>🔄 Routing DSOL</h2>
    <table>
      <tr><th>Node</th><th>Model</th><th>Reason</th></tr>
      {routing_rows if routing_rows else '<tr><td colspan="3" style="color:#64748b;">No routing data</td></tr>'}
    </table>
  </div>

</div>

<!-- Footer -->
<div class="footer">
  KosmosV2 Architecture Dashboard · Generated by kosmos_dashboard.py · {metrics.get("timestamp", "")}
</div>

</body>
</html>"""
        return dashboard_html

    def generate(self, output_dir: str | Path = ".memory/dashboard") -> str:
        """Genera dashboard completo y retorna path.

        Args:
            output_dir: Directorio de salida.

        Returns:
            Path al archivo HTML generado.
        """
        output_path = Path(output_dir) if isinstance(output_dir, str) else output_dir
        output_path.mkdir(parents=True, exist_ok=True)

        filepath = output_path / "kosmos-architecture.html"

        try:
            metrics = self.collect_metrics()
            html = self.render_html(metrics)
            filepath.write_text(html, encoding="utf-8")
            logger.info("Dashboard generated: %s", filepath)
        except Exception as exc:
            logger.error("Dashboard generation failed: %s", exc)
            # Fallback: minimal HTML
            fallback = self._fallback_html()
            filepath.write_text(fallback, encoding="utf-8")
            logger.info("Fallback dashboard generated: %s", filepath)

        return str(filepath)

    def serve(self, port: int = 9090) -> None:
        """Sirve dashboard en HTTP local.

        Args:
            port: Puerto HTTP (default 9090).
        """
        # Generate dashboard first
        self.generate()

        dashboard_file = self._dashboard_dir / "kosmos-architecture.html"
        if not dashboard_file.exists():
            logger.error("Dashboard file not found — run generate() first")
            return

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args: Any, **kwargs: Any):
                super().__init__(*args, directory=str(self._dashboard_dir), **kwargs)  # type: ignore[arg-type]
            def log_message(self, fmt: str, *args: Any) -> None:
                logger.info(fmt, *args)

        # Bind Handler._dashboard_dir
        Handler._dashboard_dir = self._dashboard_dir  # type: ignore[attr-defined]

        server = HTTPServer(("0.0.0.0", port), Handler)
        logger.info("KosmosV2 Dashboard served at http://0.0.0.0:%d/kosmos-architecture.html", port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Dashboard server stopped")
            server.server_close()

    # ── Internal: Metric Collection ──

    def _collect_adr_metrics(self) -> list[dict[str, Any]]:
        """Collect ADR metrics from L0 memory."""
        adrs: list[dict[str, Any]] = []
        try:
            if self._memory_l0 is not None:
                stats = self._memory_l0.get_stats()
                total = stats.get("total_adrs", 0)
                for i in range(max(1, total - 9), total + 1):
                    adr = self._memory_l0.get_adr(i)
                    if adr:
                        adrs.append({
                            "id": adr.get("adr_id", f"ADR-{i:03d}"),
                            "title": adr.get("title", "")[:60],
                            "status": adr.get("status", "?"),
                            "reflection_score": adr.get("reflection_score", "—"),
                        })
            else:
                # Scan raw ADR files
                for f in sorted(_PIPELINE_DIR.rglob("*adr*.md"))[:10]:
                    try:
                        text = f.read_text(encoding="utf-8", errors="replace")
                        title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
                        id_match = re.search(r'id:\s*(ADR-\d+)', text)
                        status_match = re.search(r'status:\s*(\w+)', text)
                        adrs.append({
                            "id": id_match.group(1) if id_match else f.stem,
                            "title": title_match.group(1)[:60] if title_match else f.stem[:60],
                            "status": status_match.group(1) if status_match else "unknown",
                            "reflection_score": "—",
                        })
                    except (OSError, IOError):
                        pass
        except Exception as exc:
            logger.debug("ADR collection failed: %s", exc)

        return sorted(adrs, key=lambda x: x.get("id", ""), reverse=True)

    def _collect_contract_metrics(self) -> dict[str, Any]:
        """Collect contract status from ContractOrchestrator."""
        try:
            from lib.kosmos_contracts import ContractOrchestrator

            orchestrator = ContractOrchestrator()
            statuses = orchestrator.get_contract_statuses()
            return {
                "contracts": statuses,
                "summary": orchestrator.get_summary(),
            }
        except Exception as exc:
            logger.debug("Contract metrics unavailable: %s", exc)

        # Fallback: try L0 memory stats
        if self._memory_l0 is not None:
            try:
                stats = self._memory_l0.get_stats()
                return {
                    "contracts": {
                        "kosmos_kratos": stats.get("contract_kratos", "unknown"),
                        "kosmos_metis": stats.get("contract_metis", "unknown"),
                        "kosmos_mnemosyne": stats.get("contract_mnemosyne", "unknown"),
                        "kosmos_aletheia": stats.get("contract_aletheia", "unknown"),
                    },
                }
            except Exception:
                pass

        return {"contracts": {}, "summary": "Contract Orcherstrator not available"}

    def _collect_pipeline_metrics(self) -> dict[str, Any]:
        """Collect pipeline execution status."""
        info = {
            "status": "idle",
            "nodes_executed": 0,
            "total_nodes": 8,
            "nodes_with_errors": 0,
            "last_run": "N/A",
        }
        try:
            # Check pipeline health file
            health_file = _CACHE_DIR / "kosmos" / "pipeline_health.json"
            if health_file.exists():
                data = json.loads(health_file.read_text(encoding="utf-8"))
                history = data.get("history", [])
                if history:
                    latest = history[-1]
                    info["status"] = "completed" if latest.get("nodes_with_errors", 0) == 0 else "with_errors"
                    info["nodes_executed"] = latest.get("nodes_executed", 0)
                    info["nodes_with_errors"] = latest.get("nodes_with_errors", 0)
                    info["last_run"] = latest.get("timestamp", "N/A")

            # Also check status.md
            status_file = _PIPELINE_DIR / "status.md"
            if status_file.exists():
                text = status_file.read_text(encoding="utf-8")
                sm = re.search(r"\*\*status\*\*:\s*(\S+)", text)
                if sm:
                    info["status"] = sm.group(1)
        except Exception as exc:
            logger.debug("Pipeline metrics unavailable: %s", exc)

        return info

    def _collect_routing_metrics(self) -> dict[str, Any]:
        """Collect current DSOL routing table."""
        try:
            from lib.kosmos_node_v2 import ROUTING_TABLE, resolve_routing

            routing = {}
            for node in ROUTING_TABLE:
                routing[node] = {
                    "model": ROUTING_TABLE[node].get("model", "?"),
                    "reason": ROUTING_TABLE[node].get("reason", ""),
                }

            # Try Aether-enhanced routing
            try:
                from lib.aether.router import resolve_model as aether_resolve

                task_type_map = {
                    "discover": "lint", "model": "analyze", "analyze": "analyze",
                    "quality": "verify", "visualize": "lint", "document": "adr",
                    "govern": "lint", "validate": "verify",
                }
                for node, task in task_type_map.items():
                    result = aether_resolve(task_type=task, agent="kosmos")
                    routing[node]["aether_model"] = result.get("model", "?")
                    routing[node]["resolved_by"] = result.get("resolved_by", "")
            except Exception:
                pass

            return routing
        except Exception as exc:
            logger.debug("Routing metrics unavailable: %s", exc)
            return {}

    # ── Internal: SVG generators ──

    @staticmethod
    def _ring_gauge_svg(value: float, max_val: float, color: str, label: str) -> str:
        """Generate an inline SVG ring gauge."""
        pct = min(100, (value / max(max_val, 1)) * 100)
        r = 36
        circ = 2 * 3.14159 * r
        offset = circ - (pct / 100) * circ
        return f"""
        <div class="ring-wrapper" style="width:90px;">
          <svg width="90" height="90" viewBox="0 0 90 90">
            <circle cx="45" cy="45" r="{r}" fill="none" stroke="#334155" stroke-width="6"/>
            <circle cx="45" cy="45" r="{r}" fill="none" stroke="{color}" stroke-width="6"
              stroke-dasharray="{circ}" stroke-dashoffset="{offset}" stroke-linecap="round"
              transform="rotate(-90 45 45)"/>
            <text x="45" y="40" text-anchor="middle" fill="{TEXT_PRIMARY}" font-size="18" font-weight="bold">{value:.0f}</text>
            <text x="45" y="55" text-anchor="middle" fill="{TEXT_SECONDARY}" font-size="9">/{max_val:.0f}</text>
          </svg>
          <div class="ring-label">{label}</div>
        </div>"""

    @staticmethod
    def _sparkline_svg(
        values: list[float],
        label: str = "",
        width: int = 200,
        height: int = 50,
        invert: bool = False,
    ) -> str:
        """Generate an inline SVG sparkline chart."""
        if len(values) < 2:
            return f'<div style="color:{TEXT_SECONDARY};font-size:0.8rem;text-align:center;">{label}: insufficient data</div>'

        max_v = max(values) or 1
        min_v = min(values)
        rng = max_v - min_v or 1
        pts = []
        for i, s in enumerate(values):
            x = width * i / (len(values) - 1)
            y = height - (height * (s - min_v) / rng)
            pts.append(f"{x:.1f},{y:.1f}")
        coords = " ".join(pts)

        if invert:
            color = "#22c55e" if values[-1] <= values[0] else "#ef4444"
        else:
            color = "#22c55e" if values[-1] >= values[0] else "#ef4444"

        return f"""
        <div style="display:flex;align-items:center;justify-content:center;flex-direction:column;">
          <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
            <polyline fill="none" stroke="{color}" stroke-width="2" points="{coords}"/>
          </svg>
          <div style="font-size:0.7rem;color:{TEXT_SECONDARY};margin-top:0.25rem;">{label}</div>
        </div>"""

    @staticmethod
    def _smell_bars_html(smell_breakdown: dict[str, int]) -> str:
        """Generate HTML for smell breakdown bars."""
        parts = ""
        for sev in ["critical", "high", "medium", "low"]:
            count = smell_breakdown.get(sev, 0)
            color = SEVERITY_COLORS.get(sev, "#64748b")
            max_bar = max(sum(smell_breakdown.values()), 1)
            pct = (count / max_bar) * 100
            parts += f"""
            <div class="row">
              <span class="label">{sev.capitalize()}</span>
              <span>{count}</span>
            </div>
            <div class="bar">
              <div class="bar-fill" style="width:{pct:.1f}%;background:{color};"></div>
            </div>"""
        return parts

    def _fallback_html(self) -> str:
        """Generate minimal fallback HTML."""
        return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>KosmosV2 Dashboard (Fallback)</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:system-ui,-apple-system,sans-serif; background:{BG_DARK}; color:{TEXT_PRIMARY}; padding:2rem; }}
  h1 {{ color:{KOSMOS_ACCENT}; }}
</style>
</head>
<body>
<h1>🏛️ KosmosV2 Dashboard</h1>
<p>Dashboard generation encountered an error. Check logs for details.</p>
<p style="color:{TEXT_SECONDARY};">{datetime.now().isoformat()}</p>
</body>
</html>"""


# ── Self-test ──

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("🏛️ KosmosV2 Dashboard — Self-Test")
    print("=" * 60)

    # Test 1: Instantiation
    print("\n1️⃣  KosmosDashboard instantiation...")
    dashboard = KosmosDashboard()
    print("   ✅ Dashboard created")

    # Test 2: Collect metrics
    print("\n2️⃣  Collect metrics...")
    metrics = dashboard.collect_metrics()
    print(f"   Kosmos data: {json.dumps(metrics.get('kosmos', {}), default=str)[:100]}...")
    print(f"   ADRs: {len(metrics.get('adrs', []))}")
    print(f"   Alerts: {len(metrics.get('alerts', []))}")
    print(f"   Contracts: {len(metrics.get('contracts', {}).get('contracts', {}))}")
    print(f"   Pipeline: {metrics.get('pipeline', {}).get('status', '?')}")
    print(f"   Routing nodes: {len(metrics.get('routing', {}))}")

    # Test 3: Render HTML
    print("\n3️⃣  Render HTML...")
    html = dashboard.render_html(metrics)
    assert "<!DOCTYPE html>" in html
    assert "KosmosV2" in html
    print(f"   HTML length: {len(html)} chars")
    print(f"   Has ring gauge: {'ring-wrapper' in html}")
    print(f"   Has sparkline: {'sparkline' in html or 'polyline' in html}")
    print(f"   Has contract table: {'Contract' in html}")

    # Test 4: Generate
    print("\n4️⃣  Generate dashboard...")
    path = dashboard.generate()
    print(f"   Generated: {path}")
    assert Path(path).exists()

    print("\n" + "=" * 60)
    print("✅ All Dashboard tests passed")
    print("=" * 60)
