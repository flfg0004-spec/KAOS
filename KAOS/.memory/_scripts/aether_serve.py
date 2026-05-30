#!/usr/bin/env python3
"""Aether Web Dashboard — zero-dependency HTTP server.

Usage: python aether_serve.py [--port 9090]
       python -m lib.aether.cli serve --port 9090
"""

import argparse
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime


def load_status():
    from lib.aether.config_loader import get_config
    from lib.aether.tracker import EtherTracker
    from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER
    cfg = get_config()
    tracker = EtherTracker()
    stats = tracker.get_stats()
    cb_status = _ETHER_CIRCUIT_BREAKER.get_status()
    return cfg, stats, cb_status


class AetherHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/api/config":
            self._json(load_status()[0].to_dict())
        elif self.path == "/api/status":
            _, stats, cb = load_status()
            data = {
                "total_calls": stats.get("total_calls", 0),
                "total_cost_usd": stats.get("total_cost_usd", 0),
                "total_latency_ms": stats.get("total_latency_ms", 0),
                "total_multimodal_calls": stats.get("total_multimodal_calls", 0),
                "circuit_breakers": cb,
                "updated": datetime.now().isoformat(),
            }
            self._json(data)
        elif self.path == "/api/routing":
            from lib.aether.config_loader import get_config
            cfg = get_config()
            self._json(cfg.TASK_MODEL_MAP)
        elif self.path == "/":
            self._html()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404")

    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def _html(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = self._render_html()
        self.wfile.write(html.encode())

    def _render_html(self):
        return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aether Dashboard</title>
<script>
async function fetchJSON(url) {
    try { const r = await fetch(url); return await r.json(); }
    catch(e) { return null; }
}

function card(title, content, color="#38bdf8") {
    return `<div class="card" style="border-top:3px solid ${color}">
        <h2>${title}</h2>
        ${content}
    </div>`;
}

function metric(value, label, unit="") {
    return `<div class="metric">${value}</div>
        <div class="label">${label} ${unit}</div>`;
}

async function refresh() {
    const config = await fetchJSON("/api/config");
    const status = await fetchJSON("/api/status");
    const routing = await fetchJSON("/api/routing");

    let html = '<div class="grid">';

    // Calls & Cost
    if (status) {
        html += card("Llamadas API", metric(status.total_calls || 0, "total calls"), "#22c55e");
        html += card("Costo Total", metric("$" + (status.total_cost_usd || 0).toFixed(4), "USD"), "#f59e0b");
        html += card("Latencia Total", metric((status.total_latency_ms || 0).toFixed(1), "ms"), "#a78bfa");
        html += card("Multimodal", metric(status.total_multimodal_calls || 0, "calls"), "#ec4899");
    }

    // Tiers
    if (config && config.model_tiers) {
        let tiers = Object.entries(config.model_tiers)
            .map(([k,v]) => `<div class="row"><span>${k}</span><span>${v.target_pct}%</span></div>`).join("");
        html += card("Tiers", `<div class="metric">${Object.keys(config.model_tiers).length}</div><div class="labels">${tiers}</div>`, "#38bdf8");
    }

    // Models
    if (config && config.cost_rates) {
        let models = Object.keys(config.cost_rates).sort()
            .map(m => `<div class="row"><span>${m}</span><span>$${config.cost_rates[m].output.toFixed(6)}/1K</span></div>`).join("");
        html += card("Modelos (" + Object.keys(config.cost_rates).length + ")",
            `<div class="labels">${models}</div>`, "#22c55e");
    }

    // Cost Caps
    if (config && config.cost_caps) {
        let caps = Object.entries(config.cost_caps)
            .map(([k,v]) => `<div class="row"><span>${k}</span><span>$${v.weekly_usd}/sem, ${v.daily_calls}/día</span></div>`).join("");
        html += card("Budget Caps", `<div class="labels">${caps}</div>`, "#f59e0b");
    }

    // Routing
    if (routing) {
        let tasks = Object.entries(routing)
            .map(([k,v]) => `<div class="row"><span>${k}</span><span>${v.model}</span><span style="color:#64748b">${v.tier||''}</span></div>`).join("");
        html += card("Routing (" + Object.keys(routing).length + " tasks)",
            `<div class="labels">${tasks}</div>`, "#a78bfa");
    }

    // Circuit Breakers
    if (status && status.circuit_breakers) {
        let cbs = Object.entries(status.circuit_breakers)
            .map(([k,v]) => `<div class="row"><span>${k}</span><span class="cb-${v.state}">${v.state}</span><span>${v.failures} fails</span></div>`).join("");
        html += card("Circuit Breakers", `<div class="labels">${cbs}</div>`, "#ef4444");
    }

    // Feature Flags
    if (config && config.feature_flags) {
        let flags = Object.entries(config.feature_flags)
            .map(([k,v]) => `<div class="row"><span>${k}</span><span class="flag-${v?'on':'off'}">${v?'✅':'❌'}</span></div>`).join("");
        html += card("Feature Flags", `<div class="labels">${flags}</div>`, "#14b8a6");
    }

    html += '</div>';

    if (status) html += `<div class="footer">Última actualización: ${status.updated || '-'}</div>`;

    document.getElementById("dashboard").innerHTML = html;
}

setInterval(refresh, 30000);
window.onload = refresh;
</script>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:system-ui,-apple-system,sans-serif; background:#0f172a; color:#e2e8f0; padding:2rem; }
h1 { font-size:1.5rem; margin-bottom:1rem; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:1rem; }
.card { background:#1e293b; border-radius:8px; padding:1rem; border:1px solid #334155; }
.card h2 { font-size:0.85rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.75rem; }
.metric { font-size:2rem; font-weight:700; color:#38bdf8; margin-bottom:0.25rem; }
.label { font-size:0.85rem; color:#64748b; }
.labels { margin-top:0.5rem; }
.row { display:flex; justify-content:space-between; padding:0.2rem 0; font-size:0.8rem; border-bottom:1px solid #1e293b; }
.row:nth-child(even) { background:#1a2332; }
.cb-closed { color:#22c55e; }
.cb-open { color:#ef4444; }
.cb-half-open { color:#f59e0b; }
.flag-on { color:#22c55e; }
.flag-off { color:#ef4444; }
.footer { margin-top:2rem; color:#475569; font-size:0.75rem; text-align:center; }
</style>
</head>
<body>
<h1>Aether Dashboard</h1>
<div id="dashboard">Cargando...</div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Aether Web Dashboard")
    parser.add_argument("--port", type=int, default=9090, help="Port (default: 9090)")
    parser.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    args = parser.parse_args()
    server = HTTPServer((args.host, args.port), AetherHandler)
    print(f"Aether Dashboard → http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
