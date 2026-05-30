"""BCG Evaluation CLI — evalúa outputs estratégicos desde la terminal.

Uso:
    bcg_eval_cli.py [file]              Evalúa texto estratégico desde archivo o stdin
    bcg_eval_cli.py --okrs [file]       Evalúa OKRs desde JSON
    bcg_eval_cli.py --format json       Output en JSON (por defecto: tabla)
    bcg_eval_cli.py --help              Muestra ayuda detallada

Threshold: < 7.0/10 → FAIL, >= 7.0 → PASS
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from lib.bcg_evaluator import evaluate_okrs, evaluate_strategy
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lib.bcg_evaluator import evaluate_okrs, evaluate_strategy


def load_text(file_path: str | None) -> str:
    """Read text from file or stdin."""
    if file_path:
        return Path(file_path).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    print("Error: No input provided. Pipe text or specify a file.", file=sys.stderr)
    sys.exit(1)


def load_okrs(file_path: str | None) -> list[dict]:
    """Load OKRs from a JSON file or stdin."""
    raw = load_text(file_path)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        okrs = data.get("okrs", data.get("objectives", []))
        if not okrs and "objective" in data:
            okrs = [data]
        return okrs
    print("Error: JSON must be a list of OKRs or contain 'okrs' key.", file=sys.stderr)
    sys.exit(1)


def print_table(result: dict) -> None:
    """Print a human-readable table of dimension scores."""
    total = result.get("total_score_10", 0)
    passed = result.get("passed", False)
    status = "PASS" if passed else "FAIL"

    print(f"\n{'=' * 60}")
    print(f"  BCG Evaluation — {result.get('framework', '8-Dimension Rubric')}")
    print(f"{'=' * 60}")
    print(f"  Total Score:  {total}/10.0  [{status}]")
    print(f"  Score (100):  {result.get('total_score_100', 0)}%")
    print(f"{'=' * 60}\n")

    dims = result.get("dimensions", {})
    order = result.get("dimension_order", list(dims.keys()))
    print(f"  {'Dimension':<30} {'Score':<8} {'Weight':<8} {'Contrib':<8} {'Label'}")
    print(f"  {'-' * 78}")
    for dim_id in order:
        d = dims.get(dim_id, {})
        score = d.get("score", 0)
        weight = d.get("weight", 0)
        contrib = d.get("weighted", 0)
        label = d.get("label", "")[:45]
        print(f"  {dim_id:<30} {score}/5{'':<5} {weight:<8} {contrib:<8} {label}")

    print(f"\n  Threshold: 7.0/10 → {'PASS' if passed else 'FAIL'}")
    print(f"  Generated: {result.get('generated_at', 'N/A')}")
    print(f"{'=' * 60}\n")


def print_okr_table(result: dict) -> None:
    """Print OKR evaluation results."""
    total_score = result.get("score_100", 0)
    passed = result.get("passed", False)
    status = "PASS" if passed else "FAIL"

    print(f"\n{'=' * 60}")
    print("  OKR Quality Checklist")
    print(f"{'=' * 60}")
    print(f"  Total OKRs:  {result.get('total_okrs', 0)}")
    print(f"  Avg Score:   {total_score}%  [{status}]")
    print(f"{'=' * 60}\n")

    for check in result.get("checks", []):
        scores = check.get("scores", {})
        total = check.get("total", 0)
        print(f"  OKR #{check.get('okr_index', '?')}: {check.get('objective', 'N/A')}")
        print(f"    Score: {total}%")
        for criterion, val in scores.items():
            mark = "✓" if val else "✗"
            print(f"    {mark} {criterion}")
        print()

    print(f"  Threshold: 70% → {'PASS' if passed else 'FAIL'}")
    print(f"  Generated: {result.get('generated_at', 'N/A')}")
    print(f"{'=' * 60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="BCG Evaluation CLI — evalúa outputs estratégicos (threshold 7.0/10)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  bcg_eval_cli.py report.md\n"
            "  cat report.md | bcg_eval_cli.py\n"
            "  bcg_eval_cli.py --okrs objectives.json\n"
            "  bcg_eval_cli.py --okrs objectives.json --format json\n"
        ),
    )
    parser.add_argument("file", nargs="?", help="Archivo de texto a evaluar")
    parser.add_argument(
        "--okrs", nargs="?", const="-", metavar="FILE", help="Evaluar OKRs desde archivo JSON (o stdin)"
    )
    parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Formato de output (default: table)"
    )

    args = parser.parse_args()

    if args.okrs is not None:
        okrs_file = None if args.okrs == "-" else args.okrs
        result = evaluate_okrs(load_okrs(okrs_file))
    else:
        text = load_text(args.file)
        result = evaluate_strategy(text)

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.okrs is not None:
        print_okr_table(result)
    else:
        print_table(result)

    sys.exit(0 if result.get("passed", False) else 1)


if __name__ == "__main__":
    main()
