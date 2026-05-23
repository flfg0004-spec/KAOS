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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
]


def run_all() -> int:
    passed = 0
    failed = 0
    total_tests = 0
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
            total_tests += 1
            try:
                getattr(mod, test_name)()
                passed += 1
                print(f"  ✅ {mod_name}.{test_name}")
            except AssertionError as e:
                failed += 1
                print(f"  ❌ {mod_name}.{test_name}: {e}")
            except Exception as e:
                failed += 1
                print(f"  ❌ {mod_name}.{test_name}: ERROR {e}")

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
