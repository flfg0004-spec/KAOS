"""ParallelExecutor — concurrent task execution with live state tracking."""

import logging
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, wait
from enum import Enum
from typing import Any

_LOG = logging.getLogger(__name__)


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TaskResult:
    """Resultado de una tarea ejecutada."""
    def __init__(self, task_id: str, state: TaskState, result: Any = None,
                 error: str = None, elapsed_ms: float = 0.0):
        self.task_id = task_id
        self.state = state
        self.result = result
        self.error = error
        self.elapsed_ms = elapsed_ms


class ParallelExecutor:
    """Ejecuta tareas en paralelo con estado en vivo y callback por cambio.

    Args:
        max_concurrent: Máximo de tareas simultáneas (default 3).
        on_status_change: Callback opcional(task_id, state, result).
    """

    def __init__(self, max_concurrent: int = 3,
                 on_status_change: Callable = None):
        self._max = max_concurrent
        self._on_status = on_status_change
        self._lock = threading.Lock()
        self._states: dict[str, TaskState] = {}
        self._results: dict[str, TaskResult] = {}
        self._timestamps: dict[str, float] = {}

    @property
    def max_concurrent(self) -> int:
        return self._max

    @max_concurrent.setter
    def max_concurrent(self, value: int):
        self._max = max(1, value)

    def execute_all(self, tasks: list[dict], executor=None) -> list[TaskResult]:
        """Ejecuta todas las tareas respetando max_concurrent.

        Cada task es un dict con:
            - id: str (obligatorio)
            - fn: callable (obligatorio)
            - timeout: int (opcional, default 300)
            - args: tuple (opcional)
            - kwargs: dict (opcional)

        Args:
            tasks: Lista de tareas a ejecutar.
            executor: ThreadPoolExecutor externo (opcional). Si no se provee,
                      crea uno interno.

        Returns: lista de TaskResult en el mismo orden que tasks.
        """
        results: list[TaskResult] = []
        external = executor is not None

        for t in tasks:
            tid = t.get("id", str(id(t)))
            self._states[tid] = TaskState.PENDING
            self._timestamps[tid] = time.time()

        pool = executor if external else ThreadPoolExecutor(max_workers=self._max)
        try:
            futures = {}
            max_timeout = 300
            for t in tasks:
                tid = t.get("id", str(id(t)))
                fn = t.get("fn")
                if not callable(fn):
                    self._set_state(tid, TaskState.FAILED)
                    results.append(TaskResult(tid, TaskState.FAILED, error="fn not callable"))
                    continue

                task_timeout = t.get("timeout", 300)
                max_timeout = max(max_timeout, task_timeout)
                args = t.get("args", ())
                kwargs = t.get("kwargs", {})

                self._set_state(tid, TaskState.RUNNING)
                fut = pool.submit(self._run_wrapper, tid, fn, args, kwargs, task_timeout)
                futures[fut] = tid

            completed_futures, pending_futures = wait(futures, timeout=int(max_timeout))

            for fut in completed_futures:
                tid = futures[fut]
                try:
                    result, elapsed = fut.result()
                    self._set_state(tid, TaskState.COMPLETED)
                    results.append(TaskResult(tid, TaskState.COMPLETED, result=result, elapsed_ms=elapsed))
                except Exception as e:
                    self._set_state(tid, TaskState.FAILED)
                    results.append(TaskResult(tid, TaskState.FAILED, error=str(e)))

            for fut in pending_futures:
                tid = futures[fut]
                fut.cancel()
                self._set_state(tid, TaskState.TIMEOUT)
                results.append(TaskResult(tid, TaskState.TIMEOUT, error=f"Timeout after {max_timeout}s"))

        finally:
            if not external:
                pool.shutdown(wait=False)

        return results

    def _run_wrapper(self, tid: str, fn: Callable, args: tuple, kwargs: dict,
                     timeout: int) -> tuple:
        start = time.time()
        result = fn(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        return result, elapsed

    def _set_state(self, task_id: str, state: TaskState):
        with self._lock:
            self._states[task_id] = state
        if self._on_status:
            try:
                self._on_status(task_id, state.value, None)
            except Exception:
                _LOG.warning("Status callback failed for task %s", task_id, exc_info=True)

    def get_state(self, task_id: str) -> str | None:
        with self._lock:
            s = self._states.get(task_id)
        return s.value if s else None

    def get_all_states(self) -> dict[str, str]:
        with self._lock:
            return {k: v.value for k, v in self._states.items()}

    def stats(self) -> dict:
        with self._lock:
            total = len(self._states)
            counts = {}
            for s in self._states.values():
                counts[s.value] = counts.get(s.value, 0) + 1
            return {
                "max_concurrent": self._max,
                "total_tasks": total,
                "by_state": counts,
            }
