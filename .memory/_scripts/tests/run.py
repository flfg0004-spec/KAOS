#!/usr/bin/env python3
"""Test runner for KAOS Memory Vault."""

import sys
import os
import json
os.environ["KAOS_TESTING"] = "1"
os.environ["LLM_DIRECT_ENABLED"] = "false"
os.environ["RAG_ENABLED"] = "false"
os.environ["HERMES_ENABLED"] = "false"
os.environ["EXECUTOR_ENABLED"] = "false"
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-not-real")
import importlib
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TEST_TIMEOUT = 120
SLOW_TIMEOUT = 180
FAST_ONLY = "--fast" in sys.argv
if FAST_ONLY:
    sys.argv.remove("--fast")

MODULES = [
    "test_config",
    "test_pressure",
    "test_lint",
    "test_pipeline",
    "test_dsol",
    "test_synapse",
    "test_llm_quality",
    "test_full_pipeline",
    "test_ingest",
    "test_embed",
    "test_graph_analysis",
    "test_crystallize",
    "test_tagger",
    "test_wikilinks",
    "test_gaps",
    "test_lifecycle",
    "test_contradictions",
    "test_quality",
    "test_dashboard",
    "test_health",
    "test_context_cycle",
    "test_orchestrator",
    "test_memory_persistence",
    "test_viz",
    "test_validator",
    "test_crossref",
    "test_gap_query",
    "test_report_engine",
    "test_strategy",
    "test_metis",
    "test_code_memory",
    "test_bandit",
    "test_ast_match",
    "test_quality_gate",
    "test_reflexion",
    "test_sleep_cycle",
    "test_crew_integration",
]

SLOW_MODULES = {
    "test_context_cycle", "test_memory_persistence",
    "test_full_pipeline", "test_llm_quality",
}

SLOW_TEST_PREFIXES = {"test_tagger_slow", "test_lifecycle_slow", "test_contradictions_slow", "test_wikilinks_slow"}


def _is_slow(mod, test_name):
    fn = getattr(mod, test_name, None)
    return fn is not None and getattr(fn, "_slow", False)


def _run_test(mod, test_name, timeout):
    result = {"exc": None}

    def _target():
        try:
            getattr(mod, test_name)()
        except Exception as e:
            result["exc"] = e

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        return "TIMEOUT"
    if result["exc"] is None:
        return "PASS"
    return result["exc"]


def run_all() -> int:
    passed = 0
    failed = 0
    total_tests = 0
    skipped = 0
    start = time.time()

    for mod_name in MODULES:
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:
            print(f"  ERROR loading {mod_name}: {e}")
            failed += 1
            continue

        tests = [f for f in dir(mod) if f.startswith("test_")]
        for test_name in tests:
            if FAST_ONLY and (_is_slow(mod, test_name) or mod_name in SLOW_TEST_PREFIXES):
                skipped += 1
                continue

            total_tests += 1
            timeout = SLOW_TIMEOUT if _is_slow(mod, test_name) else TEST_TIMEOUT
            r = _run_test(mod, test_name, timeout)
            if r == "PASS":
                passed += 1
                print(f"  ✅ {mod_name}.{test_name}")
            elif r == "TIMEOUT":
                failed += 1
                print(f"  ⏰ {mod_name}.{test_name}: TIMEOUT ({timeout}s)")
            elif isinstance(r, AssertionError):
                failed += 1
                print(f"  ❌ {mod_name}.{test_name}: {r}")
            else:
                failed += 1
                print(f"  ❌ {mod_name}.{test_name}: ERROR {r}")

    elapsed = time.time() - start
    print(f"\n{'='*50}")
    label = " (fast mode)" if FAST_ONLY else ""
    print(f"Results{label}: {passed} passed, {failed} failed, {total_tests} total" +
          (f", {skipped} skipped" if skipped else ""))
    print(f"Time: {elapsed:.2f}s")
    _cache = os.path.join(os.path.dirname(__file__), "..", "..", "cache", "test-results.json")
    os.makedirs(os.path.dirname(_cache), exist_ok=True)
    with open(_cache, "w") as _f:
        json.dump({"passed": passed, "failed": failed, "total": total_tests}, _f)
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(run_all())
