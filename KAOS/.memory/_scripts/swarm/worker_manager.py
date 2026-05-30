import abc
import logging
from pathlib import Path

_LOG = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


class WorkerManager(abc.ABC):
    """Abstract interface for swarm worker backends."""

    def __init__(self, role: str, worker_id: str):
        self.role = role
        self.worker_id = worker_id
        self._running = False

    @abc.abstractmethod
    def start(self) -> bool: ...

    @abc.abstractmethod
    def stop(self) -> bool: ...

    @abc.abstractmethod
    def status(self) -> dict: ...

    @abc.abstractmethod
    def send(self, message: str) -> str | None: ...

    @property
    def is_running(self) -> bool:
        return self._running


def create_worker(role: str, backend: str = "native") -> WorkerManager:
    if backend == "native":
        from swarm.backends.native import NativeWorker

        return NativeWorker(role, f"{role}-{backend}")
    elif backend == "tmux":
        from swarm.backends.tmux import TmuxWorker

        return TmuxWorker(role, f"{role}-{backend}")
    raise ValueError(f"Unknown backend: {backend}")
