"""
KAOS Verification Chain — Verificación cruzada entre agentes (Fase 3)

Ejecuta 3 fases de verificación sobre un reporte:
  Fase 1 - Aletheia:   Verifica factualidad (referencias, fuentes)
  Fase 2 - Kosmos:     Verifica coherencia arquitectónica
  Fase 3 - Metis:      Verifica alineación estratégica (post_output_hook)

Uso:
  py -3 .tools/verification_chain.py <report_file> [--profile desarrollo]
  py -3 .tools/verification_chain.py --full
  py -3 .tools/verification_chain.py --help
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
KAOS_ROOT = TOOLS_DIR.parent
SCRIPTS_DIR = KAOS_ROOT / ".memory" / "_scripts"
CACHE_DIR = KAOS_ROOT / ".memory" / "cache"
VERIFICATION_DIR = CACHE_DIR / "verification"

sys.path.insert(0, str(TOOLS_DIR))
from score_engine import compute_composite, evaluate

ARCH_TERMS = [
    "arquitectura", "componente", "microservicio", "api", "interfaz",
    "patrón", "patron", "evento", "dominio", "capa", "modulo", "modulo",
    "dependencia", "acoplamiento", "cohesion", "cohesión", "escalabilidad",
    "rendimiento", "latencia", "throughput", "disponibilidad", "tolerancia",
    "cache", "cola", "broker", "balanceador", "gateway", "proxy",
    "contenedor", "orquestacion", "orquestación", "despliegue", "deploy",
    "monitoreo", "observabilidad", "telemetria", "telemetría", "tracing",
    "contrato", "schema", "versionado", "compatibilidad", "retrocompatibilidad",
]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def generate_claim_id(agent: str, topic: str) -> str:
    raw = f"{agent}-{date.today().isoformat()}-{topic}"
    return raw.lower().replace(" ", "-")


def _extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s\)\]>'\"]+", text)


def _extract_citations(text: str) -> list[str]:
    citations = []
    patterns = [
        r"\[([^\]]+)\]\(https?://[^\)]+\)",
        r"fuente[s]?:\s*([^\n]+)",
        r"ref(?:erencia)?:\s*([^\n]+)",
        r"\[([^\]]+)\]",
        r"source[s]?:\s*([^\n]+)",
    ]
    for p in patterns:
        citations.extend(re.findall(p, text, re.IGNORECASE))
    return [c.strip() for c in citations if len(c.strip()) > 3]


def _extract_arch_terms(text: str) -> dict[str, int]:
    found = {}
    text_lower = text.lower()
    for term in ARCH_TERMS:
        count = len(re.findall(re.escape(term), text_lower))
        if count > 0:
            found[term] = count
    return found


def _compute_factual_score(references: list[str], citations: list[str]) -> dict:
    total_refs = len(references) + len(citations)
    if total_refs == 0:
        return {"veracidad": 20, "coherencia": 30, "total_refs": 0}
    score = min(100, 30 + total_refs * 10)
    coherencia = min(100, 40 + total_refs * 8)
    return {"veracidad": score, "coherencia": coherencia, "total_refs": total_refs}


def _compute_arch_score(terms: dict[str, int], text_length: int) -> dict:
    unique_terms = len(terms)
    total_mentions = sum(terms.values())
    if unique_terms == 0:
        return {"completitud": 10, "reproducibilidad": 20}
    completitud = min(100, 20 + unique_terms * 8)
    reproducibilidad = min(100, 30 + total_mentions * 3)
    return {"completitud": completitud, "reproducibilidad": reproducibilidad}


def _compute_strategic_score(hook_result: dict) -> dict:
    okr_passed = hook_result.get("okr_check", {}).get("passed", False)
    foda_passed = hook_result.get("foda_check", {}).get("passed", False)
    risk_passed = hook_result.get("risk_check", {}).get("passed", False)
    bcg_score = hook_result.get("bcg_result", {}).get("bcg_strategy", 0) if hook_result.get("bcg_result") else 0
    composite = hook_result.get("composite", 0) if hook_result.get("composite") else 0
    veracidad = 60 if okr_passed else 30
    veracidad += 20 if foda_passed else 0
    veracidad += 10 if risk_passed else 0
    veracidad += min(10, int(bcg_score))
    utilidad = min(100, 40 + int(composite) + (10 if okr_passed else 0))
    return {"veracidad": min(100, veracidad), "utilidad": utilidad}


def fase1_aletheia(report_text: str) -> dict:
    urls = _extract_urls(report_text)
    citations = _extract_citations(report_text)
    scores = _compute_factual_score(urls, citations)
    return {
        "agent": "aletheia",
        "phase": 1,
        "label": "Verificación de Factualidad",
        "scores": scores,
        "details": {
            "urls_found": len(urls),
            "citations_found": len(citations),
            "urls": urls[:10],
            "citations": citations[:10],
        },
    }


def fase2_kosmos(report_text: str) -> dict:
    terms = _extract_arch_terms(report_text)
    scores = _compute_arch_score(terms, len(report_text))
    return {
        "agent": "kosmos",
        "phase": 2,
        "label": "Verificación de Coherencia Arquitectónica",
        "scores": scores,
        "details": {
            "unique_arch_terms": len(terms),
            "total_mentions": sum(terms.values()),
            "terms_found": dict(sorted(terms.items(), key=lambda x: -x[1])[:15]),
        },
    }


def fase3_metis(report_path: Path) -> dict:
    hook_path = TOOLS_DIR / "post_output_hook.py"
    if not hook_path.exists():
        return {
            "agent": "metis",
            "phase": 3,
            "label": "Verificación de Alineación Estratégica",
            "scores": {"veracidad": 50, "utilidad": 50},
            "details": {"error": "post_output_hook.py not found"},
            "hook_result": {},
        }
    try:
        result = subprocess.run(
            [sys.executable, str(hook_path), str(report_path), "--checklist", "both"],
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
        hook_result = {}
        okr_check = re.search(r"OKRs:\s*(\d+)\s+found", result.stdout)
        if okr_check:
            hook_result["okr_check"] = {"passed": int(okr_check.group(1)) > 0}
        foda_check = re.search(r"FODA:\s*\{([^}]+)\}", result.stdout)
        if foda_check:
            hook_result["foda_check"] = {"passed": True}
        risk_check = re.search(r"Risks:\s*(\d+)", result.stdout)
        if risk_check:
            hook_result["risk_check"] = {"passed": int(risk_check.group(1)) >= 2}
        bcg_match = re.search(r"BCG:\s*([\d.]+)/10", result.stdout)
        if bcg_match:
            hook_result["bcg_result"] = {"bcg_strategy": float(bcg_match.group(1))}
        output = result.stdout
        composite = 50
        passed_checks = sum(1 for k in ["okr_check", "foda_check", "risk_check"] if k in hook_result and hook_result[k].get("passed"))
        composite += passed_checks * 15
        hook_result["composite"] = min(100, composite)
        hook_result["stdout"] = output[:500]
        hook_result["stderr"] = result.stderr[:500] if result.stderr else ""
        scores = _compute_strategic_score(hook_result)
        return {
            "agent": "metis",
            "phase": 3,
            "label": "Verificación de Alineación Estratégica",
            "scores": scores,
            "details": {
                "exit_code": result.returncode,
                "okr_found": okr_check.group(1) if okr_check else "?",
                "bcg_score": bcg_match.group(1) if bcg_match else "N/A",
            },
            "hook_result": hook_result,
        }
    except subprocess.TimeoutExpired:
        return {
            "agent": "metis",
            "phase": 3,
            "label": "Verificación de Alineación Estratégica",
            "scores": {"veracidad": 30, "utilidad": 30},
            "details": {"error": "post_output_hook timed out"},
            "hook_result": {},
        }
    except Exception as e:
        return {
            "agent": "metis",
            "phase": 3,
            "label": "Verificación de Alineación Estratégica",
            "scores": {"veracidad": 30, "utilidad": 30},
            "details": {"error": str(e)},
            "hook_result": {},
        }


def verify_output(claim_id: str, agent_origin: str, agent_verifier: str, scores: dict, profile: str = "desarrollo", discrepancies: list | None = None) -> tuple[dict, Path]:
    verification = {
        "verification_id": f"v-{date.today().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}",
        "claim_id": claim_id,
        "agent_origin": agent_origin,
        "agent_verifier": agent_verifier,
        "timestamp": datetime.now().isoformat(),
        "profile": profile,
        "scores": scores,
        "evaluations": {k: evaluate(k, v, profile) for k, v in scores.items()},
        "discrepancies": discrepancies or [],
        "evidence_hash": hashlib.sha256(json.dumps(scores, sort_keys=True).encode()).hexdigest()[:16],
        "verifier_notes": "",
    }
    VERIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    path = VERIFICATION_DIR / f"{verification['verification_id']}.json"
    path.write_text(json.dumps(verification, indent=2, ensure_ascii=False), encoding="utf-8")
    return verification, path


def run_verification_chain(outputs: dict, profile: str = "desarrollo") -> list[dict]:
    chain_results = []
    pairs = [
        ("aletheia", "kosmos", ["veracidad", "coherencia"]),
        ("kosmos", "metis", ["completitud", "utilidad"]),
        ("metis", "aletheia", ["veracidad", "reproducibilidad"]),
    ]
    for origin, verifier, dims in pairs:
        if origin in outputs:
            scores = {d: outputs[origin].get(d, 50) for d in dims}
            claim_id = generate_claim_id(origin, "output")
            verification, path = verify_output(claim_id, origin, verifier, scores, profile)
            chain_results.append(verification)
    return chain_results


def _build_score_row(label: str, score: float, threshold: float = 50) -> str:
    passed = score >= threshold
    icon = "✅" if passed else "❌"
    return f"| {label} | {score:.1f}/100 | {'PASS' if passed else 'FAIL'} {icon} |"


def generate_report(fases: list[dict], composite: float, profile: str) -> str:
    now = _now()
    lines = []
    lines.append("# Verification Chain Report")
    lines.append("")
    lines.append(f"**Generated**: {now}")
    lines.append(f"**Profile**: {profile}")
    lines.append(f"**Composite Score**: {composite:.1f}/100")
    lines.append("")
    lines.append("---")
    lines.append("")
    for fase in fases:
        lines.append(f"## Fase {fase['phase']}: {fase['label']} ({fase['agent'].title()})")
        lines.append("")
        scores = fase.get("scores", {})
        lines.append("| Dimensión | Score | Estado |")
        lines.append("|-----------|-------|--------|")
        for dim, val in scores.items():
            if dim in ("veracidad", "coherencia", "completitud", "reproducibilidad", "utilidad"):
                lines.append(f"| {dim.title()} | {val}/100 | {'✅' if val >= 50 else '❌'} |")
        lines.append("")
        details = fase.get("details", {})
        if details:
            lines.append("### Detalles")
            lines.append("")
            for k, v in details.items():
                if isinstance(v, dict):
                    items = "\n".join(f"  - {sk}: {sv}" for sk, sv in v.items())
                    lines.append(f"- **{k}**:\n{items}")
                elif isinstance(v, list):
                    items = "\n".join(f"  - {item}" for item in v)
                    lines.append(f"- **{k}**:\n{items}")
                else:
                    lines.append(f"- **{k}**: {v}")
            lines.append("")
        lines.append("---")
        lines.append("")
    lines.append("## Score Composite")
    lines.append("")
    lines.append(f"| Métrica | Valor |")
    lines.append(f"|---------|-------|")
    lines.append(f"| **Composite** | **{composite:.1f}/100** |")
    if composite >= 70:
        lines.append(f"| **Veredicto** | **✅ APROBADO** |")
    elif composite >= 40:
        lines.append(f"| **Veredicto** | **⚠️ REVISIÓN** |")
    else:
        lines.append(f"| **Veredicto** | **❌ RECHAZADO** |")
    lines.append("")
    return "\n".join(lines)


def run_all_fases(report_path: Path, profile: str) -> list[dict]:
    if not report_path.exists():
        print(f"Error: File not found: {report_path}", file=sys.stderr)
        sys.exit(1)
    text = report_path.read_text(encoding="utf-8")
    f1 = fase1_aletheia(text)
    f2 = fase2_kosmos(text)
    f3 = fase3_metis(report_path)
    return [f1, f2, f3]


def compute_composite_score(fases: list[dict], profile: str) -> float:
    all_scores = {}
    for fase in fases:
        all_scores.update(fase.get("scores", {}))
    if not all_scores:
        return 0.0
    composite, _ = compute_composite(all_scores, profile)
    return composite


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verification Chain — verificación cruzada entre agentes (Aletheia → Kosmos → Metis).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  py -3 .tools/verification_chain.py report.md\n"
            "  py -3 .tools/verification_chain.py report.md --profile produccion\n"
            "  py -3 .tools/verification_chain.py --full\n"
        ),
    )
    parser.add_argument("report_file", nargs="?", default=None, help="Path al reporte markdown a verificar")
    parser.add_argument("--profile", default="desarrollo", choices=["exploracion", "desarrollo", "produccion", "auditoria", "qa"], help="Perfil de evaluación")
    parser.add_argument("--full", action="store_true", help="Ejecuta en modo full (usa el último reporte en cache)")
    args = parser.parse_args()

    if args.full:
        candidates = sorted(VERIFICATION_DIR.glob("*.json")) if VERIFICATION_DIR.exists() else []
        if candidates:
            last = max(candidates, key=lambda p: p.stat().st_mtime)
            data = json.loads(last.read_text(encoding="utf-8"))
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            last_hook = sorted(Path(KAOS_ROOT / ".memory" / "cache").glob("verification_*.md"))
            if last_hook:
                report_path = last_hook[-1]
                fases = run_all_fases(report_path, args.profile)
                composite = compute_composite_score(fases, args.profile)
                report = generate_report(fases, composite, args.profile)
                VERIFICATION_DIR.mkdir(parents=True, exist_ok=True)
                out_path = VERIFICATION_DIR / f"chain-report-{date.today().isoformat()}.md"
                out_path.write_text(report, encoding="utf-8")
                print(report)
                print(f"\n✓ Report saved: {out_path}")
            else:
                print("No verification reports found in cache. Run with a report file first.", file=sys.stderr)
                sys.exit(1)
        return

    if not args.report_file:
        parser.print_help()
        sys.exit(1)

    report_path = Path(args.report_file)
    if not report_path.exists():
        candidates = sorted(Path(KAOS_ROOT / ".memory" / "cache").rglob(args.report_file))
        if candidates:
            report_path = candidates[0]
        else:
            print(f"Error: Report file not found: {args.report_file}", file=sys.stderr)
            sys.exit(1)

    print(f"🔍 Verification Chain iniciada")
    print(f"  Reporte: {report_path}")
    print(f"  Perfil: {args.profile}")
    print()

    fases = run_all_fases(report_path, args.profile)
    composite = compute_composite_score(fases, args.profile)

    for fase in fases:
        scores = fase.get("scores", {})
        dims = ", ".join(f"{k}={v}" for k, v in scores.items())
        print(f"  [{fase['agent'].title()}] Fase {fase['phase']}: {dims}")

    print(f"\n  Score Composite: {composite:.1f}/100")
    print()

    report = generate_report(fases, composite, args.profile)
    VERIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    out_path = VERIFICATION_DIR / f"chain-report-{date.today().isoformat()}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"✓ Reporte guardado: {out_path}")

    for fase in fases:
        claim_id = generate_claim_id(fase["agent"], f"fase-{fase['phase']}")
        verify_output(claim_id, fase["agent"], "verification_chain", fase.get("scores", {}), args.profile)

    print(f"\n{'=' * 50}")
    print(f"  Verification Chain Complete")
    print(f"  Composite: {composite:.1f}/100")
    verdict = "APROBADO" if composite >= 70 else "REVISION" if composite >= 40 else "RECHAZADO"
    print(f"  Veredicto: {verdict}")
    print(f"{'=' * 50}")


def run(report_path: str, profile: str = "desarrollo") -> dict:
    path = Path(report_path)
    if not path.exists():
        return {"error": f"File not found: {report_path}", "composite": 0}
    fases = run_all_fases(path, profile)
    composite = compute_composite_score(fases, profile)
    report = generate_report(fases, composite, profile)
    VERIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    out_path = VERIFICATION_DIR / f"chain-report-{date.today().isoformat()}.md"
    out_path.write_text(report, encoding="utf-8")
    return {
        "composite": composite,
        "fases": fases,
        "report_path": str(out_path),
        "veredicto": "APROBADO" if composite >= 70 else "REVISION" if composite >= 40 else "RECHAZADO",
    }


if __name__ == "__main__":
    main()
