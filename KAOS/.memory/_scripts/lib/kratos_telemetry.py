"""Telemetry for Kratos agent — invocation recording, circuit breaker, summary stats.

Provides:
- KratosTelemetry TypedDict for structured telemetry data
- CircuitBreaker with CLOSED / OPEN / HALF_OPEN states
- record_invocation() — thread-safe CSV write via file_lock.py
- telemetry_summary() — aggregate stats from CSV
"""

import csv
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, TypedDict

from lib.file_lock import acquire_lock, release_lock

logger = logging.getLogger(__name__)

# ── CSV telemetry storage ─────────────────────────────────────────────

TELEMETRY_DIR = Path(__file__).resolve().parent.parent.parent / ".memory" / "telemetry"
TELEMETRY_FILE = TELEMETRY_DIR / "kratos_invocations.csv"

TELEMETRY_HEADER = [
    "timestamp",
    "decision",
    "quality_score",
    "language",
    "flags_active",
    "duration_ms",
    "iteration",
]


class KratosTelemetry(TypedDict, total=False):
    """Structured telemetry data for a single Kratos invocation."""
    start_time: str
    end_time: str
    duration_ms: float
    decision: str
    quality_score: float
    flags_active: list[str]
    language: str
    iteration: int


# ── Circuit Breaker ──────────────────────────────────────────────────

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreaker:
    """Simple circuit breaker for Kratos operations.

    States:
        CLOSED — normal operation, calls pass through
        OPEN — failures exceeded threshold, calls are rejected
        HALF_OPEN — recovery timeout elapsed, one trial call allowed
    """

    failure_threshold: int = 3
    recovery_timeout: float = 300.0
    _failure_count: int = 0
    _last_failure_time: float = 0.0
    _state: CircuitState = CircuitState.CLOSED

    @property
    def state(self) -> CircuitState:
        """Current circuit breaker state."""
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker → HALF_OPEN (recovery timeout elapsed)")
        return self._state

    def record_success(self) -> None:
        """Record a successful call. Resets failure count to 0."""
        self._failure_count = 0
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            logger.info("Circuit breaker → CLOSED (success in half-open state)")

    def record_failure(self) -> None:
        """Record a failed call. Opens circuit if threshold exceeded."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker → OPEN (%d failures, threshold=%d)",
                self._failure_count,
                self.failure_threshold,
            )

    def __call__(self, func: Callable) -> Callable:
        """Decorator: wrap a function with circuit breaker protection."""
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if self.state == CircuitState.OPEN:
                raise RuntimeError(
                    f"Circuit breaker OPEN — call rejected "
                    f"({self._failure_count} failures, "
                    f"recovery in {max(0, self.recovery_timeout - (time.time() - self._last_failure_time)):.0f}s)"
                )
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception:
                self.record_failure()
                raise
        return wrapper


# ── CSV recording ───────────────────────────────────────────────────

def _ensure_csv_header() -> None:
    """Create CSV file with header if it doesn't exist."""
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    if not TELEMETRY_FILE.exists():
        with open(TELEMETRY_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(TELEMETRY_HEADER)


def record_invocation(
    decision: str,
    quality_score: float = 0.0,
    language: str = "python",
    flags_active: list[str] | None = None,
    duration_ms: float = 0.0,
    iteration: int = 0,
) -> None:
    """Record a Kratos invocation to CSV telemetry.

    Thread-safe via file_lock.acquire_lock / release_lock.
    """
    _ensure_csv_header()

    lock_name = f"telemetry_{TELEMETRY_FILE.stem}"
    if not acquire_lock(lock_name, timeout=5):
        logger.warning("Could not acquire telemetry lock — skipping record")
        return

    try:
        with open(TELEMETRY_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                decision,
                f"{quality_score:.2f}",
                language,
                ",".join(sorted(flags_active)) if flags_active else "",
                f"{duration_ms:.1f}",
                str(iteration),
            ])
    except Exception as e:
        logger.warning("Failed to write telemetry: %s", e)
    finally:
        release_lock(lock_name)


def telemetry_summary() -> dict[str, Any]:
    """Read telemetry CSV and return aggregate statistics.

    Returns:
        Dict with total, by_decision, avg_quality, avg_duration, etc.
        Returns empty stats if CSV doesn't exist or is unreadable.
    """
    if not TELEMETRY_FILE.exists():
        return {
            "total": 0,
            "by_decision": {},
            "by_language": {},
            "avg_quality_score": 0.0,
            "avg_duration_ms": 0.0,
            "recent": [],
        }

    rows: list[dict[str, Any]] = []
    try:
        with open(TELEMETRY_FILE, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except Exception as e:
        logger.warning("Failed to read telemetry CSV: %s", e)
        return {"total": 0, "error": str(e)}

    if not rows:
        return {
            "total": 0,
            "by_decision": {},
            "by_language": {},
            "avg_quality_score": 0.0,
            "avg_duration_ms": 0.0,
            "recent": [],
        }

    by_decision: dict[str, int] = {}
    by_language: dict[str, int] = {}
    quality_scores: list[float] = []
    durations: list[float] = []

    for row in rows:
        d = row.get("decision", "unknown")
        by_decision[d] = by_decision.get(d, 0) + 1

        lang = row.get("language", "unknown")
        by_language[lang] = by_language.get(lang, 0) + 1

        try:
            quality_scores.append(float(row.get("quality_score", 0)))
        except (ValueError, TypeError):
            pass

        try:
            durations.append(float(row.get("duration_ms", 0)))
        except (ValueError, TypeError):
            pass

    recent = rows[-10:] if len(rows) > 10 else rows

    return {
        "total": len(rows),
        "by_decision": by_decision,
        "by_language": by_language,
        "avg_quality_score": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0.0,
        "avg_duration_ms": round(sum(durations) / len(durations), 1) if durations else 0.0,
        "recent": recent,
    }
