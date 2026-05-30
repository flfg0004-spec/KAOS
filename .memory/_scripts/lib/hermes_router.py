"""Hermes Router — único punto de envío de mensajes.

Jerarquía:
  1. Hermes send → Telegram/Discord/Slack vía `hermes send`
  2. Telegram Bot API directa (fallback si Hermes no disponible)
"""

import logging
import os
import subprocess

from lib.format import boxify

_LOG = logging.getLogger(__name__)
HERMES_BIN = "hermes"

HERMES_AVAILABLE = None
_HERMES_LAST_CHECK = 0.0
_HERMES_TTL = 30


def _check_hermes() -> bool:
    global HERMES_AVAILABLE, _HERMES_LAST_CHECK
    now = __import__("time").time()
    if HERMES_AVAILABLE is not None and (now - _HERMES_LAST_CHECK) < _HERMES_TTL:
        return HERMES_AVAILABLE
    try:
        r = subprocess.run([HERMES_BIN, "--version"], capture_output=True, text=True, timeout=5)
        HERMES_AVAILABLE = r.returncode == 0
    except Exception:
        HERMES_AVAILABLE = False
    _HERMES_LAST_CHECK = now
    return HERMES_AVAILABLE


def send(message: str, channel: str = "telegram", chat_id: str = None, silent: bool = False) -> bool:
    if _check_hermes():
        try:
            target = f"{channel}:{chat_id}" if chat_id else channel
            r = subprocess.run(
                [HERMES_BIN, "send", "--to", target, message],
                capture_output=True, text=True, timeout=30,
                env={**os.environ}
            )
            if r.returncode == 0:
                return True
            _LOG.warning("Hermes send failed: %s", r.stderr[:200])
        except Exception as e:
            _LOG.warning("Hermes send error: %s", e)
    return _telegram_fallback(message, silent)


def _telegram_fallback(message: str, silent: bool = False) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "1487561068")
    if not token:
        return False
    try:
        import json, urllib.request
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "disable_notification": silent, "parse_mode": "Markdown"}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode("utf-8")).get("ok", False)
    except Exception:
        return False


def send_boxed(body: str, title: str, channel: str = "telegram", chat_id: str = None) -> bool:
    return send(boxify(body, title), channel=channel, chat_id=chat_id)


def notify_pipeline(topic: str, score: float, duration_s: int, passed: bool, agents: int = 5) -> bool:
    from lib.format import fmt_duration
    icon = "✅" if passed else "❌"
    status = "PASÓ" if passed else "FALLÓ"
    body = (
        f"{icon} Pipeline KAOS — {status}\n"
        f"📌 {topic[:60]}\n"
        f"📊 Score: {score}/100\n"
        f"⏱ {fmt_duration(duration_s)}"
    )
    if agents:
        body += f"\n🔄 Agentes: {agents}/5 completados"
    return send_boxed(body, f"{icon} PIPELINE {status}")


def notify_degradation(old_score: float, new_score: float) -> bool:
    drop = old_score - new_score
    if drop < 10:
        return False
    return send_boxed(
        f"⚠️ DEGRADACIÓN DETECTADA\nCalidad: {old_score} → {new_score} ({drop:+.1f} pts)",
        "⚠️ DEGRADACIÓN"
    )


def notify_service_down(service: str, error: str = "") -> bool:
    body = f"🔴 {service} CAÍDO\n{error}" if error else f"🔴 {service} CAÍDO"
    return send_boxed(body, "🔴 SERVICE DOWN")


def notify_report(report_type: str, path: str) -> bool:
    return send_boxed(f"📄 Nuevo reporte: {report_type}\n{path}", "📄 REPORTE")
