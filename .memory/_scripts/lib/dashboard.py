"""Static HTML dashboard for vault health — v2 with ring gauges, sparklines, lifecycle + contradictions."""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE = (Path(__file__).resolve().parent.parent.parent)
KAOS_ROOT = BASE.parent
DASHBOARD_DIR = KAOS_ROOT / ".memory" / "dashboard"
DATA_FILE = DASHBOARD_DIR / "dashboard.json"
HTML_FILE = DASHBOARD_DIR / "index.html"


def _git_log(n: int = 5) -> list[str]:
    try:
        r = subprocess.run(
            ["git", "log", "--oneline", f"-{n}"],
            cwd=KAOS_ROOT / ".memory", capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        )
        return [l.strip() for l in r.stdout.strip().split("\n") if l.strip()]
    except Exception:
        return []


def _count_files(base: Path, pattern: str = "**/*.md") -> int:
    return len(list(base.glob(pattern)))


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _calc_quality_v2() -> dict:
    import importlib as _il
    _il.invalidate_caches()
    _il.import_module("lib.quality")
    _q = _il.import_module("lib.quality")
    _status = _q.status()
    import re as _re
    score = 0
    for _line in _status.split("\n"):
        if _line.startswith("Quality Score:"):
            _m = _re.search(r"([\d.]+)", _line.split(":")[1])
            if _m: score = float(_m.group(1))
    details = _q.calculate().get("details", {})
    return {
        "score": score,
        "connectivity": details.get("connectivity", {}).get("score", 0),
        "freshness": details.get("freshness", {}).get("score", 0),
        "embeddings": details.get("embeddings", {}).get("score", 0),
        "confidence_matrix": details.get("confidence_matrix", {}).get("score", 0),
        "completeness": score,
    }


def _lifecycle_data() -> dict:
    try:
        from lib import memory_lifecycle as mlc
        results = mlc.run_evaluate_all(dry_run=True)
        tiers = {}
        for r in results:
            tiers[r.get("tier", "unknown")] = tiers.get(r.get("tier", "unknown"), 0) + 1
        avg_conf = sum(r.get("confidence", 0) for r in results) / max(len(results), 1)
        flagged = [r for r in results if r.get("recommendation", "OK") != "OK"]
        return {
            "tiers": tiers,
            "total": len(results),
            "avg_confidence": round(avg_conf, 3),
            "flagged": len(flagged),
        }
    except Exception:
        return {"tiers": {}, "total": 0, "avg_confidence": 0, "flagged": 0}


def _strategy_metrics() -> dict:
    """Strategy analytics metrics for dashboard."""
    try:
        from lib.strategy_analytics import get_summary
        return get_summary()
    except Exception:
        return {
            "total_sessions": 0,
            "latest_bcg": 0,
            "latest_okr": 0,
            "trend": "stable",
            "recommendation": "Analytics module not available",
        }


def _contradictions_data() -> dict:
    try:
        from lib import contradictions as ct
        state = ct._load_state()
        active = [e for e in state if e.get("status") != "resolved"]
        contradictions = [e for e in active if e.get("verdict") == "contradiction"]
        complements = [e for e in active if e.get("verdict") == "complement"]
        return {
            "total": len(active),
            "contradictions": len(contradictions),
            "complements": len(complements),
        }
    except Exception:
        return {"total": 0, "contradictions": 0, "complements": 0}


def _sparklines() -> str:
    """Inline SVG sparkline for quality trend."""
    ts_file = KAOS_ROOT / ".vault" / "quality" / "timeseries" / "daily.jsonl"
    if not ts_file.exists():
        return ""
    scores = []
    with open(ts_file) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    scores.append(json.loads(line).get("score", 0))
                except Exception:
                    pass
    if len(scores) < 2:
        return ""
    scores = scores[-30:]
    w, h = 120, 30
    max_s = max(scores) or 1
    min_s = min(scores)
    rng = max_s - min_s or 1
    pts = []
    for i, s in enumerate(scores):
        x = w * i / (len(scores) - 1)
        y = h - (h * (s - min_s) / rng)
        pts.append(f"{x:.1f},{y:.1f}")
    coords = " ".join(pts)
    color = "#22c55e" if scores[-1] >= scores[0] else "#ef4444"
    return f"""
<div class="sparkline">
  <svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">
    <polyline fill="none" stroke="{color}" stroke-width="1.5" points="{coords}"/>
  </svg>
  <span class="spark-label">{scores[-1]:.1f}</span>
</div>"""


def _ring_gauge(value: float, max_val: float, label: str, color: str = "#38bdf8") -> str:
    pct = min(100, (value / max(max_val, 1)) * 100)
    r = 36
    circ = 2 * 3.14159 * r
    offset = circ - (pct / 100) * circ
    return f"""
<div class="ring-wrapper">
  <svg width="90" height="90" viewBox="0 0 90 90">
    <circle cx="45" cy="45" r="{r}" fill="none" stroke="#334155" stroke-width="6"/>
    <circle cx="45" cy="45" r="{r}" fill="none" stroke="{color}" stroke-width="6"
      stroke-dasharray="{circ}" stroke-dashoffset="{offset}" stroke-linecap="round"
      transform="rotate(-90 45 45)"/>
    <text x="45" y="40" text-anchor="middle" fill="#e2e8f0" font-size="18" font-weight="bold">{value:.0f}</text>
    <text x="45" y="55" text-anchor="middle" fill="#64748b" font-size="9">/{max_val:.0f}</text>
  </svg>
  <div class="ring-label">{label}</div>
</div>"""


def _pipeline_executions() -> list:
    """Read recent DAG executions from timeseries."""
    exec_log = KAOS_ROOT / ".vault" / "quality" / "timeseries" / "dag-executions.json"
    if exec_log.exists():
        try:
            return json.loads(exec_log.read_text()).get("executions", [])[-10:]
        except Exception:
            pass
    return []


def collect_data() -> dict:
    import re

    log_text = _read(KAOS_ROOT / ".memory" / "wiki" / "log.md")
    log_entries = re.findall(r"^## \[(\d{4}-\d{2}-\d{2})\] (\S+)(?: \| (.+))?$", log_text, re.MULTILINE)

    cache_file = KAOS_ROOT / ".memory" / "cache" / "hydrate-cache.json"
    cache_data = {}
    if cache_file.exists():
        try:
            cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            cache_data = {}

    lint = _read(KAOS_ROOT / ".memory" / "schema" / "lint-report.md")
    lint_issues = 0
    lm = re.search(r"Total issues:\s*(\d+)", lint)
    if lm:
        lint_issues = int(lm.group(1))

    health = _read(KAOS_ROOT / ".memory" / "schema" / "health-report.md")
    git_clean = "OK: Git clean" in health

    pipeline_status = _read(KAOS_ROOT / ".memory" / "_pipeline" / "status.md")
    pm = re.search(r"\*\*status\*\*:\s*(\S+)", pipeline_status)
    pipeline_active = pm.group(1) if pm else "unknown"
    profile_m = re.search(r"\*\*profile\*\*:\s*(.+)", pipeline_status)
    pipeline_profile = profile_m.group(1).strip() if profile_m else "none"

    ingest_manifest = KAOS_ROOT / ".memory" / "ingest" / "queue" / "manifest.json"
    ingest_metrics = {"total_ingested": 0, "total_deduped": 0}
    if ingest_manifest.exists():
        try:
            im = json.loads(ingest_manifest.read_text(encoding="utf-8"))
            ingest_metrics = {"total_ingested": im.get("total_ingested", 0), "total_deduped": im.get("total_deduped", 0)}
        except Exception:
            pass

    synapse_info = {"concepts": 0, "wikilinks": 0}
    try:
        sr = subprocess.run(
            [sys.executable, str(KAOS_ROOT / ".memory" / "_scripts" / "vault.py"), "synapse", "status"],
            cwd=KAOS_ROOT / ".memory", capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15
        )
        if sr.returncode == 0:
            sm = re.search(r"Concepts indexed: (\d+)", sr.stdout)
            sw = re.search(r"Total \[\[wikilinks\]\]: (\d+)", sr.stdout)
            synapse_info = {"concepts": int(sm.group(1)) if sm else 0, "wikilinks": int(sw.group(1)) if sw else 0}
    except Exception:
        pass

    pressure = "unknown"
    pc = cache_data.get("pressure", "unknown")

    wikilinks_result = subprocess.run(
        [sys.executable, str(KAOS_ROOT / ".memory" / "_scripts" / "vault.py"), "wikilinks", "report"],
        cwd=KAOS_ROOT / ".memory", capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
    )
    wl_text = wikilinks_result.stdout
    wl_valid = int(re.search(r"Valid wikilinks:\s*(\d+)", wl_text).group(1)) if re.search(r"Valid wikilinks:\s*(\d+)", wl_text) else 0
    wl_broken = int(re.search(r"Broken wikilinks:\s*(\d+)", wl_text).group(1)) if re.search(r"Broken wikilinks:\s*(\d+)", wl_text) else 0

    cache_entries = len(cache_data.get("entries", []))
    cache_max = cache_data.get("maxEntries", 30)

    token_usage_path = KAOS_ROOT / ".memory" / "cache" / "token-usage.json"
    dsol_metrics = {"total_calls": 0, "total_cost_usd": 0, "cache_hit_rate": None,
                     "total_prompt_tokens": 0, "total_completion_tokens": 0, "per_agent": {}}
    if token_usage_path.exists():
        try:
            from lib.aether.tracker import EtherTracker as TokenTracker
            tt = TokenTracker()
            dsol_metrics = tt.get_stats()
            dsol_metrics["cache_hit_rate"] = round(
                dsol_metrics.get("total_cache_hit_tokens", 0) / max(dsol_metrics.get("total_prompt_tokens", 1), 1) * 100, 1
            )
        except Exception:
            pass

    # Session analytics
    try:
        from lib import session_analytics
        sa = session_analytics.build_analytics()
    except Exception:
        sa = {}

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "session_analytics": {
            "total_sessions": sa.get("total_sessions", 0),
            "total_messages": sa.get("total_messages", 0),
            "avg_duration_min": sa.get("avg_duration_min"),
            "feedback_avg": sa.get("feedback", {}).get("avg_rating", 0),
            "feedback_count": sa.get("feedback", {}).get("total", 0),
        },
        "vault": {
            "total_md": _count_files(KAOS_ROOT / ".memory", "**/*.md"),
            "by_directory": {
                "wiki": _count_files(KAOS_ROOT / ".memory" / "wiki", "**/*.md"),
                "schema": _count_files(KAOS_ROOT / ".memory" / "schema", "*.md"),
                "raw": _count_files(KAOS_ROOT / ".memory" / "raw", "*.md"),
                "_scripts": len(list((KAOS_ROOT / ".memory" / "_scripts").rglob("*.py"))) + len(list((KAOS_ROOT / ".memory" / "_scripts").rglob("*.ps1"))),
                "_pipeline": _count_files(KAOS_ROOT / ".memory" / "_pipeline", "*.md"),
            },
            "total_scripts": len(list((KAOS_ROOT / ".memory" / "_scripts").rglob("*.py"))) + len(list((KAOS_ROOT / ".memory" / "_scripts").rglob("*.ps1"))),
        },
        "health": {
            "git_clean": git_clean,
            "lint_issues": lint_issues,
            "overall": "healthy" if (git_clean and lint_issues == 0) else "warning",
        },
        "cache": {
            "entries": cache_entries,
            "max_entries": cache_max,
            "pressure": pressure,
        },
        "pipeline": {
            "status": pipeline_active,
            "profile": pipeline_profile,
        },
        "ingest": ingest_metrics,
        "synapse": synapse_info,
        "activity": {
            "recent_commits": _git_log(5),
            "recent_logs": log_entries[-5:],
        },
        "wikilinks": {
            "valid": wl_valid,
            "broken": wl_broken,
        },
        "deepseek": {**dsol_metrics, **dsol_metrics.get("per_agent", {})},
        "token_usage": dsol_metrics,
        "quality": _calc_quality_v2(),
        "lifecycle": _lifecycle_data(),
        "contradictions": _contradictions_data(),
        "strategy": _strategy_metrics(),
    "agents": {
        "total": 4,
        "active": [
            "aletheia",
            "kosmos",
            "metis",
            "mnemosyne"
        ],
        "mcp_issues": 0
    },
    "pipeline_executions": _pipeline_executions()
}



def render_html(data: dict) -> str:
    status_icon = "✅" if data["health"]["overall"] == "healthy" else "⚠️"
    color = "#22c55e" if data["health"]["overall"] == "healthy" else "#eab308"
    spark = _sparklines()

    q = data.get("quality", {})
    lc = data.get("lifecycle", {})
    ct = data.get("contradictions", {})
    dsol = data.get("token_usage", {})

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KAOS Vault Dashboard</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:system-ui,-apple-system,sans-serif; background:#0f172a; color:#e2e8f0; padding:2rem; }}
  h1 {{ font-size:1.5rem; margin-bottom:0.5rem; display:flex; align-items:center; gap:0.5rem; }}
  .status {{ color:{color}; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:1rem; margin:1rem 0; }}
  .card {{ background:#1e293b; border-radius:8px; padding:1rem; border:1px solid #334155; }}
  .card h2 {{ font-size:0.9rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.75rem; }}
  .metric {{ font-size:2rem; font-weight:700; color:#38bdf8; }}
  .metric.green {{ color:{color}; }}
  .metric.red {{ color:#ef4444; }}
  .row {{ display:flex; justify-content:space-between; padding:0.25rem 0; font-size:0.85rem; }}
  .row:nth-child(even) {{ background:#1a2332; }}
  .label {{ color:#94a3b8; }}
  .bar {{ height:8px; background:#334155; border-radius:4px; margin-top:0.5rem; overflow:hidden; }}
  .bar-fill {{ height:100%; background:{color}; border-radius:4px; transition:width 0.3s; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.8rem; }}
  th {{ text-align:left; color:#94a3b8; padding:0.4rem 0.25rem; border-bottom:1px solid #334155; }}
  td {{ padding:0.3rem 0.25rem; border-bottom:1px solid #1e293b; }}
  .footer {{ margin-top:2rem; color:#475569; font-size:0.75rem; text-align:center; }}
  .badge {{ display:inline-block; padding:0.15rem 0.5rem; border-radius:4px; font-size:0.75rem; }}
  .badge.green {{ background:#166534; color:#86efac; }}
  .badge.yellow {{ background:#854d0e; color:#fde047; }}
  .badge.red {{ background:#7f1d1d; color:#fca5a5; }}
  .ring-gauges {{ display:flex; flex-wrap:wrap; gap:0.5rem; justify-content:center; }}
  .ring-wrapper {{ text-align:center; width:90px; }}
  .ring-label {{ font-size:0.7rem; color:#94a3b8; margin-top:0.25rem; }}
  .sparkline {{ display:flex; align-items:center; gap:0.5rem; margin-top:0.5rem; }}
  .spark-label {{ font-size:1.2rem; font-weight:700; color:#38bdf8; }}
</style>
</head>
<body>
<h1>{status_icon} KAOS Vault Dashboard <span class="status">●</span></h1>
<p style="color:#64748b;font-size:0.85rem;">{data["timestamp"]}</p>

<div class="grid">
  <div class="card">
    <h2>Archivos</h2>
    <div class="metric">{data["vault"]["total_md"]}</div>
    <div style="margin-top:0.5rem;">
      <div class="row"><span class="label">Wiki</span><span>{data["vault"]["by_directory"]["wiki"]}</span></div>
      <div class="row"><span class="label">Schema</span><span>{data["vault"]["by_directory"]["schema"]}</span></div>
      <div class="row"><span class="label">Raw</span><span>{data["vault"]["by_directory"]["raw"]}</span></div>
      <div class="row"><span class="label">Scripts</span><span>{data["vault"]["total_scripts"]}</span></div>
    </div>
  </div>

  <div class="card">
    <h2>Salud</h2>
    <div class="metric {'green' if data['health']['overall']=='healthy' else 'red'}">{data["health"]["lint_issues"]}</div>
    <div style="font-size:0.85rem;color:#94a3b8;">issues de lint</div>
    <div style="margin-top:0.5rem;">
      <div class="row"><span class="label">Git clean</span><span>{'✅' if data['health']['git_clean'] else '❌'}</span></div>
    </div>
  </div>

  <div class="card">
    <h2>Pipeline</h2>
    <div class="metric {'green' if data['pipeline']['status']=='complete' else 'yellow'}">{data["pipeline"]["status"]}</div>
    <div style="margin-top:0.5rem;font-size:0.85rem;color:#94a3b8;">Perfil: {data['pipeline'].get('profile','none')}</div>
    <div class="bar"><div class="bar-fill" style="width:{min(100, data['cache']['entries']/data['cache']['max_entries']*100)}%"></div></div>
    <div style="margin-top:0.5rem;font-size:0.85rem;color:#94a3b8;">Cache: {data['cache']['entries']}/{data['cache']['max_entries']}</div>
  </div>

  <div class="card">
    <h2>Ingesta</h2>
    <div class="metric">{data.get('ingest',{}).get('total_ingested',0)}</div>
    <div style="font-size:0.85rem;color:#94a3b8;">archivos ingeridos</div>
    <div style="margin-top:0.5rem;">
      <div class="row"><span class="label">Deduplicados</span><span>{data.get('ingest',{}).get('total_deduped',0)}</span></div>
    </div>
  </div>

  <div class="card">
    <h2>Sinapsis</h2>
    <div class="metric">{data.get('synapse',{}).get('concepts',0)}</div>
    <div style="font-size:0.85rem;color:#94a3b8;">conceptos indexados</div>
    <div style="margin-top:0.5rem;">
      <div class="row"><span class="label">[[wikilinks]]</span><span>{data.get('synapse',{}).get('wikilinks',0)}</span></div>
    </div>
  </div>

  <div class="card">
    <h2>Wikilinks</h2>
    <div class="metric green">{data["wikilinks"]["valid"]}</div>
    <div style="font-size:0.85rem;color:#94a3b8;">válidos</div>
    <div style="margin-top:0.5rem;">
      <div class="row"><span class="label">Broken</span><span>{'✅ 0' if data['wikilinks']['broken']==0 else '❌ '+str(data['wikilinks']['broken'])}</span></div>
    </div>
  </div>

  <div class="card">
    <h2>Calidad</h2>
    <div class="metric green">{q.get("score", 0)}</div>
    <div style="font-size:0.85rem;color:#94a3b8;">score compuesto</div>
    {spark}
    <div style="margin-top:0.5rem;">
      <div class="row"><span class="label">Connectivity</span><span>{q.get('connectivity', 0)} pts</span></div>
      <div class="row"><span class="label">Freshness</span><span>{q.get('freshness', 0)} pts</span></div>
      <div class="row"><span class="label">Completitud</span><span>{q.get('completeness', 0)}%</span></div>
    </div>
  </div>

  <div class="card">
    <h2>Gasto</h2>
    <div class="metric">{dsol.get('total_calls', 0)}</div>
    <div style="font-size:0.85rem;color:#94a3b8;">llamadas API</div>
    <div style="margin-top:0.5rem;">
      <div class="row"><span class="label">Costo total</span><span>${dsol.get('total_cost_usd', 0):.4f}</span></div>
      <div class="row"><span class="label">Cache hit</span><span>{dsol.get('cache_hit_rate', 0)}%</span></div>
      <div class="row"><span class="label">Tokens prompt</span><span>{dsol.get('total_prompt_tokens', 0):,}</span></div>
      <div class="row"><span class="label">Tokens completion</span><span>{dsol.get('total_completion_tokens', 0):,}</span></div>
    </div>
    {'<div style="margin-top:0.5rem;"><h3 style="font-size:0.8rem;color:#94a3b8;">Por agente</h3>' + "".join(
        f'<div class="row"><span class="label">{agent}</span><span>${stats["cost_usd"]:.4f} ({stats["calls"]} calls)</span></div>'
        for agent, stats in sorted(dsol.get("per_agent", {}).items(), key=lambda x: -x[1]["cost_usd"])
    ) + "</div>" if dsol.get("per_agent") else ""}
  </div>
</div>

<div class="ring-gauges" style="display:flex; gap:1rem; margin-bottom:1rem;">
  <div style="flex:1; background:#1e293b; border-radius:8px; padding:1rem; border:1px solid #334155;">
    <h2 style="font-size:0.9rem; color:#94a3b8; text-transform:uppercase; margin-bottom:0.75rem;">Lifecycle</h2>
    <div style="display:flex; flex-wrap:wrap; gap:0.5rem; justify-content:center;">
      {_ring_gauge(lc.get("total", 0), max(lc.get("total", 1), 1), "Total", "#38bdf8")}
      {_ring_gauge(lc.get("avg_confidence", 0) * 100, 100, "Avg Conf", "#22c55e")}
      {_ring_gauge(lc.get("flagged", 0), max(lc.get("total", 1), 1), "Flagged", "#ef4444")}
    </div>
    <div style="margin-top:0.5rem; font-size:0.8rem;">
      {''.join(f'<div class="row"><span class="label">{tier}</span><span>{count}</span></div>'
               for tier, count in lc.get("tiers", {}).items())}
    </div>
  </div>
  <div style="flex:1; background:#1e293b; border-radius:8px; padding:1rem; border:1px solid #334155;">
    <h2 style="font-size:0.9rem; color:#94a3b8; text-transform:uppercase; margin-bottom:0.75rem;">Contradicciones</h2>
    <div style="display:flex; flex-wrap:wrap; gap:0.5rem; justify-content:center;">
      {_ring_gauge(ct.get("total", 0), max(ct.get("total", 1), 1), "Pairs", "#f59e0b")}
      {_ring_gauge(ct.get("contradictions", 0), max(ct.get("total", 1), 1), "Contrad", "#ef4444")}
      {_ring_gauge(ct.get("complements", 0), max(ct.get("total", 1), 1), "Complem", "#22c55e")}
    </div>
  </div>
</div>

<div class="grid">
  <div class="card">
    <h2>Actividad Reciente</h2>
    <table>
      <tr><th>Commit</th></tr>
      {''.join(f'<tr><td style="font-family:monospace;font-size:0.75rem;">{c}</td></tr>' for c in data['activity']['recent_commits'])}
    </table>
  </div>
  <div class="card">
    <h2>Log Reciente</h2>
    <table>
      <tr><th>Fecha</th><th>Evento</th></tr>
      {''.join(f'<tr><td>{e[0]}</td><td>{e[1]}</td></tr>' for e in data['activity']['recent_logs'])}
    </table>
  </div>
</div>

<div class="footer">KAOS Memory Vault — generado por vault.py dashboard | F6+F7 activo</div>
</body>
</html>"""


def run() -> str:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    data = collect_data()
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    HTML_FILE.write_text(render_html(data), encoding="utf-8")
    return f"Dashboard generated: {HTML_FILE}"
