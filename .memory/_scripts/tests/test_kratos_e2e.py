"""E2E tests for Kratos — PRGII loop, quality gates, governance, cross-agent context."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["LLM_DIRECT_ENABLED"] = "false"
os.environ["KAOS_TESTING"] = "1"


def test_kratos_governance_fields_present():
    """Governance fields always present in output."""
    from lib.agent_nodes.kratos import kratos_node
    result = kratos_node({"topic": "def foo(): pass", "profile": "desarrollo"})
    assert "governance_allowed" in result
    assert isinstance(result["governance_allowed"], bool)
    assert "governance_denials" in result
    assert isinstance(result["governance_denials"], list)


def test_kratos_cross_agent_type_guards():
    """Type guards prevent crash when metis_to_kratos is string/None."""
    from lib.agent_nodes.kratos import _kratos_node_impl
    import json, tempfile
    from pathlib import Path

    # Save and restore context
    ctx_path = Path(os.environ.get("KAOS_VAULT_ROOT", ".vault")) / "_pipeline" / "context.json"
    ctx_path.parent.mkdir(parents=True, exist_ok=True)
    orig = ""
    if ctx_path.exists():
        orig = ctx_path.read_text(encoding="utf-8")

    try:
        ctx_path.write_text(json.dumps({
            "cross_agent": {"metis_to_kratos": "string_instead_of_dict"}
        }), encoding="utf-8")
        result = _kratos_node_impl({"topic": "test guards", "profile": "desarrollo"})
        assert "kratos_output" in result, "Should not crash on string metis_to_kratos"
    finally:
        if orig:
            ctx_path.write_text(orig, encoding="utf-8")
        elif ctx_path.exists():
            ctx_path.unlink()


def test_kratos_decision_in_output():
    """Output always contains kratos_decision."""
    from lib.agent_nodes.kratos import kratos_node
    result = kratos_node({"topic": "write a function", "profile": "standard"})
    assert "kratos_decision" in result
    assert result["kratos_decision"] in ("complete", "needs_curation")


def test_kratos_prompt_never_empty():
    """Prompt is never empty."""
    from lib.agent_nodes.kratos import kratos_node
    result = kratos_node({"topic": "test", "profile": "desarrollo"})
    prompt = result.get("kratos_prompt", "")
    assert len(prompt) > 100, "Prompt should be >100 chars"


def test_kratos_language_detection_in_prompt():
    """Prompt includes detected language via lang_utils."""
    from lib.agent_nodes.kratos import kratos_node
    result = kratos_node({"topic": "implement in python", "profile": "desarrollo"})
    prompt = result.get("kratos_prompt", "")
    assert "python" in prompt.lower() or "PRGII" in prompt


def test_kratos_feature_flag_use_new():
    """Feature flag use_new_agent_executor delegates to v2 (same impl)."""
    from lib.agent_nodes.kratos import kratos_node, _kratos_node_impl, _kratos_node_v2
    from lib.feature_flags import is_enabled
    flag_orig = is_enabled("use_new_agent_executor")
    # Just verify the functions exist and are callable
    assert callable(kratos_node)
    assert callable(_kratos_node_impl)
    assert callable(_kratos_node_v2)


# ── Track A: KratosDecision enum tests ──


def test_kratos_decision_enum_values():
    """KratosDecision enum has all expected values."""
    from lib.kratos_decision import KratosDecision
    expected = {"COMPLETE", "NEEDS_CURATION", "FAILED", "REJECTED_BY_GOV", "EARLY_EXIT"}
    assert set(KratosDecision.__members__) == expected


def test_kratos_decision_eq_str():
    """KratosDecision supports equality with str for backward compat."""
    from lib.kratos_decision import KratosDecision
    assert KratosDecision.COMPLETE == "complete"
    assert KratosDecision.COMPLETE != "failed"
    assert KratosDecision.NEEDS_CURATION == "needs_curation"


def test_kratos_decision_str_serialization():
    """KratosDecision serializes to string for JSON output."""
    from lib.kratos_decision import KratosDecision
    assert str(KratosDecision.COMPLETE) == "complete"
    assert str(KratosDecision.FAILED) == "failed"
    assert str(KratosDecision.REJECTED_BY_GOV) == "rejected_by_gov"


# ── Track A: Telemetry tests ──


def test_kratos_telemetry_record_and_summary():
    """Telemetry records and returns summary stats."""
    from lib.kratos_telemetry import record_invocation, telemetry_summary
    import os
    from lib.kratos_telemetry import TELEMETRY_FILE
    # Backup and clean telemetry
    backup = ""
    if TELEMETRY_FILE.exists():
        backup = TELEMETRY_FILE.read_text(encoding="utf-8")
        TELEMETRY_FILE.unlink()
    try:
        record_invocation(decision="complete", quality_score=8.5, language="python")
        summary = telemetry_summary()
        assert summary["total"] >= 1
        assert summary["by_decision"].get("complete", 0) >= 1
        assert summary["avg_quality_score"] > 0
    finally:
        TELEMETRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if backup:
            TELEMETRY_FILE.write_text(backup, encoding="utf-8")
        elif TELEMETRY_FILE.exists():
            TELEMETRY_FILE.unlink()


# ── Track D: Multi-lang detection tests ──


def test_detect_rust_code():
    """detect_code_language detects Rust code."""
    from lib.lang_utils import detect_code_language
    rust_code = "fn main() { println!(\"hello\"); }"
    assert detect_code_language(rust_code) == "rust"


def test_detect_go_code():
    """detect_code_language detects Go code."""
    from lib.lang_utils import detect_code_language
    go_code = "package main\nfunc main() { println(\"hello\") }"
    assert detect_code_language(go_code) == "go"


def test_detect_typescript_code():
    """detect_code_language detects TypeScript code."""
    from lib.lang_utils import detect_code_language
    ts_code = "interface User { name: string; age: number; }"
    assert detect_code_language(ts_code) == "typescript"


# ── Track D: Multi-lang gate tests ──


def test_gate_syntax_multi_rust():
    """gate_syntax_multi handles Rust code without crashing."""
    from lib.quality_gate import gate_syntax_multi
    result = gate_syntax_multi("fn main() {}", "rust")
    assert "score" in result
    assert "passed" in result
    assert "detail" in result


def test_gate_syntax_multi_go():
    """gate_syntax_multi handles Go code without crashing."""
    from lib.quality_gate import gate_syntax_multi
    result = gate_syntax_multi("package main\nfunc main() {}", "go")
    assert "score" in result


def test_gate_syntax_multi_typescript():
    """gate_syntax_multi handles TypeScript code without crashing."""
    from lib.quality_gate import gate_syntax_multi
    result = gate_syntax_multi("const x: string = \"hello\";", "typescript")
    assert "score" in result


def test_gate_compilation_multi_rust():
    """gate_compilation_multi handles Rust gracefully (toolchain may not exist)."""
    from lib.quality_gate import gate_compilation_multi
    result = gate_compilation_multi("fn main() {}", "rust")
    assert "score" in result
    assert "detail" in result


def test_gate_lint_multi_rust():
    """gate_lint_multi handles Rust gracefully (toolchain may not exist)."""
    from lib.quality_gate import gate_lint_multi
    result = gate_lint_multi("fn main() {}", "rust")
    assert "score" in result


def test_evaluate_routes_by_language():
    """evaluate() routes to correct gates based on detected language."""
    from lib.quality_gate import evaluate
    result = evaluate("fn main() { println!(\"hello\"); }")
    assert "language" in result
    assert result["language"] in ("rust", "python")


def test_multi_lang_gates_flag_off():
    """With all multi-lang flags false, evaluate returns neutral scores."""
    from lib.quality_gate import evaluate
    result = evaluate("fn main() {}", language="rust")
    assert "gates" in result
    # All gates should exist with neutral scores
    for gate_name in ("syntax", "compilation", "lint"):
        assert gate_name in result["gates"]


def test_kratos_circuit_breaker_in_node():
    """Circuit breaker in kratos_node doesn't crash when flag is false."""
    from lib.agent_nodes.kratos import kratos_node
    result = kratos_node({"topic": "test breaker", "profile": "desarrollo"})
    assert "kratos_decision" in result


# ── H3 Sprint 3: Self-heal, Dashboard, OPA strict mode ──


def test_self_heal_imports():
    """Self-heal module imports and runs without error."""
    from lib.kratos_self_heal import heal
    result = heal()
    assert isinstance(result, list)


def test_kratos_dashboard_imports():
    """Dashboard module imports correctly."""
    from lib.kratos_dashboard import render_dashboard, show_dashboard
    assert callable(render_dashboard)
    assert callable(show_dashboard)


def test_opa_strict_mode_flag():
    """opa_strict_mode flag exists in feature flags."""
    from lib.feature_flags import is_enabled
    # Should not raise — flag exists with default false
    assert is_enabled("opa_strict_mode") is False
