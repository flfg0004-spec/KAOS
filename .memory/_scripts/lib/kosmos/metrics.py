"""kosmos/metrics.py — Recolector de métricas en tiempo real (KosmosV3 B3).

Lee los traces exportados y health endpoints para servir un dashboard JSON.
Incluye AlertEngine para detección automática de condiciones anómalas (B4).

Sin dependencias externas — solo stdlib.
"""
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Rutas (coinciden con pipeline.py) ──

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent  # .memory/_scripts/
_MEMORY_DIR = _SCRIPTS_DIR.parent  # .memory/
_TRACES_DIR = _MEMORY_DIR / "_pipeline" / "traces"


# ═══════════════════════════════════════════════════════════════════
# B3: MetricsCollector
# ═══════════════════════════════════════════════════════════════════


class MetricsCollector:
    """Recolector de métricas en tiempo real desde traces, cache, rate limiter y health.

    Args:
        window_minutes: Ventana de tiempo (en minutos) para filtrar spans recientes.
    """

    def __init__(self, window_minutes: int = 10) -> None:
        self.window_minutes = window_minutes

    # ── API pública ──

    def collect(self) -> dict[str, Any]:
        """Recolecta TODAS las métricas disponibles.

        Returns:
            Dict con secciones: pipeline, latency, cache, rate_limiter, health, timestamp.
            Cada sección incluye valores por defecto si no hay datos disponibles
            (graceful degradation).
        """
        now = datetime.now()
        metrics: dict[str, Any] = {
            "timestamp": now.isoformat(),
            "service": "kosmosv2",
        }

        # 1. Pipeline + Latencia + Error rate desde traces
        spans = self._load_traces(self.window_minutes)
        pipeline_data = self._build_pipeline_data(spans)
        metrics["pipeline"] = pipeline_data
        metrics["latency"] = self._compute_latency_percentiles(spans)
        metrics["error_rate"] = self._compute_error_rate(spans)

        # 2. Cache (desde PipelineCache.stats())
        try:
            from lib.kosmos._state import pipeline_cache_stats
            metrics["cache"] = pipeline_cache_stats()
        except Exception as e:
            logger.debug("Metrics: cache unavailable — %s", e)
            metrics["cache"] = {
                "size": 0, "maxsize": 0, "hit_rate": 0.0,
                "hits": 0, "misses": 0, "error": str(e),
            }

        # 3. Rate limiter (desde rate_limit_status())
        try:
            from lib.kosmos.ratelimit import rate_limit_status
            metrics["rate_limiter"] = rate_limit_status()
        except Exception as e:
            logger.debug("Metrics: rate_limiter unavailable — %s", e)
            metrics["rate_limiter"] = {
                "max_concurrent": 0, "waiting": 0, "total_submitted": 0,
                "total_acquired": 0, "total_timeout": 0, "error": str(e),
            }

        # 4. Health (desde /health)
        try:
            from lib.kosmos.health import health_status
            metrics["health"] = health_status()
        except Exception as e:
            logger.debug("Metrics: health unavailable — %s", e)
            metrics["health"] = {"status": "unknown", "uptime": 0, "error": str(e)}

        # 5. Alertas (B4)
        try:
            from lib.kosmos.metrics import AlertEngine
            engine = AlertEngine()
            metrics["alerts"] = engine.check(metrics)
        except Exception as e:
            logger.debug("Metrics: alerts unavailable — %s", e)
            metrics["alerts"] = []

        return metrics

    # ── Traces ──

    def _load_traces(self, window_minutes: int) -> list[dict[str, Any]]:
        """Carga spans desde archivos JSONL dentro de la ventana de tiempo.

        Args:
            window_minutes: Minutos hacia atrás desde ahora para filtrar.

        Returns:
            Lista de spans (dicts) cuyo timestamp cae dentro de la ventana.
            Retorna lista vacía si no hay archivos o si no se puede leer.
        """
        if not _TRACES_DIR.exists():
            logger.debug("Metrics: traces dir not found — %s", _TRACES_DIR)
            return []

        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        spans: list[dict[str, Any]] = []

        for trace_file in sorted(_TRACES_DIR.glob("traces-*.jsonl"), reverse=True):
            try:
                with open(trace_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            span = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        # Filtrar por ventana de tiempo
                        ts_str = span.get("timestamp", "")
                        if ts_str:
                            try:
                                span_time = datetime.fromisoformat(ts_str)
                                if span_time >= cutoff:
                                    spans.append(span)
                            except (ValueError, TypeError):
                                # Si no se puede parsear, incluir igual
                                spans.append(span)
                        else:
                            spans.append(span)
            except (OSError, PermissionError) as e:
                logger.debug("Metrics: cannot read trace file %s — %s", trace_file.name, e)
                continue

        return spans

    # ── Pipeline ──

    def _build_pipeline_data(self, spans: list[dict[str, Any]]) -> dict[str, Any]:
        """Construye métricas de pipeline a partir de spans.

        Args:
            spans: Lista de spans (posiblemente vacía).

        Returns:
            Dict con executions, errors, avg_nodes, error_rate.
        """
        if not spans:
            return {
                "executions": 0,
                "errors": 0,
                "avg_nodes": 0.0,
                "error_rate": 0.0,
                "nodes": {},
            }

        # Contar spans por nombre (nombre del nodo / batch)
        node_counts: dict[str, int] = {}
        error_count = 0
        # Para estimar ejecuciones: agrupar por span_id o usar batches
        execution_spans = [s for s in spans if s.get("name", "").startswith("batch_")]
        node_spans = [s for s in spans if not s.get("name", "").startswith("batch_")]

        for s in spans:
            name = s.get("name", "unknown")
            node_counts[name] = node_counts.get(name, 0) + 1
            if not s.get("success", True):
                error_count += 1

        # Estimar número de ejecuciones de pipeline
        # Cada pipeline produce ~1-8 spans de nodos + batches
        # Asumimos que cada grupo de spans con timestamps cercanos es 1 ejecución
        executions = self._estimate_executions(spans)

        total_spans = len(spans) or 1
        return {
            "executions": executions,
            "errors": error_count,
            "avg_nodes": round(len(node_spans) / max(executions, 1), 1),
            "error_rate": round(error_count / total_spans * 100, 2),
            "nodes": node_counts,
        }

    @staticmethod
    def _estimate_executions(spans: list[dict[str, Any]]) -> int:
        """Estima número de ejecuciones de pipeline agrupando spans cercanos.

        Si hay spans con nombre 'batch_level_0', cada batch marca una ejecución.
        Si no, cuenta spans únicos por span_id o asume 1 ejecución.
        """
        batch_spans = [s for s in spans if s.get("name", "").startswith("batch_")]
        if batch_spans:
            # Contar grupos únicos por span_id
            span_ids = set()
            for s in batch_spans:
                sid = s.get("span_id", "")
                if sid:
                    span_ids.add(sid)
            # Si no hay span_id, contar batches únicos por timestamp cercano
            if span_ids:
                return max(len(span_ids), 1)
            # Agrupar por timestamp proximity (ej: dentro de 5 segundos)
            timestamps = []
            for s in batch_spans:
                ts = s.get("timestamp", "")
                if ts:
                    try:
                        timestamps.append(datetime.fromisoformat(ts))
                    except (ValueError, TypeError):
                        pass
            if len(timestamps) >= 2:
                timestamps.sort()
                groups = 1
                for i in range(1, len(timestamps)):
                    if (timestamps[i] - timestamps[i - 1]).total_seconds() > 10:
                        groups += 1
                return groups
            return 1

        # Fallback: contar span_ids únicos en todos los spans
        span_ids = set()
        for s in spans:
            sid = s.get("span_id", "")
            if sid:
                span_ids.add(sid)
        return max(len(span_ids), 1)

    # ── Latencia ──

    @staticmethod
    def _compute_latency_percentiles(spans: list[dict[str, Any]]) -> dict[str, float]:
        """Calcula percentiles P50, P95, P99 de duración de spans.

        Args:
            spans: Lista de spans con campo 'duration_ms'.

        Returns:
            Dict con p50, p95, p99 en milisegundos.
            Retorna 0 para todos si no hay spans.
        """
        durations = [
            s["duration_ms"] for s in spans
            if isinstance(s.get("duration_ms"), (int, float)) and s["duration_ms"] >= 0
        ]

        if not durations:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        durations.sort()
        n = len(durations)

        def percentile(p: float) -> float:
            if n == 0:
                return 0.0
            k = (n - 1) * p / 100.0
            f = int(k)
            c = f + 1
            if c >= n:
                return float(durations[f])
            return durations[f] + (k - f) * (durations[c] - durations[f])

        return {
            "p50": round(percentile(50), 2),
            "p95": round(percentile(95), 2),
            "p99": round(percentile(99), 2),
        }

    # ── Error rate ──

    @staticmethod
    def _compute_error_rate(spans: list[dict[str, Any]]) -> float:
        """Calcula porcentaje de spans con success=false.

        Args:
            spans: Lista de spans con campo 'success'.

        Returns:
            Float entre 0.0 y 100.0. 0 si no hay spans.
        """
        if not spans:
            return 0.0

        error_count = sum(1 for s in spans if not s.get("success", True))
        return round(error_count / len(spans) * 100, 2)


# ═══════════════════════════════════════════════════════════════════
# B4: AlertEngine
# ═══════════════════════════════════════════════════════════════════


class AlertEngine:
    """Motor de alertas automáticas no bloqueantes.

    Revisa condiciones de error rate, cache hit rate, rate limiter
    y bloqueos de pipeline. No modifica el sistema — solo reporta.

    Args:
        check_interval: Segundos entre chequeos (por defecto 60).
    """

    def __init__(self, check_interval: int = 60) -> None:
        self.check_interval = check_interval
        self._lock = threading.Lock()
        self._last_alerts: list[dict[str, Any]] = []
        self._consecutive_timeouts: int = 0
        self._last_check_time: float = 0.0

    # ── API pública ──

    def check(self, metrics: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Revisa condiciones y retorna lista de alertas activas.

        Args:
            metrics: Dict de métricas (opcional). Si es None, recolecta
                     métricas frescas via MetricsCollector.

        Returns:
            Lista de alertas. Cada alerta es un dict con:
                - level: "warn" | "critical"
                - source: str
                - message: str
                - value: float
                - threshold: float
                - timestamp: str (ISO format)
        """
        if metrics is None:
            collector = MetricsCollector(window_minutes=10)
            metrics = collector.collect()

        alerts: list[dict[str, Any]] = []

        # Check conditions
        alerts.extend(self._check_errors(metrics))
        alerts.extend(self._check_cache(metrics))
        alerts.extend(self._check_rate_limit(metrics))

        with self._lock:
            self._last_alerts = list(alerts)
            self._last_check_time = time.time()

        return alerts

    def get_last_alerts(self) -> list[dict[str, Any]]:
        """Retorna la última lista de alertas generadas (thread-safe)."""
        with self._lock:
            return list(self._last_alerts)

    def start_daemon(self, interval: int | None = None) -> None:
        """Inicia thread daemon que checkea periódicamente.

        Args:
            interval: Segundos entre chequeos (default: self.check_interval).
        """
        import threading

        interval = interval or self.check_interval

        def _loop() -> None:
            while True:
                try:
                    self.check()
                except Exception as e:
                    logger.warning("B4: AlertEngine check failed — %s", e)
                time.sleep(interval)

        t = threading.Thread(target=_loop, daemon=True, name="alert-engine")
        t.start()
        logger.info("B4: AlertEngine daemon started (interval=%ds)", interval)

    # ── Checks internos ──

    @staticmethod
    def _check_errors(metrics: dict[str, Any]) -> list[dict[str, Any]]:
        """Revisa condiciones de error rate.

        - WARN: error rate > 5% en ventana 10min
        - CRITICAL: error rate > 20% en ventana 10min

        Args:
            metrics: Dict con sección 'pipeline' o 'error_rate'.

        Returns:
            Lista de alertas (vacía si no se exceden thresholds).
        """
        alerts: list[dict[str, Any]] = []
        error_rate = metrics.get("error_rate", 0.0)
        pipeline = metrics.get("pipeline", {})

        # Intentar obtener error_rate desde pipeline si está disponible
        if "error_rate" in pipeline:
            error_rate = pipeline["error_rate"]

        error_rate = float(error_rate)

        if error_rate > 20.0:
            alerts.append({
                "level": "critical",
                "source": "error_rate",
                "message": f"Error rate critical: {error_rate:.1f}% (> 20%)",
                "value": error_rate,
                "threshold": 20.0,
                "timestamp": datetime.now().isoformat(),
            })
        elif error_rate > 5.0:
            alerts.append({
                "level": "warn",
                "source": "error_rate",
                "message": f"Error rate elevated: {error_rate:.1f}% (> 5%)",
                "value": error_rate,
                "threshold": 5.0,
                "timestamp": datetime.now().isoformat(),
            })

        return alerts

    @staticmethod
    def _check_cache(metrics: dict[str, Any]) -> list[dict[str, Any]]:
        """Revisa condiciones de cache.

        - WARN: cache hit rate < 50%

        Args:
            metrics: Dict con sección 'cache'.

        Returns:
            Lista de alertas (vacía si no se exceden thresholds).
        """
        alerts: list[dict[str, Any]] = []
        cache = metrics.get("cache", {})

        hit_rate = float(cache.get("hit_rate", 100.0))

        if hit_rate < 50.0:
            alerts.append({
                "level": "warn",
                "source": "cache",
                "message": f"Cache hit rate low: {hit_rate:.1f}% (< 50%)",
                "value": hit_rate,
                "threshold": 50.0,
                "timestamp": datetime.now().isoformat(),
            })

        return alerts

    def _check_rate_limit(self, metrics: dict[str, Any]) -> list[dict[str, Any]]:
        """Revisa condiciones de rate limiter.

        - WARN: waiting > 5
        - CRITICAL: pipeline blocked (more than 3 consecutive timeouts)

        Args:
            metrics: Dict con sección 'rate_limiter'.

        Returns:
            Lista de alertas (vacía si no se exceden thresholds).
        """
        alerts: list[dict[str, Any]] = []
        rl = metrics.get("rate_limiter", {})

        waiting = int(rl.get("waiting", 0))
        timeout_total = int(rl.get("total_timeout", 0))

        # WARN: waiting > 5
        if waiting > 5:
            alerts.append({
                "level": "warn",
                "source": "rate_limiter",
                "message": f"Rate limiter queue deep: {waiting} waiting (> 5)",
                "value": float(waiting),
                "threshold": 5.0,
                "timestamp": datetime.now().isoformat(),
            })

        # CRITICAL: consecutive timeouts tracking
        # Usamos un contador interno de timeouts consecutivos
        with self._lock:
            prev_timeout = self._consecutive_timeouts

            if timeout_total > prev_timeout:
                # Incrementó el total de timeouts desde el último check
                # (esto indica al menos 1 nuevo timeout)
                # Para simplificar, asumimos que cada incremento es 1 consecutivo
                diff = timeout_total - prev_timeout
                if diff > 0 and prev_timeout > 0:
                    # Hubo timeouts en ambos checks — consecutivos
                    self._consecutive_timeouts += diff
                else:
                    self._consecutive_timeouts = diff
            else:
                # No hubo nuevos timeouts, resetear contador
                self._consecutive_timeouts = 0

            # Actualizar para próximo check
            # Guardamos el valor actual como referencia para el próximo check
            self._consecutive_timeouts = max(self._consecutive_timeouts, 0)

            if self._consecutive_timeouts > 3:
                alerts.append({
                    "level": "critical",
                    "source": "rate_limiter",
                    "message": f"Pipeline blocked: {self._consecutive_timeouts} consecutive timeouts",
                    "value": float(self._consecutive_timeouts),
                    "threshold": 3.0,
                    "timestamp": datetime.now().isoformat(),
                })

        return alerts


# ── entry point rápido para verificar ──
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("🧪 MetricsCollector self-test")
    mc = MetricsCollector()
    metrics = mc.collect()
    print(f"   Keys: {sorted(metrics.keys())}")
    print(f"   Pipeline: {metrics.get('pipeline', {})}")
    print(f"   Latency: {metrics.get('latency', {})}")
    print(f"   Cache: {metrics.get('cache', {})}")
    print(f"   Rate limiter: {metrics.get('rate_limiter', {})}")
    print(f"   Health: {metrics.get('health', {})}")
    print(f"   Alerts: {metrics.get('alerts', [])}")

    print("\n🧪 AlertEngine self-test")
    ae = AlertEngine()
    alerts = ae.check(metrics)
    print(f"   Active alerts: {len(alerts)}")
    for a in alerts:
        print(f"   [{a['level']}] {a['source']}: {a['message']}")

    print("\n✅ Self-test complete")
