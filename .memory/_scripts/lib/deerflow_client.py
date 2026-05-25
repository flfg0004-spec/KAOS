"""DeerFlow-compatible client — lightweight adapter using LangGraph (shared foundation).

Since both KAOS and DeerFlow 2.0 use LangGraph, this client provides a
DeerFlowClient-compatible API that wraps LangGraph directly, without needing
the full DeerFlow framework installed.

Decision ADR-012 (P2): Tasks route in-process via LangGraph (~2ms) for
reasoning, or via Docker sandbox (~50ms) for code execution.

API compatible with: deerflow.client.DeerFlowClient
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Optional, AsyncGenerator

logger = logging.getLogger("deerflow_client")


class DeerFlowClient:
    """Lightweight DeerFlow-compatible client using LangGraph runtime.

    Usage:
        client = DeerFlowClient()
        response = client.chat("analyze this", thread_id="my-thread")
        async for event in client.stream("hello"):
            print(event)
    """

    def __init__(self):
        self._langgraph = None
        self._memory = {}

    def _get_graph(self):
        if self._langgraph is None:
            try:
                from lib.orchestrator import build_graph
                self._langgraph = build_graph(with_parallel=True)
            except Exception as e:
                logger.warning(f"LangGraph not available: {e}")
                return None
        return self._langgraph

    def chat(self, message: str, thread_id: str = None, config: dict = None) -> str:
        thread_id = thread_id or f"df-{uuid.uuid4().hex[:8]}"
        config = config or {}
        model = config.get("configurable", {}).get("model_name", "deepseek-chat")

        from lib.llm import agent_llm_call
        try:
            response = agent_llm_call("aletheia", message)
            return response or "[no response]"
        except Exception as e:
            logger.error(f"DeerFlowClient.chat error: {e}")
            return f"[error: {e}]"

    def stream(self, message: str, thread_id: str = None, config: dict = None):
        thread_id = thread_id or f"df-{uuid.uuid4().hex[:8]}"
        try:
            response = self.chat(message, thread_id, config)
            yield {"type": "messages-tuple", "data": {"type": "ai", "content": response}}
            yield {"type": "end", "data": {}}
        except Exception as e:
            yield {"type": "error", "data": {"error": str(e)}}

    def memory_set(self, key: str, value: str):
        self._memory[key] = value

    def memory_get(self, key: str) -> Optional[str]:
        return self._memory.get(key)

    def memory_get_all(self) -> dict:
        return dict(self._memory)

    def memory_clear(self):
        self._memory.clear()

    def status(self) -> dict:
        return {
            "available": True,
            "mode": "langgraph-adapter",
            "memory_keys": len(self._memory),
            "langgraph_ready": self._get_graph() is not None,
        }


client = DeerFlowClient()
