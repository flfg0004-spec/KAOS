"""Static HTML dashboard for vault health."""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE = (Path(__file__).resolve().parent.parent.parent)  # .memory/
KAOS_ROOT = BASE.parent  # KAOS project root
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

    # Ingest metrics
    ingest_manifest = KAOS_ROOT / ".memory" / "ingest" / "queue" / "manifest.json"
    ingest_metrics = {"total_ingested": 0, "total_deduped": 0}
    if ingest_manifest.exists():
        try:
            im = json.loads(ingest_manifest.read_text(encoding="utf-8"))
            ingest_metrics = {"total_ingested": im.get("total_ingested", 0), "total_deduped": im.get("total_deduped", 0)}
        except Exception:
            pass

    # Synapse metrics (via subprocess for reliability)
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

    # Token usage from DSOL
    token_usage_path = KAOS_ROOT / ".memory" / "cache" / "token-usage.json"
    dsol_metrics = {"total_calls": 0, "total_cost_usd": 0, "cache_hit_rate": None}
    if token_usage_path.exists():
        try:
            tu = json.loads(token_usage_path.read_text(encoding="utf-8"))
            tot = tu.get("totals", {})
            dsol_metrics = {
                "total_calls": tot.get("total_calls", 0),
                "total_cost_usd": tot.get("cost_usd", 0),
                "cache_hit_rate": round(tot.get("cache_hit_tokens", 0) / max(tot.get("prompt_tokens", 1), 1) * 100, 1),
            }
        except Exception:
            pass

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
        "deepseek": dsol_metrics,
        "quality": _calc_quality_v2(),
        "agents": {
            "total": 4,
            "active": ["aletheia", "kosmos", "metis", "mnemosyne"],
            "mcp_issues": 0,
        },
    }


def _calc_quality_v2() -> dict:
    """Calculate quality metrics using quality.status() directly (fast)."""
    import sys as _sys
    import importlib as _il
    _sys.path.insert(0, str(KAOS_ROOT / ".memory" / "_scripts"))
    _sys.path.insert(0, str(KAOS_ROOT / ".memory" / "_scripts" / "lib"))
    try:
        _q = _il.import_module("quality")
        _status = _q.status()
        import re as _re
        score = 0
        cm_count = 0
        cm_total = 0
        for _line in _status.split("\n"):
            if _line.startswith("Quality Score:"):
                _m = _re.search(r"([\d.]+)", _line.split(":")[1])
                if _m: score = float(_m.group(1))
            elif "Confidence matrix" in _line:
                _m = _re.search(r"(\d+)/(\d+)", _line)
                if _m:
                    cm_count = int(_m.group(1))
                    cm_total = int(_m.group(2))
        return {"score": score, "has_confidence_matrix": cm_count, "total_investigations": cm_total, "completeness": score}
    except Exception:
        return {"score": 0, "has_confidence_matrix": 0, "total_investigations": 0, "completeness": 0}


def render_html(data: dict) -> str:
    status_icon = "✅" if data["health"]["overall"] == "healthy" else "⚠️"
    color = "#22c55e" if data["health"]["overall"] == "healthy" else "#eab308"

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
        <div class="metric green">{data["quality"]["score"]}</div>
        <div style="font-size:0.85rem;color:#94a3b8;">score compuesto</div>
        <div style="margin-top:0.5rem;">
          <div class="row"><span class="label">Matriz confianza</span><span>{data['quality']['has_confidence_matrix']}/{data['quality']['total_investigations']}</span></div>
          <div class="row"><span class="label">Completitud</span><span>{data['quality']['completeness']}%</span></div>
          <div class="row"><span class="label">Agentes</span><span>{data['agents']['total']}</span></div>
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

<div class="footer">KAOS Memory Vault — generado por vault.py dashboard</div>
</body>
</html>"""


def run() -> str:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    data = collect_data()
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    HTML_FILE.write_text(render_html(data), encoding="utf-8")
    return f"Dashboard generated: {HTML_FILE}"
