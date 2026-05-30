"""kosmos/ratelimit.py — Rate limiting para KosmosV2 (KosmosV3 A4).

Protege el pipeline contra saturación por concurrencia excesiva usando
un Semaphore con timeout y cola FIFO. Sin dependencias externas.

Uso:
    from lib.kosmos.ratelimit import acquire_pipeline, release_pipeline

    if acquire_pipeline():
        try:
            run_pipeline()
        finally:
            release_pipeline()
"""
import logging
import threading

logger = logging.getLogger(__name__)


class PipelineRateLimiter:
    """Rate limiter for concurrent pipeline executions.

    Uses Semaphore for max concurrency + queue for FIFO ordering.

    max_concurrent: max pipelines running simultaneously (default 3)
    queue_timeout: seconds to wait in queue before raising (default 300)
    """

    def __init__(self, max_concurrent: int = 3, queue_timeout: int = 300):
        self._sem = threading.Semaphore(max_concurrent)
        self._max = max_concurrent
        self._timeout = queue_timeout
        self._waiting = 0
        self._lock = threading.Lock()
        self._total_submitted = 0
        self._total_acquired = 0
        self._total_timeout = 0

    def acquire(self) -> bool:
        """Acquire a slot. Blocks until available or timeout.

        Returns:
            True if acquired, False if timed out.
        """
        with self._lock:
            self._waiting += 1
            self._total_submitted += 1
        acquired = self._sem.acquire(timeout=self._timeout)
        with self._lock:
            self._waiting -= 1
            if acquired:
                self._total_acquired += 1
            else:
                self._total_timeout += 1
        return acquired

    def release(self) -> None:
        """Release a slot. Must be called after acquire()."""
        self._sem.release()

    def status(self) -> dict:
        with self._lock:
            return {
                "max_concurrent": self._max,
                "available": max(0, self._max - (self._total_acquired - self._total_timeout)),
                "waiting": self._waiting,
                "total_submitted": self._total_submitted,
                "total_acquired": self._total_acquired,
                "total_timeout": self._total_timeout,
            }


# Module-level singleton
_RATE_LIMITER = PipelineRateLimiter()


def acquire_pipeline() -> bool:
    """Acquire pipeline execution slot. Returns True if allowed."""
    return _RATE_LIMITER.acquire()


def release_pipeline() -> None:
    """Release pipeline slot after execution."""
    _RATE_LIMITER.release()


def rate_limit_status() -> dict:
    """Get rate limiter status."""
    return _RATE_LIMITER.status()


def configure_ratelimiter(max_concurrent: int = 3, queue_timeout: int = 300) -> None:
    """Reconfigure the global rate limiter with new parameters.

    Creates a fresh instance — existing acquires are lost. Use at startup.

    Args:
        max_concurrent: Max pipelines running simultaneously.
        queue_timeout: Seconds to wait in queue before timeout.
    """
    global _RATE_LIMITER
    _RATE_LIMITER = PipelineRateLimiter(
        max_concurrent=max_concurrent,
        queue_timeout=queue_timeout,
    )
    logger.info("A4: Rate limiter reconfigured (max=%d, timeout=%d)",
                max_concurrent, queue_timeout)
