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


def _boxify(body: str, title: str = "🤖 KAOS") -> str:
    lines = body.strip().split("\n")
    w = max(len(l) for l in lines)
    top = "╔" + "═" * (w + 2) + "╗"
    hdr = "║ " + title + " " * (w - len(title) + 1) + "║"
    sep = "╠" + "═" * (w + 2) + "╣"
    bot = "╚" + "═" * (w + 2) + "╝"
    inner = "\n".join("║ " + l + " " * (w - len(l) + 1) + "║" for l in lines)
    return f"`{top}\n{hdr}\n{sep}\n{inner}\n{bot}`"


def send(message: str, silent: bool = False) -> bool:
    if not BOT_TOKEN:
        return False
    try:
        payload = {"chat_id": CHAT_ID, "text": message, "disable_notification": silent, "parse_mode": "Markdown"}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            API_URL, data=data, headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode("utf-8"))
        return result.get("ok", False)
    except Exception:
        return False


def _fmt_duration(s: int) -> str:
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def notify_pipeline(topic: str, score: float, duration_s: int, passed: bool, agents: int = 5, detail: str = "") -> bool:
    icon = "✅" if passed else "❌"
    status = "PASÓ" if passed else "FALLÓ"
    body = (
        f"{icon} Pipeline KAOS — {status}\n"
        f"📌 {topic[:60]}\n"
        f"📊 Score: {score}/100\n"
        f"⏱ {_fmt_duration(duration_s)}"
    )
    if agents:
        body += f"\n🔄 Agentes: {agents}/5 completados"
    if detail:
        body += f"\n📁 {detail[:100]}"
    return send(_boxify(body, f"{icon} PIPELINE {status}"))


def notify_degradation(old_score: float, new_score: float) -> bool:
    drop = old_score - new_score
    if drop < 10:
        return False
    body = (
        f"⚠️ DEGRADACIÓN DETECTADA\n"
        f"Calidad: {old_score} → {new_score} ({drop:+.1f} pts)"
    )
    return send(_boxify(body, "⚠️ DEGRADACIÓN"))


def notify_service_down(service: str, error: str = "") -> bool:
    body = f"🔴 {service} CAÍDO\n{error}" if error else f"🔴 {service} CAÍDO"
    return send(_boxify(body, "🔴 SERVICE DOWN"))


def notify_report(report_type: str, path: str) -> bool:
    body = f"📄 Nuevo reporte: {report_type}\n{path}"
    return send(_boxify(body, "📄 REPORTE"))
