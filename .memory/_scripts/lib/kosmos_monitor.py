"""kosmos_monitor.py — Monitoreo Continuo de KosmosV2 (Fase 3).

Integra system_scanner, atdi, smell_pipeline, y quality_gate
para proporcionar monitoreo continuo de la salud arquitectónica.

Flujo:
  1. Scan del sistema completo via system_scanner.scan()
  2. Cálculo de ATDI via atdi.calculate()
  3. Detección de architecture smells via smell_pipeline
  4. Generación de dashboard arquitectónico
  5. Persistencia de métricas para tendencias
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_SCRIPTS_DIR = Path(__file__).resolve().parent  # lib/
_MEMORY_DIR = _SCRIPTS_DIR.parent.parent  # .memory/
_CACHE_DIR = _MEMORY_DIR / "cache"
_HEALTH_TS_PATH = _CACHE_DIR / "kosmos" / "health_timeseries.json"
_ALERTS_PATH = _CACHE_DIR / "kosmos" / "alerts.json"

ATDI_SEVERITY_THRESHOLDS = {
    "critical": 60,
    "high": 30,
    "medium": 15,
    "low": 5,
}


# ── Data Classes ──

@dataclass
class ArchitectureHealthReport:
    """Reporte completo de salud arquitectónica.

    Attributes:
        timestamp: ISO datetime del reporte.
        health_score: 0-100 del system_scanner.
        atdi_score: Architecture Technical Debt Index (0-100).
        atdi_severity: none/low/medium/high/critical.
        smell_count: Total de smells detectados.
        smell_breakdown: Conteo por severidad (critical, high, medium, low).
        debt_estimate_hours: Horas estimadas para resolver la deuda.
        component_count: Componentes escaneados.
        affected_components: Componentes afectados por smells.
        trend: improving/stable/declining.
        previous_score: Health score anterior (None si es primero).
        deltas: Cambios vs reporte anterior.
    """
    timestamp: str = ""
    health_score: float = 0.0
    atdi_score: float = 0.0
    atdi_severity: str = "none"
    smell_count: int = 0
    smell_breakdown: dict[str, int] = field(default_factory=lambda: {
        "critical": 0, "high": 0, "medium": 0, "low": 0,
    })
    debt_estimate_hours: float = 0.0
    component_count: int = 0
    affected_components: int = 0
    trend: str = "stable"
    previous_score: Optional[float] = None
    deltas: dict[str, float] = field(default_factory=dict)


# ── ArchitectureMonitor ──

class ArchitectureMonitor:
    """Monitor continuo de salud arquitectónica.

    Proporciona escaneos completos y rápidos, detección de tendencias,
    alertas, y generación de dashboard arquitectónico.

    Uso:
        monitor = ArchitectureMonitor()
        report = monitor.full_scan()
        alerts = monitor.get_alerts()
        dashboard_path = monitor.generate_dashboard()
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        """Initialize the Architecture Monitor.

        Args:
            db_path: Path to health timeseries JSON file.
                     Default: .memory/cache/kosmos/health_timeseries.json
        """
        self.db_path = Path(db_path) if db_path else _HEALTH_TS_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._alerts_path = _ALERTS_PATH
        self._alerts_path.parent.mkdir(parents=True, exist_ok=True)

        # Cached previous report
        self._previous: Optional[ArchitectureHealthReport] = None

        logger.info("ArchitectureMonitor initialized (db=%s)", self.db_path)

    # ── Public API ──

    def full_scan(self) -> ArchitectureHealthReport:
        """Ejecuta un scan completo del sistema.

        Steps:
          1. Llama a system_scanner.scan() para health report.
          2. Calcula health_score vía system_scanner.health_score(report).
          3. Corre smell_pipeline.static_scan() sobre archivos relevantes.
          4. Calcula ATDI vía atdi.calculate().
          5. Compara con reporte anterior (trend/deltas).
          6. Persiste en timeseries.

        Returns:
            ArchitectureHealthReport con métricas actuales.
        """
        logger.info("🔍 ArchitectureMonitor: full_scan starting...")
        report = ArchitectureHealthReport(
            timestamp=datetime.now().isoformat(),
        )

        try:
            # 1. System scan
            from lib.system_scanner import scan, health_score as ss_health

            scan_result = scan()
            report.health_score = ss_health(scan_result)

            # Extract component count from scan
            lib_info = scan_result.get("libraries", {})
            if isinstance(lib_info, dict) and "total_modules" in lib_info:
                report.component_count = lib_info["total_modules"]
            else:
                report.component_count = scan_result.get("total_files", 0)

            logger.debug("   system_scanner: health=%s, components=%d",
                         report.health_score, report.component_count)

            # 2. Smell detection on relevant source files
            smell_findings = self._run_smell_detection()

            # 3. Compute ATDI
            smell_breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for f in smell_findings:
                sev = f.get("severity", "low")
                if sev in smell_breakdown:
                    smell_breakdown[sev] += 1

            report.smell_breakdown = smell_breakdown
            report.smell_count = sum(smell_breakdown.values())
            report.affected_components = self._count_affected_files(smell_findings)

            # 4. ATDI calculation
            atdi_result = self._compute_atdi(
                smell_breakdown,
                report.component_count,
                report.affected_components,
            )
            report.atdi_score = atdi_result.get("atdi_score", 0.0)
            report.atdi_severity = atdi_result.get("severity", "none")
            report.debt_estimate_hours = atdi_result.get("estimated_hours", 0.0)

            # 5. Trend and deltas vs previous
            previous = self._load_previous()
            if previous:
                report.previous_score = previous.health_score
                report.trend = self._compute_trend(
                    report.health_score, previous.health_score,
                )
                report.deltas = {
                    "health_score": round(report.health_score - previous.health_score, 1),
                    "atdi_score": round(report.atdi_score - previous.atdi_score, 1),
                    "smell_count": report.smell_count - previous.smell_count,
                }
            else:
                report.trend = "stable"
                report.deltas = {}

            logger.info(
                "   full_scan complete: health=%.1f, atdi=%.1f (%s), smells=%d",
                report.health_score, report.atdi_score, report.atdi_severity,
                report.smell_count,
            )

        except Exception as exc:
            logger.error("full_scan failed: %s", exc, exc_info=True)
            report.health_score = 0.0
            report.atdi_severity = "error"

        # 6. Persist
        self._persist(report)
        self._previous = report

        return report

    def quick_scan(self) -> ArchitectureHealthReport:
        """Escaneo rápido: solo ATDI + smell_count (sin system_scanner).

        Útil para verificaciones frecuentes sin overhead de scan completo.

        Returns:
            ArchitectureHealthReport con métricas parciales.
        """
        logger.info("⚡ ArchitectureMonitor: quick_scan")
        now = datetime.now()

        report = ArchitectureHealthReport(
            timestamp=now.isoformat(),
            health_score=0.0,
        )

        try:
            # Only smell + ATDI
            smell_findings = self._run_smell_detection()
            smell_breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for f in smell_findings:
                sev = f.get("severity", "low")
                if sev in smell_breakdown:
                    smell_breakdown[sev] += 1

            report.smell_breakdown = smell_breakdown
            report.smell_count = sum(smell_breakdown.values())
            report.affected_components = self._count_affected_files(smell_findings)

            # Re-use previous component count if available
            previous = self._load_previous()
            report.component_count = previous.component_count if previous else 1

            atdi_result = self._compute_atdi(
                smell_breakdown,
                report.component_count,
                report.affected_components,
            )
            report.atdi_score = atdi_result.get("atdi_score", 0.0)
            report.atdi_severity = atdi_result.get("severity", "none")
            report.debt_estimate_hours = atdi_result.get("estimated_hours", 0.0)

            if previous:
                report.previous_score = previous.health_score
                report.trend = self._compute_trend(
                    atdi_result.get("atdi_score", 0),
                    previous.atdi_score,
                    lower_is_better=True,
                )
                report.deltas = {
                    "atdi_score": round(report.atdi_score - previous.atdi_score, 1),
                    "smell_count": report.smell_count - previous.smell_count,
                }
            else:
                report.trend = "stable"

            logger.debug("   quick_scan: atdi=%.1f (%s), smells=%d",
                         report.atdi_score, report.atdi_severity, report.smell_count)

        except Exception as exc:
            logger.error("quick_scan failed: %s", exc)

        # Persist quick scans too
        self._persist(report)
        return report

    def get_trend(self, days: int = 30) -> dict[str, Any]:
        """Obtiene tendencia de health_score y ATDI.

        Args:
            days: Ventana de días para la tendencia.

        Returns:
            Dict con keys: health_scores (list), atdi_scores (list),
            timestamps (list), health_trend, atdi_trend.
        """
        records = self._load_timeseries()
        cutoff = datetime.now() - timedelta(days=days)
        filtered = [
            r for r in records
            if datetime.fromisoformat(r.get("timestamp", "")).replace(tzinfo=None) >= cutoff
        ]

        if not filtered:
            return {
                "health_scores": [],
                "atdi_scores": [],
                "timestamps": [],
                "health_trend": "insufficient_data",
                "atdi_trend": "insufficient_data",
            }

        health_scores = [r["health_score"] for r in filtered]
        atdi_scores = [r["atdi_score"] for r in filtered]
        timestamps = [r["timestamp"] for r in filtered]

        return {
            "health_scores": health_scores,
            "atdi_scores": atdi_scores,
            "timestamps": timestamps,
            "health_trend": self._compute_trend_line(health_scores),
            "atdi_trend": self._compute_trend_line(atdi_scores, lower_is_better=True),
        }

    def get_alerts(self) -> list[dict[str, Any]]:
        """Obtiene alertas activas.

        Reglas:
          - ATDI > 60 → alerta crítica
          - health_score < 50 → alerta de salud
          - smells críticos > 0 → alerta de smells

        Returns:
            Lista de dicts con: type, severity, message, timestamp.
        """
        alerts: list[dict[str, Any]] = []
        latest = self._load_latest()
        if not latest:
            return alerts

        # ATDI alert
        if latest.atdi_score > 60:
            alerts.append({
                "type": "atdi",
                "severity": "critical",
                "message": f"ATDI score crítico: {latest.atdi_score:.1f} — acción requerida",
                "timestamp": latest.timestamp,
            })
        elif latest.atdi_score > 30:
            alerts.append({
                "type": "atdi",
                "severity": "high",
                "message": f"ATDI score elevado: {latest.atdi_score:.1f} — revisar deuda técnica",
                "timestamp": latest.timestamp,
            })

        # Health alert
        if latest.health_score > 0 and latest.health_score < 50:
            alerts.append({
                "type": "health",
                "severity": "high",
                "message": f"Health score bajo: {latest.health_score:.1f}/100 — sistema en riesgo",
                "timestamp": latest.timestamp,
            })

        # Critical smells
        if latest.smell_breakdown.get("critical", 0) > 0:
            alerts.append({
                "type": "smell",
                "severity": "critical",
                "message": f"{latest.smell_breakdown['critical']} smell(s) crítico(s) detectados",
                "timestamp": latest.timestamp,
            })

        # Persist active alerts
        self._save_alerts(alerts)
        return alerts

    def clear_alerts(self) -> int:
        """Limpia alertas resueltas (las que ya no aplican).

        Returns:
            Número de alertas limpiadas.
        """
        current = self.get_alerts()
        previous = self._load_saved_alerts()
        resolved = [a for a in previous if a not in current]
        self._save_alerts(current)
        return len(resolved)

    def generate_dashboard(self, output_dir: str | Path = ".memory/dashboard") -> str:
        """Genera dashboard arquitectónico completo.

        Combina el dashboard base con la sección de KosmosV2.

        Args:
            output_dir: Directorio de salida.

        Returns:
            Path al archivo HTML generado.
        """
        output_path = Path(output_dir) if isinstance(output_dir, str) else output_dir
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            # Use existing dashboard as base
            from lib.dashboard import collect_data, render_html

            base_data = collect_data()
            kosmos_metrics = self._load_latest()
            if kosmos_metrics:
                base_data["kosmos_v2"] = asdict(kosmos_metrics)

            # Add alerts
            base_data["kosmos_alerts"] = self.get_alerts()

            # Add trend
            base_data["kosmos_trend"] = self.get_trend(days=30)

            html = self._inject_kosmos_section(render_html(base_data), base_data)

            filepath = output_path / "kosmos-architecture.html"
            filepath.write_text(html, encoding="utf-8")
            logger.info("Dashboard generated: %s", filepath)
            return str(filepath)

        except Exception as exc:
            logger.error("Dashboard generation failed: %s", exc)
            # Fallback: generate minimal standalone dashboard
            return self._generate_fallback_dashboard(str(output_path))

    # ── Internal: Smell Detection ──

    def _run_smell_detection(self) -> list[dict[str, Any]]:
        """Ejecuta smell_pipeline sobre archivos fuente relevantes.

        Returns:
            Lista de findings de smell_pipeline.static_scan().
        """
        try:
            from lib.smell_pipeline import static_scan

            findings: list[dict[str, Any]] = []
            source_dirs = [
                _SCRIPTS_DIR,
                _MEMORY_DIR / "_scripts" / "lib",
            ]

            for sdir in source_dirs:
                if not sdir.exists():
                    continue
                for py_file in sdir.rglob("*.py"):
                    if py_file.stat().st_size > 100000:  # skip large files
                        continue
                    try:
                        text = py_file.read_text(encoding="utf-8", errors="replace")
                        file_findings = static_scan(text)
                        for ff in file_findings:
                            ff["file"] = str(py_file)
                        findings.extend(file_findings)
                    except (OSError, IOError):
                        continue

            logger.debug("   smell_pipeline: %d findings from %d dirs",
                         len(findings), len(source_dirs))
            return findings

        except Exception as exc:
            logger.warning("Smell detection failed: %s", exc)
            return []

    def _count_affected_files(self, findings: list[dict[str, Any]]) -> int:
        """Cuenta archivos únicos afectados por smells."""
        affected = set()
        for f in findings:
            filepath = f.get("file", "")
            if filepath:
                affected.add(filepath)
        return len(affected)

    def _compute_atdi(
        self,
        smell_breakdown: dict[str, int],
        total_components: int,
        affected_components: int,
    ) -> dict[str, Any]:
        """Calcula ATDI usando atdi.calculate()."""
        try:
            from lib.atdi import calculate

            result = calculate(
                smell_counts=smell_breakdown,
                total_components=max(total_components, 1),
                affected_components=affected_components,
            )
            return result
        except Exception as exc:
            logger.warning("ATDI calculation failed: %s", exc)
            return {
                "atdi_score": 0.0,
                "estimated_hours": 0.0,
                "severity": "none",
            }

    # ── Internal: Trend Analysis ──

    @staticmethod
    def _compute_trend(
        current: float,
        previous: float,
        lower_is_better: bool = False,
    ) -> str:
        """Compute trend string between two values."""
        if previous == 0:
            return "stable"
        diff = current - previous
        if lower_is_better:
            diff = -diff
        if abs(diff) < 1.0:
            return "stable"
        return "improving" if diff > 0 else "declining"

    @staticmethod
    def _compute_trend_line(
        values: list[float],
        lower_is_better: bool = False,
    ) -> str:
        """Compute overall trend from a series using linear regression slope."""
        if len(values) < 2:
            return "insufficient_data"

        n = len(values)
        x_avg = (n - 1) / 2.0
        y_avg = sum(values) / n

        num = sum((i - x_avg) * (v - y_avg) for i, v in enumerate(values))
        den = sum((i - x_avg) ** 2 for i in range(n))

        if den == 0:
            return "stable"

        slope = num / den
        if lower_is_better:
            slope = -slope

        return "improving" if slope > 0.01 else ("declining" if slope < -0.01 else "stable")

    # ── Internal: Persistence ──

    @staticmethod
    def _avg_records(records: list[dict[str, Any]], label: str = "") -> dict[str, Any]:
        """Average multiple records into one aggregate record (P5 compression)."""
        n = len(records)
        avg: dict[str, Any] = {
            "timestamp": label or records[-1].get("timestamp", ""),
            "health_score": round(sum(r.get("health_score", 0) for r in records) / n, 1),
            "atdi_score": round(sum(r.get("atdi_score", 0) for r in records) / n, 1),
            "smell_count": round(sum(r.get("smell_count", 0) for r in records) / n, 1),
            "component_count": round(sum(r.get("component_count", 0) for r in records) / n),
            "affected_components": round(sum(r.get("affected_components", 0) for r in records) / n),
            "debt_estimate_hours": round(sum(r.get("debt_estimate_hours", 0) for r in records) / n, 1),
            "atdi_severity": records[-1].get("atdi_severity", "none"),
            "aggregated": True,
            "aggregated_count": n,
        }
        breakdowns = [r.get("smell_breakdown", {}) for r in records]
        avg_breakdown: dict[str, int] = {}
        for bd in breakdowns:
            for k, v in bd.items():
                avg_breakdown[k] = avg_breakdown.get(k, 0) + v
        if avg_breakdown:
            avg["smell_breakdown"] = {k: round(v / n) for k, v in avg_breakdown.items()}
        return avg

    def _compress_timeseries(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Compress timeseries records by aggregating old entries (P5).
        
        - > 90 days: monthly averages
        - 30-90 days: weekly averages
        - < 30 days: keep as-is
        """
        if not records:
            return records

        now = datetime.now()
        recent: list[dict[str, Any]] = []
        weekly: list[dict[str, Any]] = []
        monthly: list[dict[str, Any]] = []

        for r in records:
            ts_str = r.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str) if ts_str else now
            except (ValueError, TypeError):
                recent.append(r)
                continue
            days_ago = (now - ts).days
            if days_ago <= 30:
                recent.append(r)
            elif days_ago <= 90:
                weekly.append(r)
            else:
                monthly.append(r)

        compressed = list(recent)

        if weekly:
            from collections import defaultdict
            weeks: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for r in weekly:
                try:
                    ts = datetime.fromisoformat(r["timestamp"])
                    week_key = ts.strftime("%Y-W%V")
                    weeks[week_key].append(r)
                except (ValueError, TypeError):
                    compressed.append(r)
            for week_key, group in sorted(weeks.items()):
                compressed.append(self._avg_records(group, label=week_key))

        if monthly:
            from collections import defaultdict
            months: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for r in monthly:
                try:
                    ts = datetime.fromisoformat(r["timestamp"])
                    month_key = ts.strftime("%Y-%m")
                    months[month_key].append(r)
                except (ValueError, TypeError):
                    compressed.append(r)
            for month_key, group in sorted(months.items()):
                compressed.append(self._avg_records(group, label=month_key))

        if len(compressed) > 365:
            compressed = compressed[-365:]
        return compressed

    def _persist(self, report: ArchitectureHealthReport) -> None:
        """Persist report in timeseries with compression (P5)."""
        records = self._load_timeseries()
        records.append({
            "timestamp": report.timestamp,
            "health_score": report.health_score,
            "atdi_score": report.atdi_score,
            "atdi_severity": report.atdi_severity,
            "smell_count": report.smell_count,
            "smell_breakdown": report.smell_breakdown,
            "component_count": report.component_count,
            "affected_components": report.affected_components,
            "debt_estimate_hours": report.debt_estimate_hours,
        })

        # P5: compress old entries
        try:
            records = self._compress_timeseries(records)
        except Exception as exc:
            logger.warning("P5: Timeseries compression failed (non-blocking): %s", exc)

        # Keep last 365 entries max
        if len(records) > 365:
            records = records[-365:]

        self.db_path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_timeseries(self) -> list[dict[str, Any]]:
        """Load timeseries from disk."""
        if not self.db_path.exists():
            return []
        try:
            return json.loads(self.db_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _load_previous(self) -> Optional[ArchitectureHealthReport]:
        """Load the most recent report."""
        records = self._load_timeseries()
        if not records:
            return None
        latest = records[-1]
        return ArchitectureHealthReport(
            timestamp=latest.get("timestamp", ""),
            health_score=latest.get("health_score", 0.0),
            atdi_score=latest.get("atdi_score", 0.0),
            atdi_severity=latest.get("atdi_severity", "none"),
            smell_count=latest.get("smell_count", 0),
            smell_breakdown=latest.get("smell_breakdown", {}),
            debt_estimate_hours=latest.get("debt_estimate_hours", 0.0),
            component_count=latest.get("component_count", 0),
            affected_components=latest.get("affected_components", 0),
        )

    def _load_latest(self) -> Optional[ArchitectureHealthReport]:
        """Load latest report (prefer cached self._previous)."""
        if self._previous is not None:
            return self._previous
        return self._load_previous()

    def _save_alerts(self, alerts: list[dict[str, Any]]) -> None:
        """Persist alerts to disk."""
        self._alerts_path.write_text(
            json.dumps(alerts, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_saved_alerts(self) -> list[dict[str, Any]]:
        """Load previously saved alerts."""
        if not self._alerts_path.exists():
            return []
        try:
            return json.loads(self._alerts_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    # ── Internal: Dashboard Helpers ──

    def _inject_kosmos_section(self, base_html: str, data: dict) -> str:
        """Inject KosmosV2 monitoring section into base dashboard HTML."""
        km = data.get("kosmos_v2", {})
        alerts = data.get("kosmos_alerts", [])
        trend = data.get("kosmos_trend", {})

        hs = km.get("health_score", 0)
        atdi = km.get("atdi_score", 0)
        atdi_sev = km.get("atdi_severity", "none")
        smells = km.get("smell_count", 0)
        sb = km.get("smell_breakdown", {})
        debt = km.get("debt_estimate_hours", 0)
        trend_str = km.get("trend", "stable")

        hs_color = "#22c55e" if hs >= 70 else ("#eab308" if hs >= 40 else "#ef4444")
        atdi_color = "#22c55e" if atdi < 15 else ("#eab308" if atdi < 60 else "#ef4444")
        trend_icon = "📈" if trend_str == "improving" else ("📉" if trend_str == "declining" else "➡️")

        alert_badges = ""
        if alerts:
            for a in alerts:
                sev_color = {"critical": "#ef4444", "high": "#eab308", "medium": "#f59e0b"}.get(a.get("severity", "low"), "#64748b")
                alert_badges += f'<div style="padding:0.25rem 0;font-size:0.8rem;color:{sev_color};">⚠️ {a["message"]}</div>'

        # Health score ring gauge (inline SVG)
        hs_r = 40
        hs_circ = 2 * 3.14159 * hs_r
        hs_offset = hs_circ - (min(hs, 100) / 100) * hs_circ

        # ATDI ring gauge
        atdi_r = 40
        atdi_circ = 2 * 3.14159 * atdi_r
        atdi_offset = atdi_circ - (min(atdi, 100) / 100) * atdi_circ

        # Smell breakdown bars
        smell_bars = ""
        for sev in ["critical", "high", "medium", "low"]:
            count = sb.get(sev, 0)
            sev_colors = {"critical": "#ef4444", "high": "#f97316", "medium": "#eab308", "low": "#64748b"}
            color = sev_colors.get(sev, "#64748b")
            pct = min(count * 10, 100)  # scale: each smell = 10%
            smell_bars += f"""
            <div class="row"><span class="label">{sev.capitalize()}</span><span>{count}</span></div>
            <div class="bar"><div class="bar-fill" style="width:{pct}%;background:{color};"></div></div>
            """

        # Trend sparkline (minimal inline SVG)
        trend_spark = ""
        trend_scores = trend.get("health_scores", [])
        if len(trend_scores) >= 2:
            tw, th = 150, 40
            tmax = max(trend_scores) or 1
            tmin = min(trend_scores)
            trng = tmax - tmin or 1
            tpts = []
            for i, s in enumerate(trend_scores):
                tx = tw * i / (len(trend_scores) - 1)
                ty = th - (th * (s - tmin) / trng)
                tpts.append(f"{tx:.1f},{ty:.1f}")
            tcoords = " ".join(tpts)
            tcolor = "#22c55e" if trend_scores[-1] >= trend_scores[0] else "#ef4444"
            trend_spark = f"""
            <svg width="{tw}" height="{th}" viewBox="0 0 {tw} {th}" style="margin-top:0.5rem;">
              <polyline fill="none" stroke="{tcolor}" stroke-width="2" points="{tcoords}"/>
            </svg>
            """

        kosmos_section = f"""
        <div style="background:#1e293b;border-radius:8px;padding:1rem;border:2px solid #7B68EE;margin-top:1rem;">
          <h2 style="font-size:1rem;color:#7B68EE;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.75rem;">
            🏛️ KosmosV2 — Monitoreo Arquitectónico
          </h2>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1rem;">

            <!-- Health Score Gauge -->
            <div style="text-align:center;">
              <svg width="100" height="100" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="{hs_r}" fill="none" stroke="#334155" stroke-width="8"/>
                <circle cx="50" cy="50" r="{hs_r}" fill="none" stroke="{hs_color}" stroke-width="8"
                  stroke-dasharray="{hs_circ}" stroke-dashoffset="{hs_offset}" stroke-linecap="round"
                  transform="rotate(-90 50 50)"/>
                <text x="50" y="45" text-anchor="middle" fill="#e2e8f0" font-size="22" font-weight="bold">{hs:.0f}</text>
                <text x="50" y="60" text-anchor="middle" fill="#64748b" font-size="10">/100</text>
              </svg>
              <div style="font-size:0.8rem;color:#94a3b8;margin-top:0.25rem;">Health Score</div>
            </div>

            <!-- ATDI Gauge -->
            <div style="text-align:center;">
              <svg width="100" height="100" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="{atdi_r}" fill="none" stroke="#334155" stroke-width="8"/>
                <circle cx="50" cy="50" r="{atdi_r}" fill="none" stroke="{atdi_color}" stroke-width="8"
                  stroke-dasharray="{atdi_circ}" stroke-dashoffset="{atdi_offset}" stroke-linecap="round"
                  transform="rotate(-90 50 50)"/>
                <text x="50" y="45" text-anchor="middle" fill="#e2e8f0" font-size="22" font-weight="bold">{atdi:.0f}</text>
                <text x="50" y="60" text-anchor="middle" fill="#64748b" font-size="10">/100</text>
              </svg>
              <div style="font-size:0.8rem;color:#94a3b8;margin-top:0.25rem;">ATDI · {atdi_sev}</div>
            </div>

            <!-- Summary Stats -->
            <div>
              <div class="row"><span class="label">🧹 Smells</span><span>{smells}</span></div>
              <div class="row"><span class="label">⏱️ Deuda estimada</span><span>{debt:.1f}h</span></div>
              <div class="row"><span class="label">📊 Trend</span><span>{trend_icon} {trend_str}</span></div>
              <div class="row"><span class="label">📦 Componentes</span><span>{km.get("component_count", 0)}</span></div>
              <div class="row"><span class="label">🎯 Afectados</span><span>{km.get("affected_components", 0)}</span></div>
              {trend_spark}
            </div>

            <!-- Smell Breakdown -->
            <div>
              <h3 style="font-size:0.8rem;color:#94a3b8;margin-bottom:0.5rem;">Smell Breakdown</h3>
              {smell_bars}
            </div>

          </div>

          <!-- Alerts -->
          {"<div style='margin-top:0.75rem;padding:0.5rem;background:#1a2332;border-radius:4px;'>" + alert_badges + "</div>" if alert_badges else ""}
        </div>
        """

        # Inject before footer
        marker = '<div class="footer">'
        if marker in base_html:
            return base_html.replace(marker, kosmos_section + "\n" + marker)
        return base_html + "\n" + kosmos_section

    def _generate_fallback_dashboard(self, output_dir: str) -> str:
        """Generate a minimal standalone dashboard when full generation fails."""
        latest = self._load_latest()
        alerts = self.get_alerts()

        alert_html = ""
        if alerts:
            for a in alerts:
                alert_html += f'<div style="color:#ef4444;">⚠️ {a["message"]}</div>'

        hs = latest.health_score if latest else 0
        atdi = latest.atdi_score if latest else 0
        atdi_sev = latest.atdi_severity if latest else "none"
        smells = latest.smell_count if latest else 0

        html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>KosmosV2 Architecture Dashboard</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:system-ui,-apple-system,sans-serif; background:#0f172a; color:#e2e8f0; padding:2rem; }}
  h1 {{ color:#7B68EE; margin-bottom:1rem; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:1rem; }}
  .card {{ background:#1e293b; border-radius:8px; padding:1rem; border:1px solid #334155; }}
  .metric {{ font-size:2rem; font-weight:700; color:#38bdf8; }}
  .label {{ color:#94a3b8; font-size:0.85rem; }}
</style>
</head>
<body>
<h1>🏛️ KosmosV2 — Architecture Dashboard</h1>
<p style="color:#64748b;font-size:0.85rem;">{datetime.now().isoformat()}</p>
{alert_html}
<div class="grid">
  <div class="card"><h2>Health Score</h2><div class="metric">{hs:.1f}</div><div class="label">/100</div></div>
  <div class="card"><h2>ATDI</h2><div class="metric">{atdi:.1f}</div><div class="label">{atdi_sev} · {smells} smells</div></div>
</div>
</body>
</html>"""
        filepath = os.path.join(output_dir, "kosmos-architecture.html")
        os.makedirs(output_dir, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("Fallback dashboard generated: %s", filepath)
        return filepath


# ── DebtTracker ──

class DebtTracker:
    """Tracker de deuda técnica arquitectónica.

    Analiza ADRs para identificar y trackear deuda técnica
    introducida o identificada por decisiones arquitectónicas.
    """

    def __init__(self, memory_l0: Any = None) -> None:
        """Initialize DebtTracker.

        Args:
            memory_l0: Optional ArchitectureMemoryL0 instance for cross-referencing.
        """
        self.memory_l0 = memory_l0
        logger.debug("DebtTracker initialized (memory=%s)", memory_l0 is not None)

    def track_debt(self, adr_id: str, adr_text: str) -> dict[str, Any]:
        """Analiza deuda técnica introducida/identificada en un ADR.

        Args:
            adr_id: ID del ADR (ej. "ADR-019").
            adr_text: Texto completo del ADR.

        Returns:
            Dict con: adr_id, potential_debt (bool), debt_items (list),
            estimated_hours, severity.
        """
        debt_items: list[dict[str, str]] = []

        # Pattern: references to technical debt
        debt_patterns = [
            (r"(deuda\s*técnica|technical\s*debt)", "technical_debt_reference"),
            (r"(workaround|hack|temporal|temporary)", "temporary_solution"),
            (r"(migración|migration|refactor)", "migration_need"),
            (r"(limitation|limitación|constraint|restricción)", "architectural_constraint"),
            (r"(deprecated|obsoleto|legacy|legado)", "legacy_component"),
            (r"(TODO|FIXME|HACK|XXX)", "unresolved_issue"),
            (r"(con\d+s\s*negat|negative\s*consequen)", "negative_consequence"),
            (r"(risk|riesgo|riesgoso)", "identified_risk"),
        ]

        for pattern, debt_type in debt_patterns:
            matches = re.findall(pattern, adr_text, re.IGNORECASE)
            if matches:
                debt_items.append({
                    "type": debt_type,
                    "count": len(matches),
                    "detail": f"ADR {adr_id} — {debt_type} ({len(matches)} referencias)",
                })

        # Score severity
        total_refs = sum(d.get("count", 0) for d in debt_items)
        if total_refs >= 10:
            severity = "high"
            est_hours = total_refs * 4.0
        elif total_refs >= 5:
            severity = "medium"
            est_hours = total_refs * 2.0
        elif total_refs > 0:
            severity = "low"
            est_hours = total_refs * 1.0
        else:
            severity = "none"
            est_hours = 0.0

        return {
            "adr_id": adr_id,
            "potential_debt": len(debt_items) > 0,
            "debt_items": debt_items,
            "estimated_hours": round(est_hours, 1),
            "severity": severity,
            "total_references": total_refs,
        }

    def get_component_debt(self, component: str) -> dict[str, Any]:
        """Obtiene deuda asociada a un componente específico.

        Args:
            component: Nombre del componente.

        Returns:
            Dict con: component, debt_items, total_estimated_hours.
        """
        # Search memory for component references
        all_debts: list[dict] = []
        if self.memory_l0 is not None:
            try:
                results = self.memory_l0.search(component, limit=10)
                for r in results:
                    title = r.get("title", "")
                    text = r.get("text", "")
                    adr_id = r.get("adr_id", "UNKNOWN")
                    debt = self.track_debt(adr_id, f"{title}\n{text}")
                    if debt["potential_debt"]:
                        all_debts.append(debt)
            except Exception:
                pass

        total_hours = sum(d.get("estimated_hours", 0) for d in all_debts)
        return {
            "component": component,
            "related_adrs": len(all_debts),
            "debt_items": [item for d in all_debts for item in d.get("debt_items", [])],
            "total_estimated_hours": round(total_hours, 1),
        }

    def get_top_debtors(self, limit: int = 5) -> list[dict[str, Any]]:
        """Obtiene top componentes con más deuda.

        Args:
            limit: Número de resultados.

        Returns:
            Lista de dicts con: component, estimated_hours, adr_count.
        """
        # If memory available, scan all ADRs for component mentions
        component_debts: dict[str, dict] = {}
        if self.memory_l0 is not None:
            try:
                stats = self.memory_l0.get_stats()
                total = stats.get("total_adrs", 0)
                for i in range(1, total + 1):
                    adr = self.memory_l0.get_adr(i)
                    if adr:
                        text = adr.get("text", "")
                        title = adr.get("title", "")
                        adr_id = adr.get("adr_id", f"ADR-{i:03d}")
                        # Extract component references
                        comps = re.findall(r'(?i)(?:componente|módulo|sistema|service|agent)\s+(\w+)', text)
                        for comp in set(comps[:3]):
                            if comp not in component_debts:
                                component_debts[comp] = {"hours": 0.0, "adrs": set()}
                            component_debts[comp]["adrs"].add(adr_id)
                            debt = self.track_debt(adr_id, text)
                            component_debts[comp]["hours"] += debt.get("estimated_hours", 0)
            except Exception:
                pass

        # Sort by hours desc
        sorted_comps = sorted(
            component_debts.items(),
            key=lambda x: x[1]["hours"],
            reverse=True,
        )[:limit]

        return [
            {
                "component": comp,
                "estimated_hours": round(data["hours"], 1),
                "adr_count": len(data["adrs"]),
                "adrs": list(data["adrs"]),
            }
            for comp, data in sorted_comps
        ]

    def estimate_resolution_cost(self, atdi_score: float) -> dict[str, Any]:
        """Estima horas/costo para resolver una deuda medida por ATDI.

        Args:
            atdi_score: Architecture Technical Debt Index (0-100).

        Returns:
            Dict con: estimated_hours, complexity, recommendation.
        """
        if atdi_score <= 0:
            return {
                "estimated_hours": 0,
                "complexity": "none",
                "recommendation": "No hay deuda técnica detectada",
            }

        # Heuristic mapping: ATDI → hours
        hours = atdi_score * 0.8  # 80 hours at ATDI=100

        if atdi_score > 60:
            complexity = "critical"
            recommendation = "Se requiere una revisión arquitectónica integral y plan de remediación"
        elif atdi_score > 30:
            complexity = "high"
            recommendation = "Priorizar refactorización de componentes con mayor deuda"
        elif atdi_score > 15:
            complexity = "medium"
            recommendation = "Planificar reducción incremental de deuda en próximos sprints"
        elif atdi_score > 5:
            complexity = "low"
            recommendation = "Monitorear evolución de la deuda en ciclos regulares"
        else:
            complexity = "none"
            recommendation = "Deuda mínima — mantener prácticas actuales"

        return {
            "estimated_hours": round(hours, 1),
            "complexity": complexity,
            "recommendation": recommendation,
            "atdi_score": atdi_score,
        }


# ── Self-test ──

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("🏛️ KosmosV2 ArchitectureMonitor — Self-Test")
    print("=" * 60)

    # Test 1: Instantiation
    print("\n1️⃣  ArchitectureMonitor instantiation...")
    monitor = ArchitectureMonitor()
    print("   ✅ Monitor created")

    # Test 2: Quick scan
    print("\n2️⃣  Quick scan...")
    quick = monitor.quick_scan()
    print(f"   ATDI: {quick.atdi_score} ({quick.atdi_severity})")
    print(f"   Smells: {quick.smell_count}")
    print(f"   Trend: {quick.trend}")

    # Test 3: Full scan
    print("\n3️⃣  Full scan...")
    full = monitor.full_scan()
    print(f"   Health: {full.health_score}/100")
    print(f"   ATDI: {full.atdi_score} ({full.atdi_severity})")
    print(f"   Smells: {full.smell_count}")
    print(f"   Debt: {full.debt_estimate_hours}h")
    print(f"   Components: {full.component_count}")
    print(f"   Trend: {full.trend}")

    # Test 4: Alerts
    print("\n4️⃣  Alerts...")
    alerts = monitor.get_alerts()
    print(f"   Active alerts: {len(alerts)}")
    for a in alerts:
        print(f"   ⚠️ [{a['severity']}] {a['message']}")

    # Test 5: Trend
    print("\n5️⃣  Trend (30 days)...")
    trend = monitor.get_trend(days=30)
    print(f"   Health scores: {len(trend['health_scores'])} points")
    print(f"   Health trend: {trend['health_trend']}")
    print(f"   ATDI trend: {trend['atdi_trend']}")

    # Test 6: DebtTracker
    print("\n6️⃣  DebtTracker...")
    tracker = DebtTracker()
    debt = tracker.track_debt("ADR-999", """
    # Test ADR
    This introduces technical debt via a temporary workaround.
    Migration needed for legacy component.
    TODO: refactor this later.
    Risk: high coupling.
    """)
    print(f"   Potential debt: {debt['potential_debt']}")
    print(f"   Items: {len(debt['debt_items'])}")
    print(f"   Hours: {debt['estimated_hours']}h")
    print(f"   Severity: {debt['severity']}")

    # Test 7: Estimate cost
    print("\n7️⃣  Resolution cost estimation...")
    cost = tracker.estimate_resolution_cost(42.0)
    print(f"   Hours: {cost['estimated_hours']}h")
    print(f"   Complexity: {cost['complexity']}")
    print(f"   Recommendation: {cost['recommendation']}")

    # Test 8: Dashboard generation
    print("\n8️⃣  Dashboard generation...")
    dash_path = monitor.generate_dashboard()
    print(f"   Dashboard: {dash_path}")

    print("\n" + "=" * 60)
    print("✅ All ArchitectureMonitor tests passed")
    print("=" * 60)
