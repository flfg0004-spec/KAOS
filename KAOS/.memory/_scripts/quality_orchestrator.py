"""Quality Sentinel — Orquestador central de herramientas de calidad de KAOS.

Pipeline: health_check -> post_output_hook -> session_runner -> verification_chain -> monitor -> dashboard_populate

CLI:
  py -3 .memory/_scripts/quality_orchestrator.py run [--profile produccion] [--output-file <report>]
  py -3 .memory/_scripts/quality_orchestrator.py status
  py -3 .memory/_scripts/quality_orchestrator.py --help
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
KAOS_ROOT = SCRIPT_DIR.parents[1]
TOOLS_DIR = KAOS_ROOT / ".tools"
CACHE_DIR = KAOS_ROOT / ".memory" / "cache"
STATE_FILE = CACHE_DIR / "quality_orchestrator_state.json"

sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

from verification_chain import run as vc_run
from session_runner import cmd_smoke, cmd_functional
from health_check import cmd_run as hc_run, run_checks, generate_markdown
from monitor import poll as mon_poll
from dashboard_populate import main as dashboard_main


PIPELINE_STAGES = [
    "health_check",
    "post_output_hook",
    "session_runner",
    "verification_chain",
    "monitor",
    "dashboard_populate",
]


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"last_run": None, "stages": {}, "pipeline_status": "never_run"}


def _save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def _run_stage(name, fn, *args, **kwargs):
    result = {"stage": name, "status": "running", "started_at": _now(), "finished_at": None, "error": None, "details": None}
    try:
        value = fn(*args, **kwargs)
        result["status"] = "success"
        result["details"] = str(value)[:500] if value else "completed"
    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
    result["finished_at"] = _now()
    return result


def run_health_check():
    report = run_checks()
    md = generate_markdown(report)
    return f"ok={report['summary']['ok']}, warning={report['summary']['warning']}, error={report['summary']['error']}"


def run_post_output_hook(output_file):
    sys.path.insert(0, str(TOOLS_DIR))
    from post_output_hook import load_output, check_okrs, check_foda, check_roadmap, check_risks, run_bcg, generate_report
    text = load_output(output_file)
    okr = check_okrs(text)
    foda = check_foda(text)
    rdm = check_roadmap(text)
    rsk = check_risks(text)
    bcg = run_bcg(text) if okr["count"] > 0 else None
    report = generate_report(okr, foda, rdm, rsk, bcg, "both", output_file)
    report_dir = CACHE_DIR / "verification"
    report_dir.mkdir(parents=True, exist_ok=True)
    out_path = report_dir / f"hook_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    out_path.write_text(report, encoding="utf-8")
    return f"report saved: {out_path}, okr_passed={okr['passed']}, foda_passed={foda['passed']}"


def run_smoke(profile):
    result = cmd_smoke(profile)
    return f"smoke_{'passed' if result else 'failed'}"


def run_functional(profile):
    result = cmd_functional(profile)
    composite = result.get("composite", "N/A") if isinstance(result, dict) else "N/A"
    return f"functional_composite={composite}"


def run_verification(output_file, profile):
    if not output_file or output_file == "auto":
        reports = sorted((CACHE_DIR / "verification").glob("hook_report_*.md"), reverse=True)
        if not reports:
            reports = sorted(CACHE_DIR.glob("verification_*.md"), reverse=True)
        if reports:
            output_file = str(reports[0])
        else:
            return "skipped: no report file available"
    result = vc_run(output_file, profile)
    return f"composite={result.get('composite', 'N/A')}, veredicto={result.get('veredicto', 'N/A')}"


def run_monitor():
    results = mon_poll()
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    return f"passed={passed}/{total}"


def run_dashboard():
    import sys as _sys
    _saved = _sys.argv
    _sys.argv = ["dashboard_populate.py"]
    try:
        dashboard_main()
        return "dashboard_populated"
    except Exception as e:
        return f"dashboard_error: {e}"
    finally:
        _sys.argv = _saved


def run_pipeline(profile="desarrollo", output_file=None):
    print(f"\n{'=' * 60}")
    print(f"  Quality Sentinel Pipeline")
    print(f"  Profile: {profile}")
    print(f"  Output file: {output_file or '(none - some stages may be skipped)'}")
    print(f"  Started: {_now()}")
    print(f"{'=' * 60}\n")

    state = _load_state()
    state["last_run"] = _now()
    state["pipeline_status"] = "running"
    state["stages"] = {}
    _save_state(state)

    pipeline = [
        ("health_check", run_health_check),
        ("post_output_hook", lambda: run_post_output_hook(output_file) if output_file else "skipped: no output_file"),
        ("session_runner", lambda: run_smoke(profile)),
        ("verification_chain", lambda: run_verification(output_file, profile)),
        ("monitor", run_monitor),
        ("dashboard_populate", run_dashboard),
    ]

    all_passed = True
    for stage_name, stage_fn in pipeline:
        print(f"  [{stage_name}] Running...", end=" ", flush=True)
        start = time.time()
        result = _run_stage(stage_name, stage_fn)
        elapsed = time.time() - start

        if result["status"] == "success":
            print(f"✅ ({elapsed:.1f}s)")
            print(f"    -> {result['details']}")
        elif result["status"] == "failed":
            all_passed = False
            print(f"❌ ({elapsed:.1f}s)")
            print(f"    -> Error: {result['error']}")
        else:
            print(f"  {result['details']}")

        state["stages"][stage_name] = result
        _save_state(state)

    state["pipeline_status"] = "passed" if all_passed else "completed_with_failures"
    _save_state(state)

    print(f"\n{'=' * 60}")
    print(f"  Pipeline complete: {state['pipeline_status']}")
    print(f"  Finished: {_now()}")
    print(f"{'=' * 60}\n")

    return state


def cmd_status():
    state = _load_state()
    if state["last_run"] is None:
        print("No pipeline runs recorded yet.")
        return

    print(f"\nQuality Sentinel — Pipeline Status")
    print(f"{'=' * 60}")
    print(f"  Last run: {state['last_run']}")
    print(f"  Status: {state['pipeline_status']}")
    print()

    for stage_name in PIPELINE_STAGES:
        s = state.get("stages", {}).get(stage_name, {})
        status = s.get("status", "never_run")
        icon = {"success": "✅", "failed": "❌", "running": "⏳", "never_run": "⬜"}.get(status, "❓")
        error = f" - {s.get('error', '')}" if s.get("error") else ""
        print(f"  {icon} {stage_name}: {status}{error}")

    print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Quality Sentinel — Orquestador central de herramientas de calidad de KAOS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Comandos:\n"
            "  run     Ejecuta el pipeline completo de calidad\n"
            "  status  Muestra estado del ultimo pipeline ejecutado\n"
            "\n"
            "Ejemplos:\n"
            "  py -3 .memory/_scripts/quality_orchestrator.py run\n"
            "  py -3 .memory/_scripts/quality_orchestrator.py run --profile produccion\n"
            "  py -3 .memory/_scripts/quality_orchestrator.py run --output-file reporte.md\n"
            "  py -3 .memory/_scripts/quality_orchestrator.py status\n"
        ),
    )
    parser.add_argument("command", nargs="?", default=None, help="Comando: run, status")
    parser.add_argument("--profile", default="desarrollo", help="Perfil de evaluacion (exploracion, desarrollo, produccion, auditoria, qa)")
    parser.add_argument("--output-file", default=None, help="Ruta al archivo de reporte para post_output_hook y verification_chain")

    args = parser.parse_args()

    if args.command == "run":
        run_pipeline(args.profile, args.output_file)
    elif args.command == "status":
        cmd_status()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
