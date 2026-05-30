"""Generates quality dashboard markdown from system health metrics."""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

DASHBOARD_PATH = Path(__file__).resolve().parent.parent / ".vault" / "quality" / "dashboard.md"

def get_health():
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "lib" / "aether" / "metrics.py")],
        capture_output=True, text=True,
    )
    return json.loads(result.stdout)

def generate(health):
    q = health.get("quality", {})
    t = health.get("tracker", {})
    cb = health.get("circuit_breaker", {})
    audit = health.get("audit", {})
    score = health.get("overall_score", 0)

    audit_summary = {}
    recent = audit.get("recent_audits", [])
    if recent:
        audit_summary = recent[0].get("summary", {})

    md = f"""# Dashboard de Calidad — KAOS

Generado: {date.today().isoformat()}

## 1. Health Score

Score global del sistema: **{score:.0f}/100**

| Componente | Estado |
|------------|--------|
| QualityStore | {q.get('status', '?')} |
| EtherTracker | {t.get('status', '?')} |
| Circuit Breaker | {cb.get('status', '?')} |
| Kosmos Audit | {audit.get('status', '?')} |

## 2. Costos Semanales

| Concepto | Valor |
|----------|-------|
| Total calls | {t.get('total_calls', 0)} |
| Total cost USD | ${t.get('total_cost_usd', 0):.4f} |
| Tokens totales | {t.get('total_tokens', 0)} |

## 3. Última Auditoría Kosmos

- Checks: {audit_summary.get('total_checks', 'N/A')}
- Errores: {audit_summary.get('errors', 'N/A')}
- Advertencias: {audit_summary.get('warnings', 'N/A')}
- Fecha: {recent[0].get('timestamp', 'N/A') if recent else 'N/A'}

## 4. Tendencias de Calidad (7 días)

Para ver tendencias detalladas, revisar los archivos en `.memory/.vault/quality/timeseries/`

## 5. Alertas del Circuit Breaker

- Estado: {cb.get('state', '?')}
- Fallos: {cb.get('failures', 0)}
- Disponible: {'sí' if cb.get('available') else 'no'}
"""
    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_PATH.write_text(md, encoding="utf-8")
    print(f"Dashboard generado en {DASHBOARD_PATH}")

if __name__ == "__main__":
    h = get_health()
    generate(h)
