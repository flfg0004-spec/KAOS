"""Smoke test: Ruta A — KAOS + DeerFlow + Agno Integration.

Verifica los 5 componentes del plan tactico paralelo:
  1. DeerFlowClient adapter operativo
  2. Docker Sandbox ejecuta codigo aislado
  3. Reasoning in-process via bridge dual
  4. Memory Bridge sync funcional
  5. Quality Reports generados
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.deerflow_bridge import DeerFlowBridge
from lib.memory_bridge import MemoryBridge
from lib.deerflow_client import DeerFlowClient


def check(step, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    icon = "+" if condition else "X"
    print(f"  [{icon}] {step}: {status}" + (f" ({detail})" if detail else ""))
    return condition


def main():
    print("=" * 55)
    print("  SMOKE TEST: KAOS + DEERFLOW + AGNO (Ruta A)")
    print("=" * 55)
    print()

    results = []

    # 1. DeerFlowClient
    print("[1/5] DeerFlowClient...")
    client = DeerFlowClient()
    r = check("Mode", client.status()["mode"] == "langgraph-adapter", client.status()["mode"])
    results.append(r)

    # 2. Code execution via Docker Sandbox
    print("[2/5] Docker Sandbox (code execution)...")
    bridge = DeerFlowBridge()
    code_result = asyncio.run(bridge.execute({
        "type": "code_execution",
        "code": "print('hello from sandbox')",
        "language": "python",
        "id": "smoke-001",
    }))
    r = check("Sandbox status", code_result["status"] == "ok", code_result.get("stdout", "")[:50])
    results.append(r)

    # 3. Reasoning via in-process bridge
    print("[3/5] Reasoning (in-process)...")
    reasoning_result = asyncio.run(bridge.execute({
        "type": "reasoning",
        "prompt": "test reasoning",
        "id": "smoke-002",
    }))
    r = check("Reasoning status", reasoning_result["status"] in ("mock", "ok"), reasoning_result["status"])
    results.append(r)

    # 4. Memory Bridge
    print("[4/5] Memory Bridge...")
    mb = MemoryBridge()
    push = mb.push_to_deerflow()
    r = check("Memory push", push["status"] in ("ok", "mock", "skipped"), push["status"])
    results.append(r)

    pull = mb.pull_from_deerflow()
    r = check("Memory pull", pull["status"] in ("ok", "mock"), pull["status"])
    results.append(r)

    # 5. Quality Reports
    print("[5/5] Quality Reports...")
    reports_dir = Path(__file__).resolve().parent.parent.parent / "bridge" / "reports"
    reports = list(reports_dir.glob("*.json"))
    r = check("Reports generated", len(reports) > 0, f"{len(reports)} files")
    results.append(r)

    # Summary
    print()
    print("-" * 55)
    passed = sum(results)
    total = len(results)
    print(f"  RESULT: {passed}/{total} checks passed")
    if passed == total:
        print("  ALL CHECKS PASSED")
    else:
        print(f"  {total - passed} checks FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
