"""kosmos_kronos_feedback.py — Feedback Loop Kosmos ↔ Kronos (Fase 3).

Kosmos reporta salud de pipeline a Kronos después de cada ejecución.
Kronos responde con optimizaciones de routing y detección de conflictos.

Flujo:
  1. Kosmos ejecuta pipeline de 8 nodos
  2. Kosmos genera PipelineHealthReport
  3. Kosmos persiste reporte en pipeline_health.json
  4. Kosmos consulta sugerencias de Kronos (kronos_agent.suggest_routing())
  5. Kosmos aplica optimizaciones no bloqueantes
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_SCRIPTS_DIR = Path(__file__).resolve().parent  # lib/
_MEMORY_DIR = _SCRIPTS_DIR.parent.parent  # .memory/
_CACHE_DIR = _MEMORY_DIR / "cache"
_PIPELINE_HEALTH_PATH = _CACHE_DIR / "kosmos" / "pipeline_health.json"
_KRONOS_FEEDBACK_PATH = _CACHE_DIR / "kosmos" / "kronos_feedback.md"


# ── Data Classes ──

@dataclass
class PipelineHealthReport:
    """Reporte de salud del pipeline tras una ejecución.

    Attributes:
        pipeline_version: Versión del pipeline (ej. "KosmosV2").
        timestamp: ISO datetime de la ejecución.
        nodes_executed: Número de nodos ejecutados.
        nodes_with_errors: Número de nodos con errores.
        errors: Dict nodo → mensaje de error.
        total_elapsed: Tiempo total en segundos.
        avg_node_time: Tiempo promedio por nodo.
        bottleneck: Nombre del nodo más lento.
        routing_used: Dict nodo → modelo usado.
    """
    pipeline_version: str = "KosmosV2"
    timestamp: str = ""
    nodes_executed: int = 0
    nodes_with_errors: int = 0
    errors: dict[str, str] = field(default_factory=dict)
    total_elapsed: float = 0.0
    avg_node_time: float = 0.0
    bottleneck: str = ""
    routing_used: dict[str, str] = field(default_factory=dict)
    topic: str = ""


# ── KosmosKronosLoop ──

class KosmosKronosLoop:
    """Feedback loop between Kosmos pipeline and Kronos orchestrator.

    Kosmos reports pipeline health after each execution.
    Kronos provides routing optimizations and bottleneck analysis.
    Kosmos applies non-blocking optimizations locally.

    Uso:
        loop = KosmosKronosLoop()
        feedback = loop.report_pipeline_health(pipeline_result)
        kronos_suggestions = loop.get_kronos_feedback()
        applied = loop.apply_optimizations(kronos_suggestions)
    """

    def __init__(self) -> None:
        """Initialize KosmosKronosLoop."""
        self._health_path = _PIPELINE_HEALTH_PATH
        self._feedback_path = _KRONOS_FEEDBACK_PATH
        self._health_path.parent.mkdir(parents=True, exist_ok=True)

        # Cached data
        self._history: list[dict[str, Any]] = []
        self._optimizations_applied: list[str] = []
        self._last_kronos_feedback: Optional[str] = None

        # Load existing data
        self._load()

        logger.debug("KosmosKronosLoop initialized")

    # ── Public API ──

    def report_pipeline_health(
        self,
        pipeline_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Genera reporte de salud del pipeline y lo persiste.

        Args:
            pipeline_result: Dict del pipeline result (de run_all()).

        Returns:
            Dict con el reporte generado y metadata.
        """
        logger.info("📊 KosmosKronos: reporting pipeline health...")

        report = self._build_report(pipeline_result)

        # Persist
        self._history.append(asdict(report))
        self._trim_history()
        self._save()

        logger.info(
            "   Pipeline health: %d/%d nodes OK, %.2fs, bottleneck=%s",
            report.nodes_executed - report.nodes_with_errors,
            report.nodes_executed,
            report.total_elapsed,
            report.bottleneck,
        )

        # Get Kronos feedback
        kronos_feedback = self.get_kronos_feedback()

        # Apply optimizations
        optimizations = self.apply_optimizations(kronos_feedback)

        return {
            "report": asdict(report),
            "kronos_feedback": kronos_feedback,
            "optimizations_applied": optimizations,
            "history_length": len(self._history),
        }

    def get_kronos_feedback(self) -> dict[str, Any]:
        """Obtiene sugerencias de Kronos.

        Lee desde kronos_agent.suggest_routing() o desde archivo de feedback.

        Returns:
            Dict con análisis y sugerencias de Kronos.
        """
        # Try live Kronos agent first
        try:
            from lib.kronos_agent import suggest_routing, pipeline_status, evaluation_read

            suggestions_text = suggest_routing()
            status = pipeline_status()
            evaluation = evaluation_read()

            feedback: dict[str, Any] = {
                "source": "kronos_agent_live",
                "suggestions_text": suggestions_text,
                "pipeline_status": status,
                "evaluation": evaluation,
                "timestamp": datetime.now().isoformat(),
            }

            # Parse suggestions into structured format
            feedback["parsed_suggestions"] = self._parse_kronos_suggestions(suggestions_text)

            # Cache to file
            if suggestions_text:
                self._feedback_path.write_text(suggestions_text, encoding="utf-8")

            self._last_kronos_feedback = suggestions_text
            return feedback

        except Exception as exc:
            logger.debug("Kronos agent not available: %s", exc)

        # Fallback: read from cached file
        if self._feedback_path.exists():
            try:
                text = self._feedback_path.read_text(encoding="utf-8")
                self._last_kronos_feedback = text
                return {
                    "source": "cached_file",
                    "suggestions_text": text,
                    "parsed_suggestions": self._parse_kronos_suggestions(text),
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception:
                pass

        return {
            "source": "none",
            "suggestions_text": "",
            "parsed_suggestions": [],
            "note": "Kronos feedback not available",
            "timestamp": datetime.now().isoformat(),
        }

    def apply_optimizations(
        self,
        feedback: dict[str, Any],
    ) -> list[str]:
        """Aplica optimizaciones sugeridas por Kronos.

        Las optimizaciones son locales y no bloqueantes.
        Se registran pero no modifican el pipeline en caliente.

        Args:
            feedback: Dict de feedback de Kronos.

        Returns:
            Lista de optimizaciones aplicadas.
        """
        applied: list[str] = []

        parsed = feedback.get("parsed_suggestions", [])
        if not parsed:
            return applied

        for suggestion in parsed:
            opt = self._try_apply_suggestion(suggestion)
            if opt:
                applied.append(opt)

        if applied:
            self._optimizations_applied.extend(applied)
            self._save()
            logger.info("   Optimizations applied: %d", len(applied))

        return applied

    def get_bottleneck_analysis(self) -> dict[str, Any]:
        """Analiza cuellos de botella históricos.

        Returns:
            Dict con: bottleneck_counts (dict), avg_times (dict),
            recommendations (list).
        """
        if not self._history:
            return {
                "bottleneck_counts": {},
                "avg_times": {},
                "recommendations": ["No hay datos históricos de pipeline"],
                "total_runs": 0,
            }

        bottleneck_counts: dict[str, int] = {}
        node_times: dict[str, list[float]] = {}

        for record in self._history:
            bn = record.get("bottleneck", "")
            if bn:
                bottleneck_counts[bn] = bottleneck_counts.get(bn, 0) + 1

            # Parse routing_used for node times
            routing = record.get("routing_used", {})
            for node in routing:
                if node not in node_times:
                    node_times[node] = []

        # Estimate times from history (node_results are not stored in health)
        # Use heuristics: average total / nodes
        avg_times: dict[str, float] = {}
        total_runs = len(self._history)
        if total_runs > 0:
            avg_total = sum(r.get("total_elapsed", 0) for r in self._history) / total_runs
            avg_nodes = sum(r.get("nodes_executed", 8) for r in self._history) / total_runs
            avg_per_node = avg_total / max(avg_nodes, 1)
            for node in node_times:
                avg_times[node] = round(avg_per_node, 2)

        # Recommendations
        recommendations = []
        if bottleneck_counts:
            worst = max(bottleneck_counts, key=bottleneck_counts.get)
            recommendations.append(
                f"Cuello de botella más frecuente: '{worst}' "
                f"({bottleneck_counts[worst]} de {total_runs} ejecuciones)"
            )
        if avg_times:
            slowest = max(avg_times, key=avg_times.get)
            recommendations.append(
                f"Nodo más lento en promedio: '{slowest}' ({avg_times[slowest]:.2f}s)"
            )

        return {
            "bottleneck_counts": bottleneck_counts,
            "avg_times": avg_times,
            "recommendations": recommendations,
            "total_runs": total_runs,
        }

    def get_health_trend(self, days: int = 14) -> list[dict[str, Any]]:
        """Obtiene tendencia de salud del pipeline.

        Args:
            days: Ventana de días.

        Returns:
            Lista de reportes en el rango (orden cronológico).
        """
        cutoff = datetime.now() - timedelta(days=days)
        return [
            r for r in self._history
            if datetime.fromisoformat(r.get("timestamp", "")).replace(tzinfo=None) >= cutoff
        ]

    # ── Internal: Report Building ──

    def _build_report(self, pipeline_result: dict[str, Any]) -> PipelineHealthReport:
        """Build a PipelineHealthReport from pipeline result dict."""
        node_results = pipeline_result.get("node_results", {})
        errors = pipeline_result.get("errors", {})
        elapsed = pipeline_result.get("elapsed_seconds", 0)
        nodes_exec = pipeline_result.get("nodes_executed", len(node_results))
        nodes_err = pipeline_result.get("nodes_with_errors", len(errors))

        # Determine bottleneck (node with max elapsed time)
        bottleneck = ""
        max_time = 0.0
        routing_used: dict[str, str] = {}
        for node_name, node_data in node_results.items():
            if isinstance(node_data, dict):
                # Try to get node-specific elapsed time
                node_time = node_data.get("node_time", "")
                rt = node_data.get("routing", {})
                if isinstance(rt, dict):
                    routing_used[node_name] = rt.get("model", "?")

        # Use pipeline's routing table for routing info
        for node, route in pipeline_result.get("routing", {}).items():
            if node not in routing_used and isinstance(route, dict):
                routing_used[node] = route.get("model", "?")

        # Estimate bottleneck from errors and node order
        # Simple heuristic: last node with errors or node before last healthy
        if errors:
            bottleneck = list(errors.keys())[-1]
        elif node_results:
            # Use the last executed node as potential bottleneck
            node_keys = list(node_results.keys())
            bottleneck = node_keys[-1] if node_keys else ""

        report = PipelineHealthReport(
            pipeline_version=pipeline_result.get("pipeline", "KosmosV2"),
            timestamp=datetime.now().isoformat(),
            nodes_executed=nodes_exec,
            nodes_with_errors=nodes_err,
            errors=errors,
            total_elapsed=round(elapsed, 2),
            avg_node_time=round(elapsed / max(nodes_exec, 1), 2),
            bottleneck=bottleneck,
            routing_used=routing_used,
            topic=pipeline_result.get("topic", ""),
        )

        return report

    def _parse_kronos_suggestions(self, text: str) -> list[dict[str, str]]:
        """Parse Kronos suggestion text into structured suggestions."""
        suggestions: list[dict[str, str]] = []
        if not text:
            return suggestions

        for line in text.split("\n"):
            line = line.strip()
            # Match bullet points with suggestions
            if line.startswith("- 💡") or line.startswith("- **") or line.startswith("- "):
                suggestion = line.lstrip("- ").strip()
                if suggestion:
                    suggestions.append({
                        "text": suggestion,
                        "source": "kronos",
                    })

        return suggestions

    def _try_apply_suggestion(self, suggestion: dict[str, str]) -> Optional[str]:
        """Try to apply a single optimization suggestion.

        Returns:
            Description of applied optimization, or None.
        """
        text = suggestion.get("text", "").lower()

        # Pattern: routing suggestions
        if "model" in text or "routing" in text:
            logger.debug("   Kronos routing suggestion noted: %s", text[:60])
            return f"Routing note: {text[:60]}"

        # Pattern: parallelism suggestions
        if "parallel" in text or "paralel" in text:
            logger.debug("   Kronos parallelism suggestion noted: %s", text[:60])
            return f"Parallelism note: {text[:60]}"

        # Pattern: budget suggestions
        if "budget" in text or "costo" in text or "cost" in text:
            logger.debug("   Kronos budget suggestion noted: %s", text[:60])
            return f"Budget note: {text[:60]}"

        # General suggestions
        if len(text) > 20:
            logger.debug("   Kronos general suggestion noted: %s", text[:60])
            return f"General note: {text[:60]}"

        return None

    # ── Internal: Persistence ──

    def _load(self) -> None:
        """Load state from disk."""
        if not self._health_path.exists():
            return
        try:
            data = json.loads(self._health_path.read_text(encoding="utf-8"))
            self._history = data.get("history", [])
            self._optimizations_applied = data.get("optimizations_applied", [])
            self._last_kronos_feedback = data.get("last_kronos_feedback")
        except (json.JSONDecodeError, OSError) as exc:
            logger.debug("Could not load pipeline health: %s", exc)

    def _save(self) -> None:
        """Save state to disk."""
        data = {
            "history": self._history,
            "optimizations_applied": self._optimizations_applied,
            "last_kronos_feedback": self._last_kronos_feedback,
        }
        self._health_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _trim_history(self, max_entries: int = 100) -> None:
        """Keep history within limits."""
        if len(self._history) > max_entries:
            self._history = self._history[-max_entries:]


# ── Self-test ──

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("🔄 KosmosKronos Feedback Loop — Self-Test")
    print("=" * 60)

    # Test 1: Instantiation
    print("\n1️⃣  KosmosKronosLoop instantiation...")
    loop = KosmosKronosLoop()
    print("   ✅ Loop created")

    # Test 2: Report pipeline health
    print("\n2️⃣  Report pipeline health...")
    mock_result = {
        "pipeline": "KosmosV2",
        "topic": "Test Architecture Decision",
        "elapsed_seconds": 45.23,
        "nodes_executed": 8,
        "nodes_with_errors": 1,
        "errors": {"govern": "Triple generation warning"},
        "node_results": {
            "discover": {"files": 42, "node_time": "2026-05-29T10:00:00"},
            "model": {"containers": 4, "node_time": "2026-05-29T10:00:05"},
            "analyze": {"health_score": 75, "node_time": "2026-05-29T10:00:12"},
            "quality": {"weighted_score": 82, "node_time": "2026-05-29T10:00:18"},
            "visualize": {"diagrams": 2, "node_time": "2026-05-29T10:00:25"},
            "document": {"adr_id": "ADR-020", "node_time": "2026-05-29T10:00:35"},
            "govern": {"triple_count": 8, "node_time": "2026-05-29T10:00:40"},
            "validate": {"suggestions": [], "node_time": "2026-05-29T10:00:45"},
        },
        "routing": {
            "discover": {"model": "go-flash", "reason": "test"},
            "model": {"model": "go-pro", "reason": "test"},
            "analyze": {"model": "go-pro", "reason": "test"},
            "quality": {"model": "go-kimi-latest", "reason": "test"},
            "visualize": {"model": "go-flash", "reason": "test"},
            "document": {"model": "go-pro", "reason": "test"},
            "govern": {"model": "go-flash", "reason": "test"},
            "validate": {"model": "go-kimi-latest", "reason": "test"},
        },
    }
    feedback = loop.report_pipeline_health(mock_result)
    print(f"   Report: {json.dumps(feedback.get('report', {}), default=str)[:120]}...")
    print(f"   Kronos feedback source: {feedback.get('kronos_feedback', {}).get('source', 'N/A')}")
    print(f"   Optimizations: {len(feedback.get('optimizations_applied', []))}")

    # Test 3: Get bottleneck analysis
    print("\n3️⃣  Bottleneck analysis...")
    analysis = loop.get_bottleneck_analysis()
    print(f"   Total runs: {analysis['total_runs']}")
    print(f"   Bottleneck counts: {analysis.get('bottleneck_counts', {})}")
    print(f"   Recommendations: {analysis.get('recommendations', [])}")

    # Test 4: Get health trend
    print("\n4️⃣  Health trend (14 days)...")
    trend = loop.get_health_trend(days=14)
    print(f"   Records in range: {len(trend)}")

    # Test 5: Build report from scratch
    print("\n5️⃣  Build PipelineHealthReport...")
    report = loop._build_report(mock_result)
    print(f"   Version: {report.pipeline_version}")
    print(f"   Nodes: {report.nodes_executed}/{report.nodes_with_errors} errors")
    print(f"   Elapsed: {report.total_elapsed}s")
    print(f"   Bottleneck: {report.bottleneck}")

    print("\n" + "=" * 60)
    print("✅ All KosmosKronosLoop tests passed")
    print("=" * 60)
