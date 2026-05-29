"""Utilidades MCP para conectar agents agno a los MCP servers de KAOS.

Provee safe_mcp_tools() que verifica disponibilidad de comandos y
resuelve paths relativos a absolutos.
"""

import logging
import shutil
import time
import threading
from pathlib import Path

logger = logging.getLogger("agno_kaos.mcp")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _command_exists(cmd: str) -> bool:
    """Verifica si un comando base existe en PATH."""
    base = cmd.split()[0]
    return shutil.which(base) is not None


def _resolve_path(cmd: str) -> str:
    """Resuelve paths relativos a absolutos para comandos py."""
    parts = cmd.split()
    resolved = []
    for p in parts:
        if p.startswith(".memory") or p.startswith("agno_kaos"):
            resolved.append(str((_PROJECT_ROOT / p).resolve()))
        else:
            resolved.append(p)
    return " ".join(resolved)


def safe_mcp_tools(commands: list[str]) -> list:
    """Crea MCPTools para cada comando, saltando los que fallan.

    Args:
        commands: Lista de comandos MCP (ej: "npx -y exa-mcp-server")

    Returns:
        Lista de MCPTools o vacío si ninguno funciona.
    """
    from agno.tools.mcp import MCPTools

    tools = []
    for cmd in commands:
        try:
            base = cmd.split()[0]
            if not _command_exists(base):
                logger.info("MCP skip: '%s' no encontrado en PATH — %s", base, cmd[:60])
                continue
            resolved = _resolve_path(cmd)
            tools.append(MCPTools(command=resolved))
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning("MCP import error: %s — %s", e, cmd[:50])
        except (FileNotFoundError, PermissionError) as e:
            logger.warning("MCP file error: %s — %s", e, cmd[:50])
        except Exception as e:
            logger.warning("MCP error inesperado: %s — %s", e, cmd[:50])
    return tools


class RateLimiter:
    """Token bucket rate limiter para MCP tool calls.

    Args:
        rpm: Requests per minute máximo.
    """

    def __init__(self, rpm: int = 30):
        self.rpm = rpm
        self.tokens = float(rpm)
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self) -> bool:
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.rpm, self.tokens + elapsed * (self.rpm / 60.0))
            self.last_refill = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


def load_mcp_config(agent_name: str) -> list[str]:
    """Carga la lista de comandos MCP desde config.yaml para un agente."""
    from agno_kaos import load_config
    cfg = load_config()
    return cfg.get("mcp_servers", {}).get(agent_name, [])
