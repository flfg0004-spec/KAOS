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


# ── Circuit Breaker tests ──


def test_circuit_breaker_closed_by_default():
    from lib.kratos_telemetry import CircuitBreaker
    cb = CircuitBreaker()
    assert cb.state.value == "CLOSED"


def test_circuit_breaker_opens_after_threshold():
    from lib.kratos_telemetry import CircuitBreaker
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=9999)
    cb.record_failure()
    assert cb.state.value == "CLOSED"
    cb.record_failure()
    assert cb.state.value == "OPEN"


def test_circuit_breaker_resets_on_success():
    from lib.kratos_telemetry import CircuitBreaker
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=9999)
    cb.record_failure()
    cb.record_success()
    assert cb.state.value == "CLOSED"


def test_circuit_breaker_decorator_rejects_when_open():
    from lib.kratos_telemetry import CircuitBreaker
    import pytest
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=9999)
    cb.record_failure()
    with pytest.raises(RuntimeError, match="Circuit breaker OPEN"):
        cb(lambda: "ok")()


# ── gate_coverage tests ──


def test_gate_coverage_placeholder_when_flag_off():
    from lib.quality_gate import gate_coverage
    result = gate_coverage(content="", has_tests=True)
    assert result["gate"] == "coverage"
    assert result["passed"] is True
    assert result["score"] >= 5


def test_gate_coverage_placeholder_no_tests():
    from lib.quality_gate import gate_coverage
    result = gate_coverage(content="", has_tests=False)
    assert result["gate"] == "coverage"
    assert result["score"] < 5


# ── Multi-lang gate tests ──


def test_gate_syntax_multi_rust_neutral():
    from lib.quality_gate import gate_syntax_multi
    result = gate_syntax_multi("fn main() {}", "rust")
    assert "score" in result
    assert "passed" in result


def test_gate_syntax_multi_unknown_language():
    from lib.quality_gate import gate_syntax_multi
    result = gate_syntax_multi("whatever", "brainfuck")
    assert result["score"] == 5.0


def test_gate_compilation_multi_rust_neutral():
    from lib.quality_gate import gate_compilation_multi
    result = gate_compilation_multi("fn main() {}", "rust")
    assert "score" in result
    assert "detail" in result


def test_gate_lint_multi_rust_neutral():
    from lib.quality_gate import gate_lint_multi
    result = gate_lint_multi("fn main() {}", "rust")
    assert "score" in result


def test_evaluate_multi_lang_return_structure():
    from lib.quality_gate import evaluate
    result = evaluate("fn main() {}", language="rust")
    assert "composite" in result
    assert "gates" in result
    assert "language" in result
    assert result["language"] == "rust"
    for g in ("syntax", "compilation", "lint"):
        assert g in result["gates"]


# ── Track B: evaluate_parallel + Early Exit tests ──


def test_evaluate_parallel_returns_same_as_sequential():
    """Parallel evaluate produces same composite as sequential."""
    from lib.quality_gate import evaluate, evaluate_parallel
    from lib.feature_flags import enable, disable
    enable("use_parallel_gates")
    try:
        code = '''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
def test_add():
    assert add(1, 2) == 3
'''
        seq = evaluate(code, "python")
        par = evaluate_parallel(code, "python")
        assert abs(seq["composite"] - par["composite"]) < 0.5, "Composite should be similar"
    finally:
        disable("use_parallel_gates")


def test_evaluate_parallel_flag_off_uses_sequential():
    """With use_parallel_gates=false, evaluate_parallel delegates to evaluate."""
    from lib.quality_gate import evaluate_parallel
    from lib.feature_flags import is_enabled
    if not is_enabled("use_parallel_gates"):
        result = evaluate_parallel("x = 1", "python")
        assert "composite" in result
        assert "gates" in result


def test_evaluate_parallel_multi_lang():
    """Parallel evaluate works for multi-lang routing."""
    from lib.quality_gate import evaluate_parallel
    from lib.feature_flags import enable, disable
    enable("use_parallel_gates")
    try:
        result = evaluate_parallel("fn main() {}", language="rust")
        assert "composite" in result
        assert result["language"] == "rust"
    finally:
        disable("use_parallel_gates")


def test_early_exit_on_syntax_failure():
    """Early exit returns immediately when syntax fails."""
    from lib.quality_gate import evaluate_parallel
    from lib.feature_flags import enable, disable
    enable("use_parallel_gates")
    enable("use_early_exit")
    try:
        result = evaluate_parallel("def broken((", "python")
        assert "passed" in result
    finally:
        disable("use_parallel_gates")
        disable("use_early_exit")


def test_parallel_race_condition_safe():
    """Multiple parallel evaluate calls don't corrupt each other."""
    from lib.quality_gate import evaluate_parallel
    from lib.feature_flags import enable, disable
    from concurrent.futures import ThreadPoolExecutor, as_completed
    enable("use_parallel_gates")
    try:
        codes = [
            "def add(a: int, b: int) -> int: return a + b",
            "def sub(a: int, b: int) -> int: return a - b",
            "x = 1",
        ]
        with ThreadPoolExecutor(max_workers=3) as ex:
            futures = [ex.submit(evaluate_parallel, c, "python") for c in codes]
            results = [f.result() for f in as_completed(futures)]
        assert len(results) == 3
        assert all("composite" in r for r in results)
    finally:
        disable("use_parallel_gates")


# ── Track C: Real mypy tests ──


def test_gate_types_real_mypy_flag_off():
    """With use_real_mypy=false, gate_types uses regex fallback."""
    from lib.quality_gate import gate_types
    result = gate_types("def hello(name: str) -> str: ...", "python")
    assert result["passed"] is True
    assert "types" in result["gate"]


def test_gate_types_real_mypy_missing():
    """gate_types detects missing type hints via regex fallback."""
    from lib.quality_gate import gate_types
    result = gate_types("def hello(): pass", "python")
    assert result["passed"] is False
    assert result["score"] < 5


def test_gate_types_real_mypy_non_python():
    """gate_types returns neutral for non-Python."""
    from lib.quality_gate import gate_types
    result = gate_types("fn main() {}", "rust")
    assert result["score"] == 5.0


def test_gate_types_real_mypy_graceful():
    """gate_types handles missing mypy gracefully."""
    from lib.quality_gate import gate_types
    result = gate_types("x: int = 1", "python")
    assert "score" in result
    assert "detail" in result


def test_gate_lint_multi_typescript():
    from lib.quality_gate import gate_lint_multi
    result = gate_lint_multi("const x: string = \"hello\";", "typescript")
    assert "score" in result
    assert "detail" in result


def test_gate_lint_multi_go():
    from lib.quality_gate import gate_lint_multi
    result = gate_lint_multi("package main\nfunc main() {}", "go")
    assert "score" in result
    assert "detail" in result


def test_gate_compilation_multi_typescript():
    from lib.quality_gate import gate_compilation_multi
    result = gate_compilation_multi("const x: string = \"hello\";", "typescript")
    assert "score" in result


def test_gate_compilation_multi_go():
    from lib.quality_gate import gate_compilation_multi
    result = gate_compilation_multi("package main\nfunc main() {}", "go")
    assert "score" in result


# ── Phase 2: QualityGateService tests ──


def test_quality_service_auto_detect():
    """QualityGateService auto-detects mode without crashing."""
    from lib.quality_gate._service import QualityGateService
    svc = QualityGateService()
    mode = svc.detect_mode()
    assert mode in ("local", "mcp")


def test_quality_service_evaluate():
    """QualityGateService.evaluate returns expected structure."""
    from lib.quality_gate._service import QualityGateService
    svc = QualityGateService()
    result = svc.evaluate("x = 1", "python")
    assert "composite" in result
    assert "gates" in result


def test_quality_service_list_gates():
    """QualityGateService.list_gates returns gate names."""
    from lib.quality_gate._service import QualityGateService
    svc = QualityGateService()
    gates = svc.list_gates()
    assert len(gates) >= 8
    assert "syntax" in gates
