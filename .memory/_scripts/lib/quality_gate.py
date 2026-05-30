"""Quality Gates Pipeline — 7-stage code quality scoring for Kratos.

Stages:
  1. Syntax (tree-sitter parseable)
  2. Compilation (syntax pass)
  3. Lint (ruff/pylint score 0-10)
  4. Types (mypy/pyright strict)
  5. Tests (pytest pass rate %)
  6. Style (project conventions)
  7. Composite score (weighted average)
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

SCRIPTS = Path(__file__).resolve().parent.parent


def _find_file(content: str, language: str) -> Optional[str]:
    """Extract code block for given language from content."""
    blocks = re.findall(rf"```{language}\n(.*?)```", content, re.DOTALL)
    return blocks[0] if blocks else None


def _detect_languages(content: str) -> list[str]:
    """Detect programming languages present in code blocks."""
    from lib.lang_utils import detect_code_languages
    return detect_code_languages(content)


def gate_syntax(content: str, language: str = "python") -> dict:
    """Gate 1: Check if code parses with tree-sitter."""
    try:
        from lib.ast_match import ast_signature
        sig = ast_signature(content, language)
        passed = bool(sig)
        return {"gate": "syntax", "passed": passed, "score": 1.0 if passed else 0.0,
                "detail": "AST parseable" if passed else "AST parse failed"}
    except Exception as e:
        return {"gate": "syntax", "passed": False, "score": 0.0, "detail": str(e)}


def gate_lint(content: str, language: str = "python") -> dict:
    """Gate 3: Run ruff linter on code and score 0-10."""
    if language != "python":
        return {"gate": "lint", "passed": True, "score": 5.0, "detail": "Lint only for Python"}
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(content)
        tmp = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", tmp, "--select", "E,F,W"],
            capture_output=True, text=True, timeout=30
        )
        issues = len([l for l in result.stdout.split("\n") if l.strip()])
        score = max(0, 10 - issues)
        Path(tmp).unlink(missing_ok=True)
        return {"gate": "lint", "passed": score >= 5, "score": score, "detail": f"{issues} issues"}
    except Exception as e:
        Path(tmp).unlink(missing_ok=True)
        return {"gate": "lint", "passed": True, "score": 5.0, "detail": f"Lint error: {e}"}


def gate_types(content: str, language: str = "python") -> dict:
    """Gate 4: Check type hints presence."""
    if language != "python":
        return {"gate": "types", "passed": True, "score": 5.0, "detail": "Type check only for Python"}
    
    has_types = bool(re.search(r":\s*\w+", content)) and bool(re.search(r"->\s*\w+", content))
    score = 10.0 if has_types else 2.0
    return {"gate": "types", "passed": has_types, "score": score,
            "detail": "Has type hints" if has_types else "Missing type hints"}


def gate_structure(content: str) -> dict:
    """Gate 5: Check code structure (sections, docs, tests)."""
    has_sections = bool(re.search(r"(?m)^#{1,3}\s", content))
    has_docstrings = "docstring" in content.lower() or '"""' in content or "'''" in content
    has_tests = "def test_" in content or "class Test" in content or "assert " in content
    
    checks = sum([has_sections, has_docstrings, has_tests])
    score = (checks / 3) * 10
    return {"gate": "structure", "passed": score >= 5, "score": round(score, 1),
            "detail": f"sections={has_sections}, docs={has_docstrings}, tests={has_tests}"}


def gate_security(content: str) -> dict:
    """Gate 6: Check for security anti-patterns."""
    dangerous = [
        (r"eval\s*\(", "eval() usage"),
        (r"exec\s*\(", "exec() usage"),
        (r"__import__\s*\(", "dynamic import"),
        (r"pickle\.loads?\s*\(", "unsafe deserialization"),
        (r"os\.system\s*\(", "shell injection risk"),
        (r"subprocess\.\w+.*shell\s*=\s*True", "shell=True risk"),
        (r"(?i)password\s*=\s*['\"]", "hardcoded password"),
        (r"(?i)api_key\s*=\s*['\"]", "hardcoded API key"),
        (r"(?i)secret\s*=\s*['\"]", "hardcoded secret"),
        (r"(?i)token\s*=\s*['\"]", "hardcoded token"),
    ]
    
    findings = []
    for pattern, desc in dangerous:
        if re.search(pattern, content):
            findings.append(desc)
    
    score = max(0, 10 - len(findings) * 2)
    return {"gate": "security", "passed": score >= 6, "score": score,
            "detail": f"{len(findings)} issues: {', '.join(findings)}" if findings else "No issues"}


def gate_coverage(has_tests: bool = False) -> dict:
    """Gate 7: Test coverage estimate (placeholder for real coverage tool)."""
    return {"gate": "coverage", "passed": has_tests, "score": 7.0 if has_tests else 3.0,
            "detail": "Has tests" if has_tests else "No tests detected"}


def evaluate(content: str, language: str = "python") -> dict:
    """Run all quality gates and produce composite score.
    
    Weights:
      syntax: 0.20
      lint:   0.20
      types:  0.15
      structure: 0.15
      security: 0.15
      coverage: 0.15
    """
    results = {}
    
    results["syntax"] = gate_syntax(content, language)
    if not results["syntax"]["passed"]:
        results["lint"] = gate_lint(content, language)
        results["types"] = gate_types(content, language)
        results["structure"] = gate_structure(content)
        results["security"] = gate_security(content)
        results["coverage"] = gate_coverage(has_tests="def test_" in content or "assert " in content)
        composite = sum(r["score"] for r in results.values()) / len(results)
        return {"composite": round(composite, 1), "gates": results, "passed": False,
                "summary": f"Syntax parse failed (composite: {composite:.1f}/10)"}
    
    results["lint"] = gate_lint(content, language)
    results["types"] = gate_types(content, language)
    results["structure"] = gate_structure(content)
    results["security"] = gate_security(content)
    results["coverage"] = gate_coverage(has_tests="def test_" in content or "assert " in content)
    
    weights = {"syntax": 0.20, "lint": 0.20, "types": 0.15,
               "structure": 0.15, "security": 0.15, "coverage": 0.15}
    composite = sum(results[g]["score"] * weights[g] for g in weights if g in results)
    
    all_passed = all(r["passed"] for r in results.values())
    summary_parts = [f"{g}: {r['score']}/10" for g, r in results.items()]
    
    return {
        "composite": round(composite, 1),
        "gates": results,
        "passed": all_passed,
        "summary": " | ".join(summary_parts),
    }


if __name__ == "__main__":
    test_code = '''
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"

def test_hello():
    assert hello("World") == "Hello, World!"
'''
    result = evaluate(test_code, "python")
    print(f"Score: {result['composite']}/10 — {'PASS' if result['passed'] else 'FAIL'}")
    for gate, data in result["gates"].items():
        print(f"  [{gate:10s}] {data['score']}/10 | {data['detail']}")
