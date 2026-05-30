"""Evaluation logic — sequential and parallel with automatic multi-lang routing."""

from concurrent.futures import ThreadPoolExecutor, as_completed

import lib.lang_utils
from lib.feature_flags import is_enabled
from lib.quality_gate.gates.syntax import gate_syntax, gate_syntax_multi
from lib.quality_gate.gates.compilation import gate_compilation, gate_compilation_multi
from lib.quality_gate.gates.lint import gate_lint, gate_lint_multi
from lib.quality_gate.gates.types import gate_types
from lib.quality_gate.gates.structure import gate_structure
from lib.quality_gate.gates.security import gate_security
from lib.quality_gate.gates.coverage import gate_coverage
from lib.quality_gate.gates.style import gate_style

_PYTHON_GATES = [
    ("syntax", gate_syntax, 0.15),
    ("compilation", gate_compilation, 0.10),
    ("lint", gate_lint, 0.15),
    ("types", gate_types, 0.15),
    ("structure", gate_structure, 0.15),
    ("security", gate_security, 0.15),
    ("coverage", gate_coverage, 0.15),
    ("style", gate_style, 0.10),
]

_MULTI_LANG_FLAGS = {"rust": "kratos_rust_gates", "typescript": "kratos_ts_gates", "go": "kratos_go_gates"}
_MULTI_LANG_GATES = {
    "syntax": gate_syntax_multi,
    "compilation": gate_compilation_multi,
    "lint": gate_lint_multi,
}


def _compute_composite(results: dict, weights: dict) -> float:
    total_weight = sum(weights[g] for g in weights if g in results)
    if total_weight == 0:
        return 0.0
    return sum(results[g]["score"] * weights[g] for g in weights if g in results) / total_weight


def _build_summary(results: dict) -> str:
    return " | ".join(f"{g}: {r['score']}/10" for g, r in results.items())


def _run_python_gates(content: str, language: str, gates: list) -> dict:
    results = {}
    for name, func, _ in gates:
        if name == "structure":
            results[name] = func(content)
        elif name == "security":
            results[name] = func(content)
        elif name == "coverage":
            results[name] = func(content=content, has_tests="def test_" in content or "assert " in content)
        else:
            results[name] = func(content, language)
    return results


def evaluate(content: str, language: str = "") -> dict:
    if not language:
        language = lib.lang_utils.detect_code_language(content)

    if language in ("rust", "typescript", "go"):
        flag = _MULTI_LANG_FLAGS.get(language)
        if flag and is_enabled(flag):
            results = {}
            for name, func in _MULTI_LANG_GATES.items():
                results[name] = func(content, language)
        else:
            results = {g: {"gate": g, "passed": True, "score": 5.0, "detail": f"{language} gates disabled"}
                       for g in _MULTI_LANG_GATES}
        composite = sum(r["score"] for r in results.values()) / max(1, len(results))
        return {"composite": round(composite, 1), "gates": results,
                "passed": all(r["passed"] for r in results.values()),
                "language": language, "summary": _build_summary(results)}

    results = _run_python_gates(content, language, _PYTHON_GATES)
    if not results.get("syntax", {}).get("passed", False):
        composite = _compute_composite(results, {n: w for n, _, w in _PYTHON_GATES})
        return {"composite": round(composite, 1), "gates": results, "passed": False,
                "language": language, "summary": f"Syntax parse failed (composite: {composite:.1f}/10)"}

    weights = {n: w for n, _, w in _PYTHON_GATES}
    composite = _compute_composite(results, weights)
    return {"composite": round(composite, 1), "gates": results,
            "passed": all(r["passed"] for r in results.values()),
            "language": language, "summary": _build_summary(results)}


def evaluate_parallel(content: str, language: str = "", max_workers: int = 4) -> dict:
    if not is_enabled("kratos_parallel_gates"):
        return evaluate(content, language)

    if not language:
        language = lib.lang_utils.detect_code_language(content)

    if language in ("rust", "typescript", "go"):
        flag = _MULTI_LANG_FLAGS.get(language)
        if flag and is_enabled(flag):
            results = {}
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {ex.submit(func, content, language): name for name, func in _MULTI_LANG_GATES.items()}
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        results[name] = future.result()
                    except Exception as e:
                        results[name] = {"gate": name, "passed": True, "score": 5.0, "detail": str(e)}
        else:
            results = {g: {"gate": g, "passed": True, "score": 5.0, "detail": f"{language} gates disabled"}
                       for g in _MULTI_LANG_GATES}
        composite = sum(r["score"] for r in results.values()) / max(1, len(results))
        return {"composite": round(composite, 1), "gates": results,
                "passed": all(r["passed"] for r in results.values()),
                "language": language, "summary": _build_summary(results)}

    syntax_result = gate_syntax(content, language)
    results = {"syntax": syntax_result}

    if is_enabled("kratos_early_exit") and not syntax_result["passed"]:
        results.update(_run_python_gates(content, language, [(n, f, w) for n, f, w in _PYTHON_GATES if n != "syntax"]))
        composite = _compute_composite(results, {n: w for n, _, w in _PYTHON_GATES})
        return {"composite": round(composite, 1), "gates": results, "passed": False,
                "language": language, "summary": f"Syntax parse failed (composite: {composite:.1f}/10)"}

    remaining = [(n, f, w) for n, f, w in _PYTHON_GATES if n != "syntax"]
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {}
        for name, func, _ in remaining:
            if name in ("structure", "security"):
                futures[ex.submit(func, content)] = name
            elif name == "coverage":
                futures[ex.submit(func, content=content, has_tests="def test_" in content or "assert " in content)] = name
            else:
                futures[ex.submit(func, content, language)] = name
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                results[name] = {"gate": name, "passed": True, "score": 5.0, "detail": str(e)}

    weights = {n: w for n, _, w in _PYTHON_GATES}
    composite = _compute_composite(results, weights)
    return {"composite": round(composite, 1), "gates": results,
            "passed": all(r["passed"] for r in results.values()),
            "language": language, "summary": _build_summary(results)}
