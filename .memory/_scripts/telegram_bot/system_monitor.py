"""Monitoreo pasivo del sistema — alertas automáticas por Telegram.

Corre como tarea asíncrona dentro del bot.
Se activa/desactiva con /alertas on|off|status.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from lib.format import boxify as _box

_LOG = logging.getLogger(__name__)

CHECK_INTERVAL = 300
ALERTS_ENABLED = False
_LAST_ALERTS: dict[str, float] = {}
_ALERT_COOLDOWN = 600

def _should_alert(key: str) -> bool:
    now = time.time()
    last = _LAST_ALERTS.get(key, 0)
    if now - last >= _ALERT_COOLDOWN:
        _LAST_ALERTS[key] = now
        return True
    return False

async def cmd_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ALERTS_ENABLED
    args = context.args
    if not args:
        status = "✅ ACTIVADO" if ALERTS_ENABLED else "❌ DESACTIVADO"
        await update.message.reply_text(
            _box(f"Alertas automáticas: {status}\n\n"
                 f"  /alertas on   — activar\n"
                 f"  /alertas off  — desactivar\n"
                 f"  /alertas status — estado", "🔔 ALERTAS"),
            parse_mode="Markdown"
        )
        return

    cmd = args[0].lower()
    if cmd == "on":
        ALERTS_ENABLED = True
        await update.message.reply_text("✅ Alertas automáticas activadas.")
    elif cmd == "off":
        ALERTS_ENABLED = False
        await update.message.reply_text("❌ Alertas automáticas desactivadas.")
    elif cmd == "status":
        status = "✅ ACTIVADO" if ALERTS_ENABLED else "❌ DESACTIVADO"
        await update.message.reply_text(
            _box(f"Estado: {status}\n"
                 f"Intervalo: {CHECK_INTERVAL}s\n"
                 f"Cooldown: {_ALERT_COOLDOWN}s", "🔔 ALERTAS"),
            parse_mode="Markdown"
        )

async def monitor_loop(app, chat_id: int):
    _LOG.info("System monitor loop started (interval: %ds)", CHECK_INTERVAL)
    while True:
        try:
            if ALERTS_ENABLED:
                alerts = _check_alerts()
                for alert in alerts:
                    await app.bot.send_message(
                        chat_id=chat_id,
                        text=_box(alert["msg"], alert["title"]),
                        parse_mode="Markdown"
                    )
        except Exception as e:
            _LOG.error("Monitor check error: %s", e)
        await asyncio.sleep(CHECK_INTERVAL)

def _check_alerts() -> list[dict]:
    alerts = []
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        if cpu > 85 and _should_alert("cpu"):
            alerts.append({"title": "💻 CPU ALTA", "msg": f"CPU al {cpu}% — revisa procesos."})

        mem = psutil.virtual_memory()
        if mem.percent > 90 and _should_alert("ram"):
            alerts.append({"title": "🧠 RAM CRÍTICA", "msg": f"RAM al {mem.percent}% ({round(mem.used/1e9,1)}/{round(mem.total/1e9,1)} GB)."})

        disk = psutil.disk_usage("C:\\")
        free_gb = disk.free / 1e9
        if free_gb < 5 and _should_alert("disk"):
            alerts.append({"title": "💾 DISCO BAJO", "msg": f"Solo {round(free_gb,1)} GB libres en C:. Libera espacio."})

        try:
            batt = psutil.sensors_battery()
            if batt and not batt.power_plugged and batt.percent < 20 and _should_alert("battery"):
                alerts.append({"title": "🔋 BATERÍA BAJA", "msg": f"Batería al {batt.percent}% — conecta el cargador."})
        except Exception:
            pass
    except ImportError:
        pass
    return alerts
