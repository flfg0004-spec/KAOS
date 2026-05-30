"""QualityGateService — auto-detects local vs MCP mode for gate execution."""

import logging

from lib.feature_flags import is_enabled

logger = logging.getLogger(__name__)

_QUALITY_GATE_SERVICE = None


class QualityGateService:
    """Service that abstracts local vs remote (MCP) quality gate execution.

    Auto-detects MCP availability. Falls back to local imports.
    """

    def __init__(self):
        self._use_mcp = False
        self._mcp_client = None

    def detect_mode(self) -> str:
        """Auto-detect: 'mcp' if MCP server available, else 'local'."""
        if not is_enabled("mcp_quality_client"):
            self._use_mcp = False
            return "local"
        try:
            from lib.mcp_client import McpClient
            self._mcp_client = McpClient()
            self._use_mcp = True
            return "mcp"
        except ImportError:
            self._use_mcp = False
            return "local"

    @property
    def mode(self) -> str:
        return "mcp" if self._use_mcp else "local"

    def evaluate(self, content: str, language: str = "") -> dict:
        if self._use_mcp and self._mcp_client:
            try:
                return self._mcp_client.call("gate/evaluate", {"content": content, "language": language})
            except Exception as e:
                logger.warning("MCP evaluate failed, falling back to local: %s", e)
                self._use_mcp = False
        from lib.quality_gate import evaluate
        return evaluate(content, language)

    def evaluate_parallel(self, content: str, language: str = "", max_workers: int = 4) -> dict:
        if self._use_mcp and self._mcp_client:
            try:
                return self._mcp_client.call("gate/evaluate_parallel", {
                    "content": content, "language": language, "max_workers": max_workers
                })
            except Exception as e:
                logger.warning("MCP evaluate_parallel failed, falling back to local: %s", e)
                self._use_mcp = False
        from lib.quality_gate import evaluate_parallel
        return evaluate_parallel(content, language, max_workers)

    def list_gates(self) -> list[str]:
        if self._use_mcp and self._mcp_client:
            try:
                return self._mcp_client.call("gate/list", {})
            except Exception:
                self._use_mcp = False
        from lib.quality_gate.gates import list_gates
        return list_gates()


def get_service() -> QualityGateService:
    global _QUALITY_GATE_SERVICE
    if _QUALITY_GATE_SERVICE is None:
        _QUALITY_GATE_SERVICE = QualityGateService()
        _QUALITY_GATE_SERVICE.detect_mode()
    return _QUALITY_GATE_SERVICE
