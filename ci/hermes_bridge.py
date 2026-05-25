"""Hermes CI Bridge — notifica resultados del pipeline via Telegram.

Refactorizado: delega en lib/hermes_router para envío y formato.
"""
import json
import logging
from pathlib import Path

from lib.hermes_router import send_boxed

_LOG = logging.getLogger(__name__)


def notify_result(result_path: str = "pipeline-result.json") -> bool:
    path = Path(result_path)
    if not path.exists():
        print(f"Result file not found: {result_path}")
        return False

    try:
        r = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error reading result: {e}")
        return False

    score = r.get("composite", 0)
    health = r.get("system_health", 0)
    critic = r.get("critic_score", 0)
    topic = r.get("topic", "desconocido")
    duration = r.get("duration_seconds", 0)
    passed = r.get("passed", False)

    icon = "✅" if passed else "❌"
    status = "PASÓ" if passed else "FALLÓ"
    minutes, sec = divmod(int(duration), 60)

    body = (
        f"{icon} Pipeline KAOS — {status}\n"
        f"📌 {topic}\n"
        f"📊 Composite: {score}/100\n"
        f"💚 Health: {health}/100\n"
        f"⭐ Critic: {critic}/100\n"
        f"⏱ {minutes}m {sec}s"
    )

    ok = send_boxed(body, f"{icon} PIPELINE {status}")
    if ok:
        print("Notification sent via Hermes router")
    else:
        print("Notification failed")
    return ok


def notify_degradation(current_score: float, previous_score: float, threshold: float = 10.0) -> None:
    drop = previous_score - current_score
    if drop >= threshold:
        send_boxed(
            f"⚠️ DEGRADACIÓN DETECTADA\nComposite bajó de {previous_score} a {current_score} ({drop:+.1f} pts)",
            "⚠️ DEGRADACIÓN"
        )


if __name__ == "__main__":
    import sys
    result_path = sys.argv[1] if len(sys.argv) > 1 else "pipeline-result.json"
    success = notify_result(result_path)
    sys.exit(0 if success else 1)
