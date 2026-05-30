"""Benchmark Strategist — compares Metis strategic decisions against human decisions."""
import json, re, sys, argparse, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".memory" / "_scripts"))

DIMENSIONS = ["clarity", "measurability", "realism", "risk_awareness", "creativity", "actionability"]


class StrategistBenchmark:
    def load_case(self, case_file: str) -> dict:
        data = json.loads(Path(case_file).read_text(encoding="utf-8"))
        return {
            "problem": data.get("problem", ""),
            "human_decision": data.get("human_decision", {}),
            "human_outcome": data.get("human_outcome"),
            "context": data.get("context", {}),
        }

    def evaluate_metis_decision(self, case: dict) -> dict:
        context = case.get("context", {})
        problem = case.get("problem", "")
        plan = {
            "context_analyzed": bool(context),
            "has_okrs": "okrs" in json.dumps(context).lower() if context else False,
            "dimensions": {},
        }
        scores = []
        for dim in DIMENSIONS:
            score = self._score_dimension(dim, context, problem)
            plan["dimensions"][dim] = score
            scores.append(score)
        plan["composite_score"] = round(sum(scores) / len(scores), 1) if scores else 0
        max_dim = max(plan["dimensions"], key=plan["dimensions"].get)
        min_dim = min(plan["dimensions"], key=plan["dimensions"].get)
        plan["recommendation"] = (
            f"Fortaleza: {max_dim} ({plan['dimensions'][max_dim]}/10). "
            f"Mejorable: {min_dim} ({plan['dimensions'][min_dim]}/10). "
            f"Score compuesto: {plan['composite_score']}/10"
        )
        return plan

    def _score_dimension(self, dim: str, context: dict, problem: str) -> int:
        context_str = json.dumps(context).lower() if context else ""
        problem_lower = problem.lower() if problem else ""
        full_text = f"{context_str} {problem_lower}"
        words = full_text.split()
        word_count = len(words)

        if word_count == 0:
            return 1

        dim_keywords = {
            "clarity": ["goal", "objective", "target", "metric", "objetivo", "meta", "clear"],
            "measurability": ["%", "metric", "kpi", "measure", "dato", "indicador", "cantidad"],
            "realism": ["fecha", "deadline", "plazo", "time", "meses", "fase", "restricción"],
            "risk_awareness": ["riesgo", "risk", "amenaza", "incertidumbre", "peligro", "problema"],
            "creativity": ["opción", "alternativa", "innovación", "creative", "nuevo", "diferente"],
            "actionability": ["paso", "step", "acción", "implementar", "concreto", "ejecutar"],
        }

        keywords = dim_keywords.get(dim, [])
        keyword_hits = sum(1 for kw in keywords if kw in full_text)
        has_numbers = bool(re.findall(r'\d+', full_text))
        unique_words = len(set(full_text.split()))
        diversity = unique_words / max(word_count, 1)

        base = 2
        kw_bonus = min(4, keyword_hits)
        num_bonus = 2 if has_numbers and dim in ("measurability", "realism") else 0
        div_bonus = min(2, int(diversity * 4))
        len_bonus = 1 if word_count > 30 else 0

        score = base + kw_bonus + num_bonus + div_bonus + len_bonus
        return max(1, min(10, score))

    def compare_decisions(self, human: dict, metis: dict) -> dict:
        comparison = {"dimensions": {}, "overall": {}}
        human_dims = human.get("dimensions", {})
        metis_dims = metis.get("dimensions", {})
        all_dims = set(list(human_dims.keys()) + list(metis_dims.keys()))
        for dim in sorted(all_dims):
            h = human_dims.get(dim, 0)
            m = metis_dims.get(dim, 0)
            comparison["dimensions"][dim] = {"human": h, "metis": m, "delta": round(m - h, 1), "winner": "metis" if m > h else "human" if h > m else "tie"}
        h_total = human.get("composite_score", 0) or 0
        m_total = metis.get("composite_score", 0) or 0
        comparison["overall"] = {"human_composite": h_total, "metis_composite": m_total, "delta": round(m_total - h_total, 1), "winner": "metis" if m_total > h_total else "human" if h_total > m_total else "tie"}
        return comparison

    def generate_report(self, cases_results: list[dict]) -> str:
        lines = []
        lines.append("# Strategist Benchmark Report")
        lines.append(f"*Generated: {__import__('datetime').datetime.now().isoformat()}*")
        lines.append("")
        metis_wins = sum(1 for r in cases_results if r.get("comparison", {}).get("overall", {}).get("winner") == "metis")
        human_wins = sum(1 for r in cases_results if r.get("comparison", {}).get("overall", {}).get("winner") == "human")
        ties = len(cases_results) - metis_wins - human_wins
        lines.append(f"**Cases evaluated**: {len(cases_results)}")
        lines.append(f"**Metis wins**: {metis_wins}")
        lines.append(f"**Human wins**: {human_wins}")
        lines.append(f"**Ties**: {ties}")
        lines.append(f"**Win rate**: {metis_wins / max(len(cases_results), 1):.0%}")
        lines.append("")
        for i, r in enumerate(cases_results):
            lines.append(f"## Case {i+1}: {r.get('case_name', 'Unnamed')}")
            lines.append("")
            comp = r.get("comparison", {})
            ov = comp.get("overall", {})
            lines.append(f"**Metis**: {ov.get('metis_composite', '?')}/10 | **Human**: {ov.get('human_composite', '?')}/10 | **Winner**: {ov.get('winner', '?')}")
            lines.append("")
            dims = comp.get("dimensions", {})
            lines.append("| Dimension | Human | Metis | Delta | Winner |")
            lines.append("|-----------|-------|-------|-------|--------|")
            for dim, data in sorted(dims.items()):
                lines.append(f"| {dim} | {data['human']} | {data['metis']} | {data['delta']:+.1f} | {data['winner']} |")
            lines.append("")
        lines.append("---")
        lines.append(f"**Final score**: {metis_wins}/{len(cases_results)} wins ({metis_wins / max(len(cases_results), 1):.0%})")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Benchmark Metis strategic decisions against human decisions.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_p = subparsers.add_parser("run", help="Run benchmark on a case file")
    run_p.add_argument("case_file", help="Path to case JSON file")
    compare_p = subparsers.add_parser("compare", help="Compare human vs metis decisions")
    compare_p.add_argument("case_file", help="Path to case JSON file")
    compare_p.add_argument("--metis-plan", required=True, help="Path to Metis plan JSON")
    report_p = subparsers.add_parser("report", help="Generate benchmark report from results directory")
    report_p.add_argument("results_dir", help="Directory with result JSON files")
    args = parser.parse_args()
    b = StrategistBenchmark()
    if args.command == "run":
        case = b.load_case(args.case_file)
        metis = b.evaluate_metis_decision(case)
        print(json.dumps({"case": case.get("problem", "")[:80], "metis_decision": metis}, indent=2))
    elif args.command == "compare":
        case = b.load_case(args.case_file)
        metis = b.evaluate_metis_decision(case)
        human = case.get("human_decision", {})
        comparison = b.compare_decisions(human, metis)
        print(json.dumps(comparison, indent=2))
    elif args.command == "report":
        results = []
        for f in sorted(Path(args.results_dir).glob("*.json")):
            results.append(json.loads(f.read_text(encoding="utf-8")))
        print(b.generate_report(results))


if __name__ == "__main__":
    main()
