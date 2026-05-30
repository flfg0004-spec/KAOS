"""Kratos Bash Hook — wraps CodeExperience capture around subprocess execution.

Usage (recommended — context manager):
    from kratos_hook import CodeMemoryCapture
    
    # Scoped capture via context manager (safe, no global side-effects):
    with CodeMemoryCapture():
        result = subprocess.run(["py", "-3", "script.py"], capture_output=True)
    
    # Or per-command:
    result = run_and_capture(["py", "-3", "script.py"], cwd="/project")

    # DEPRECATED — global monkey-patch (fragile, prefer context manager):
    from kratos_hook import init_code_memory_hook  # noqa
"""
import builtins
import logging
import os
import subprocess
import sys
import threading
from pathlib import Path

logger = logging.getLogger("kratos_hook")

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS.parent))

from lib.code_memory import capture_from_bash

_original_run = subprocess.run
_hook_lock = threading.Lock()


class CodeMemoryCapture:
    """Context manager that captures subprocess errors into CodeExperience.
    
    Usage:
        with CodeMemoryCapture():
            subprocess.run(["py", "script.py"], capture_output=True)
        
        # Out of context: subprocess.run behaves normally
    """
    
    def __enter__(self):
        subprocess.run = _hooked_run
        builtins._code_memory_hook_active = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        subprocess.run = _original_run
        builtins._code_memory_hook_active = False
        if exc_type is not None:
            logger.warning("CodeMemoryCapture caught exception: %s: %s", exc_type.__name__, exc_val)


def init_code_memory_hook():
    """DEPRECATED — use CodeMemoryCapture context manager instead.
    
    Patch subprocess.run globally to auto-capture errors into CodeExperience.
    This is fragile — prefer the scoped CodeMemoryCapture context manager.
    """
    logger.warning("init_code_memory_hook is deprecated, use CodeMemoryCapture context manager instead")
    subprocess.run = _hooked_run
    builtins._code_memory_hook_active = True
    logger.info("CodeMemory hook activated (global monkey-patch)")


def _hooked_run(*args, **kwargs):
    with _hook_lock:
        result = _original_run(*args, **kwargs)
    try:
        if result.returncode != 0 and result.stderr and len(result.stderr) > 5:
            cmd_str = str(kwargs.get("args", args[0] if args else ""))
            cap = capture_from_bash(result.returncode, result.stderr[:500], cmd_str[:500])
            if cap.get("status") == "created":
                logger.debug("Captured error into CodeExperience: %s", cap.get("hash", ""))
    except Exception as e:
        logger.warning("CodeExperience capture failed (non-blocking): %s", e)
    return result


def unhook():
    """Restore original subprocess.run."""
    subprocess.run = _original_run
    builtins._code_memory_hook_active = False
    logger.info("CodeMemory hook deactivated")


def capture_agent_output(text: str) -> int:
    """Parse agent output text and capture code errors into CodeExperience.
    
    Scans for Python/Rust/JS/Go error patterns, tracebacks, and code blocks
    with exceptions. Feeds them into CodeExperience for Kratos learning.
    
    Args:
        text: Agent output text (markdown, code, etc.)
    
    Returns:
        Number of experiences captured
    """
    import re
    count = 0
    
    patterns = [
        # Python Tracebacks
        (r'(Traceback.*?)(?=\n\n|\Z|```)', "python"),
        # Rust panics  
        (r"(thread '.*?' panicked at '.*?')", "rust"),
        # Rust compiler errors
        (r"(error\[E\d+\]: .*?)(?=\n\n|\Z)", "rust"),
        # JS/TS errors
        (r"(Uncaught (Type|Reference|Syntax)Error: .*?)(?=\n|\r)", "javascript"),
        # Go errors
        (r"(panic: .*?)(?=\n|\r)", "go"),
        (r"(cannot .*? as type .*?)(?=\n|\r)", "go"),
    ]
    
    for pattern, lang in patterns:
        for m in re.finditer(pattern, text, re.DOTALL if "Traceback" in pattern else 0):
            err = m.group(1).strip()
            if len(err) > 20:
                from lib.code_memory import capture_from_bash
                try:
                    capture_from_bash(exit_code=1, stderr=err[:500], cmd="agent_output", cwd=lang)
                    count += 1
                except Exception as e:
                    logger.warning("Failed to capture agent output: %s", e)
    
    # Pattern: error blocks in code fences (any language)
    for block in re.finditer(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL):
        code = block.group(1)
        err_match = re.search(r'(Error|Exception|Traceback|panic|Fail)\b.*', code, re.IGNORECASE)
        if err_match:
            from lib.code_memory import capture_from_bash
            try:
                capture_from_bash(exit_code=1, stderr=err_match.group()[:500],
                                 cmd=code[:200], cwd="python")
                count += 1
            except Exception as e:
                logger.warning("Failed to capture code block error: %s", e)
    return count


def run_and_capture(cmd: list, cwd: str = None, shell: bool = False,
                    capture_error: bool = True, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run a command and capture any errors into CodeExperience.
    
    Args:
        cmd: Command to run (list or string if shell=True)
        cwd: Working directory (used for language detection)
        shell: Use shell execution
        capture_error: Capture errors into CodeExperience
        timeout: Command timeout in seconds
    
    Returns:
        subprocess.CompletedProcess with stdout, stderr, returncode
    """
    if cwd is None:
        cwd = os.getcwd()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            shell=shell,
            timeout=timeout
        )
    except subprocess.TimeoutExpired as e:
        return subprocess.CompletedProcess(
            args=cmd, returncode=-1,
            stdout=e.stdout or "", stderr=f"TIMEOUT after {timeout}s"
        )
    
    if capture_error and result.returncode != 0 and result.stderr:
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
        capture_from_bash(
            exit_code=result.returncode,
            stderr=result.stderr,
            cmd=cmd_str[:500],
            cwd=cwd
        )
    
    return result


if __name__ == "__main__":
    result = run_and_capture(["py", "-3", "-c", "x = None; print(x['key'])"] if sys.platform == "win32" else
                             ["python3", "-c", "x = None; print(x['key'])"])
    print(f"Exit code: {result.returncode}")
    print(f"Stderr: {str(result.stderr)[:100]}...")
    
    import json

    from lib.code_memory import status
    print(f"\nCodeExperience: {json.dumps(status(), indent=2)}")
