"""TmuxWorker — opt-in backend using WSL2 + tmux sessions."""

import logging
import subprocess
import time
from pathlib import Path

from swarm.worker_manager import WorkerManager

_LOG = logging.getLogger(__name__)
_SCRIPTS = Path(__file__).resolve().parent.parent.parent
_PROJECT = _SCRIPTS.parent.parent

WSL_DISTRO = "Ubuntu"
TMUX_SESSION_PREFIX = "kaos-worker-"


def _wsl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--"] + list(args),
        capture_output=True,
        text=True,
        timeout=30,
    )


class TmuxWorker(WorkerManager):
    """Worker using WSL2 + tmux sessions (opt-in). Requires WSL2 + tmux installed."""

    def __init__(self, role: str, worker_id: str):
        super().__init__(role, worker_id)
        self._session_name = f"{TMUX_SESSION_PREFIX}{role}"
        self._health_checked = False

    def _check_health(self) -> bool:
        try:
            r = _wsl("tmux", "-V")
            return r.returncode == 0 and "tmux" in r.stdout
        except Exception:
            return False

    def start(self) -> bool:
        if not self._check_health():
            _LOG.error("TmuxWorker %s: WSL2/tmux not available", self.worker_id)
            return False

        script = f"py -3 -m swarm.roles.{self.role}"
        win_path = str(_SCRIPTS).replace("\\", "/")
        # Convert Windows path to WSL path
        wsl_path = f"/mnt/{win_path[0].lower()}/{win_path[3:]}"

        cmds = [
            f"cd {wsl_path}",
            f"PYTHONPATH={wsl_path} {script}",
        ]
        shell_cmd = "; ".join(cmds)

        r = _wsl("tmux", "new-session", "-d", "-s", self._session_name, shell_cmd)
        if r.returncode != 0:
            _LOG.error("TmuxWorker %s: tmux new-session failed: %s", self.worker_id, r.stderr)
            return False

        self._running = True
        _LOG.info("TmuxWorker %s started (session: %s)", self.worker_id, self._session_name)
        return True

    def stop(self) -> bool:
        r = _wsl("tmux", "kill-session", "-t", self._session_name)
        self._running = False
        return r.returncode == 0

    def status(self) -> dict:
        r = _wsl("tmux", "has-session", "-t", self._session_name)
        is_running = r.returncode == 0
        return {
            "role": self.role,
            "worker_id": self.worker_id,
            "status": "running" if is_running else "stopped",
            "session": self._session_name if is_running else None,
        }

    def send(self, message: str) -> str | None:
        r = _wsl("tmux", "send-keys", "-t", self._session_name, message + "\n", "Enter")
        if r.returncode != 0:
            return None
        time.sleep(0.5)
        r = _wsl("tmux", "capture-pane", "-t", self._session_name, "-p")
        return r.stdout if r.returncode == 0 else None
