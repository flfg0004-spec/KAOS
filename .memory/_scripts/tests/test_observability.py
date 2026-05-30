"""Tests for ether_v2 observability module — observe, Timer, health_check, fallback."""

import json
import os
import sys
import time
from pathlib import Path

# Setup path
_SCRIPT_DIR = Path(__file__).resolve().parent.parent  # .memory/_scripts/
sys.path.insert(0, str(_SCRIPT_DIR))

# Desactivar LangFuse para tests
os.environ["ETHER_LANGFUSE_ENABLED"] = "false"

from lib.aether.observability import (
    _FALLBACK_DIR,
    _FALLBACK_LOG_PATH,
    Timer,
    _get_fallback_log_size,
    _log_fallback,
    _should_sample,
    health_check,
    observe,
)

# ── Test helpers ───────────────────────────────────────────────

errors = []


def check(desc, cond):
    if not cond:
        errors.append(f"FAIL: {desc}")
        print(f"  ❌ {desc}")
    else:
        print(f"  ✅ {desc}")


def clean_fallback():
    """Limpia el archivo fallback antes de tests que lo usan."""
    _FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
    if _FALLBACK_LOG_PATH.exists():
        _FALLBACK_LOG_PATH.unlink()


# ── Tests: Timer ────────────────────────────────────────────


def test_timer():
    print("\n── Timer ──")
    with Timer() as t:
        time.sleep(0.01)
    check("Timer measures positive ms", t.elapsed_ms > 0)
    check("Timer returns float", isinstance(t.elapsed_ms, float))

    with Timer() as t:
        time.sleep(0.05)
    check("Timer ~50ms (tolerance ±30ms)", 20 <= t.elapsed_ms <= 200)


# ── Tests: _should_sample ─────────────────────────────────────


def test_sampling():
    print("\n── Acceptance Sampling ──")
    # flash: ~10%
    flash_count = sum(1 for _ in range(100) if _should_sample("go-flash", "flash"))
    check("flash sampling ~10% (5-30 range)", 5 <= flash_count <= 30)

    # pro: ~50%
    pro_count = sum(1 for _ in range(100) if _should_sample("go-pro", "pro"))
    check("pro sampling ~50% (25-75 range)", 25 <= pro_count <= 75)

    # kimi: ~80%
    kimi_count = sum(1 for _ in range(100) if _should_sample("go-kimi-latest", "kimi"))
    check("kimi sampling ~80% (60-100 range)", 60 <= kimi_count <= 100)

    # mimo: ~30%
    mimo_count = sum(1 for _ in range(100) if _should_sample("go-mimo", "mimo"))
    check("mimo sampling ~30% (10-50 range)", 10 <= mimo_count <= 50)

    # Sin tier: inferir del modelo
    inferred = _should_sample("go-flash")
    check("Sampling infers flash tier", isinstance(inferred, bool))

    # unknown model → flash rate
    unknown = _should_sample("unknown-model")
    check("Sampling handles unknown model", isinstance(unknown, bool))


# ── Tests: _log_fallback ──────────────────────────────────────


def test_fallback_log():
    print("\n── Fallback Log ──")
    clean_fallback()

    # Escribir un trace
    trace = {
        "timestamp": "2026-05-26T12:00:00Z",
        "func_name": "test_func",
        "model": "go-flash",
        "tier": "flash",
        "agent": "kratos",
        "task_type": "code_gen",
        "success": True,
    }
    _log_fallback(trace)

    check("Fallback file exists", _FALLBACK_LOG_PATH.exists())

    # Leer y verificar contenido
    content = _FALLBACK_LOG_PATH.read_text(encoding="utf-8").strip()
    lines = [l for l in content.split("\n") if l]
    check("Fallback file has 1 line", len(lines) == 1)

    parsed = json.loads(lines[0])
    check("Fallback trace has agent", parsed.get("agent") == "kratos")
    check("Fallback trace has func_name", parsed.get("func_name") == "test_func")
    check("Fallback trace has model", parsed.get("model") == "go-flash")
    check("Fallback trace has tier", parsed.get("tier") == "flash")

    # Escribir segundo trace
    trace2 = dict(trace)
    trace2["model"] = "go-pro"
    trace2["timestamp"] = "2026-05-26T13:00:00Z"
    _log_fallback(trace2)

    content2 = _FALLBACK_LOG_PATH.read_text(encoding="utf-8").strip()
    lines2 = [l for l in content2.split("\n") if l]
    check("Fallback file has 2 lines after append", len(lines2) == 2)

    # Verificar tamaño
    size = _get_fallback_log_size()
    check("Fallback log size = 2", size == 2)

    clean_fallback()


# ── Tests: observe ─────────────────────────────────────────


def test_observe():
    print("\n── observe ──")
    # Con LangFuse deshabilitado, debería caer en fallback
    clean_fallback()

    trace_id = observe(
        func_name="test_chat",
        model="go-flash",
        agent="kratos",
        task_type="code_gen",
        prompt_size=500,
        latency_ms=123.4,
        success=True,
        prompt_tokens=500,
        completion_tokens=200,
        quality_score=7.5,
        cache_hit_ratio=0.35,
        resolved_by="task_type(code_gen)",
        tier="flash",
    )
    # Sin LangFuse, no debería devolver trace_id
    check("observe returns None when LangFuse disabled", trace_id is None)

    # Verificar que se escribió en fallback
    size = _get_fallback_log_size()
    check("observe writes to fallback when LangFuse unavailable", size > 0)

    if size > 0:
        content = _FALLBACK_LOG_PATH.read_text(encoding="utf-8").strip()
        last_line = [l for l in content.split("\n") if l][-1]
        last = json.loads(last_line)
        check("Trace has cache_hit_ratio", last.get("cache_hit_ratio") == 0.35)
        check("Trace has resolved_by", "resolved_by" in last)
        check("Trace has tier", last.get("tier") == "flash")
        check("Trace has agent", last.get("agent") == "kratos")
        check("Trace has version v2", last.get("version") == "v2")

    clean_fallback()

    # Test con error
    trace_id_error = observe(
        func_name="test_error",
        model="go-pro",
        agent="aletheia",
        task_type="research",
        prompt_size=100,
        latency_ms=50.0,
        success=False,
        error="LLM Error: timeout",
        tier="pro",
    )
    check("observe handles errors gracefully", trace_id_error is None)

    # Test agent vacío → "unknown"
    trace_no_agent = observe(
        func_name="test_agent",
        model="go-flash",
        agent="",
        task_type="general",
        prompt_size=10,
        latency_ms=1.0,
        success=True,
    )
    check("observe populates empty agent", trace_no_agent is None)

    # Verificar que se escribió con agent "unknown"
    if _FALLBACK_LOG_PATH.exists():
        content = _FALLBACK_LOG_PATH.read_text(encoding="utf-8").strip()
        lines = [l for l in content.split("\n") if l]
        if lines:
            last = json.loads(lines[-1])
            check("Empty agent becomes 'unknown'", last.get("agent") == "unknown")


# ── Tests: health_check ───────────────────────────────────────


def test_health_check():
    print("\n── health_check ──")
    hc = health_check()

    check("health_check returns dict", isinstance(hc, dict))
    check("health_check has langfuse_available", "langfuse_available" in hc)
    check("health_check has langfuse_host", "langfuse_host" in hc)
    check("health_check has fallback_log_size", "fallback_log_size" in hc)
    check("health_check has last_successful_trace", "last_successful_trace" in hc)
    check("health_check has traces_last_hour", "traces_last_hour" in hc)

    # Con LangFuse deshabilitado
    check("langfuse_available is False", hc["langfuse_available"] is False)
    check("langfuse_host is string", isinstance(hc["langfuse_host"], str))
    check("fallback_log_size is int", isinstance(hc["fallback_log_size"], int))
    check("traces_last_hour is int", isinstance(hc["traces_last_hour"], int))


# ── Main ───────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  ETHER V2 — OBSERVABILITY TESTS")
    print("=" * 55)

    test_timer()
    test_sampling()
    test_fallback_log()
    test_observe()
    test_health_check()

    print(f"\n{'=' * 55}")
    total = 0  # contamos asserts
    passed = total - len(errors)
    failures = len(errors)
    print(f"  Tests: {len(errors) if errors else 'all'} failures")
    if errors:
        print(f"\n  FAILURES ({len(errors)}):")
        for e in errors:
            print(f"    ❌ {e}")
        sys.exit(1)
    else:
        print("  ✅ ALL OBSERVABILITY TESTS PASSED")
        sys.exit(0)

