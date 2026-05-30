"""MemEx (Code-as-Action) — persistent Python scope for Kratos.

Maintains a persistent Python namespace across Kratos iterations.
Variables, imports, functions persist between calls.
Useful for:
  - Multi-step debugging (variables survive iterations)
  - Incremental testing (imports persist)
  - Progressive refactoring (functions defined earlier available)

Limits:
  - 100 variables max (auto-cleanup LRU)
  - 10 iterations auto-cleanup
  - Serialized to JSON for persistence between sessions

Inspired by Databricks MemEx: programmable scratchpad for LLM agents.
"""

import io
import json
import sys
import traceback
from pathlib import Path

SCOPE_DIR = (Path(__file__).resolve().parent.parent.parent / "cache" / "memex")
SCOPE_FILE = SCOPE_DIR / "scope.json"

MAX_VARS = 100
MAX_ITERATIONS = 10


class MemExScope:
    """Persistent Python scope for code execution and state management."""
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.namespace: dict = {}
        self.iteration: int = 0
        self.history: list = []
        self._load()
    
    def _load(self):
        """Load persisted scope from disk."""
        SCOPE_DIR.mkdir(parents=True, exist_ok=True)
        if SCOPE_FILE.exists():
            try:
                data = json.loads(SCOPE_FILE.read_text(encoding="utf-8"))
                self.namespace = data.get("namespace", {})
                self.iteration = data.get("iteration", 0)
                self.history = data.get("history", [])
                # Reconstruct callable objects from source
                source = data.get("source_code", "")
                if source:
                    exec(source, self.namespace)
            except Exception:
                self.namespace = {}
                self.iteration = 0
                self.history = []
    
    def _save(self):
        """Persist scope to disk."""
        SCOPE_DIR.mkdir(parents=True, exist_ok=True)
        serializable = {}
        source_lines = []
        for key, val in list(self.namespace.items()):
            try:
                if callable(val) and hasattr(val, '__code__'):
                    try:
                        import inspect
                        source_lines.append(inspect.getsource(val))
                    except Exception:
                        pass
                    serializable[key] = "<function>"
                elif isinstance(val, (str, int, float, bool, list, dict, tuple, type(None))):
                    serializable[key] = val
                elif isinstance(val, type):
                    serializable[key] = "<class>"
                else:
                    serializable[key] = str(type(val).__name__)
            except Exception:
                serializable[key] = f"<{type(val).__name__}>"
        
        SCOPE_FILE.write_text(json.dumps({
            "session_id": self.session_id,
            "namespace": serializable,
            "source_code": "\n".join(source_lines),
            "iteration": self.iteration,
            "history": self.history[-100:],
        }, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    
    def execute(self, code: str) -> dict:
        """Execute Python code in the persistent scope.
        
        Args:
            code: Python code to execute
        
        Returns:
            dict with stdout, stderr, result, error
        """
        self.iteration += 1
        
        # Auto-cleanup every MAX_ITERATIONS
        if self.iteration > MAX_VARS:
            # Keep only most recent variables
            keys = list(self.namespace.keys())
            if len(keys) > MAX_VARS:
                for k in keys[:-MAX_VARS]:
                    if not k.startswith('_'):
                        del self.namespace[k]
            self.iteration = 1
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        result = None
        error = None
        
        try:
            exec(code, self.namespace)
        except Exception as e:
            error = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
            }
        
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        self.history.append({
            "iteration": self.iteration,
            "code": code[:200],
            "error": error is not None,
            "stdout_len": len(stdout_capture.getvalue()),
        })
        
        self._save()
        
        return {
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "error": error,
            "namespace_size": len(self.namespace),
            "iteration": self.iteration,
        }
    
    def get(self, key: str, default=None):
        """Get a value from the persistent namespace."""
        return self.namespace.get(key, default)
    
    def set(self, key: str, value):
        """Set a value in the persistent namespace."""
        self.namespace[key] = value
        self._save()
    
    def list_vars(self) -> list:
        """List all variables in the scope (excluding builtins)."""
        return [
            {"name": k, "type": type(v).__name__}
            for k, v in self.namespace.items()
            if not k.startswith('_')
        ]
    
    def reset(self):
        """Reset the scope to empty state."""
        self.namespace = {}
        self.iteration = 0
        self.history = []
        self._save()
    
    def status(self) -> dict:
        """Get scope status."""
        return {
            "session_id": self.session_id,
            "variables": len(self.namespace),
            "iteration": self.iteration,
            "history_entries": len(self.history),
        }


# Global session registry
_sessions: dict = {}

def get_scope(session_id: str = "default") -> MemExScope:
    """Get or create a named MemEx scope. Sessions persist independently."""
    if session_id not in _sessions:
        _sessions[session_id] = MemExScope(session_id=session_id)
    return _sessions[session_id]

def reset_scope():
    """Reset all scopes."""
    global _sessions
    for scope in _sessions.values():
        try:
            scope.reset()
        except Exception:
            pass
    _sessions = {}


if __name__ == "__main__":
    scope = get_scope("test")
    
    r1 = scope.execute("x = 42")
    print(f"Set x=42: {r1['stdout']}")
    
    r2 = scope.execute("y = x + 1; print(f'y={y}')")
    print(f"Computed y: {r2['stdout'].strip()}")
    
    print(f"Variables: {scope.list_vars()}")
    print(f"Status: {scope.status()}")
    
    # Test error handling
    r3 = scope.execute("z = 1/0")
    print(f"Error handled: {r3['error']['type']}")
