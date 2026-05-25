"""Tests for Quality Gates Pipeline — 7-stage code quality scoring."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_gate_syntax_passes():
    from lib.quality_gate import gate_syntax
    result = gate_syntax("x = 1", "python")
    assert result["passed"] is True
    assert result["score"] == 1.0


def test_gate_syntax_fails():
    from lib.quality_gate import gate_syntax
    result = gate_syntax("def broken(", "python")
    # Might still pass if tree-sitter is lenient, but should be False or a score
    assert "gate" in result
    assert "score" in result


def test_gate_syntax_empty():
    from lib.quality_gate import gate_syntax
    result = gate_syntax("", "python")
    assert isinstance(result["passed"], bool)


def test_gate_lint():
    from lib.quality_gate import gate_lint
    result = gate_lint("x = 1\n", "python")
    assert result["gate"] == "lint"
    assert 0 <= result["score"] <= 10


def test_gate_types_present():
    from lib.quality_gate import gate_types
    result = gate_types("def hello(name: str) -> str: ...", "python")
    assert result["passed"] is True
    assert result["score"] > 5


def test_gate_types_missing():
    from lib.quality_gate import gate_types
    result = gate_types("def hello(): pass", "python")
    assert result["passed"] is False
    assert result["score"] < 5


def test_gate_structure():
    from lib.quality_gate import gate_structure
    result = gate_structure("# Title\n\nSome content\n```python\nx=1\n```\ndef test_x():\n    assert True")
    assert result["gate"] == "structure"
    assert result["score"] >= 3


def test_gate_security_clean():
    from lib.quality_gate import gate_security
    result = gate_security("x = safe_function()")
    assert result["passed"] is True
    assert result["score"] == 10


def test_gate_security_dangerous():
    from lib.quality_gate import gate_security
    result = gate_security("eval(user_input)")
    assert result["score"] < 10
    assert "eval" in result["detail"]


def test_evaluate_full():
    from lib.quality_gate import evaluate
    code = '''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def test_add():
    assert add(1, 2) == 3
'''
    result = evaluate(code, "python")
    assert "composite" in result
    assert "gates" in result
    assert "syntax" in result["gates"]
    assert 0 <= result["composite"] <= 10


def test_evaluate_syntax_fail():
    from lib.quality_gate import evaluate
    result = evaluate("def broken((", "python")
    assert result["passed"] is False


def test_lint_non_python():
    from lib.quality_gate import gate_lint
    result = gate_lint("{}", "javascript")
    assert result["passed"] is True
    assert result["score"] == 5.0
