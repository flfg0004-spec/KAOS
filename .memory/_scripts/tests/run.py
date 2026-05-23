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
os.environ["OPENAI_API_KEY"] = "sk-test-dummy"
import importlib
import time
import signal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TEST_TIMEOUT = 90  # seconds per test (embedding model loading takes ~15-20s)

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
    "test_quality",
    "test_dashboard",
    "test_health",
    "test_context_cycle",
    "test_orchestrator",
    "test_memory_persistence",
]


def run_all() -> int:
    passed = 0
    failed = 0
    total_tests = 0
    start = time.time()

    def _run_test(mod, test_name):
        import threading
        result = {"exc": None}

        def _target():
            try:
                getattr(mod, test_name)()
            except Exception as e:
                result["exc"] = e

        t = threading.Thread(target=_target, daemon=True)
        t.start()
        t.join(timeout=TEST_TIMEOUT)
        if t.is_alive():
            return "TIMEOUT"
        if result["exc"] is None:
            return "PASS"
        return result["exc"]

    for mod_name in MODULES:
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:
            print(f"  ERROR loading {mod_name}: {e}")
            failed += 1
            continue

        tests = [f for f in dir(mod) if f.startswith("test_")]
        for test_name in tests:
            total_tests += 1
            r = _run_test(mod, test_name)
            if r == "PASS":
                passed += 1
                print(f"  ✅ {mod_name}.{test_name}")
            elif r == "TIMEOUT":
                failed += 1
                print(f"  ⏰ {mod_name}.{test_name}: TIMEOUT ({TEST_TIMEOUT}s)")
            elif isinstance(r, AssertionError):
                failed += 1
                print(f"  ❌ {mod_name}.{test_name}: {r}")
            else:
                failed += 1
                print(f"  ❌ {mod_name}.{test_name}: ERROR {r}")

    elapsed = time.time() - start
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {total_tests} total")
    print(f"Time: {elapsed:.2f}s")
    _cache = os.path.join(os.path.dirname(__file__), "..", "..", "cache", "test-results.json")
    os.makedirs(os.path.dirname(_cache), exist_ok=True)
    with open(_cache, "w") as _f:
        json.dump({"passed": passed, "failed": failed, "total": total_tests}, _f)
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(run_all())
