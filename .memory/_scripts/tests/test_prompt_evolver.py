"""Tests for Self-Evolving Prompts (SEMAG)."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_record_execution():
    from lib.prompt_evolver import record_execution
    result = record_execution("def foo(): pass", 7.5)
    assert result["status"] == "recorded"
    assert result["total"] >= 1


def test_detect_error_patterns():
    from lib.prompt_evolver import _detect_error_patterns
    patterns = _detect_error_patterns("lint error: unused import\nmypy: type mismatch")
    assert "lint_issues" in patterns
    assert "type_issues" in patterns


def test_detect_no_patterns():
    from lib.prompt_evolver import _detect_error_patterns
    patterns = _detect_error_patterns("perfect code with no issues")
    assert len(patterns) == 0


def test_analyze_early():
    from lib.prompt_evolver import analyze_and_evolve
    result = analyze_and_evolve(force=False)
    assert result["status"] in ("skipped", "analyzed", "evolved")


def test_analyze_force():
    from lib.prompt_evolver import analyze_and_evolve, record_execution
    for i in range(6):
        record_execution(f"code_{i}", 6.0 + (i % 3))
    result = analyze_and_evolve(force=True)
    assert result["status"] in ("analyzed", "evolved")


def test_status():
    from lib.prompt_evolver import status
    s = status()
    assert "current_variant" in s
    assert "total_variants" in s
    assert "total_executions" in s


def test_get_current_prompt():
    from lib.prompt_evolver import get_current_prompt_sections
    sections = get_current_prompt_sections()
    assert "methodology" in sections
    assert "code_rules" in sections
    assert "test_rules" in sections


def test_compute_variant_hash():
    from lib.prompt_evolver import _compute_variant_hash
    h = _compute_variant_hash({"a": "test"})
    assert len(h) == 12


def test_generate_variant():
    from lib.prompt_evolver import _generate_variant
    sections = _generate_variant(["lint_issues", "test_failures"])
    assert "code_rules" in sections
    assert "test_rules" in sections
    assert "ruff" in sections["code_rules"].lower()
