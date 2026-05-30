"""kosmos/health.py — Health endpoints para KosmosV2 (KosmosV3 A5, B3, B4).

Endpoints:
- GET /health     → 200 OK si el módulo está vivo
- GET /ready      → 200 OK si pipeline puede ejecutarse, 503 si no
- GET /metrics    → JSON con métricas de cache, rate limiter, spans, estado
- GET /metrics/v2 → JSON extendido con pipeline, latencia, percentiles, alertas (B3+B4)
- GET /dashboard  → HTML autónomo con auto-refresh cada 5s (B3)

Uso:
    python -m lib.kosmos.health  # sirve en puerto 9876
    # o importar e iniciar desde código:
    from lib.kosmos.health import serve_daemon
    serve_daemon()

Sin dependencias externas — solo stdlib (http.server, threading).
"""
import json
import logging
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)

_HEALTH_PORT = 9876
_START_TIME = time.time()
_DEFAULT_RESPONSE_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
}


def health_status() -> Dict[str, Any]:
    """Return current health status with uptime.

    Útil para MetricsCollector y monitoreo externo.

    Returns:
        Dict con status, service, uptime (segundos), timestamp.
    """
    return {
        "status": "ok",
        "service": "kosmosv2",
        "uptime": round(time.time() - _START_TIME, 1),
        "timestamp": datetime.now().isoformat(),
    }


class _HealthHandler(BaseHTTPRequestHandler):
    """HTTP request handler for /health, /ready, /metrics endpoints."""

    def _respond(self, code: int, data: Dict[str, Any]) -> None:
        """Send JSON response with status code and CORS headers."""
        self.send_response(code)
        for key, value in _DEFAULT_RESPONSE_HEADERS.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def do_GET(self) -> None:
        """Route GET requests to the appropriate handler."""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/ready":
            self._handle_ready()
        elif self.path == "/metrics":
            self._handle_metrics()
        elif self.path == "/metrics/v2":
            self._handle_metrics_v2()
        elif self.path == "/dashboard":
            self._handle_dashboard()
        elif self.path == "/tune":
            self._handle_tune()
        elif self.path == "/tune/apply":
            self._handle_tune_apply()
        else:
            self._respond(404, {
                "error": "not found",
                "paths": ["/health", "/ready", "/metrics", "/metrics/v2", "/dashboard", "/tune", "/tune/apply"],
            })

    def _handle_health(self) -> None:
        """Return 200 OK with service status, uptime and timestamp."""
        self._respond(200, health_status())

    def _handle_ready(self) -> None:
        """Return 200 if pipeline can accept work, 503 if saturated.

        Checks the rate limiter queue depth: if more than 10 pipelines
        are waiting, the service is considered not ready.
        """
        ready = True
        try:
            from lib.kosmos.ratelimit import rate_limit_status
            rl = rate_limit_status()
            if rl.get("waiting", 0) > 10:
                ready = False
                logger.info("A5: Not ready — %d pipelines waiting", rl["waiting"])
        except Exception as exc:
            logger.debug("A5: ready check failed (non-fatal): %s", exc)
        self._respond(200 if ready else 503, {
            "ready": ready,
            "timestamp": datetime.now().isoformat(),
        })

    def _handle_metrics(self) -> None:
        """Return JSON with cache, rate limiter, and span metrics."""
        metrics: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "service": "kosmosv2",
        }

        # Pipeline cache metrics (A1+A3)
        try:
            from lib.kosmos._state import pipeline_cache_stats
            metrics["cache"] = pipeline_cache_stats()
        except Exception as e:
            metrics["cache_error"] = str(e)

        # Rate limiter metrics (A4)
        try:
            from lib.kosmos.ratelimit import rate_limit_status
            metrics["rate_limiter"] = rate_limit_status()
        except Exception as e:
            metrics["rate_limiter_error"] = str(e)

        # B1+B2: OpenTelemetry + trace export
        try:
            from lib.kosmos.otel import get_trace_summary, is_otel_available
            metrics["otel"] = {"available": is_otel_available()}
            metrics["traces"] = get_trace_summary()
        except Exception:
            pass

        self._respond(200, metrics)

    def _handle_metrics_v2(self) -> None:
        """Return extended metrics with pipeline, latency, percentiles, alerts (B3+B4)."""
        try:
            from lib.kosmos.metrics import MetricsCollector, AlertEngine
            mc = MetricsCollector()
            metrics = mc.collect()
            metrics["alerts"] = AlertEngine().check()
            self._respond(200, metrics)
        except Exception as e:
            self._respond(500, {"error": str(e), "timestamp": datetime.now().isoformat()})

    def _handle_dashboard(self) -> None:
        """Return autonomous HTML dashboard with auto-refresh (B3)."""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(_DASHBOARD_HTML.encode())

    def _handle_tune(self) -> None:
        """Return routing table auto-tuning dry-run (C4)."""
        try:
            from lib.kosmos.routing import auto_tune
            self._respond(200, auto_tune(dry_run=True))
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _handle_tune_apply(self) -> None:
        """Apply auto-tuning suggestions (C4)."""
        try:
            from lib.kosmos.routing import auto_tune
            self._respond(200, auto_tune(dry_run=False))
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def log_message(self, format: str, *args) -> None:
        """Route HTTP server log messages to Python logger."""
        logger.debug("Health: %s", format % args)


_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KosmosV2 — Live Metrics</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:system-ui,sans-serif; background:#0f172a; color:#e2e8f0; padding:1rem; }
  h1 { color:#7B68EE; font-size:1.2rem; margin-bottom:1rem; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:1rem; }
  .card { background:#1e293b; border-radius:8px; padding:1rem; border:1px solid #334155; }
  .card h2 { font-size:0.8rem; color:#94a3b8; text-transform:uppercase; margin-bottom:0.5rem; }
  .metric { font-size:2rem; font-weight:700; color:#38bdf8; }
  .row { display:flex; justify-content:space-between; padding:0.25rem 0; font-size:0.85rem; border-bottom:1px solid #1a2332; }
  .label { color:#94a3b8; }
  .green { color:#22c55e; }
  .red { color:#ef4444; }
  .yellow { color:#eab308; }
  .footer { margin-top:1rem; font-size:0.7rem; color:#475569; text-align:center; }
</style>
</head>
<body>
<h1>🏛️ KosmosV2 — Live Metrics</h1>
<div class="grid" id="metrics">Loading...</div>
<div class="footer" id="footer"></div>
<script>
async function refresh() {
  try {
    const r = await fetch('/metrics/v2');
    const d = await r.json();
    let html = '';
    html += '<div class="card"><h2>Health</h2><div class="metric">'+(d.health?.status||'?')+'</div>';
    if(d.cache) html += '<div class="row"><span class="label">Cache</span><span>'+d.cache.size+'/'+d.cache.maxsize+' ('+d.cache.hit_rate+'%)</span></div>';
    html += '</div>';
    if(d.pipeline) {
      html += '<div class="card"><h2>Pipeline</h2>';
      html += '<div class="row"><span class="label">Executions</span><span>'+d.pipeline.executions+'</span></div>';
      html += '<div class="row"><span class="label">Error rate</span><span class="'+(d.pipeline.error_rate>5?'red':'green')+'">'+d.pipeline.error_rate+'%</span></div>';
      html += '</div>';
    }
    if(d.latency) {
      html += '<div class="card"><h2>Latency (ms)</h2>';
      html += '<div class="row"><span class="label">P50</span><span>'+d.latency.p50+'</span></div>';
      html += '<div class="row"><span class="label">P95</span><span>'+d.latency.p95+'</span></div>';
      html += '<div class="row"><span class="label">P99</span><span>'+d.latency.p99+'</span></div>';
      html += '</div>';
    }
    if(d.rate_limiter) {
      html += '<div class="card"><h2>Rate Limiter</h2>';
      html += '<div class="row"><span class="label">Waiting</span><span>'+(d.rate_limiter.waiting||0)+'</span></div>';
      html += '<div class="row"><span class="label">Submitted</span><span>'+(d.rate_limiter.total_submitted||0)+'</span></div>';
      html += '<div class="row"><span class="label">Timeouts</span><span class="'+(d.rate_limiter.total_timeout>0?'red':'green')+'">'+(d.rate_limiter.total_timeout||0)+'</span></div>';
      html += '</div>';
    }
    if(d.alerts && d.alerts.length>0) {
      let ahtml = '';
      d.alerts.forEach(function(a) {
        const cls = a.level==='critical'?'red':'yellow';
        ahtml += '<div class="row"><span class="'+cls+'">&#9679;</span><span>'+a.message+'</span></div>';
      });
      html += '<div class="card"><h2>Alerts ('+d.alerts.length+')</h2>'+ahtml+'</div>';
    }
    document.getElementById('metrics').innerHTML = html;
    document.getElementById('footer').textContent = 'Updated: '+d.timestamp;
  } catch(e) {
    document.getElementById('metrics').innerHTML = '<div class="card"><h2>Error</h2><p>'+e.message+'</p></div>';
  }
}
refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>"""


def serve_forever(port: int = _HEALTH_PORT) -> None:
    """Start health HTTP server (blocking).

    Args:
        port: TCP port to listen on (default 9876).
    """
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    logger.info("A5: Health server listening on :%d", port)
    logger.info("A5: Endpoints — /health  /ready  /metrics  /metrics/v2  /dashboard  /tune  /tune/apply")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("A5: Health server shutting down")
        server.shutdown()


def serve_daemon(port: int = _HEALTH_PORT) -> None:
    """Start health server in a daemon thread (non-blocking).

    Args:
        port: TCP port to listen on (default 9876).
    """
    import threading
    t = threading.Thread(target=serve_forever, args=(port,), daemon=True)
    t.start()
    logger.info("A5: Health daemon started on :%d", port)


# ── CLI entry point ──
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys

    port = _HEALTH_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Usage: python -m lib.kosmos.health [port]")
            sys.exit(1)

    print(f"🧪 KosmosV2 Health Server — http://localhost:{port}")
    print(f"   Endpoints: GET /health  GET /ready  GET /metrics  GET /metrics/v2  GET /dashboard  GET /tune  GET /tune/apply")
    serve_forever(port)
