"""DeerFlow Bridge — dual channel: in-process DeerFlowClient + sandbox MCP/HTTP.

Decision ADR-012 (P2):
  - Tareas de razonamiento puro: DeerFlowClient.chat() in-process (~2ms)
  - Tareas de ejecucion de codigo: MCP/HTTP hacia Sandbox Docker (~50ms)
  - Tareas mixtas: lead agent decide internamente

Auto-deteccion: si deerflow no esta instalado, opera en modo 'mock' (degradacion
gradual sin bloqueo del pipeline KAOS).
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("deerflow_bridge")

BRIDGE_REPORTS = Path(__file__).resolve().parent.parent.parent / "bridge" / "reports"
BRIDGE_CONTEXT = Path(__file__).resolve().parent.parent.parent / "bridge" / "context"

DEERFLOW_AVAILABLE = False
DEERFLOW_SANDBOX_URL = os.getenv("DEERFLOW_SANDBOX_URL", "http://localhost:8001")
MOCK_MODE = False


class DeerFlowQualityReport:
    def __init__(self, task_id: str, agent: str, execution_time_ms: int,
                 token_usage: dict, error_count: int, steps: list,
                 confidence: float, output_summary: str):
        self.task_id = task_id
        self.agent = agent
        self.execution_time_ms = execution_time_ms
        self.token_usage = token_usage
        self.error_count = error_count
        self.steps = steps
        self.confidence = confidence
        self.output_summary = output_summary
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent": self.agent,
            "execution_time_ms": self.execution_time_ms,
            "token_usage": self.token_usage,
            "error_count": self.error_count,
            "steps_executed": self.steps,
            "confidence_score": self.confidence,
            "output_summary": self.output_summary,
            "timestamp": self.timestamp,
        }

    def save(self):
        BRIDGE_REPORTS.mkdir(parents=True, exist_ok=True)
        path = BRIDGE_REPORTS / f"deerflow-{self.task_id}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2))
        return path


def _check_deerflow() -> bool:
    global DEERFLOW_AVAILABLE, MOCK_MODE
    if DEERFLOW_AVAILABLE:
        return True
    for modname in ("deerflow.client", "lib.deerflow_client"):
        try:
            __import__(modname, fromlist=["DeerFlowClient"])
            DEERFLOW_AVAILABLE = True
            MOCK_MODE = False
            logger.info(f"DeerFlowClient from {modname} — bridge active")
            return True
        except ImportError:
            continue
    MOCK_MODE = True
    logger.warning("DeerFlow not installed — bridge in MOCK mode (install deerflow or use lib.deerflow_client)")
    return False


class DeerFlowBridge:
    def __init__(self, mode: str = "auto"):
        self.mode = mode
        self.client = None
        self.sandbox_url = DEERFLOW_SANDBOX_URL
        _check_deerflow()

    def _get_client(self):
        if self.client is None and not MOCK_MODE:
            try:
                from deerflow.client import DeerFlowClient
                self.client = DeerFlowClient()
            except ImportError:
                try:
                    from lib.deerflow_client import DeerFlowClient
                    self.client = DeerFlowClient()
                except ImportError:
                    logger.warning("No DeerFlowClient available")
        return self.client

    def _needs_sandbox(self, task: dict) -> bool:
        task_type = task.get("type", "")
        if task_type in ("code_execution", "external_request", "untrusted"):
            return True
        return False

    async def execute(self, task: dict) -> dict:
        start = datetime.now()

        task_type = task.get("type", "reasoning")
        task_id = task.get("id", datetime.now().strftime("df-%Y%m%d-%H%M%S-%f"))

        if MOCK_MODE:
            return self._mock_execute(task, task_id, start)

        if self._needs_sandbox(task):
            return await self._via_sandbox(task, task_id, start)
        else:
            return await self._via_client(task, task_id, start)

    async def _via_client(self, task: dict, task_id: str, start: datetime) -> dict:
        client = self._get_client()
        if client is None:
            return self._mock_execute(task, task_id, start)

        try:
            config = task.get("config", {})
            thread_id = task.get("thread_id", task_id)
            message = task.get("prompt", task.get("message", ""))

            response = client.chat(
                message,
                thread_id=thread_id,
                config={"configurable": {
                    "model_name": config.get("model", "deepseek-chat"),
                    "subagent_enabled": config.get("subagent_enabled", True),
                    "recursion_limit": config.get("recursion_limit", 25),
                }}
            )

            elapsed = (datetime.now() - start).total_seconds() * 1000
            report = DeerFlowQualityReport(
                task_id=task_id,
                agent="deerflow-client",
                execution_time_ms=int(elapsed),
                token_usage={"input": 0, "output": 0},
                error_count=0,
                steps=["chat"],
                confidence=0.85,
                output_summary=str(response)[:200],
            )
            report.save()

            return {"status": "ok", "output": str(response), "quality_report": report.to_dict()}

        except Exception as e:
            elapsed = (datetime.now() - start).total_seconds() * 1000
            logger.error(f"DeerFlowClient error: {e}")
            report = DeerFlowQualityReport(
                task_id=task_id,
                agent="deerflow-client",
                execution_time_ms=int(elapsed),
                token_usage={"input": 0, "output": 0},
                error_count=1,
                steps=["chat", "error"],
                confidence=0.0,
                output_summary=f"Error: {str(e)[:100]}",
            )
            report.save()
            return {"status": "error", "error": str(e), "quality_report": report.to_dict()}

    async def _via_sandbox(self, task: dict, task_id: str, start: datetime) -> dict:
        import subprocess
        import json as _json

        code = task.get("code", "")
        language = task.get("language", "python")
        timeout = task.get("timeout", 30)

        payload = _json.dumps({"code": code, "language": language, "timeout": timeout})

        try:
            result = subprocess.run(
                ["docker", "run", "--rm", "-i", "kaos-sandbox"],
                input=payload,
                capture_output=True,
                text=True,
                timeout=timeout + 10,
            )

            sandbox_output = _json.loads(result.stdout.strip()) if result.stdout.strip() else {}

            elapsed = (datetime.now() - start).total_seconds() * 1000
            exit_code = sandbox_output.get("exit_code", -1)
            error_count = 1 if exit_code != 0 else 0
            report = DeerFlowQualityReport(
                task_id=task_id,
                agent="kaos-sandbox",
                execution_time_ms=int(elapsed),
                token_usage={"input": 0, "output": 0},
                error_count=error_count,
                steps=["sandbox_execute"],
                confidence=0.9 if error_count == 0 else 0.3,
                output_summary=str(sandbox_output.get("stdout", ""))[:200],
            )
            report.save()

            return {
                "status": "ok" if error_count == 0 else "error",
                "stdout": sandbox_output.get("stdout", ""),
                "stderr": sandbox_output.get("stderr", ""),
                "exit_code": exit_code,
                "quality_report": report.to_dict(),
            }

        except subprocess.TimeoutExpired:
            elapsed = (datetime.now() - start).total_seconds() * 1000
            report = DeerFlowQualityReport(
                task_id=task_id, agent="kaos-sandbox",
                execution_time_ms=int(elapsed), token_usage={},
                error_count=1, steps=["sandbox_execute", "timeout"],
                confidence=0.0, output_summary="Sandbox timeout",
            )
            report.save()
            return {"status": "error", "error": "timeout", "quality_report": report.to_dict()}

        except Exception as e:
            elapsed = (datetime.now() - start).total_seconds() * 1000
            logger.error(f"Sandbox error: {e}")
            report = DeerFlowQualityReport(
                task_id=task_id, agent="kaos-sandbox",
                execution_time_ms=int(elapsed), token_usage={},
                error_count=1, steps=["sandbox_execute", "error"],
                confidence=0.0, output_summary=f"Sandbox error: {str(e)[:100]}",
            )
            report.save()
            return {"status": "error", "error": str(e), "quality_report": report.to_dict()}

    def _mock_execute(self, task: dict, task_id: str, start: datetime) -> dict:
        elapsed = (datetime.now() - start).total_seconds() * 1000
        logger.info(f"[MOCK] DeerFlowBridge.execute({task.get('type', 'unknown')})")
        report = DeerFlowQualityReport(
            task_id=task_id,
            agent="deerflow-mock",
            execution_time_ms=int(elapsed),
            token_usage={"input": 0, "output": 0},
            error_count=0,
            steps=["mock"],
            confidence=0.5,
            output_summary=f"[MOCK] output for: {task.get('prompt', task.get('message', ''))[:100]}",
        )
        report.save()
        return {
            "status": "mock",
            "output": f"[MOCK] DeerFlowBridge processed task {task_id}",
            "quality_report": report.to_dict(),
        }

    def status(self) -> dict:
        return {
            "available": DEERFLOW_AVAILABLE,
            "mock_mode": MOCK_MODE,
            "sandbox_url": self.sandbox_url,
            "mode": self.mode,
            "client_ready": self.client is not None,
        }


bridge = DeerFlowBridge()
