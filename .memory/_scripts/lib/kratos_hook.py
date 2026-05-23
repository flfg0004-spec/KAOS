"""Kratos Bash Hook — wraps CodeExperience capture around subprocess execution.

Usage:
    from kratos_hook import run_and_capture, init_code_memory_hook
    
    # Auto-capture all subprocess errors globally:
    init_code_memory_hook()
    
    # Or per-command:
    result = run_and_capture(["py", "-3", "script.py"], cwd="/project")
    # If error: automatically stored in CodeExperience
    # Returns: subprocess.CompletedProcess
"""
import subprocess, sys, os, builtins
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS.parent))

from lib.code_memory import capture_from_bash, status as ce_status

# Store original for unhooking
_original_run = subprocess.run

def init_code_memory_hook():
    """Patch subprocess.run globally to auto-capture errors into CodeExperience.
    
    After calling this, every subprocess.run() call that produces stderr
    will be recorded in CodeExperience for Kratos learning.
    """
    subprocess.run = _hooked_run
    builtins._code_memory_hook_active = True

def _hooked_run(*args, **kwargs):
    result = _original_run(*args, **kwargs)
    try:
        if result.returncode != 0 and result.stderr and len(result.stderr) > 5:
            cmd_str = str(kwargs.get("args", args[0] if args else ""))
            capture_from_bash(result.returncode, result.stderr[:500], cmd_str[:500])
    except Exception:
        pass  # Don't break execution for capture failures
    return result

def unhook():
    """Restore original subprocess.run."""
    subprocess.run = _original_run
    builtins._code_memory_hook_active = False

def capture_agent_output(text: str) -> int:
    """Parse agent output text and capture code errors into CodeExperience.
    
    Scans for Python Traceback patterns, error blocks, and code snippets
    with exceptions. Feeds them into CodeExperience for Kratos learning.
    
    Args:
        text: Agent output text (markdown, code, etc.)
    
    Returns:
        Number of experiences captured
    """
    import re
    count = 0
    # Pattern 1: Python Tracebacks (multiline)
    for m in re.finditer(r'(Traceback.*?)(?=\n\n|\Z|```)', text, re.DOTALL):
        err = m.group(1).strip()
        if len(err) > 20:
            from lib.code_memory import capture_from_bash
            try:
                capture_from_bash(exit_code=1, stderr=err[:500], cmd="agent_output", cwd="python")
                count += 1
            except Exception:
                pass
    # Pattern 2: Inline errors in code blocks (```python ... ```)
    for block in re.finditer(r'```python\n(.*?)```', text, re.DOTALL):
        code = block.group(1)
        err_match = re.search(r'(Error|Exception|Traceback|Fail)\b.*', code, re.IGNORECASE)
        if err_match:
            from lib.code_memory import capture_from_bash
            try:
                capture_from_bash(exit_code=1, stderr=err_match.group()[:500],
                                 cmd=code[:200], cwd="python")
                count += 1
            except Exception:
                pass
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

def wrap_bash():
    """Replace subprocess.run in the calling context with run_and_capture."""
    import builtins
    original_run = subprocess.run
    
    def hooked_run(*args, **kwargs):
        result = original_run(*args, **kwargs)
        if kwargs.get("capture_output") and result.returncode != 0 and result.stderr:
            cmd_str = str(kwargs.get("args", args[0] if args else ""))
            capture_from_bash(result.returncode, result.stderr[:500], cmd_str[:500])
        return result
    
    return hooked_run

if __name__ == "__main__":
    # Test: run a command that will fail
    result = run_and_capture(["py", "-3", "-c", "x = None; print(x['key'])"])
    print(f"Exit code: {result.returncode}")
    print(f"Stderr: {result.stderr[:100]}...")
    print(f"Captured to CodeExperience: {'stderr' in str(result.stderr)[:50]}")
    
    from lib.code_memory import status
    import json
    print(f"\nCodeExperience: {json.dumps(status(), indent=2)}")
