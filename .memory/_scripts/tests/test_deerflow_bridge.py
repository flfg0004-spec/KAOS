"""Tests for DeerFlowBridge, AgnoGateway, and MemoryBridge.

ADR-012: Verifica que los 3 puentes de integracion:
  1. Operan en modo mock cuando DeerFlow/Agno no estan instalados
  2. Producen DeerFlowQualityReport validos
  3. Degradan gradualmente sin bloquear el pipeline
"""

import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DEERFLOW_SANDBOX_URL", "http://localhost:8001")

from datetime import datetime
from lib.deerflow_bridge import DeerFlowBridge, DeerFlowQualityReport
from lib.agno_gateway import AgnoGateway
from lib.memory_bridge import MemoryBridge


# ── DeerFlowBridge Tests ────────────────────────────────────

def test_bridge_mock_mode():
    bridge = DeerFlowBridge()
    status = bridge.status()
    assert "available" in status
    assert "mock_mode" in status


def test_bridge_execute_mock():
    bridge = DeerFlowBridge()
    result = bridge._mock_execute(
        {"type": "reasoning", "prompt": "test task", "id": "test-001"},
        "test-001",
        start=datetime.now(),
    )
    assert result["status"] == "mock"
    assert "quality_report" in result
    assert result["quality_report"]["task_id"] == "test-001"


import asyncio

def _run_async(coro):
    return asyncio.run(coro)


def test_bridge_execute_reasoning():
    bridge = DeerFlowBridge()
    result = _run_async(bridge.execute({
        "type": "reasoning",
        "prompt": "analiza este codigo",
        "id": "test-reasoning-001",
    }))
    assert result["status"] in ("mock", "ok", "error")


def test_bridge_execute_code():
    bridge = DeerFlowBridge()
    result = _run_async(bridge.execute({
        "type": "code_execution",
        "code": "print('hello')",
        "language": "python",
        "id": "test-code-001",
    }))
    assert result["status"] in ("mock", "ok", "error")


def test_bridge_detects_sandbox():
    bridge = DeerFlowBridge()
    assert bridge._needs_sandbox({"type": "code_execution"}) is True
    assert bridge._needs_sandbox({"type": "reasoning"}) is False
    assert bridge._needs_sandbox({"type": "external_request"}) is True
    assert bridge._needs_sandbox({"type": "untrusted"}) is True
    assert bridge._needs_sandbox({"type": "analysis"}) is False


# ── DeerFlowQualityReport Tests ─────────────────────────────

def test_quality_report_creation():
    report = DeerFlowQualityReport(
        task_id="test-001",
        agent="deerflow-test",
        execution_time_ms=150,
        token_usage={"input": 100, "output": 50},
        error_count=0,
        steps=["plan", "execute", "verify"],
        confidence=0.85,
        output_summary="Test output summary",
    )
    data = report.to_dict()
    assert data["task_id"] == "test-001"
    assert data["agent"] == "deerflow-test"
    assert data["execution_time_ms"] == 150
    assert data["confidence_score"] == 0.85
    assert data["error_count"] == 0


def test_quality_report_save():
    import tempfile
    report = DeerFlowQualityReport(
        task_id="test-save-001",
        agent="deerflow-test",
        execution_time_ms=100,
        token_usage={},
        error_count=0,
        steps=["test"],
        confidence=0.5,
        output_summary="save test",
    )
    path = report.save()
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["task_id"] == "test-save-001"
    path.unlink()


# ── AgnoGateway Tests ──────────────────────────────────────

def test_agno_mock_mode():
    gateway = AgnoGateway()
    status = gateway.status()
    assert "available" in status
    assert "mock_mode" in status
    assert "tools_registered" in status


def test_agno_register_tool():
    gateway = AgnoGateway()

    def dummy_tool(param: str) -> str:
        return f"processed: {param}"

    gateway.register_tool("test_tool", dummy_tool, "A test tool")
    assert "test_tool" in gateway.tools
    assert gateway.tools["test_tool"]["description"] == "A test tool"


def test_agno_start_stop():
    gateway = AgnoGateway()
    gateway.register_tool("test", lambda: "ok", "test")
    gateway.start()
    status = gateway.status()
    assert status["mock_mode"] is True  # En CI debe estar en mock
    gateway.stop()


# ── Kaos MCP Tools Tests ───────────────────────────────────

def test_vault_read_mock():
    from lib.agno_gateway import _vault_read
    result = _vault_read(".memory/wiki/index.md")
    assert isinstance(result, str)
    assert len(result) > 0


def test_vault_search_mock():
    from lib.agno_gateway import _vault_search
    result = _vault_search("index")
    assert isinstance(result, str)


def test_kaos_research_mock():
    from lib.agno_gateway import _kaos_research
    result = _kaos_research("test topic")
    assert isinstance(result, str)


# ── MemoryBridge Tests ─────────────────────────────────────

def test_memory_bridge_mock():
    bridge = MemoryBridge()
    status = bridge.status()
    assert "deerflow_available" in status
    assert "last_sync" in status


def test_memory_bridge_push():
    bridge = MemoryBridge()
    result = bridge.push_to_deerflow()
    assert "status" in result
    assert result["status"] in ("ok", "mock", "skipped", "error")


def test_memory_bridge_pull():
    bridge = MemoryBridge()
    result = bridge.pull_from_deerflow()
    assert "status" in result
    assert result["status"] in ("ok", "mock", "error")


def test_memory_bridge_top_facts():
    bridge = MemoryBridge()
    facts = bridge._get_top_facts(max_facts=5)
    assert isinstance(facts, list)
    assert len(facts) <= 5


# ── Integration Tests ──────────────────────────────────────

def test_full_bridge_chain():
    bridge = DeerFlowBridge()
    memory = MemoryBridge()

    task_result = bridge._mock_execute(
        {"type": "reasoning", "prompt": "integ test", "id": "integ-test-001"},
        "integ-test-001",
        start=datetime.now(),
    )
    assert "quality_report" in task_result

    push_result = memory.push_to_deerflow()
    assert "status" in push_result

    pull_result = memory.pull_from_deerflow()
    assert "status" in pull_result


def test_bridge_degradation_graceful():
    bridge = DeerFlowBridge()
    _orig = bridge._via_client
    async def fast_fallback(task, task_id, start):
        return {"status": "mock", "output": "degraded gracefully", "quality_report": {}}
    bridge._via_client = fast_fallback
    result = _run_async(bridge.execute({"type": "unknown_type", "id": "degrad-test"}))
    assert result is not None
    assert "status" in result
    bridge._via_client = _orig
