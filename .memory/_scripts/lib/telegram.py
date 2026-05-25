"""Telegram notifications for KAOS via direct Bot API.

No depende de Hermes gateway. Envía directamente a Telegram Bot API.
Token y chat_id se leen de variables de entorno.
"""

import json
import os
import urllib.request
from datetime import datetime

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1487561068")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send(message: str, silent: bool = False) -> bool:
    """Send a message to the configured Telegram chat.

    Args:
        message: Text to send (plain text, no markdown)
        silent: If True, send without notification sound

    Returns:
        True if sent successfully
    """
    if not BOT_TOKEN:
        return False
    try:
        payload = {"chat_id": CHAT_ID, "text": message, "disable_notification": silent}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            API_URL, data=data, headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode("utf-8"))
        return result.get("ok", False)
    except Exception:
        return False


def notify_pipeline(topic: str, score: float, duration_s: int, passed: bool) -> bool:
    """Notify pipeline completion."""
    icon = "✅" if passed else "❌"
    status = "PASÓ" if passed else "FALLÓ"
    msg = (
        f"{icon} Pipeline KAOS {status}\n"
        f"📌 {topic}\n"
        f"📊 Score: {score}/100\n"
        f"⏱ {duration_s}s"
    )
    return send(msg)


def notify_degradation(old_score: float, new_score: float) -> bool:
    """Notify quality degradation."""
    drop = old_score - new_score
    if drop < 10:
        return False
    msg = (
        f"⚠️ DEGRADACIÓN DETECTADA\n"
        f"Quality bajó de {old_score} a {new_score} ({drop:+.1f} pts)"
    )
    return send(msg)


def notify_service_down(service: str, error: str = "") -> bool:
    """Notify a service is down."""
    msg = f"🔴 {service} CAÍDO\n{error}" if error else f"🔴 {service} CAÍDO"
    return send(msg)


def notify_report(report_type: str, path: str) -> bool:
    """Notify a new report is available."""
    msg = f"📄 Nuevo reporte: {report_type}\n{path}"
    return send(msg)
