"""Generates weekly quality report from system health metrics."""
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

REPORT_DIR = Path(__file__).resolve().parent.parent / ".vault" / "quality" / "reports"

def get_health():
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "lib" / "aether" / "metrics.py")],
        capture_output=True, text=True,
    )
    return json.loads(result.stdout)

def generate_report(health):
    q = health.get("quality", {})
    t = health.get("tracker", {})
    cb = health.get("circuit_breaker", {})
    audit = health.get("audit", {})
    score = health.get("overall_score", 0)

    today = date.today()
    week_ago = today - timedelta(days=7)

    report = f"""# Reporte Semanal de Calidad — KAOS

**Período**: {week_ago.isoformat()} → {today.isoformat()}
**Generado**: {today.isoformat()}

## Resumen Ejecutivo

- **Health Score**: {score:.0f}/100
- **Total calls**: {t.get('total_calls', 0)}
- **Costo total**: ${t.get('total_cost_usd', 0):.4f}
- **Circuit Breaker**: {cb.get('state', '?')}

## Hallazgos de Auditoría

"""
    recent = audit.get("recent_audits", [])
    if recent:
        s = recent[0].get("summary", {})
        report += f"- {s.get('total_checks', 0)} checks, {s.get('errors', 0)} errores, {s.get('warnings', 0)} advertencias\n"
    else:
        report += "- Sin datos de auditoría\n"

    report += f"""
## Recomendaciones

1. {'Sistema saludable' if score >= 80 else 'Revisar componentes con estado error'}
2. {'Circuit Breaker requiere atención' if cb.get('state') != 'closed' else 'Circuit Breaker operando normalmente'}
3. {'Acumular más datos de calidad para mejorar precisión' if q.get('total_entries', 0) < 50 else 'Volumen de calidad adecuado'}
"""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"weekly_{today.isoformat()}.md"
    path.write_text(report, encoding="utf-8")
    print(f"Reporte generado en {path}")

if __name__ == "__main__":
    h = get_health()
    generate_report(h)
