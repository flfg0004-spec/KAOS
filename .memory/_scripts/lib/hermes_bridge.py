"""Hermes Pipeline Bridge — notify Telegram via Hermes gateway on pipeline steps."""
import subprocess, datetime, logging
from pathlib import Path

from lib.config import HERMES_CHANNEL

_LOG = logging.getLogger(__name__)
HERMES_BIN = "hermes"

def _boxify(body: str, title: str = "🤖 KAOS") -> str:
    lines = body.strip().split("\n")
    w = max(len(l) for l in lines)
    top = "╔" + "═" * (w + 2) + "╗"
    hdr = "║ " + title + " " * (w - len(title) + 1) + "║"
    sep = "╠" + "═" * (w + 2) + "╣"
    bot = "╚" + "═" * (w + 2) + "╝"
    inner = "\n".join("║ " + l + " " * (w - len(l) + 1) + "║" for l in lines)
    return f"{top}\n{hdr}\n{sep}\n{inner}\n{bot}"


def _hermes_send(message: str) -> bool:
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
    """Notify pipeline step status via Hermes with rich box format."""
    topic = state.get("topic", "unknown")
    score = state.get("critic_score", state.get("evaluation_score", None))
    ts = datetime.datetime.now().strftime("%H:%M")

    emoji = {"in_progress": "🔄", "completed": "✅", "failed": "❌"}
    icon = emoji.get(status, "ℹ️")
    status_upper = status.upper()

    body_lines = [f"{icon} {step_name} — {status_upper}", f"📌 {topic[:80]}"]
    if score is not None:
        body_lines.append(f"📊 Score: {score:.1f}")
    if status == "failed":
        err = state.get("error", "unknown error")
        body_lines.append(f"❌ Error: {str(err)[:100]}")
    body_lines.append(f"🕐 {ts}")

    body = "\n".join(body_lines)
    boxed = _boxify(body, f"{icon} {step_name}")
    return _hermes_send(boxed)


def notify_pipeline_result(topic: str, score: float, duration_s: int, passed: bool) -> bool:
    """Send a final pipeline result notification via Hermes."""
    icon = "✅" if passed else "❌"
    status = "PASÓ" if passed else "FALLÓ"
    minutes, sec = divmod(duration_s, 60)
    duration_str = f"{minutes}m {sec}s" if minutes else f"{sec}s"
    body = (
        f"{icon} Pipeline KAOS — {status}\n"
        f"📌 {topic[:60]}\n"
        f"📊 Score: {score}/100\n"
        f"⏱ {duration_str}"
    )
    return _hermes_send(_boxify(body, f"{icon} PIPELINE {status}"))
