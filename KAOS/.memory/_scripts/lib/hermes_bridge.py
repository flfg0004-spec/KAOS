"""Hermes Pipeline Bridge — notifica via Hermes router."""
import datetime
import logging

from lib.hermes_router import send_boxed

_LOG = logging.getLogger(__name__)


def pipeline_notify(state, step_name: str, status: str = "in_progress") -> bool:
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
        body_lines.append(f"❌ Error: {str(state.get('error', 'unknown error'))[:100]}")
    body_lines.append(f"🕐 {ts}")

    return send_boxed("\n".join(body_lines), f"{icon} {step_name}")


def notify_pipeline_result(topic: str, score: float, duration_s: int, passed: bool) -> bool:
    from lib.hermes_router import notify_pipeline as _np
    return _np(topic, score, duration_s, passed)
