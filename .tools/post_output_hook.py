"""Post-Output Hook — verify Metis strategic outputs for completeness and quality.

Usage:
    py -3 .tools/post_output_hook.py <output_file>
    py -3 .tools/post_output_hook.py <output_file> --checklist quality
    py -3 .tools/post_output_hook.py <output_file> --checklist strategy
    py -3 .tools/post_output_hook.py <output_file> --checklist both
    py -3 .tools/post_output_hook.py <output_file> --monitor
    py -3 .tools/post_output_hook.py --help

The hook parses the last Metis output, runs structural checks (OKR
integrity, FODA completeness, Roadmap 3-horizons, risk identification),
executes BCG evaluation when OKRs are present, and produces a markdown
verification report.

Use --monitor to also run the proactive monitor check on the generated
report (compares scores against eval-profile.yaml thresholds).
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

CAUSAL_AVAILABLE = False
try:
    from causal_graph import CausalModeler
    CAUSAL_AVAILABLE = True
except ImportError:
    pass

TOOLS_DIR = Path(__file__).resolve().parent
KAOS_ROOT = TOOLS_DIR.parent
SCRIPTS_DIR = KAOS_ROOT / ".memory" / "_scripts"
CACHE_DIR = KAOS_ROOT / ".memory" / "cache"

sys.path.insert(0, str(SCRIPTS_DIR))
try:
    from lib.bcg_evaluator import evaluate_okrs, evaluate_strategy
except ImportError:
    sys.path.insert(0, str(SCRIPTS_DIR / "lib"))
    from bcg_evaluator import evaluate_okrs, evaluate_strategy


def load_output(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        candidates = sorted(CACHE_DIR.rglob(file_path))
        if candidates:
            path = candidates[0]
        else:
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
    return path.read_text(encoding="utf-8")


def parse_okrs(text: str) -> list[dict]:
    okrs = []
    sections = re.split(r"\n(?=##\s+O\d+:)", text)
    for section in sections:
        obj_match = re.search(r"\*\*Objective\*\*:\s*(.*)", section)
        if not obj_match:
            continue
        objective = obj_match.group(1).strip()
        krs = re.findall(r"\*\s*(KR\d+.*?)(?:\n|$)", section)
        if not krs:
            krs = re.findall(r"-\s*(KR\d+.*)", section)
        okrs.append({"objective": objective, "key_results": krs})
    if not okrs:
        data = try_parse_json(text)
        if data:
            raw = data if isinstance(data, list) else data.get("okrs", [])
            okrs = [
                {"objective": o.get("objective", ""), "key_results": o.get("key_results", [])}
                for o in raw if isinstance(o, dict)
            ]
    return okrs


def try_parse_json(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


def check_okrs(text: str) -> dict:
    okrs = parse_okrs(text)
    result = {"count": len(okrs), "kr_targets": 0, "kr_no_target": [], "passed": False}
    if not okrs:
        return result
    for okr in okrs:
        obj = okr.get("objective", "")
        has_baseline = bool(re.search(r"\d+[%x]|de\s+\d+|baseline|actual", obj, re.IGNORECASE))
        has_target = bool(re.search(r"\d+[%x]|a\s+\d+|target|goal|\+", obj, re.IGNORECASE))
        for kr in okr.get("key_results", []):
            if re.search(r"\d+[%x/]|alcanzar|llegar a|reducir a|aumentar a", str(kr)):
                result["kr_targets"] += 1
            else:
                result["kr_no_target"].append(str(kr)[:80])
    result["passed"] = (
        result["count"] >= 1
        and result["kr_targets"] >= 1
        and len(result["kr_no_target"]) <= result["kr_targets"]
    )
    return result


def check_foda(text: str) -> dict:
    quadrants = {
        "strengths": ["strength", "fortaleza", "strengths"],
        "weaknesses": ["weakness", "debilidad", "weaknesses"],
        "opportunities": ["opportunit", "oportunidad", "opportunities"],
        "threats": ["threat", "amenaza", "threats"],
    }
    found = {}
    for qname, keywords in quadrants.items():
        items = []
        for kw in keywords:
            pattern = rf"(?:^|\n)#{{1,3}}\s+{kw}\s*\n(.*?)(?=\n#|\Z)"
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                block = match.group(1)
                items = re.findall(r"^\s*[-*]\s+(.+)", block, re.MULTILINE)
                break
        if not items:
            for kw in keywords:
                pattern = rf'"{kw}"\s*:\s*\[(.*?)\]'
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    items = re.findall(r'"([^"]+)"', match.group(1))
                    break
        found[qname] = items
    all_present = all(len(v) >= 3 for v in found.values())
    return {
        "quadrants": found,
        "counts": {k: len(v) for k, v in found.items()},
        "all_quadrants_min_3": all_present,
        "passed": all_present,
    }


def check_roadmap(text: str) -> dict:
    horizons = {"h1": [], "h2": [], "h3": []}
    for hid in ["h1", "h2", "h3"]:
        pattern = rf"(?:^|\n)#{{1,3}}\s+{hid}[^#]*?(?=\n#|\Z)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            milestones = re.findall(r"[-*]\s+(.+?)(?:\n|$)", match.group(0))
            horizons[hid] = milestones
    data = try_parse_json(text)
    if data and isinstance(data, dict):
        hdata = data.get("horizons", data)
        for hid in horizons:
            for entry in (hdata.get(hid, hdata.get(hid.upper(), [])) if isinstance(hdata, dict) else []):
                if isinstance(entry, dict):
                    initiatives = entry.get("initiatives", [])
                    if isinstance(initiatives, list):
                        horizons[hid].extend(initiatives)
                elif isinstance(entry, str):
                    horizons[hid].append(entry)
    has_all = all(len(horizons[h]) > 0 for h in horizons)
    return {
        "horizons": {k: len(v) for k, v in horizons.items()},
        "sample_items": {k: v[:3] for k, v in horizons.items()},
        "all_horizons_present": has_all,
        "passed": has_all,
    }


def check_risks(text: str) -> dict:
    risks = []
    risk_section = re.search(
        r"(?:^|\n)#{1,3}\s+(?:risks?|riesgos?|risk matrix)[^#]*?(?=\n#|\Z)",
        text, re.IGNORECASE | re.DOTALL,
    )
    if risk_section:
        block = risk_section.group(0)
        items = re.findall(r"[-*]\s+(.*(?:\n\s+.*)*)", block)
        risks = [re.sub(r"\n\s+", " ", item).strip() for item in items if item.strip()]
    data = try_parse_json(text)
    if data and isinstance(data, dict):
        for r in data.get("risks", []):
            if isinstance(r, dict):
                risks.append(f"{r.get('risk', '')} [{r.get('probability','?')}/{r.get('impact','?')}]")
            elif isinstance(r, str):
                risks.append(r)
    with_mitigation = 0
    for r in risks:
        if re.search(r"mitigaci[oó]n|mitigation|contramedida|countermeasure|acci[oó]n|plan", r, re.IGNORECASE):
            with_mitigation += 1
    return {
        "total": len(risks),
        "with_mitigation": with_mitigation,
        "items": risks[:10],
        "passed": len(risks) >= 2 and with_mitigation >= 1,
    }


def run_bcg(text: str) -> dict:
    okrs = parse_okrs(text)
    strategy_result = evaluate_strategy(text)
    okr_result = evaluate_okrs(okrs) if okrs else {"score_100": 0, "passed": False, "total_okrs": 0}
    return {
        "bcg_strategy": strategy_result.get("total_score_10", 0),
        "bcg_passed": strategy_result.get("passed", False),
        "okr_health": okr_result.get("score_100", 0),
        "okr_passed": okr_result.get("passed", False),
        "okr_count": okr_result.get("total_okrs", 0),
        "dimensions": strategy_result.get("dimensions", {}),
    }


def generate_report(
    okr_check: dict,
    foda_check: dict,
    roadmap_check: dict,
    risk_check: dict,
    bcg_result: dict | None,
    checklist_type: str,
    source_file: str,
    simulation_result: list | None = None,
    causal_report: str | None = None,
) -> str:
    now = datetime.now().isoformat(timespec="minutes")
    report = []
    report.append(f"# Verification Report — Metis Post-Output Hook")
    report.append(f"")
    report.append(f"- **Source**: `{source_file}`")
    report.append(f"- **Checklist**: {checklist_type}")
    report.append(f"- **Generated**: {now}")
    report.append(f"")
    report.append(f"## 1. OKR Integrity Check")
    report.append(f"")
    report.append(f"| Metric | Value |")
    report.append(f"|--------|-------|")
    report.append(f"| OKRs found | {okr_check['count']} |")
    report.append(f"| KRs with numeric target | {okr_check['kr_targets']} |")
    report.append(f"| KRs without target | {len(okr_check['kr_no_target'])} |")
    report.append(f"| **Status** | {'✅ PASS' if okr_check['passed'] else '❌ FAIL'} |")
    report.append(f"")
    if okr_check["kr_no_target"]:
        report.append(f"KRs missing numeric targets:")
        for kr in okr_check["kr_no_target"][:5]:
            report.append(f"- `{kr}`")
        report.append(f"")
    report.append(f"## 2. FODA Completeness Check")
    report.append(f"")
    report.append(f"| Quadrant | Items |")
    report.append(f"|----------|-------|")
    for qname in ["strengths", "weaknesses", "opportunities", "threats"]:
        cnt = foda_check["counts"].get(qname, 0)
        report.append(f"| {qname.capitalize()} | {cnt} |")
    report.append(f"| **Min 3 per quadrant** | {'✅ PASS' if foda_check['passed'] else '❌ FAIL'} |")
    report.append(f"")
    report.append(f"## 3. Roadmap 3 Horizons Check")
    report.append(f"")
    report.append(f"| Horizon | Milestones |")
    report.append(f"|---------|-----------|")
    for hid in ["h1", "h2", "h3"]:
        cnt = roadmap_check["horizons"].get(hid, 0)
        report.append(f"| {hid.upper()} ({'0-3mo' if hid=='h1' else '3-6mo' if hid=='h2' else '6-12mo'}) | {cnt} |")
    report.append(f"| **All horizons present** | {'✅ PASS' if roadmap_check['passed'] else '❌ FAIL'} |")
    report.append(f"")
    report.append(f"## 4. Risk Identification Check")
    report.append(f"")
    report.append(f"| Metric | Value |")
    report.append(f"|--------|-------|")
    report.append(f"| Risks identified | {risk_check['total']} |")
    report.append(f"| With mitigation | {risk_check['with_mitigation']} |")
    report.append(f"| **Status** | {'✅ PASS' if risk_check['passed'] else '❌ FAIL'} |")
    report.append(f"")
    if risk_check["items"]:
        report.append(f"Top risks:")
        for r in risk_check["items"][:5]:
            report.append(f"- {r}")
        report.append(f"")
    if bcg_result:
        report.append(f"## 5. BCG Evaluation")
        report.append(f"")
        report.append(f"| Metric | Score |")
        report.append(f"|--------|-------|")
        report.append(f"| BCG Strategy | {bcg_result['bcg_strategy']}/10 {'✅' if bcg_result['bcg_passed'] else '❌'} |")
        report.append(f"| OKR Health | {bcg_result['okr_health']}% {'✅' if bcg_result['okr_passed'] else '❌'} |")
        report.append(f"| OKRs evaluated | {bcg_result['okr_count']} |")
        report.append(f"")
        dims = bcg_result.get("dimensions", {})
        if dims:
            report.append(f"### Dimension Breakdown")
            report.append(f"")
            report.append(f"| Dimension | Score/5 | Weight | Weighted |")
            report.append(f"|-----------|---------|--------|----------|")
            for dim_id, d in sorted(dims.items()):
                s = d.get("score", 0)
                w = d.get("weight", 0)
                c = d.get("weighted", 0)
                report.append(f"| {dim_id} | {s}/5 | {w} | {c} |")
            report.append(f"")
    if simulation_result:
        report.append(f"## 6. Simulation Engine \u2014 Monte Carlo Analysis")
        report.append(f"")
        report.append(f"| OKR | Combined P | Veredict |")
        report.append(f"|-----|-----------|----------|")
        for okr_res in simulation_result:
            pct = f"{okr_res['combined_probability']:.1%}"
            report.append(f"| {okr_res['objective'][:50]} | {pct} | {okr_res['verdict']} |")
        report.append(f"")
        for okr_res in simulation_result:
            report.append(f"### {okr_res['objective']}")
            report.append(f"")
            report.append(f"| KR | E[V] | P(Success) | 95% CI | \u03c3 |")
            report.append(f"|---|------|-----------|--------|---|")
            for kr in okr_res["key_results"]:
                ci = f"[{kr['ci_95_lower']}, {kr['ci_95_upper']}]"
                pct = f"{kr['probability_success']:.1%}"
                report.append(f"| {kr['name'][:40]} | {kr['expected_value']} | {pct} | {ci} | {kr['std']} |")
            report.append(f"")
    if causal_report:
        report.append(causal_report)
        report.append("")
    checks = [okr_check["passed"], foda_check["passed"], risk_check["passed"]]
    if checklist_type in ("strategy", "both"):
        checks.append(roadmap_check["passed"])
    overall = all(checks)
    report.append(f"---")
    report.append(f"")
    report.append(f"## Overall Result")
    report.append(f"")
    report.append(f"| Component | Status |")
    report.append(f"|-----------|--------|")
    report.append(f"| OKR Check | {'✅' if okr_check['passed'] else '❌'} |")
    report.append(f"| FODA Check | {'✅' if foda_check['passed'] else '❌'} |")
    if checklist_type in ("strategy", "both"):
        report.append(f"| Roadmap Check | {'✅' if roadmap_check['passed'] else '❌'} |")
    report.append(f"| Risk Check | {'✅' if risk_check['passed'] else '❌'} |")
    if bcg_result:
        report.append(f"| BCG Score | {'✅' if bcg_result['bcg_passed'] else '❌'} |")
    report.append(f"| **Overall** | **{'✅ PASS' if overall else '❌ FAIL'}** |")
    report.append(f"")
    return "\n".join(report)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post-Output Hook — verify Metis strategic outputs for completeness and quality.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  py -3 .tools/post_output_hook.py output.md\n"
            "  py -3 .tools/post_output_hook.py output.md --checklist both\n"
            "  py -3 .tools/post_output_hook.py output.md --checklist quality\n"
        ),
    )
    parser.add_argument("output_file", help="Metis output file to verify")
    parser.add_argument(
        "--checklist",
        choices=["quality", "strategy", "both"],
        default="both",
        help="Checklist type: quality (OKR+FODA+Risk), strategy (+Roadmap), both (default)",
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Run proactive monitor check on the generated report",
    )
    parser.add_argument(
        "--store-memory",
        action="store_true",
        help="Store verification result in Strategic Memory Bank after checks",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run Monte Carlo simulation on detected OKRs with variable distributions",
    )
    parser.add_argument(
        "--plan-type",
        default="strategic_analysis",
        help="Plan type for strategy memory (used with --store-memory)",
    )
    parser.add_argument(
        "--causal",
        action="store_true",
        help="Run causal analysis on the output context (Week 3 — Causal Modeler)",
    )
    parser.add_argument(
        "--creative",
        action="store_true",
        help="Run creative divergence engine on the output context (Week 4 — Dynamic Temperature)",
    )
    args = parser.parse_args()

    text = load_output(args.output_file)
    print(f"✓ Loaded: {args.output_file} ({len(text)} chars)")

    okr_check = check_okrs(text)
    print(f"  OKRs: {okr_check['count']} found, {okr_check['kr_targets']} with numeric targets")

    foda_check = check_foda(text)
    print(f"  FODA: {foda_check['counts']}")

    roadmap_check = check_roadmap(text)
    print(f"  Roadmap: {roadmap_check['horizons']}")

    risk_check = check_risks(text)
    print(f"  Risks: {risk_check['total']} identified, {risk_check['with_mitigation']} with mitigation")

    bcg_result = None
    if okr_check["count"] > 0:
        bcg_result = run_bcg(text)
        print(f"  BCG: {bcg_result['bcg_strategy']}/10 (OKR health: {bcg_result['okr_health']}%)")

    causal_report = None
    if args.causal:
        if CAUSAL_AVAILABLE:
            try:
                modeler = CausalModeler()
                causal_report = modeler.generate_report(text)
                print(f"  Causal: {modeler.analyze(text)['node_count']} nodes, {modeler.analyze(text)['edge_count']} edges")
            except Exception as e:
                print(f"  ⚠️  Causal analysis failed: {e}", file=sys.stderr)
        else:
            print(f"  ⚠️  Causal Modeler not available (causal_graph.py not found)", file=sys.stderr)

    simulation_result = None
    if args.simulate:
        try:
            data = try_parse_json(text)
            if data:
                okrs_list = data if isinstance(data, list) else data.get("okrs", [])
                if okrs_list and any(
                    kr.get("variables") for okr in okrs_list
                    for kr in (okr.get("key_results") or [])
                ):
                    sys.path.insert(0, str(TOOLS_DIR))
                    from simulate import SimulationEngine
                    engine = SimulationEngine()
                    simulation_result = engine.evaluate_okrs({"okrs": okrs_list})
                    print(f"  Simulation: {len(simulation_result)} OKRs evaluated")
        except ImportError as e:
            print(f"  \u26a0\ufe0f Simulation not available: {e}", file=sys.stderr)
        except Exception as e:
            print(f"  \u26a0\ufe0f Simulation failed: {e}", file=sys.stderr)

    creative_report = None
    if args.creative:
        sys.path.insert(0, str(TOOLS_DIR))
        try:
            from creative_spark import generate_options, format_evaluation_report, evaluate_options
            options = generate_options(f"Strategic analysis: {Path(args.output_file).stem}", count=3)
            eval_results = evaluate_options(
                json.dumps({"options": options})
            ) if False else None

            temp_file = TOOLS_DIR / f"_creative_{Path(args.output_file).stem}.json"
            temp_file.write_text(
                json.dumps({"options": options, "source": args.output_file}, indent=2),
                encoding="utf-8",
            )
            eval_results = evaluate_options(str(temp_file))
            creative_report = format_evaluation_report(eval_results)
            temp_file.unlink(missing_ok=True)
            print(f"  Creative: {len(options)} divergent options generated, {len(eval_results)} evaluated")
        except ImportError as e:
            print(f"  \u26a0\ufe0f Creative Spark not available: {e}", file=sys.stderr)
        except Exception as e:
            print(f"  \u26a0\ufe0f Creative divergence failed: {e}", file=sys.stderr)

    report = generate_report(
        okr_check, foda_check, roadmap_check, risk_check,
        bcg_result, args.checklist, args.output_file,
        simulation_result, causal_report,
    )

    report_path = KAOS_ROOT / ".memory" / "cache" / f"verification_{Path(args.output_file).stem}.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n✓ Report saved: {report_path}")
    print(report)

    if args.store_memory:
        try:
            sys.path.insert(0, str(SCRIPTS_DIR))
            from strategy_memory import StrategicMemoryBank
            bank = StrategicMemoryBank()
            context = {
                "checklist": args.checklist,
                "source_file": args.output_file,
                "timestamp": datetime.now().isoformat(),
            }
            content = {
                "okr_check": okr_check,
                "foda_check": foda_check,
                "roadmap_check": roadmap_check,
                "risk_check": risk_check,
                "bcg": bcg_result,
            }
            store_id = bank.store(context, content, args.plan_type)
            print(f"\n  ✅ Strategy memory stored (id={store_id}, type={args.plan_type})")
        except ImportError as e:
            print(f"\n  ⚠️  Could not store strategy memory: {e}")
        except Exception as e:
            print(f"\n  ⚠️  Strategy memory store failed: {e}")

    if args.monitor:
        print(f"\n{'─' * 50}")
        print("  Running proactive monitor check...")
        sys.path.insert(0, str(SCRIPTS_DIR))
        try:
            from monitor import check_scores
            result = check_scores(str(report_path))
            if result["passed"]:
                print(f"  ✅ Monitor: PASS (pass_rate={result['pass_rate']:.1f}%)")
            else:
                print(f"  ⚠️  Monitor: FAIL (pass_rate={result['pass_rate']:.1f}%)")
                for a in result["alerts"]:
                    print(f"       {a}")
        except ImportError as e:
            print(f"  ⚠️  Monitor not available: {e}")
        print(f"{'─' * 50}")


if __name__ == "__main__":
    main()
