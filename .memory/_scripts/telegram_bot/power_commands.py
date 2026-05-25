import asyncio
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from lib.format import boxify as _box

_LOG = logging.getLogger(__name__)

POWER_LOG = Path(__file__).resolve().parent.parent.parent / "_pipeline" / "power_events.log"
POWER_LOG.parent.mkdir(parents=True, exist_ok=True)

PENDING_OPERATION = {
    "type": None,
    "expires_at": 0,
    "chat_id": None,
}

def _log_power(event: str, detail: str = ""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(POWER_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {event} {detail}\n".strip() + "\n")

async def cmd_sleep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        _box("💤 Suspendiendo equipo a RAM...\n\nPuedes reanudar moviendo\nel mouse o presionando tecla.", "💤 SLEEP"),
        parse_mode="Markdown"
    )
    _log_power("SLEEP")
    asyncio.create_task(_do_sleep())

async def cmd_hibernate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        _box("❄️ Hibernando equipo...\n\nSe guarda el estado actual\ny se apaga. Al encender,\ntodo vuelve a donde estaba.", "❄️ HIBERNATE"),
        parse_mode="Markdown"
    )
    _log_power("HIBERNATE")
    asyncio.create_task(_do_hibernate())

async def cmd_shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    mins = 5
    if args:
        try:
            mins = max(1, min(120, int(args[0])))
        except ValueError:
            pass
    secs = mins * 60
    PENDING_OPERATION["type"] = "shutdown"
    PENDING_OPERATION["expires_at"] = time.time() + 60
    PENDING_OPERATION["chat_id"] = update.effective_chat.id

    await update.message.reply_text(
        _box(
            f"🛑 Apagando en {mins} min\n\n"
            f"  /confirm  para confirmar\n"
            f"  /cancel   para cancelar\n\n"
            f"⏳ Expira en 60s",
            "🛑 SHUTDOWN"
        ),
        parse_mode="Markdown"
    )
    subprocess.run(["shutdown", "/s", "/t", str(secs)], capture_output=True)
    _log_power("SHUTDOWN_SCHEDULED", f"{mins}min")

async def cmd_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    mins = 5
    if args:
        try:
            mins = max(1, min(120, int(args[0])))
        except ValueError:
            pass
    secs = mins * 60
    PENDING_OPERATION["type"] = "restart"
    PENDING_OPERATION["expires_at"] = time.time() + 60
    PENDING_OPERATION["chat_id"] = update.effective_chat.id

    await update.message.reply_text(
        _box(
            f"🔄 Reiniciando en {mins} min\n\n"
            f"  /confirm  para confirmar\n"
            f"  /cancel   para cancelar\n\n"
            f"⏳ Expira en 60s",
            "🔄 RESTART"
        ),
        parse_mode="Markdown"
    )
    subprocess.run(["shutdown", "/r", "/t", str(secs)], capture_output=True)
    _log_power("RESTART_SCHEDULED", f"{mins}min")

async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    op = PENDING_OPERATION["type"]
    if not op or time.time() > PENDING_OPERATION["expires_at"]:
        await update.message.reply_text("⚠️ No hay operación pendiente o expiró.")
        return
    await update.message.reply_text(
        _box(f"✅ {op.upper()} confirmado.\n\nYa no puedes cancelarlo.", f"✅ CONFIRMADO"),
        parse_mode="Markdown"
    )
    PENDING_OPERATION["type"] = None
    _log_power(f"{op.upper()}_CONFIRMED")

async def cmd_cancel_power(update: Update, context: ContextTypes.DEFAULT_TYPE):
    op = PENDING_OPERATION.get("type")
    cancelled_shutdown = False
    try:
        r = subprocess.run(["shutdown", "/a"], capture_output=True, text=True)
        cancelled_shutdown = r.returncode == 0
    except Exception:
        pass
    PENDING_OPERATION["type"] = None
    if cancelled_shutdown:
        await update.message.reply_text(
            _box("✅ Apagado/reinicio cancelado.", "✅ CANCELADO"),
            parse_mode="Markdown"
        )
        _log_power("SHUTDOWN_CANCELLED")
    elif op:
        await update.message.reply_text(
            _box("✅ Operación cancelada.", "✅ CANCELADO"),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("No hay operación pendiente.")

async def cmd_powerstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = _get_system_info()
    msg = (
        f"⏱ Uptime: {info.get('uptime', 'N/A')}\n"
        f"💻 CPU: {info.get('cpu_percent', 'N/A')}%\n"
        f"🧠 RAM: {info.get('ram_percent', 'N/A')}% "
        f"({info.get('ram_used_gb', '?')}/{info.get('ram_total_gb', '?')} GB)\n"
        f"💾 Disco C: {info.get('disk_percent', 'N/A')}% "
        f"({info.get('disk_free_gb', '?')} GB libres)\n"
        f"🔋 Batería: {info.get('battery', 'N/A')}"
    )
    await update.message.reply_text(_box(msg, "📊 STATUS PC"), parse_mode="Markdown")

def _get_system_info() -> dict:
    info = {}
    try:
        import psutil
        info["cpu_percent"] = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        info["ram_percent"] = mem.percent
        info["ram_used_gb"] = round(mem.used / 1e9, 1)
        info["ram_total_gb"] = round(mem.total / 1e9, 1)
        disk = psutil.disk_usage("C:\\")
        info["disk_percent"] = disk.percent
        info["disk_free_gb"] = round(disk.free / 1e9, 1)
        boot = datetime.fromtimestamp(psutil.boot_time())
        delta = datetime.now() - boot
        d = delta.days
        h = delta.seconds // 3600
        m = (delta.seconds % 3600) // 60
        info["uptime"] = f"{d}d {h}h {m}m"
        try:
            batt = psutil.sensors_battery()
            if batt:
                pct = batt.percent
                plug = "🔌" if batt.power_plugged else "🔋"
                info["battery"] = f"{pct}% {plug}"
        except Exception:
            pass
    except ImportError:
        try:
            r = subprocess.run(
                ["powershell", "-Command",
                 "Get-CimInstance Win32_OperatingSystem | Select-Object LastBootUpTime,TotalVisibleMemorySize,FreePhysicalMemory"],
                capture_output=True, text=True, timeout=10
            )
            info["raw"] = r.stdout[:200]
        except Exception:
            info["error"] = "psutil no instalado"
    return info

async def _do_sleep():
    await asyncio.sleep(1)
    try:
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"], timeout=5)
    except Exception as e:
        _log_power("SLEEP_FAILED", str(e))

async def _do_hibernate():
    await asyncio.sleep(1)
    try:
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "1", "0", "0"], timeout=5)
    except Exception as e:
        _log_power("HIBERNATE_FAILED", str(e))
