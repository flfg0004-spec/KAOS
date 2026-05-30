"""
Strategy Feedback Loop — Metis→Kratos communication bridge (Fase 3)

Implementa el contrato strategy-feedback-contract.json para el envío de
iniciativas estratégicas desde Metis a Kratos y la recolección de feedback
de implementación.

Uso:
  py -3 .tools/strategy_feedback.py dispatch --okr-id O1-KR3 --initiative "Optimizar API" --criteria '{"latency": "<200ms"}'
  py -3 .tools/strategy_feedback.py poll --okr-id O1-KR3
  py -3 .tools/strategy_feedback.py feedback --okr-id O1-KR3 --status completed --metrics '{"coverage": 85}'
  py -3 .tools/strategy_feedback.py report --okr-id O1-KR3
  py -3 .tools/strategy_feedback.py list
  py -3 .tools/strategy_feedback.py --help
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

TOOLS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TOOLS_DIR.parent / ".memory" / "_scripts"
KAOS_ROOT = TOOLS_DIR.parent
TRANSFERS_DIR = KAOS_ROOT / ".memory" / "transfers" / "metis_to_kratos"

sys.path.insert(0, str(SCRIPTS_DIR))
from strategy_memory import StrategicMemoryBank


def _ensure_dirs():
    TRANSFERS_DIR.mkdir(parents=True, exist_ok=True)


def _transfer_path(okr_id: str) -> Path:
    safe = okr_id.replace("/", "_").replace("\\", "_")
    return TRANSFERS_DIR / f"{safe}.json"


def _status_path(okr_id: str) -> Path:
    safe = okr_id.replace("/", "_").replace("\\", "_")
    return TRANSFERS_DIR / f"{safe}_feedback.json"


def _load_json(path: Path) -> dict | None:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            return None
    return None


def dispatch_strategy(okr_id: str, initiative: str, criteria: dict | None = None) -> str:
    _ensure_dirs()
    payload = {
        "type": "strategy_feedback",
        "session_id": str(uuid4())[:8],
        "generated_at": datetime.now().isoformat(),
        "okr_id": okr_id,
        "initiative_id": f"I-{okr_id}",
        "initiative_title": initiative,
        "completion": {
            "percentage": 0,
            "status": "not_started",
        },
        "success_criteria": [],
        "status": "dispatched",
        "source": "metis",
    }
    if criteria:
        payload["success_criteria"] = [
            {"criterion": k, "met": False, "actual_value": ""}
            for k in criteria.keys()
        ]
    criteria_file = _transfer_path(okr_id)
    criteria_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Iniciativa despachada a Kratos")
    print(f"  OKR ID: {okr_id}")
    print(f"  Initiative: {initiative}")
    print(f"  File: {criteria_file}")
    if criteria:
        print(f"  Criteria: {json.dumps(criteria, ensure_ascii=False)}")
    return str(criteria_file)


def submit_feedback(okr_id: str, status: str, metrics: dict | None = None, blockers: list | None = None) -> str:
    _ensure_dirs()
    transfer = _load_json(_transfer_path(okr_id))
    if transfer is None:
        print(f"Error: No dispatch found for OKR ID '{okr_id}'. Run dispatch first.", file=sys.stderr)
        sys.exit(1)
    feedback = {
        "type": "strategy_feedback",
        "session_id": transfer.get("session_id", str(uuid4())[:8]),
        "generated_at": datetime.now().isoformat(),
        "okr_id": okr_id,
        "initiative_id": transfer.get("initiative_id", f"I-{okr_id}"),
        "initiative_title": transfer.get("initiative_title", ""),
        "completion": {
            "percentage": 100 if status in ("completed", "complete") else 50 if status == "partial" else 0,
            "status": status,
            "completed_at": datetime.now().isoformat() if status in ("completed", "complete") else None,
        },
        "code_quality": {
            "test_coverage": (metrics or {}).get("coverage", 0),
            "cyclomatic_complexity": (metrics or {}).get("complexity", 0),
            "lint_errors": (metrics or {}).get("lint_errors", 0),
            "tech_debt_minutes": (metrics or {}).get("tech_debt", 0),
            "code_smells": (metrics or {}).get("code_smells", 0),
            "duplication_percentage": (metrics or {}).get("duplication", 0),
        },
        "performance": {
            "latency_ms": (metrics or {}).get("latency", 0),
            "throughput_rps": (metrics or {}).get("throughput", 0),
            "memory_mb": (metrics or {}).get("memory", 0),
            "error_rate": (metrics or {}).get("error_rate", 0),
        },
        "blockers": blockers or [],
        "estimated_remaining_effort": {
            "hours": (metrics or {}).get("remaining_hours", 0),
            "confidence": (metrics or {}).get("confidence", "media"),
        },
        "success_criteria_met": [],
        "recommendations": [],
        "status": "feedback_received",
        "source": "kratos",
    }
    previous_criteria = transfer.get("success_criteria", [])
    feedback["success_criteria_met"] = [
        {
            "criterion": c.get("criterion", ""),
            "met": (metrics or {}).get(c.get("criterion", ""), False) if isinstance((metrics or {}).get(c.get("criterion", "")), bool) else False,
            "actual_value": str((metrics or {}).get(c.get("criterion", ""), "")),
        }
        for c in previous_criteria
    ]
    status_file = _status_path(okr_id)
    status_file.write_text(json.dumps(feedback, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Feedback recibido de Kratos")
    print(f"  OKR ID: {okr_id}")
    print(f"  Status: {status}")
    if metrics:
        print(f"  Metrics: {json.dumps(metrics, ensure_ascii=False)}")
    return str(status_file)


def poll_feedback(okr_id: str) -> dict | None:
    feedback = _load_json(_status_path(okr_id))
    if feedback is None:
        transfer = _load_json(_transfer_path(okr_id))
        if transfer:
            print(f"⏳ Iniciativa '{okr_id}' despachada pero sin feedback aún.")
            print(f"  Status: {transfer.get('status', 'dispatched')}")
            return None
        print(f"ℹ️  No se encontró la iniciativa '{okr_id}'.")
        return None
    print(f"✓ Feedback encontrado para '{okr_id}':")
    print(f"  Status: {feedback.get('completion', {}).get('status', '?')}")
    print(f"  Completion: {feedback.get('completion', {}).get('percentage', 0)}%")
    quality = feedback.get("code_quality", {})
    if quality:
        print(f"  Coverage: {quality.get('test_coverage', 'N/A')}%")
        print(f"  Lint errors: {quality.get('lint_errors', 'N/A')}")
    perf = feedback.get("performance", {})
    if perf:
        print(f"  Latency: {perf.get('latency_ms', 'N/A')}ms")
    blockers = feedback.get("blockers", [])
    if blockers:
        print(f"  Blockers: {len(blockers)}")
        for b in blockers:
            print(f"    - {b.get('description', '?')} [{b.get('severity', '?')}]")
    return feedback


def generate_report(okr_id: str) -> str:
    transfer = _load_json(_transfer_path(okr_id))
    feedback = _load_json(_status_path(okr_id))
    now = datetime.now().isoformat(timespec="minutes")
    lines = []
    lines.append(f"# Strategy Feedback Report — {okr_id}")
    lines.append("")
    lines.append(f"**Generated**: {now}")
    lines.append("")
    if transfer is None and feedback is None:
        lines.append("ℹ️ No strategy data found for this OKR ID.")
        return "\n".join(lines)
    lines.append("## Dispatch Info")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    if transfer:
        lines.append(f"| Initiative | {transfer.get('initiative_title', '?')} |")
        lines.append(f"| Dispatched | {transfer.get('generated_at', '?')[:16]} |")
        lines.append(f"| Session | {transfer.get('session_id', '?')} |")
        criteria = transfer.get("success_criteria", [])
        if criteria:
            lines.append(f"| Criteria | {len(criteria)} defined |")
    if feedback:
        lines.append(f"| Feedback | {feedback.get('generated_at', '?')[:16]} |")
        lines.append(f"| Status | {feedback.get('completion', {}).get('status', '?')} |")
        lines.append(f"| Completion | {feedback.get('completion', {}).get('percentage', 0)}% |")
    lines.append("")
    if feedback:
        quality = feedback.get("code_quality", {})
        if any(quality.values()):
            lines.append("## Code Quality Metrics")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Test Coverage | {quality.get('test_coverage', 'N/A')}% |")
            lines.append(f"| Cyclomatic Complexity | {quality.get('cyclomatic_complexity', 'N/A')} |")
            lines.append(f"| Lint Errors | {quality.get('lint_errors', 'N/A')} |")
            lines.append(f"| Tech Debt (min) | {quality.get('tech_debt_minutes', 'N/A')} |")
            lines.append(f"| Code Smells | {quality.get('code_smells', 'N/A')} |")
            lines.append(f"| Duplication | {quality.get('duplication_percentage', 'N/A')}% |")
            lines.append("")
        perf = feedback.get("performance", {})
        if any(perf.values()):
            lines.append("## Performance Metrics")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Latency | {perf.get('latency_ms', 'N/A')} ms |")
            lines.append(f"| Throughput | {perf.get('throughput_rps', 'N/A')} rps |")
            lines.append(f"| Memory | {perf.get('memory_mb', 'N/A')} MB |")
            lines.append(f"| Error Rate | {perf.get('error_rate', 'N/A')}% |")
            lines.append("")
        blockers = feedback.get("blockers", [])
        if blockers:
            lines.append("## Blockers")
            lines.append("")
            lines.append("| Description | Severity | Status |")
            lines.append("|-------------|----------|--------|")
            for b in blockers:
                lines.append(f"| {b.get('description', '?')} | {b.get('severity', '?')} | {b.get('status', 'open')} |")
            lines.append("")
        criteria_met = feedback.get("success_criteria_met", [])
        if criteria_met:
            lines.append("## Success Criteria")
            lines.append("")
            lines.append("| Criterion | Met | Actual |")
            lines.append("|-----------|-----|--------|")
            for c in criteria_met:
                met_icon = "✅" if c.get("met") else "❌"
                lines.append(f"| {c.get('criterion', '?')} | {met_icon} | {c.get('actual_value', '')} |")
            lines.append("")
        recommendations = feedback.get("recommendations", [])
        if recommendations:
            lines.append("## Recommendations")
            lines.append("")
            for r in recommendations:
                lines.append(f"- **{r.get('priority', 'media').upper()}**: {r.get('action', '')}")
            lines.append("")
    lines.append("---")
    lines.append(f"*Report generated by strategy_feedback.py*")
    return "\n".join(lines)


def list_initiatives() -> list[dict]:
    _ensure_dirs()
    items = []
    for f in sorted(TRANSFERS_DIR.glob("*.json")):
        data = _load_json(f)
        if data:
            is_feedback = "_feedback" in f.name
            items.append({
                "okr_id": data.get("okr_id", f.stem),
                "file": f.name,
                "type": "feedback" if is_feedback else "dispatch",
                "initiative": data.get("initiative_title", "?"),
                "status": data.get("completion", {}).get("status", data.get("status", "?")),
                "updated": data.get("generated_at", "?")[:16],
            })
    return items


def monitor_execution(okr_id: str, actual_progress: float) -> dict:
    transfer = _load_json(_transfer_path(okr_id))
    if transfer is None:
        print(f"Error: No dispatch found for OKR ID '{okr_id}'.", file=sys.stderr)
        sys.exit(1)
    expected_pct = transfer.get("completion", {}).get("percentage", 0)
    expected_progress = expected_pct / 100.0
    deviation = abs(actual_progress - expected_progress)
    deviation_pct = deviation * 100
    threshold = 20.0
    alert = deviation_pct > threshold
    result = {
        "okr_id": okr_id,
        "initiative": transfer.get("initiative_title", ""),
        "expected_progress": round(expected_progress, 4),
        "actual_progress": round(actual_progress, 4),
        "deviation_pct": round(deviation_pct, 2),
        "threshold_pct": threshold,
        "alert": alert,
        "status": "ALERT" if alert else "ON_TRACK",
        "message": (
            f"Desviación del {deviation_pct:.1f}% supera el umbral del {threshold:.0f}%."
            if alert
            else f"Progreso dentro del umbral ({deviation_pct:.1f}% < {threshold:.0f}%)."
        ),
    }
    print(f"Monitor: {okr_id}")
    print(f"  Expected: {expected_progress:.1%}  Actual: {actual_progress:.1%}")
    print(f"  Deviation: {deviation_pct:.1f}%  Threshold: {threshold:.0f}%")
    if alert:
        print(f"  \u26a0\ufe0f  ALERT: {result['message']}")
    else:
        print(f"  \u2705 {result['message']}")
    return result


def rephase_strategy(okr_id: str, new_context: dict) -> dict:
    transfer = _load_json(_transfer_path(okr_id))
    if transfer is None:
        print(f"Error: No dispatch found for OKR ID '{okr_id}'.", file=sys.stderr)
        sys.exit(1)
    bank = StrategicMemoryBank()
    content = {
        "previous_initiative": transfer.get("initiative_title", ""),
        "previous_okr_id": okr_id,
        "previous_session_id": transfer.get("session_id", ""),
        "updated_context": new_context,
    }
    sid = bank.store(new_context, content, "rephase")
    analysis = {"rephase_id": sid, "okr_id": okr_id, "context_keys": list(new_context.keys())}
    if "variables" in new_context or "key_results" in new_context:
        try:
            sys.path.insert(0, str(TOOLS_DIR))
            from simulate import SimulationEngine
            engine = SimulationEngine()
            results = engine.evaluate_okrs(new_context)
            analysis["simulation_results"] = results
        except Exception as e:
            analysis["simulation_error"] = str(e)
    print(f"Rephase stored for {okr_id}: strategy id={sid}")
    print(f"  Context includes: {', '.join(analysis['context_keys'])}")
    if "simulation_results" in analysis:
        for r in analysis["simulation_results"]:
            print(f"  {r.get('objective', '?')}: P(success)={r.get('combined_probability', 0):.2%}")
    return analysis


def detect_dead_plans(days_threshold: int = 14) -> list[dict]:
    _ensure_dirs()
    now = datetime.now()
    deadline = now - timedelta(days=days_threshold)
    dead = []
    for f in sorted(TRANSFERS_DIR.glob("*.json")):
        if "_feedback" in f.name:
            continue
        data = _load_json(f)
        if data is None:
            continue
        okr_id = data.get("okr_id", f.stem.replace("_feedback", ""))
        generated_str = data.get("generated_at", "")
        try:
            generated_dt = datetime.fromisoformat(generated_str)
        except (ValueError, TypeError):
            continue
        feedback_path = _status_path(okr_id)
        has_feedback = feedback_path.exists()
        if not has_feedback and generated_dt < deadline:
            days_old = (now - generated_dt).days
            dead.append({
                "okr_id": okr_id,
                "initiative": data.get("initiative_title", "?"),
                "dispatched_at": generated_str[:19],
                "days_without_feedback": days_old,
                "threshold_days": days_threshold,
            })
    if dead:
        print(f"Found {len(dead)} dead plan(s) (> {days_threshold} days without feedback):")
        for d in dead:
            print(f"  \u2620\ufe0f  {d['okr_id']}: {d['initiative']} ({d['days_without_feedback']}d, since {d['dispatched_at']})")
    else:
        print(f"No dead plans found. All initiatives have feedback or are within {days_threshold} days.")
    return dead


def learning_loop(okr_id: str, outcome_score: float, factors: dict) -> dict:
    transfer = _load_json(_transfer_path(okr_id))
    if transfer is None:
        transfer = _load_json(_status_path(okr_id))
    context = {
        "okr_id": okr_id,
        "source": "learning_loop",
        "factors": factors,
    }
    if transfer:
        context["initiative_title"] = transfer.get("initiative_title", "")
        context["previous_status"] = transfer.get("completion", {}).get("status", transfer.get("status", ""))
    content = {
        "okr_id": okr_id,
        "outcome_score": outcome_score,
        "factors": factors,
        "timestamp": datetime.now().isoformat(),
    }
    bank = StrategicMemoryBank()
    sid = bank.store(context, content, "learning_loop", outcome_score=outcome_score)
    result = {
        "stored_id": sid,
        "okr_id": okr_id,
        "outcome_score": outcome_score,
    }
    print(f"Learning loop stored: okr_id={okr_id} score={outcome_score}/10 id={sid}")
    if outcome_score >= 7.0:
        print(f"  \U0001f31f High outcome ({outcome_score}/10) — pattern reinforced.")
    elif outcome_score < 4.0:
        print(f"  \u26a0\ufe0f Low outcome ({outcome_score}/10) — consider strategy adjustment.")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Strategy Feedback Loop — Metis→Kratos communication bridge.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  strategy_feedback.py dispatch --okr-id O1-KR3 --initiative \"Optimizar API\" --criteria '{\"latency\": \"<200ms\"}'\n"
            "  strategy_feedback.py poll --okr-id O1-KR3\n"
            "  strategy_feedback.py feedback --okr-id O1-KR3 --status completed --metrics '{\"coverage\": 85}'\n"
            "  strategy_feedback.py report --okr-id O1-KR3\n"
            "  strategy_feedback.py list\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    dispatch_parser = subparsers.add_parser("dispatch", help="Despachar iniciativa estratégica a Kratos")
    dispatch_parser.add_argument("--okr-id", required=True, help="ID del OKR (ej: O1-KR3)")
    dispatch_parser.add_argument("--initiative", required=True, help="Nombre de la iniciativa")
    dispatch_parser.add_argument("--criteria", default=None, help="JSON con criterios de éxito")

    poll_parser = subparsers.add_parser("poll", help="Consultar estado de feedback de Kratos")
    poll_parser.add_argument("--okr-id", required=True, help="ID del OKR")

    feedback_parser = subparsers.add_parser("feedback", help="Enviar feedback desde Kratos a Metis")
    feedback_parser.add_argument("--okr-id", required=True, help="ID del OKR")
    feedback_parser.add_argument("--status", required=True, choices=["completed", "partial", "blocked", "not_started"], help="Estado de completitud")
    feedback_parser.add_argument("--metrics", default=None, help="JSON con métricas de implementación")
    feedback_parser.add_argument("--blockers", default=None, help="JSON con lista de blockers")

    report_parser = subparsers.add_parser("report", help="Generar reporte markdown de una iniciativa")
    report_parser.add_argument("--okr-id", required=True, help="ID del OKR")

    list_parser = subparsers.add_parser("list", help="Listar todas las iniciativas")

    monitor_parser = subparsers.add_parser("monitor", help="Monitorear progreso vs planificado")
    monitor_parser.add_argument("--okr-id", required=True, help="ID del OKR")
    monitor_parser.add_argument("--progress", required=True, type=float, help="Progreso actual (0.0-1.0)")

    rephase_parser = subparsers.add_parser("rephase", help="Generar plan alternativo basado en nuevo contexto")
    rephase_parser.add_argument("--okr-id", required=True, help="ID del OKR")
    rephase_parser.add_argument("--context", required=True, help="JSON con nuevo contexto (variables, key_results, etc.)")

    detect_parser = subparsers.add_parser("detect-dead", help="Detectar planes sin feedback por mas de N dias")
    detect_parser.add_argument("--days", type=int, default=14, help="Umbral de dias sin feedback (default: 14)")

    learn_parser = subparsers.add_parser("learn", help="Almacenar leccion aprendida de un OKR")
    learn_parser.add_argument("--okr-id", required=True, help="ID del OKR")
    learn_parser.add_argument("--outcome", required=True, type=float, help="Outcome score (0-10)")
    learn_parser.add_argument("--factors", default=None, help="JSON con factores clave")

    args = parser.parse_args()

    if args.command == "dispatch":
        criteria = json.loads(args.criteria) if args.criteria else None
        dispatch_strategy(args.okr_id, args.initiative, criteria)

    elif args.command == "poll":
        poll_feedback(args.okr_id)

    elif args.command == "feedback":
        metrics = json.loads(args.metrics) if args.metrics else None
        blockers = json.loads(args.blockers) if args.blockers else None
        submit_feedback(args.okr_id, args.status, metrics, blockers)

    elif args.command == "report":
        report = generate_report(args.okr_id)
        print(report)
        report_dir = KAOS_ROOT / ".memory" / "cache" / "strategy"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"strategy-feedback-{args.okr_id}.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"\n✓ Report saved: {report_path}")

    elif args.command == "list":
        items = list_initiatives()
        if not items:
            print("No initiatives found.")
            return
        print(f"{'OKR ID':<15} {'Initiative':<35} {'Type':<12} {'Status':<18} {'Updated':<20}")
        print("-" * 100)
        for item in items:
            print(f"{item['okr_id']:<15} {item['initiative'][:33]:<35} {item['type']:<12} {item['status']:<18} {item['updated']:<20}")

    elif args.command == "monitor":
        monitor_execution(args.okr_id, args.progress)

    elif args.command == "rephase":
        context = json.loads(args.context) if isinstance(args.context, str) else args.context
        rephase_strategy(args.okr_id, context)

    elif args.command == "detect-dead":
        detect_dead_plans(args.days)

    elif args.command == "learn":
        factors = json.loads(args.factors) if args.factors else {}
        learning_loop(args.okr_id, args.outcome, factors)


if __name__ == "__main__":
    main()
