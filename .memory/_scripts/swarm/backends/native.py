import logging
import os
import subprocess
import threading
from pathlib import Path

from swarm.worker_manager import WorkerManager

_LOG = logging.getLogger(__name__)
_SCRIPTS = Path(__file__).resolve().parent.parent.parent
_PROJECT = _SCRIPTS.parent.parent


class NativeWorker(WorkerManager):
    """Worker using subprocess.Popen + JSON-RPC over stdin/stdout."""

    def __init__(self, role: str, worker_id: str):
        super().__init__(role, worker_id)
        self._process: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._pid_file = _PROJECT / ".memory" / "_pipeline" / f"swarm-{worker_id}.pid"

    def start(self) -> bool:
        with self._lock:
            if self._running:
                return True
            try:
                env = os.environ.copy()
                env["PYTHONPATH"] = str(_SCRIPTS)
                self._process = subprocess.Popen(
                    ["py", "-3", "-m", f"swarm.roles.{self.role}"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
                self._pid_file.write_text(str(self._process.pid))
                self._running = True
                _LOG.info("NativeWorker %s started (PID %d)", self.worker_id, self._process.pid)
                return True
            except Exception as e:
                _LOG.error("NativeWorker %s start failed: %s", self.worker_id, e)
                return False

    def stop(self) -> bool:
        with self._lock:
            if not self._running or not self._process:
                return True
            try:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=3)
                self._running = False
                if self._pid_file.exists():
                    self._pid_file.unlink()
                _LOG.info("NativeWorker %s stopped", self.worker_id)
                return True
            except Exception as e:
                _LOG.error("NativeWorker %s stop failed: %s", self.worker_id, e)
                return False

    def status(self) -> dict:
        if not self._process:
            return {"role": self.role, "worker_id": self.worker_id, "status": "stopped"}
        poll = self._process.poll()
        return {
            "role": self.role,
            "worker_id": self.worker_id,
            "status": "running" if poll is None else f"exited({poll})",
            "pid": self._process.pid,
        }

    def send(self, message: str) -> str | None:
        if not self._process or self._process.stdin is None:
            return None
        try:
            self._process.stdin.write(message + "\n")
            self._process.stdin.flush()
            line = self._process.stdout.readline() if self._process.stdout else None
            return line.strip() if line else None
        except Exception as e:
            _LOG.error("NativeWorker %s send failed: %s", self.worker_id, e)
            return None
