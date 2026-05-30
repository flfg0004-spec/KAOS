"""
Counterfactual Simulation Engine — "What if we had prioritized X over Y?"

Simulates counterfactual scenarios by modifying variables in a strategy
and comparing original vs modified outcomes via Monte Carlo.

Usage:
    py -3 .tools/counterfactual.py what-if --strategy-id <id> --changes '{"variable": "adopcion", "alpha": 5}'
    py -3 .tools/counterfactual.py compare --original <id> --modified <id>
    py -3 .tools/counterfactual.py report --original <id> --what-if "description" --results <results.json>
    py -3 .tools/counterfactual.py --help
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TOOLS_DIR.parent / ".memory" / "_scripts"

sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from simulate import SimulationEngine
from strategy_memory import StrategicMemoryBank


DB_PATH = SCRIPTS_DIR / "strategy_memory.db"


class CounterfactualEngine:
    def __init__(self, iterations=10000):
        self.engine = SimulationEngine(iterations=iterations)
        self.bank = StrategicMemoryBank()

    def load_strategy(self, strategy_id):
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM strategies WHERE id = ?", (strategy_id,)
        ).fetchone()
        conn.close()
        if row is None:
            raise ValueError(f"Strategy id={strategy_id} not found in memory bank.")
        record = dict(row)
        record["context"] = json.loads(record.get("context_json", "{}"))
        record["content"] = json.loads(record.get("content_json", "{}"))
        return record

    def apply_what_if(self, strategy, changes):
        modified = json.loads(json.dumps(strategy))
        var_key = changes.get("variable", "")
        new_alpha = changes.get("alpha")
        new_beta = changes.get("beta")
        content = modified.get("content", {})
        krs = content.get("key_results", content.get("okrs", []))
        if isinstance(krs, dict):
            krs = [krs]
        found = False
        for kr in krs:
            variables = kr.get("variables", [])
            for v in variables:
                vname = v.get("name", "")
                if var_key and var_key.lower() in vname.lower():
                    if new_alpha is not None:
                        v["alpha"] = new_alpha
                    if new_beta is not None:
                        v["beta"] = new_beta
                    found = True
        if not found and "variables" in content:
            for v in content["variables"]:
                vname = v.get("name", "")
                if var_key and var_key.lower() in vname.lower():
                    if new_alpha is not None:
                        v["alpha"] = new_alpha
                    if new_beta is not None:
                        v["beta"] = new_beta
                    found = True
        return modified

    def _extract_okr_list(self, strategy):
        content = strategy.get("content", {})
        if not content:
            content = json.loads(strategy.get("content_json", "{}"))
        if "okrs" in content:
            return content["okrs"]
        if "objective" in content:
            return [content]
        return [content]

    def run_comparison(self, original, modified):
        orig_okrs = self._extract_okr_list(original)
        mod_okrs = self._extract_okr_list(modified)
        orig_results = self.engine.evaluate_okrs(orig_okrs)
        mod_results = self.engine.evaluate_okrs(mod_okrs)
        comparison = []
        for i in range(max(len(orig_results), len(mod_results))):
            o = orig_results[i] if i < len(orig_results) else {}
            m = mod_results[i] if i < len(mod_results) else {}
            o_name = o.get("objective", f"OKR {i}")
            o_prob = o.get("combined_probability", 0)
            o_verdict = o.get("verdict", "N/A")
            m_prob = m.get("combined_probability", 0)
            m_verdict = m.get("verdict", "N/A")
            delta = round(m_prob - o_prob, 4)
            comparison.append({
                "objective": o_name,
                "original_probability": round(o_prob, 4),
                "original_verdict": o_verdict,
                "modified_probability": round(m_prob, 4),
                "modified_verdict": m_verdict,
                "delta": delta,
                "delta_pct": round(delta / max(o_prob, 0.001) * 100, 2) if o_prob > 0 else 0,
            })
        return comparison

    def generate_report(self, original_id, what_if_description, results):
        now = datetime.now().isoformat(timespec="minutes")
        lines = []
        lines.append(f"# Counterfactual Simulation Report")
        lines.append("")
        lines.append(f"**Generated**: {now}")
        lines.append(f"**Original Strategy ID**: {original_id}")
        lines.append(f"**What-If Scenario**: {what_if_description}")
        lines.append("")
        lines.append("## Comparison Results")
        lines.append("")
        lines.append("| Objective | Original P | Modified P | Δ | Δ% | Impact |")
        lines.append("|-----------|-----------|------------|------|------|--------|")
        for r in results:
            o_prob = r.get("original_probability", 0)
            m_prob = r.get("modified_probability", 0)
            delta = r.get("delta", 0)
            delta_pct = r.get("delta_pct", 0)
            if delta > 0.05:
                impact = "🟢 Positive"
            elif delta < -0.05:
                impact = "🔴 Negative"
            else:
                impact = "⚪ Neutral"
            lines.append(
                f"| {r['objective']} | {o_prob:.2%} | {m_prob:.2%} | "
                f"{delta:+.4f} | {delta_pct:+.2f}% | {impact} |"
            )
        lines.append("")
        lines.append("## Verdicts")
        lines.append("")
        lines.append("### Original")
        for r in results:
            lines.append(f"- **{r['objective']}**: {r.get('original_verdict', 'N/A')}")
        lines.append("")
        lines.append("### Modified (What-If)")
        for r in results:
            lines.append(f"- **{r['objective']}**: {r.get('modified_verdict', 'N/A')}")
        lines.append("")
        positive = sum(1 for r in results if r.get("delta", 0) > 0.05)
        negative = sum(1 for r in results if r.get("delta", 0) < -0.05)
        if positive > negative:
            verdict = "The what-if scenario shows overall improvement."
        elif negative > positive:
            verdict = "The what-if scenario shows overall degradation."
        else:
            verdict = "The what-if scenario shows no significant overall change."
        lines.append("## Overall Verdict")
        lines.append("")
        lines.append(f"{verdict}")
        lines.append("")
        lines.append("---")
        lines.append("*Report generated by Counterfactual Engine*")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Counterfactual Simulation Engine — compare strategic scenarios via Monte Carlo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  py -3 .tools/counterfactual.py what-if --strategy-id 1 --changes '{\"variable\": \"adopcion\", \"alpha\": 5}'\n"
            "  py -3 .tools/counterfactual.py compare --original 1 --modified 2\n"
            "  py -3 .tools/counterfactual.py report --original 1 --what-if \"Increase adoption alpha\" --results results.json\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    wi_parser = subparsers.add_parser("what-if", help="Apply a what-if change to a strategy and compare")
    wi_parser.add_argument("--strategy-id", required=True, help="Strategy ID in memory bank")
    wi_parser.add_argument("--changes", required=True, help='JSON with changes, e.g. \'{"variable": "adopcion", "alpha": 5}\'')
    wi_parser.add_argument("--iterations", type=int, default=10000, help="Monte Carlo iterations (default: 10000)")

    cmp_parser = subparsers.add_parser("compare", help="Compare two strategies by ID")
    cmp_parser.add_argument("--original", required=True, help="Original strategy ID")
    cmp_parser.add_argument("--modified", required=True, help="Modified strategy ID")
    cmp_parser.add_argument("--iterations", type=int, default=10000, help="Monte Carlo iterations (default: 10000)")

    rep_parser = subparsers.add_parser("report", help="Generate markdown report from comparison results")
    rep_parser.add_argument("--original", required=True, help="Original strategy ID")
    rep_parser.add_argument("--what-if", required=True, help="Description of the what-if scenario")
    rep_parser.add_argument("--results", required=True, help="Path to results JSON file")

    args = parser.parse_args()

    if args.command == "what-if":
        engine = CounterfactualEngine(iterations=args.iterations)
        strategy = engine.load_strategy(args.strategy_id)
        changes = json.loads(args.changes)
        modified = engine.apply_what_if(strategy, changes)
        results = engine.run_comparison(strategy, modified)
        print(json.dumps(results, indent=2, ensure_ascii=False))

    elif args.command == "compare":
        engine = CounterfactualEngine(iterations=args.iterations)
        original = engine.load_strategy(args.original)
        modified = engine.load_strategy(args.modified)
        results = engine.run_comparison(original, modified)
        print(json.dumps(results, indent=2, ensure_ascii=False))

    elif args.command == "report":
        engine = CounterfactualEngine()
        results_path = Path(args.results)
        if not results_path.is_file():
            print(f"Error: Results file not found: {args.results}", file=sys.stderr)
            sys.exit(1)
        results = json.loads(results_path.read_text(encoding="utf-8"))
        report = engine.generate_report(args.original, args.what_if, results)
        print(report)
        report_dir = TOOLS_DIR.parent / ".memory" / "cache" / "counterfactual"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"counterfactual-{args.original}.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    main()
