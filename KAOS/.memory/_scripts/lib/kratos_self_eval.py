"""Kratos Self-Evaluation — measures code generation quality across 5 dimensions."""

import ast
import logging
import re

_LOG = logging.getLogger(__name__)


def _check_syntax(code: str) -> tuple[bool, str]:
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, str(e)


def _check_security(code: str) -> list[str]:
    issues = []
    dangerous = [
        (r"exec\s*\(", "exec() usage"),
        (r"eval\s*\(", "eval() usage"),
        (r"__import__\s*\(", "__import__ usage"),
        (r"subprocess\.(call|Popen|run)\s*\(", "subprocess call"),
        (r"os\.system\s*\(", "os.system usage"),
        (r"pickle\.loads\s*\(", "pickle.loads (unsafe)"),
        (r"open\(.*['\"].*['\"]\s*,\s*['\"]w['\"]", "file write without validation"),
    ]
    for pattern, msg in dangerous:
        if re.search(pattern, code):
            issues.append(msg)
    return issues


def _estimate_complexity(code: str) -> dict:
    lines = code.strip().split("\n")
    total = len(lines)
    nested = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("for ", "while ", "if ", "elif ", "with ", "try ", "except ")):
            nested += 1
    return {"total_lines": total, "control_structures": nested}


def kratos_self_eval(agent: str, output: dict) -> dict:
    output = output or {}
    code = output.get("code", "")
    description = output.get("description", "")
    has_tests = bool(output.get("tests"))
    errors = output.get("errors", [])

    if not code:
        return {
            "agent": agent,
            "score": 0.0,
            "dimensions": {
                "correccion": {"score": 0.0, "justificacion": "No code provided"},
                "eficiencia": {"score": 0.0, "justificacion": "No code provided"},
                "estilo": {"score": 0.0, "justificacion": "No code provided"},
                "seguridad": {"score": 0.0, "justificacion": "No code provided"},
                "cobertura_tests": {"score": 0.0, "justificacion": "No code provided"},
            },
        }

    syntax_ok, syntax_err = _check_syntax(code)
    security_issues = _check_security(code)
    complexity = _estimate_complexity(code)

    correccion = 1.0 if syntax_ok else 0.3
    if errors:
        correccion = max(0.0, correccion - 0.1 * len(errors))
    correccion = max(0.0, min(1.0, correccion))

    control = complexity.get("control_structures", 0)
    eficiencia = 1.0
    if control > 15:
        eficiencia = 0.5
    elif control > 10:
        eficiencia = 0.7
    if complexity.get("total_lines", 0) > 500:
        eficiencia = max(0.1, eficiencia - 0.2)

    desc_ok = bool(description and len(description) > 20)
    estilo = 0.8 if desc_ok else 0.4
    if complexity.get("total_lines", 0) > 0:
        has_docstring = '"""' in code or "'''" in code
        if has_docstring:
            estilo = min(1.0, estilo + 0.1)

    seguridad = 1.0
    if security_issues:
        seguridad = max(0.0, 1.0 - 0.2 * len(security_issues))

    cobertura_tests = 1.0 if has_tests else 0.0

    score = round((correccion + eficiencia + estilo + seguridad + cobertura_tests) / 5, 2)

    return {
        "agent": agent,
        "score": score,
        "dimensions": {
            "correccion": {
                "score": correccion,
                "justificacion": "Syntax OK" if syntax_ok else f"Syntax error: {syntax_err}",
            },
            "eficiencia": {
                "score": eficiencia,
                "justificacion": f"{control} control structures, {complexity['total_lines']} lines",
            },
            "estilo": {
                "score": estilo,
                "justificacion": "Has docstring" if '"""' in code else "Missing docstring",
            },
            "seguridad": {
                "score": seguridad,
                "justificacion": (
                    f"{len(security_issues)} security patterns found"
                    if security_issues else "No security issues detected"
                ),
            },
            "cobertura_tests": {
                "score": cobertura_tests,
                "justificacion": "Tests included" if has_tests else "No tests found",
            },
        },
    }
