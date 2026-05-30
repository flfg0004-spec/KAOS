"""
simulate.py — Monte Carlo simulation engine for strategic OKRs.

Estimates probability of success for each Key Result using
beta distributions to model uncertainty.

Usage:
    py -3 .tools/simulate.py evaluate <okrs_json_file>
    py -3 .tools/simulate.py sensitivity <okrs_json_file>
    py -3 .tools/simulate.py --help
"""

import argparse
import json
import math
import random
import sys
from pathlib import Path


BETA_PRIORS = {
    "adopcion_nueva_funcionalidad": (3, 5),
    "velocidad_desarrollo": (4, 2),
    "engagement_stakeholders": (2, 3),
    "calidad_datos": (3, 3),
    "riesgo_competencia": (2, 4),
    "alineacion_organizacional": (5, 2),
    "capacidad_tecnica": (4, 3),
    "presupuesto_disponible": (3, 4),
}


class SimulationEngine:
    def __init__(self, iterations=10000):
        self.iterations = iterations

    def beta_distribution(self, alpha, beta_val, n):
        if alpha <= 0 or beta_val <= 0:
            raise ValueError(f"Alpha and beta must be positive, got alpha={alpha}, beta={beta_val}")
        return [random.betavariate(alpha, beta_val) for _ in range(n)]

    def _resolve_variable(self, var):
        if "alpha" in var and "beta" in var:
            return var["alpha"], var["beta"]
        name = var.get("name", "").lower()
        if name in BETA_PRIORS:
            return BETA_PRIORS[name]
        return (1, 1)

    def _evaluate_formula(self, formula, values):
        safe = {"__builtins__": {}}
        env = {f"v{i}": val for i, val in enumerate(values)}
        return eval(formula, safe, env)

    def _run_simulation(self, variables, formula, target):
        samples = []
        for var in variables:
            alpha, beta_val = self._resolve_variable(var)
            samples.append(self.beta_distribution(alpha, beta_val, self.iterations))

        results = []
        for i in range(self.iterations):
            values = [s[i] for s in samples]
            result = self._evaluate_formula(formula, values)
            results.append(result)

        results.sort()
        n = len(results)
        expected = sum(results) / n
        variance = sum((x - expected) ** 2 for x in results) / n
        std = math.sqrt(variance)
        successes = sum(1 for r in results if r >= target)
        prob = successes / n
        ci_lower = results[int(n * 0.025)]
        ci_upper = results[int(n * 0.975)]
        return expected, prob, ci_lower, ci_upper, std

    def evaluate_key_result(self, kr):
        name = kr.get("name", "Unnamed KR")
        target = kr.get("target_value", 0)
        variables = kr.get("variables", [])
        formula = kr.get("formula", "v0")
        expected, prob, ci_lower, ci_upper, std = self._run_simulation(variables, formula, target)
        return {
            "name": name,
            "expected_value": round(expected, 4),
            "probability_success": round(prob, 4),
            "ci_95_lower": round(ci_lower, 4),
            "ci_95_upper": round(ci_upper, 4),
            "std": round(std, 4),
        }

    def evaluate_okr(self, okr):
        objective = okr.get("objective", "Unnamed OKR")
        krs = okr.get("key_results", [])
        kr_results = [self.evaluate_key_result(kr) for kr in krs]
        combined_prob = 1.0
        for r in kr_results:
            combined_prob *= r["probability_success"]
        if combined_prob > 0.8:
            verdict = "\U0001f7e2 Alta confianza"
        elif combined_prob > 0.6:
            verdict = "\U0001f7e1 Riesgo moderado"
        elif combined_prob > 0.4:
            verdict = "\U0001f7e0 Incertidumbre significativa"
        else:
            verdict = "\U0001f534 Alta incertidumbre"
        return {
            "objective": objective,
            "key_results": kr_results,
            "combined_probability": round(combined_prob, 4),
            "verdict": verdict,
        }

    def evaluate_okrs(self, okrs_data):
        if isinstance(okrs_data, dict):
            okrs_data = okrs_data.get("okrs", [])
        results = [self.evaluate_okr(okr) for okr in okrs_data]
        return results

    def sensitivity_analysis(self, okr):
        objective = okr.get("objective", "Unnamed OKR")
        baseline = self.evaluate_okr(okr)
        base_prob = baseline["combined_probability"]
        analysis = {"objective": objective, "baseline_probability": round(base_prob, 4), "key_results": []}
        for kr_idx, kr in enumerate(okr.get("key_results", [])):
            name = kr.get("name", f"KR{kr_idx + 1}")
            variables = kr.get("variables", [])
            formula = kr.get("formula", "v0")
            target = kr.get("target_value", 0)
            base_kr_prob = baseline["key_results"][kr_idx]["probability_success"]
            var_impacts = []
            for var_idx, var in enumerate(variables):
                var_name = var.get("name", f"var{var_idx}")
                alpha, beta_val = self._resolve_variable(var)
                low_vars = [dict(v) for v in variables]
                low_vars[var_idx]["alpha"] = alpha * 0.8
                low_vars[var_idx]["beta"] = beta_val * 0.8
                low_kr = {"name": name, "target_value": target, "variables": low_vars, "formula": formula}
                low_result = self.evaluate_key_result(low_kr)
                high_vars = [dict(v) for v in variables]
                high_vars[var_idx]["alpha"] = alpha * 1.2
                high_vars[var_idx]["beta"] = beta_val * 1.2
                high_kr = {"name": name, "target_value": target, "variables": high_vars, "formula": formula}
                high_result = self.evaluate_key_result(high_kr)
                impact = max(
                    abs(low_result["probability_success"] - base_kr_prob),
                    abs(high_result["probability_success"] - base_kr_prob),
                )
                var_impacts.append({
                    "name": var_name,
                    "base_probability": round(base_kr_prob, 4),
                    "low_probability": round(low_result["probability_success"], 4),
                    "high_probability": round(high_result["probability_success"], 4),
                    "impact": round(impact, 4),
                })
            var_impacts.sort(key=lambda x: x["impact"], reverse=True)
            analysis["key_results"].append({
                "name": name,
                "baseline_probability": round(base_kr_prob, 4),
                "variables": var_impacts,
            })
        return analysis

    def tornado_analysis(self, okr):
        objective = okr.get("objective", "Unnamed OKR")
        baseline = self.evaluate_okr(okr)
        base_prob = baseline["combined_probability"]
        results = []
        for kr_idx, kr in enumerate(okr.get("key_results", [])):
            kr_name = kr.get("name", f"KR{kr_idx + 1}")
            variables = kr.get("variables", [])
            formula = kr.get("formula", "v0")
            target = kr.get("target_value", 0)
            base_kr_prob = baseline["key_results"][kr_idx]["probability_success"]
            for var_idx, var in enumerate(variables):
                var_name = var.get("name", f"var{var_idx}")
                alpha, beta_val = self._resolve_variable(var)
                perturbations = []
                for change_pct in [-30, -20, -10, 10, 20, 30]:
                    factor = 1 + change_pct / 100
                    mod_vars = [dict(v) for v in variables]
                    mod_vars[var_idx]["alpha"] = max(0.1, alpha * factor)
                    mod_vars[var_idx]["beta"] = max(0.1, beta_val * factor)
                    mod_kr = {
                        "name": kr_name,
                        "target_value": target,
                        "variables": mod_vars,
                        "formula": formula,
                    }
                    mod_result = self.evaluate_key_result(mod_kr)
                    new_prob = mod_result["probability_success"]
                    if base_kr_prob > 0 and change_pct != 0:
                        elasticity = ((new_prob - base_kr_prob) / base_kr_prob) / (change_pct / 100)
                    else:
                        elasticity = 0.0
                    perturbations.append({
                        "change_pct": change_pct,
                        "probability": round(new_prob, 4),
                        "elasticity": round(abs(elasticity), 4),
                    })
                avg_el = sum(p["elasticity"] for p in perturbations) / max(len(perturbations), 1)
                low_prob = min(p["probability"] for p in perturbations)
                high_prob = max(p["probability"] for p in perturbations)
                results.append({
                    "variable": var_name,
                    "base_probability": round(base_kr_prob, 4),
                    "low_probability": round(low_prob, 4),
                    "high_probability": round(high_prob, 4),
                    "range": round(high_prob - low_prob, 4),
                    "avg_elasticity": round(avg_el, 4),
                    "perturbations": perturbations,
                })
        results.sort(key=lambda x: x["range"], reverse=True)
        return {
            "objective": objective,
            "baseline_probability": round(base_prob, 4),
            "variables": results,
        }

    @staticmethod
    def generate_tornado_chart(tornado_result):
        objective = tornado_result.get("objective", "Unnamed OKR")
        variables = tornado_result.get("variables", [])
        if not variables:
            return "No variables to display."
        lines = []
        max_name_len = max(len(v["variable"]) for v in variables)
        col_width = max(max_name_len + 2, 25)
        lines.append(f"Tornado Sensitivity Chart: {objective}")
        lines.append("=" * 80)
        header = f"{'Variable':<{col_width}} {'Base':<8} {'Low':<8} {'High':<8} {'Range':<8} {'Elasticity':<10}"
        lines.append(header)
        lines.append("-" * 80)
        max_range = max(v["range"] for v in variables) if variables else 1
        bar_width = 25
        for v in variables:
            name = v["variable"]
            base = v["base_probability"]
            low = v["low_probability"]
            high = v["high_probability"]
            rng = v["range"]
            el = v["avg_elasticity"]
            low_bar = int((low / max(low, high)) * bar_width) if max(low, high) > 0 else 0
            high_bar = int((high / max(low, high)) * bar_width) if max(low, high) > 0 else 0
            left = "#" * low_bar
            right = "#" * high_bar
            bar = f"{left:<{bar_width}}{'|':^1}{right:<{bar_width}}"
            lines.append(f"{name:<{col_width}} {base:<8.4f} {low:<8.4f} {high:<8.4f} {rng:<8.4f} {el:<10.4f}")
        lines.append("=" * 80)
        lines.append("Range = |high_probability - low_probability| across ±30% perturbations")
        lines.append("Elasticity = average |ΔP/P| / |Δparam/param| across ±10%, ±20%, ±30%")
        return "\n".join(lines)


def _load_okrs(file_path):
    path = Path(file_path)
    if not path.is_file():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(
        description="Monte Carlo simulation engine for strategic OKR uncertainty quantification.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  py -3 .tools/simulate.py evaluate okrs.json\n"
            "  py -3 .tools/simulate.py sensitivity okrs.json\n"
            "  py -3 .tools/simulate.py tornado okrs.json\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    eval_parser = subparsers.add_parser("evaluate", help="Run full Monte Carlo evaluation on OKRs")
    eval_parser.add_argument("okrs_file", help="Path to OKRs JSON file")
    eval_parser.add_argument("--iterations", type=int, default=10000, help="Number of Monte Carlo iterations (default: 10000)")
    sens_parser = subparsers.add_parser("sensitivity", help="Run sensitivity analysis on OKR variables")
    sens_parser.add_argument("okrs_file", help="Path to OKRs JSON file")
    sens_parser.add_argument("--iterations", type=int, default=10000, help="Number of Monte Carlo iterations (default: 10000)")
    tornado_parser = subparsers.add_parser("tornado", help="Run tornado sensitivity analysis with elasticity (+-10%%, +-20%%, +-30%%)")
    tornado_parser.add_argument("okrs_file", help="Path to OKRs JSON file")
    tornado_parser.add_argument("--iterations", type=int, default=10000, help="Number of Monte Carlo iterations (default: 10000)")
    args = parser.parse_args()
    okrs_data = _load_okrs(args.okrs_file)
    engine = SimulationEngine(iterations=args.iterations)
    if args.command == "evaluate":
        results = engine.evaluate_okrs(okrs_data)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif args.command == "sensitivity":
        okrs_list = okrs_data.get("okrs", []) if isinstance(okrs_data, dict) else okrs_data
        for okr in okrs_list:
            analysis = engine.sensitivity_analysis(okr)
            print(json.dumps(analysis, indent=2, ensure_ascii=False))
            print()
    elif args.command == "tornado":
        okrs_list = okrs_data.get("okrs", []) if isinstance(okrs_data, dict) else okrs_data
        for okr in okrs_list:
            result = engine.tornado_analysis(okr)
            chart = engine.generate_tornado_chart(result)
            print(chart)
            print()


if __name__ == "__main__":
    main()
