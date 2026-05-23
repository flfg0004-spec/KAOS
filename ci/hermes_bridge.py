"""Hermes CI Bridge — notifica resultados del pipeline via Telegram."""
import json, subprocess, os
from pathlib import Path

HERMES_CMD = "hermes"
CHANNEL = os.environ.get("HERMES_CHANNEL", "kaos-ci")


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

    status_icon = "✅" if passed else "❌"
    status_text = "PASÓ" if passed else "FALLÓ"

    msg = (
        f"{status_icon} Pipeline KAOS {status_text}\n"
        f"📌 {topic}\n"
        f"📊 Composite: {score}/100\n"
        f"💚 Health: {health}/100\n"
        f"⭐ Critic: {critic}/100\n"
        f"⏱ {duration}s"
    )

    try:
        cmd = [HERMES_CMD, "gateway", "send",
               "--channel", CHANNEL,
               "--message", msg]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print(f"Notification sent to #{CHANNEL}")
            return True
        else:
            print(f"Notification failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print(f"Hermes CLI not found ('{HERMES_CMD}'). Install with: npm i -g hermes-agent")
        return False
    except Exception as e:
        print(f"Notification error: {e}")
        return False


def notify_degradation(current_score: float, previous_score: float,
                       threshold: float = 10.0) -> None:
    """Send alert if composite dropped significantly."""
    drop = previous_score - current_score
    if drop >= threshold:
        msg = (
            f"⚠️ DEGRADACIÓN DETECTADA\n"
            f"Composite bajó de {previous_score} a {current_score} "
            f"({drop:+.1f} puntos)"
        )
        try:
            subprocess.run([HERMES_CMD, "gateway", "send",
                           "--channel", CHANNEL, "--message", msg],
                          capture_output=True, timeout=15)
        except Exception:
            pass


if __name__ == "__main__":
    import sys
    result_path = sys.argv[1] if len(sys.argv) > 1 else "pipeline-result.json"
    success = notify_result(result_path)
    sys.exit(0 if success else 1)
