"""
creative_spark.py — Creative divergence engine for Metis.

Generates radically different strategic options using prompt templates
that force creative thinking. Designed to compensate for fixed low temperature.

Usage:
    py -3 .tools/creative_spark.py generate --problem "description" --count 3
    py -3 .tools/creative_spark.py evaluate --options <json_file>
    py -3 .tools/creative_spark.py --help
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

_SCRIPTS_LIB = str(Path(__file__).resolve().parents[1] / ".memory" / "_scripts" / "lib")
if _SCRIPTS_LIB not in sys.path:
    sys.path.insert(0, _SCRIPTS_LIB)

_AGY_AVAILABLE = None
def _get_agy():
    global _AGY_AVAILABLE
    if _AGY_AVAILABLE is None:
        try:
            from agy_client import call_agy as _c
            _AGY_AVAILABLE = _c
        except ImportError:
            _AGY_AVAILABLE = False
    return _AGY_AVAILABLE

DIVERGENCE_TEMPLATES = {
    "first_principles": {
        "name": "First Principles",
        "prompt": "Descompón el problema hasta sus fundamentos más básicos. "
                  "Identifica qué supuestos son verdaderos y cuáles no. "
                  "Construye una solución desde cero usando solo verdades fundamentales.",
        "description": "Descomponer el problema hasta fundamentos",
    },
    "inversion": {
        "name": "Inversion",
        "prompt": "Imagina que quieres lograr exactamente lo OPUESTO al objetivo deseado. "
                  "Diseña el plan perfecto para fracasar. Luego, invierte cada acción.",
        "description": "Cómo lograr lo opuesto, luego invertir",
    },
    "analogy": {
        "name": "Analogy",
        "prompt": "Encuentra un dominio completamente no relacionado que haya resuelto "
                  "un problema estructuralmente similar. Extrae el patrón y aplícalo.",
        "description": "Buscar solución en dominio no relacionado",
    },
    "what_if": {
        "name": "What If",
        "prompt": "Identifica la restricción más limitante del problema actual. "
                  "Elimínala por completo. ¿Qué soluciones aparecen? "
                  "Luego, reintroduce la restricción de forma modificada.",
        "description": "Eliminar una restricción clave",
    },
    "devils_advocate": {
        "name": "Devil's Advocate",
        "prompt": "Toma la solución más obvia que todos elegirían. "
                  "Construye el mejor argumento posible en su contra. "
                  "Propón una alternativa que supere cada objeción.",
        "description": "Argumentar contra la solución obvia",
    },
}

EVALUATION_CRITERIA = [
    "impact",
    "effort",
    "risk",
    "vision_alignment",
]


def generate_options(problem: str, count: int = 3) -> list[dict]:
    if count < 1:
        count = 1
    if count > len(DIVERGENCE_TEMPLATES):
        count = len(DIVERGENCE_TEMPLATES)

    selected_keys = random.sample(list(DIVERGENCE_TEMPLATES.keys()), count)
    options = []

    for key in selected_keys:
        template = DIVERGENCE_TEMPLATES[key]
        option = {
            "template": key,
            "name": template["name"],
            "prompt": template["prompt"],
            "description": template["description"],
            "problem": problem,
            "option_text": _synthesize_option(problem, template),
        }
        options.append(option)

    return options


def _synthesize_option(problem: str, template: dict) -> str:
    prompt = (
        f"Genera una opción estratégica usando el template {template['name']}. "
        f"Problema: {problem}. {template['prompt']}"
    )

    if not os.environ.get("KAOS_TESTING"):
        agy_fn = _get_agy()
        if agy_fn:
            try:
                result = agy_fn(prompt, tier="flash", timeout=5)
                if result.get("success") and result.get("text", "").strip():
                    return result["text"].strip()
            except Exception:
                pass
        try:
            _code = (
                f"import sys; sys.path.insert(0, {_SCRIPTS_LIB!r}); "
                f"from agy_client import call_agy; "
                f"_r = call_agy({prompt!r}, tier='flash'); "
                f"print(_r.get('text', ''))"
            )
            r = subprocess.run(
                ["py", "-3", "-c", _code],
                timeout=3, capture_output=True, text=True,
            )
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except Exception:
            pass

    lines = [
        f"## Option: {template['name']}",
        f"",
        f"**Approach**: {template['description']}",
        f"",
        f"**Problem**: {problem}",
        f"",
        f"**Prompt template**: {template['prompt']}",
        f"",
        f"### Divergent exploration",
        f"",
        f"Applying {template['name']} thinking to this problem suggests:",
        f"- Starting from a radically different premise",
        f"- Challenging assumptions embedded in the problem statement",
        f"- Generating alternatives that conventional analysis would miss",
        f"",
        f"### Strategic implications",
        f"- This path changes the risk profile significantly",
        f"- Resource requirements differ from baseline approaches",
        f"- Success metrics may need redefinition",
    ]
    return "\n".join(lines)


def evaluate_options(file_path: str) -> list[dict]:
    path = Path(file_path)
    if not path.exists():
        candidates = sorted(Path.cwd().rglob(file_path))
        if candidates:
            path = candidates[0]
        else:
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {file_path}", file=sys.stderr)
        sys.exit(1)

    options = data if isinstance(data, list) else data.get("options", [])
    results = []

    for opt in options:
        scores = {}
        total = 0.0
        for criterion in EVALUATION_CRITERIA:
            score = _score_criterion(opt, criterion)
            scores[criterion] = score
            total += score

        avg = total / len(EVALUATION_CRITERIA)
        results.append({
            "name": opt.get("name", opt.get("template", "Unknown")),
            "scores": scores,
            "average": round(avg, 2),
            "recommended": avg >= 3.0,
            "option_text": opt.get("option_text", ""),
        })

    results.sort(key=lambda r: r["average"], reverse=True)
    return results


def _score_criterion(option: dict, criterion: str) -> float:
    text = option.get("option_text", "") or option.get("name", "") or ""
    text_lower = text.lower()
    words = text.split()
    word_count = len(words)

    if word_count < 3:
        return 1.0

    unique_ratio = len(set(w.lower() for w in words)) / word_count
    has_numbers = bool(re.search(r'\d+', text))

    criterion_keywords = {
        "impact": [
            "impacto", "impact", "crecimiento", "growth", "aumento", "mejora",
            "resultado", "result", "beneficio", "benefit", "transformación",
        ],
        "effort": [
            "esfuerzo", "effort", "tiempo", "time", "recursos", "resources",
            "costo", "cost", "inversión", "investment", "trabajo", "work",
        ],
        "risk": [
            "riesgo", "risk", "incertidumbre", "uncertainty", "peligro", "danger",
            "probabilidad", "probability", "mitigación", "mitigation", "amenaza",
        ],
        "vision_alignment": [
            "visión", "vision", "alineación", "alignment", "propósito",
            "purpose", "misión", "mission", "valores", "values", "largo plazo",
        ],
    }

    kw_hits = sum(1 for kw in criterion_keywords.get(criterion, []) if kw in text_lower)

    len_score = min(4.0, 1.0 + word_count / 30)
    div_bonus = unique_ratio * 0.5
    kw_bonus = min(1.0, kw_hits / 5.0)
    num_bonus = 0.3 if has_numbers else 0.0

    score = len_score + div_bonus + kw_bonus + num_bonus
    return round(min(5.0, max(1.0, score)), 1)


def format_evaluation_report(results: list[dict]) -> str:
    lines = [
        "# Creative Spark — Evaluation Report",
        "",
        "| Option | Impact | Effort | Risk | Alignment | Avg | Recommended |",
        "|--------|--------|--------|------|-----------|-----|-------------|",
    ]
    for r in results:
        s = r["scores"]
        rec = "✅" if r["recommended"] else "❌"
        lines.append(
            f"| {r['name'][:30]} | {s['impact']} | {s['effort']} | "
            f"{s['risk']} | {s['vision_alignment']} | {r['average']} | {rec} |"
        )

    if results:
        lines.append("")
        lines.append(f"**Top option**: {results[0]['name']} (avg: {results[0]['average']})")
        lines.append("")
        lines.append("### Divergent Options")
        for r in results:
            lines.append("")
            lines.append(f"#### {r['name']}")
            lines.append(f"- Average score: {r['average']}/5")
            lines.append(f"- Recommended: {'Yes' if r['recommended'] else 'No'}")
            if r.get("option_text"):
                lines.append("")
                lines.append(r["option_text"])

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Creative divergence engine for Metis. Generates radically "
                    "different strategic options using lateral thinking templates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  py -3 .tools/creative_spark.py generate --problem \"How to grow market share\"\n"
            "  py -3 .tools/creative_spark.py generate --problem \"X\" --count 5\n"
            "  py -3 .tools/creative_spark.py evaluate --options options.json\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-command")

    gen_parser = subparsers.add_parser("generate", help="Generate divergent options")
    gen_parser.add_argument("--problem", required=True, help="Strategic problem description")
    gen_parser.add_argument("--count", type=int, default=3, help="Number of options (default: 3)")
    gen_parser.add_argument("--output", "-o", help="Save options to JSON file")

    eval_parser = subparsers.add_parser("evaluate", help="Evaluate generated options")
    eval_parser.add_argument("--options", required=True, help="JSON file with options")
    eval_parser.add_argument("--output", "-o", help="Save evaluation report to file")

    args = parser.parse_args()

    if args.command == "generate":
        options = generate_options(args.problem, args.count)
        result = {"problem": args.problem, "count": len(options), "options": options}

        output_text = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(output_text, encoding="utf-8")
            print(f"Options saved to {args.output}")
        else:
            print(output_text)

    elif args.command == "evaluate":
        results = evaluate_options(args.options)
        report = format_evaluation_report(results)

        if args.output:
            Path(args.output).write_text(report, encoding="utf-8")
            print(f"Report saved to {args.output}")
        else:
            print(report)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
