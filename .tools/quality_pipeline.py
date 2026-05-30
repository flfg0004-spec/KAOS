"""Quality Pipeline — ejecuta verificacion de calidad + auto-adr + auto-tuning.

Uso:
    py .tools/quality_pipeline.py          # Ejecuta pipeline completo
    py .tools/quality_pipeline.py --score  # Solo score
    py .tools/quality_pipeline.py --adr    # Solo auto-adr
    py .tools/quality_pipeline.py --tune   # Solo auto-tuning
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".memory" / "_scripts"))

VAULT_ROOT = Path(__file__).resolve().parent.parent


def run_score_pipeline():
    """Evalua calidad de todo el vault y persiste resultados."""
    print("=== Quality Pipeline: Score ===")
    from lib.quality.vault import calculate
    q = calculate()
    score = q.get("score", q.get("composite", 0))
    print(f"  Score compuesto: {score}/100")
    print(f"  Detalles: {json.dumps(q, indent=2, default=str)[:500]}")
    return q


def run_auto_adr():
    """Ejecuta detector de auto-adr contra health/lint reports."""
    print("=== Quality Pipeline: Auto-ADR ===")
    from lib.auto_adr import detector

    proposal = detector.scan_vault_health()
    if proposal:
        path = proposal.save()
        print(f"  ADR propuesto: {path.name}")
        print(f"  Contexto: {proposal.context[:100]}...")
    else:
        print("  Sin issues detectados — vault saludable")

    return proposal


def run_auto_tune():
    """Ejecuta auto-tuning DSOL."""
    print("=== Quality Pipeline: Auto-Tuning ===")
    from lib.auto_tuning import optimize_budget, status as tune_status

    s = tune_status()
    print(f"  Cache hit rate: {s['cache_hit_rate']}%")
    print(f"  Costo semanal: ${s['weekly_cost']}")
    print(f"  Budget actual: {s['budget']}")
    print(f"  Thinking: {s['thinking_mode']}")

    result = optimize_budget()
    if result["changes"]:
        print(f"  Cambios aplicados: {', '.join(result['changes'])}")
    else:
        print("  Sin cambios necesarios")

    return result


def run_quality_gate() -> bool:
    """Quality gate: score > 80 pasa, < 80 bloquea."""
    print("=== Quality Pipeline: Gate ===")
    from lib.quality.vault import calculate
    q = calculate()
    score = q.get("score", q.get("composite", 0))

    threshold = int(os.getenv("KAOS_QUALITY_THRESHOLD", "80"))
    passed = score >= threshold

    print(f"  Score: {score}/100 (threshold: {threshold})")
    print(f"  Resultado: {'PASS' if passed else 'FAIL'}")

    return passed


def main():
    pipelines = {
        "score": run_score_pipeline,
        "adr": run_auto_adr,
        "tune": run_auto_tune,
        "gate": run_quality_gate,
    }

    args = sys.argv[1:] if len(sys.argv) > 1 else ["score", "adr", "tune"]

    results = {}
    for arg in args:
        arg = arg.lstrip("-")
        if arg in pipelines:
            results[arg] = pipelines[arg]()
        elif arg == "all":
            for name, fn in pipelines.items():
                results[name] = fn()
        else:
            print(f"  Comando desconocido: {arg}")
            print(f"  Opciones: {', '.join(pipelines.keys())}, all")

    return results


if __name__ == "__main__":
    main()
