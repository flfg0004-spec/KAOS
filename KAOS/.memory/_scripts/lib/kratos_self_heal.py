"""Self-healing for Kratos — auto-corrects flags based on telemetry."""

import logging
from datetime import datetime, timedelta

from lib.feature_flags import enable, disable, is_enabled
from lib.kratos_telemetry import telemetry_summary

logger = logging.getLogger(__name__)

_ACTION_COUNT = 0
_LAST_RESET = None


def _check_rate_limit() -> bool:
    global _ACTION_COUNT, _LAST_RESET
    now = datetime.now()
    if _LAST_RESET is None or (now - _LAST_RESET) > timedelta(hours=1):
        _ACTION_COUNT = 0
        _LAST_RESET = now
    if _ACTION_COUNT >= 3:
        logger.warning("Self-heal rate limit reached (3 actions/hour)")
        return False
    _ACTION_COUNT += 1
    return True


def heal() -> list[str]:
    actions = []
    if not _check_rate_limit():
        return actions

    summary = telemetry_summary()
    total = summary.get("total", 0)
    if total < 5:
        return actions

    by_decision = summary.get("by_decision", {})
    failed_count = by_decision.get("failed", 0) + by_decision.get("rejected_by_gov", 0)
    failure_rate = failed_count / max(1, total)

    if failure_rate > 0.3 and is_enabled("use_parallel_gates"):
        disable("use_parallel_gates")
        actions.append("Disabled use_parallel_gates (failure rate >30%)")
        logger.warning("Self-heal: disabled parallel gates (failure rate %.0f%%)", failure_rate * 100)

    avg_quality = summary.get("avg_quality_score", 10.0)
    if avg_quality < 5.0 and not is_enabled("use_real_mypy"):
        enable("use_real_mypy")
        actions.append("Enabled use_real_mypy (avg quality <5.0)")
        logger.warning("Self-heal: enabled real mypy (avg quality %.1f)", avg_quality)

    if failure_rate > 0.15 and not is_enabled("use_circuit_breaker"):
        enable("use_circuit_breaker")
        actions.append("Enabled use_circuit_breaker (failure rate >15%)")
        logger.warning("Self-heal: enabled circuit breaker (failure rate %.0f%%)", failure_rate * 100)

    return actions
