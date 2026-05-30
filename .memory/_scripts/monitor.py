"""Monitor proactivo de scores post-ejecución.

Lee verification reports, compara contra umbrales
de eval-profile.yaml y genera alertas.

Usage:
    python .memory/_scripts/monitor.py check [--file report.md] [--profile desarrollo]
    python .memory/_scripts/monitor.py poll [--profile desarrollo]
    python .memory/_scripts/monitor.py alerts [--last 5]
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
KAOS_ROOT = SCRIPTS_DIR.parent.parent
CACHE_DIR = KAOS_ROOT / ".memory" / "cache"
ALERTS_DIR = CACHE_DIR / "alerts"
SCHEMA_DIR = KAOS_ROOT / ".memory" / "schema"
PROFILES_PATH = SCHEMA_DIR / "eval-profile.yaml"


def _load_profiles() -> dict:
    import yaml
    if not PROFILES_PATH.exists():
        return {"default_profile": "desarrollo", "profiles": {}}
    with open(PROFILES_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {"default_profile": "desarrollo", "profiles": {}}


def _get_thresholds(profile_name: str = None) -> dict:
    profiles_data = _load_profiles()
    profiles = profiles_data.get("profiles", {})
    default = profiles_data.get("default_profile", "desarrollo")
    name = profile_name or default
    profile = profiles.get(name, profiles.get(default, {}))
    return profile.get("thresholds", {})


def _find_report(file_path: str = None) -> Path:
    if file_path:
        path = Path(file_path)
        if path.exists():
            return path
        candidates = sorted(CACHE_DIR.rglob(file_path))
        if candidates:
            return candidates[0]
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    reports = sorted(CACHE_DIR.glob("verification_*.md"), reverse=True)
    if not reports:
        print("Error: No verification reports found in cache.", file=sys.stderr)
        sys.exit(1)
    return reports[0]


def parse_verification_report(file_path: str) -> dict:
    path = _find_report(file_path)
    text = path.read_text(encoding="utf-8")

    result = {
        "source": str(path),
        "generated": "",
        "components": {},
        "overall": None,
        "bcg_strategy": None,
        "okr_health": None,
    }

    gen_match = re.search(r"\*\*Generated\*\*:\s*(.+)", text)
    if gen_match:
        result["generated"] = gen_match.group(1).strip()

    bcg_match = re.search(r"\*\*BCG Strategy\*\*\s*\|\s*([\d.]+)/10", text)
    if bcg_match:
        result["bcg_strategy"] = float(bcg_match.group(1))

    okr_match = re.search(r"\*\*OKR Health\*\*\s*\|\s*([\d.]+)%", text)
    if okr_match:
        result["okr_health"] = float(okr_match.group(1))

    in_overall = False
    for line in text.split("\n"):
        if "## Overall Result" in line:
            in_overall = True
            continue
        if not in_overall:
            continue
        if line.startswith("| **Overall**"):
            m = re.search(r"\|\s*\*\*Overall\*\*\s*\|\s*\*\*([✅❌]+\s*(PASS|FAIL)?)", line)
            if m:
                result["overall"] = "PASS" if "PASS" in m.group(1) else "FAIL"
            break
        if line.startswith("|") and "Component" in line:
            continue
        if "---" in line:
            continue
        if line.startswith("|"):
            m = re.search(r"\|\s*([\w\s/]+?)\s*\|\s*([✅❌])", line)
            if m:
                name = m.group(1).strip()
                status = "PASS" if "✅" in m.group(2) else "FAIL"
                result["components"][name] = status

    return result


def check_scores(file_path: str = None, profile: str = None) -> dict:
    report = parse_verification_report(file_path)
    thresholds = _get_thresholds(profile)
    composite_critical = thresholds.get("composite_critical", 40)

    total = len(report["components"])
    passed = sum(1 for s in report["components"].values() if s == "PASS")
    pass_rate = (passed / total * 100) if total > 0 else 0

    alerts = []
    if pass_rate < composite_critical:
        alerts.append(
            f"Component pass rate {pass_rate:.1f}% "
            f"below critical threshold {composite_critical}%"
        )

    bcg = report.get("bcg_strategy")
    if bcg is not None and bcg < 5:
        alerts.append(
            f"BCG Strategy score {bcg}/10 below acceptable threshold 5/10"
        )

    okr = report.get("okr_health")
    if okr is not None and okr < composite_critical:
        alerts.append(
            f"OKR Health {okr}% below critical threshold {composite_critical}%"
        )

    return {
        "report": report,
        "thresholds": thresholds,
        "total_components": total,
        "passed_components": passed,
        "pass_rate": pass_rate,
        "composite_critical": composite_critical,
        "alerts": alerts,
        "passed": len(alerts) == 0,
    }


def generate_alert(check_result: dict) -> str:
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    path = ALERTS_DIR / f"{date_str}.md"

    lines = [
        f"# Alerta de Monitoreo — {date_str}",
        "",
        f"- **Generado**: {time_str}",
        f"- **Fuente**: {check_result['report']['source']}",
        f"- **Perfil**: {check_result.get('profile', 'desarrollo')}",
        "",
        "## Resultados",
        "",
        "| Métrica | Valor | Umbral | Estado |",
        "|---------|-------|--------|--------|",
        f"| Component Pass Rate | {check_result['pass_rate']:.1f}% | ≥{check_result['composite_critical']}% | "
        f"{'✅' if check_result['passed'] else '❌'} |",
    ]

    bcg = check_result["report"].get("bcg_strategy")
    if bcg is not None:
        lines.append(
            f"| BCG Strategy | {bcg}/10 | ≥5/10 | "
            f"{'✅' if bcg >= 5 else '❌'} |"
        )

    okr = check_result["report"].get("okr_health")
    if okr is not None:
        lines.append(
            f"| OKR Health | {okr}% | ≥{check_result['composite_critical']}% | "
            f"{'✅' if okr >= check_result['composite_critical'] else '❌'} |"
        )

    lines.append("")

    if check_result["alerts"]:
        lines.append("## Alertas")
        lines.append("")
        for a in check_result["alerts"]:
            lines.append(f"- ⚠️ {a}")
        lines.append("")

    lines.append("## Detalle de Componentes")
    lines.append("")
    for comp, status in check_result["report"]["components"].items():
        lines.append(f"- {comp}: {'✅' if status == 'PASS' else '❌'}")

    lines.append("")
    lines.append("---")
    lines.append("*Alerta generada automáticamente por monitor.py*")

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def poll(profile: str = None) -> list[dict]:
    reports = sorted(CACHE_DIR.glob("verification_*.md"))
    if not reports:
        print("No verification reports found in cache.")
        return []

    results = []
    for r in reports:
        result = check_scores(str(r), profile)
        result["profile"] = profile or "desarrollo"
        if not result["passed"]:
            alert_path = generate_alert(result)
            result["alert_path"] = alert_path
            print(
                f"  ⚠️  {r.name}: pass_rate={result['pass_rate']:.1f}% "
                f"(threshold ≥{result['composite_critical']}%) → alert: {alert_path}"
            )
        else:
            print(
                f"  ✅ {r.name}: pass_rate={result['pass_rate']:.1f}% "
                f"(threshold ≥{result['composite_critical']}%)"
            )
        results.append(result)

    return results


def cmd_check(args: argparse.Namespace) -> int:
    result = check_scores(args.file, args.profile)
    r = result["report"]
    print(f"Verification Report: {r['source']}")
    print(f"  Generated: {r.get('generated', 'unknown')}")
    print(f"  Components: {result['passed_components']}/{result['total_components']} passed")
    print(f"  Pass rate: {result['pass_rate']:.1f}% (critical threshold: ≥{result['composite_critical']}%)")
    if r.get("bcg_strategy") is not None:
        print(f"  BCG Strategy: {r['bcg_strategy']}/10")
    if r.get("okr_health") is not None:
        print(f"  OKR Health: {r['okr_health']}%")
    print(f"  Overall: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
    if result["alerts"]:
        print(f"\n  Alertas:")
        for a in result["alerts"]:
            print(f"    ⚠️  {a}")
    return 0 if result["passed"] else 1


def cmd_poll(args: argparse.Namespace) -> int:
    results = poll(args.profile)
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"\nPoll complete: {passed}/{total} reports passed thresholds")
    return 0 if passed == total else 1


def cmd_alerts(args: argparse.Namespace) -> int:
    if not ALERTS_DIR.exists():
        print("No alerts directory found.")
        return 0

    alert_files = sorted(ALERTS_DIR.glob("*.md"), reverse=True)
    if not alert_files:
        print("No alerts found.")
        return 0

    last = args.last
    if last and last > 0:
        alert_files = alert_files[:last]

    print(f"Alertas de monitoreo ({len(alert_files)} mostradas):\n")
    for af in alert_files:
        text = af.read_text(encoding="utf-8")
        title_m = re.search(r"^# (.+)", text)
        title = title_m.group(1) if title_m else af.stem
        alert_count = len(re.findall(r"⚠️", text))
        print(f"  {af.name}")
        print(f"    {title}")
        print(f"    {alert_count} alerta(s)\n")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monitor proactivo de scores post-ejecución.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Comandos:\n"
            "  check   Evaluar un verification report\n"
            "  poll    Evaluar todos los reports y generar alertas\n"
            "  alerts  Listar alertas recientes\n"
            "\n"
            "Ejemplos:\n"
            "  python .memory/_scripts/monitor.py check\n"
            "  python .memory/_scripts/monitor.py check --file verification_output.md\n"
            "  python .memory/_scripts/monitor.py poll\n"
            "  python .memory/_scripts/monitor.py alerts --last 5\n"
        ),
    )
    parser.add_argument("--schedule", choices=["daily", "weekly"], default=None,
                        help="Configurar schedule de monitoreo (interfaz documentada, scheduling pendiente)")

    subparsers = parser.add_subparsers(dest="command")

    check_p = subparsers.add_parser("check", help="Evaluar un verification report")
    check_p.add_argument("--file", default=None, help="Ruta al verification report (por defecto: el más reciente)")
    check_p.add_argument("--profile", default=None, help="Perfil de evaluación (desarrollo, produccion, etc.)")

    poll_p = subparsers.add_parser("poll", help="Evaluar todos los reports y generar alertas")
    poll_p.add_argument("--profile", default=None, help="Perfil de evaluación")

    alerts_p = subparsers.add_parser("alerts", help="Listar alertas recientes")
    alerts_p.add_argument("--last", type=int, default=None, help="Número de alertas a mostrar (por defecto: todas)")

    args = parser.parse_args()

    if args.schedule:
        print(f"Schedule configurado: {args.schedule}")
        print("Nota: el scheduling automático no está implementado. Ejecutar manualmente via cron o Kronos.")
        return 0

    if args.command == "check":
        return cmd_check(args)
    elif args.command == "poll":
        return cmd_poll(args)
    elif args.command == "alerts":
        return cmd_alerts(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
