"""Hermes Pipeline Bridge — notify Telegram via Hermes gateway on pipeline steps."""
import subprocess, datetime, logging
from pathlib import Path

from lib.config import HERMES_CHANNEL

_LOG = logging.getLogger(__name__)
HERMES_BIN = "hermes"

def _hermes_send(message: str) -> bool:
    """Send a message via Hermes gateway to the KAOS channel."""
    try:
        result = subprocess.run(
            [HERMES_BIN, "gateway", "send", HERMES_CHANNEL, message],
            capture_output=True, text=True, timeout=15
        )
        return result.returncode == 0
    except FileNotFoundError:
        _LOG.warning("Hermes binary not found — notifications disabled")
        return False
    except subprocess.TimeoutExpired:
        _LOG.warning("Hermes send timed out")
        return False

def pipeline_notify(state, step_name: str, status: str = "in_progress") -> bool:
    """Notify pipeline step status via Hermes.

    Args:
        state: Current pipeline state
        step_name: Human-readable step name
        status: 'in_progress', 'completed', or 'failed'

    Returns True if notification was sent.
    """
    topic = state.get("topic", "unknown")
    score = state.get("critic_score", state.get("evaluation_score", None))
    ts = datetime.datetime.now().strftime("%H:%M:%S")

    emoji = {"in_progress": "🔄", "completed": "✅", "failed": "❌"}
    icon = emoji.get(status, "ℹ️")

    msg = f"{icon} [{ts}] **{step_name}** — {status}"
    msg += f"\n  Tema: {topic[:80]}"
    if score is not None:
        msg += f"\n  Score: {score:.1f}"
    if status == "failed":
        err = state.get("error", "unknown error")
        msg += f"\n  Error: {str(err)[:100]}"

    return _hermes_send(msg)
