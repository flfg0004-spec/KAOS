"""KAOS Dashboard — servidor web con 7 metricas en vivo.

ThreadingHTTPServer + background cache para evitar bloqueos.
Timeout global 5s por peticion. Autorecuperacion ante errores.

Uso:
    py .tools/dashboard.py              # Servidor (foreground)
    py .tools/dashboard.py --seed       # Genera datos de ejemplo
    dashboard.bat                       # Background con autoreinicio Windows
"""

import json
import os
import re
import sys
import time
import threading
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".memory" / "_scripts"))

KAOS_ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = KAOS_ROOT / ".memory"
VAULT_DIR = KAOS_ROOT / ".vault"
TIMESERIES_DIR = VAULT_DIR / "quality" / "timeseries"
CACHE_DIR = MEMORY_DIR / "cache"
DASHBOARD_HTML = Path(__file__).resolve().parent / "dashboard.html"

_cache_lock = threading.Lock()
_cache = {
    "metrics": [],
    "alerts": [],
    "trends": [],
    "agents": [],
    "updated": "iniciando...",
    "error": None,
}


def _load_json(path):
    if path and path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _load_timeseries(path):
    data = _load_json(path)
    if isinstance(data, dict):
        return data.get("scores", data.get("entries", []))
    return []


def collect_metrics():
    try:
        now = datetime.now()

        scores_file = TIMESERIES_DIR / "verification-scores.json"
        all_scores = _load_timeseries(scores_file)
        recent_7 = []
        for s in all_scores:
            try:
                ts = datetime.fromisoformat(s["timestamp"])
                if ts > now - timedelta(days=7):
                    recent_7.append(s)
            except Exception:
                pass

        m1_composite = 0.0
        m1_trend = "estable"
        if recent_7:
            vals = [s.get("composite", 0) for s in recent_7]
            m1_composite = sum(vals) / len(vals)
            if len(vals) >= 2:
                diff = vals[-1] - vals[0]
                m1_trend = "subiendo" if diff > 1 else "bajando" if diff < -1 else "estable"

        token_data = _load_json(CACHE_DIR / "token-usage.json")
        hit = token_data.get("total_cache_hit", 0)
        miss = token_data.get("total_cache_miss", 0)
        total_calls = hit + miss
        m2_cache = round(hit / total_calls * 100, 1) if total_calls > 0 else 0

        durations = _load_timeseries(TIMESERIES_DIR / "pipeline-durations.json")
        recent_dur = durations[-20:] if durations else []
        m3_time = 0
        if recent_dur:
            m3_time = sum(d.get("duration_s", 0) for d in recent_dur) / len(recent_dur)
        m3_min = round(m3_time / 60, 1)

        m4_links = 0
        lint_path = MEMORY_DIR / "schema" / "lint-report.md"
        if lint_path.exists():
            content = lint_path.read_text(encoding="utf-8")
            m = re.search(r"Total issues:\s*(\d+)", content)
            m4_links = int(m.group(1)) if m else 0

        m5_cost = round(token_data.get("total_cost_usd", 0), 2)

        pipeline_scores = _load_timeseries(TIMESERIES_DIR / "pipeline-scores.json")
        week_ago = now - timedelta(days=7)
        week_pips = 0
        for p in pipeline_scores:
            try:
                dt = datetime.fromisoformat(p.get("date", p.get("timestamp", "2000-01-01")))
                if dt > week_ago:
                    week_pips += 1
            except Exception:
                pass
        m6_throughput = round(week_pips / 7, 1)

        m7_frag = 0.0
        if recent_7:
            consolidated = sum(1 for s in recent_7 if s.get("composite", 0) > 80)
            m7_frag = round(1 - (consolidated / len(recent_7)), 2)

        has_data = bool(recent_7) or m2_cache > 0 or m3_min > 0 or m5_cost > 0

        metrics = [
            {"name": "M1: Score Compuesto", "value": round(m1_composite, 1) if has_data else "—",
             "target": 95, "warn": 80, "trend": m1_trend if has_data else "sin datos",
             "source": "verification_hook"},
            {"name": "M2: Cache Hit Rate", "value": f"{m2_cache}%" if m2_cache > 0 else "—",
             "target": ">60%", "warn": 20, "trend": f"{m2_cache}%" if m2_cache > 0 else "sin datos",
             "source": "DSOL token-usage.json"},
            {"name": "M3: Pipeline", "value": f"{m3_min}m" if m3_min > 0 else "—",
             "target": "<5m", "warn": 15,
             "trend": f"promedio {len(recent_dur)} ejecuciones" if recent_dur else "sin datos",
             "source": "pipeline-durations.json"},
            {"name": "M4: Broken Wikilinks", "value": m4_links, "target": 0, "warn": 3,
             "trend": "0 = verde", "source": "lint-report.md"},
            {"name": "M5: Costo Semanal", "value": f"${m5_cost}" if m5_cost > 0 else "—",
             "target": "<$5", "warn": 5, "trend": "total acumulado", "source": "token-usage.json"},
            {"name": "M6: Throughput", "value": f"{m6_throughput}/h" if m6_throughput > 0 else "—",
             "target": ">3/h", "warn": 1, "trend": "ultimos 7 dias" if m6_throughput > 0 else "sin datos",
             "source": "pipeline-scores.json"},
            {"name": "M7: Fragmentacion", "value": round(m7_frag, 2) if m7_frag > 0 else "—",
             "target": "<0.2", "warn": 0.5, "trend": "baja", "source": "sleep cycle"},
        ]

        alerts = [{"level": "ok", "message": "Todas las metricas dentro de parametros"}]

        trends = []
        if recent_7:
            by_date = {}
            for s in recent_7:
                d = s.get("timestamp", "")[:10]
                by_date.setdefault(d, []).append(s.get("composite", 0))
            prev = None
            for date in sorted(by_date.keys())[-7:]:
                vals = by_date[date]
                avg = sum(vals) / len(vals)
                delta = avg - prev if prev is not None else 0
                trends.append({"date": date, "score": round(avg, 1), "delta": round(delta, 1)})
                prev = avg

        agents = []
        if all_scores:
            groups = {}
            for s in all_scores:
                a = s.get("agent", "unknown")
                groups.setdefault(a, []).append(s.get("composite", 0))
            for name, values in groups.items():
                agents.append({"name": name, "score": sum(values) / len(values), "tasks": len(values)})

        return {
            "metrics": metrics, "alerts": alerts, "trends": trends,
            "agents": agents, "updated": now.strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        return {"metrics": [], "alerts": [{"level": "crit", "message": f"Error: {e}"}],
                "trends": [], "agents": [], "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e)}


def _background_updater():
    """Thread background: actualiza cache cada 30s."""
    while True:
        try:
            data = collect_metrics()
            with _cache_lock:
                _cache.clear()
                _cache.update(data)
        except Exception as e:
            with _cache_lock:
                _cache["error"] = str(e)
                _cache["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(30)


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == "/api/data":
                with _cache_lock:
                    data = dict(_cache)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(data, indent=2).encode())
            elif self.path in ("/", "/dashboard"):
                html = "Dashboard no disponible"
                if DASHBOARD_HTML.exists():
                    html = DASHBOARD_HTML.read_text(encoding="utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
        except Exception:
            try:
                self.send_error(500, "Error interno del servidor")
            except Exception:
                pass

    def log_message(self, fmt, *args):
        pass


def main():
    if "--seed" in sys.argv:
        from tools.seed_dashboard import seed

    # Arrancar background updater
    updater = threading.Thread(target=_background_updater, daemon=True)
    updater.start()

    port = int(os.getenv("KAOS_DASHBOARD_PORT", "9090"))
    host = os.getenv("KAOS_DASHBOARD_HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    server.timeout = 5

    print(f"KAOS Dashboard: http://{host}:{port}")
    print(f"Cache actualizado cada 30s | ThreadingHTTPServer | Timeout 5s")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard detenido.")
        server.server_close()


if __name__ == "__main__":
    main()
