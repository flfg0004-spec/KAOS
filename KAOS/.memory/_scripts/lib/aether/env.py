"""Environment detection for Aether routing — identifies the caller context."""

import logging
import os
import sys

_LOG = logging.getLogger(__name__)

_CALLER_CACHE = None


def detect_caller() -> str:
    """Detecta quién está llamando a Aether.

    Returns:
        ``"opencode"`` — Llamado desde OpenCode Go
        ``"codex"`` — Llamado desde Codex CLI
        ``"claude"`` — Llamado desde Claude Code
        ``"kaos_agent"`` — Llamado desde un agente KAOS (Aletheia, Kratos, etc.)
        ``"test"`` — Llamado desde tests
        ``"script"`` — Script Python directo
        ``"unknown"`` — No se pudo determinar
    """
    global _CALLER_CACHE
    if _CALLER_CACHE is not None:
        return _CALLER_CACHE

    # 1. Variable de entorno explícita
    explicit = os.environ.get("KAOS_CALLER", "").strip().lower()
    if explicit in ("opencode", "codex", "claude", "kaos_agent", "test", "script"):
        _CALLER_CACHE = explicit
        return _CALLER_CACHE

    # 2. Variables de entorno específicas de cada herramienta
    if os.environ.get("OPENCODE_GO_SESSION"):
        _CALLER_CACHE = "opencode"
        return _CALLER_CACHE
    if os.environ.get("CLAUDE_CODE"):
        _CALLER_CACHE = "claude"
        return _CALLER_CACHE
    if os.environ.get("CODEX_CLI"):
        _CALLER_CACHE = "codex"
        return _CALLER_CACHE

    # 3. Variables KAOS
    agent = os.environ.get("KAOS_AGENT", "").strip().lower()
    if agent:
        _CALLER_CACHE = "kaos_agent"
        return _CALLER_CACHE

    # 4. Detección por proceso padre
    try:
        import psutil
        parent = psutil.Process(os.getppid())
        pname = parent.name().lower()
        if "opencode" in pname:
            _CALLER_CACHE = "opencode"
        elif "codex" in pname:
            _CALLER_CACHE = "codex"
        elif "claude" in pname:
            _CALLER_CACHE = "claude"
        elif "pytest" in pname or "unittest" in pname:
            _CALLER_CACHE = "test"
        else:
            _CALLER_CACHE = "script"
        return _CALLER_CACHE
    except ImportError:
        _LOG.debug("psutil not available — skipping parent process detection")
    except Exception:
        _LOG.debug("Failed to detect parent process", exc_info=True)

    # 5. Fallback: detectar por sys.argv
    if len(sys.argv) > 0:
        script = os.path.basename(sys.argv[0]).lower()
        if script in ("pytest", "pytest.exe"):
            _CALLER_CACHE = "test"
            return _CALLER_CACHE

    _CALLER_CACHE = "unknown"
    return _CALLER_CACHE


def reset_caller_cache():
    """Resetea la cache para forzar redetección en la próxima llamada."""
    global _CALLER_CACHE
    _CALLER_CACHE = None
