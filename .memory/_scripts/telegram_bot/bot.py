"""KAOS Telegram Bot — long polling multi-modal ingestion + dashboard + power + KAOS control."""

import asyncio
import io
import json
import logging
import os
from pathlib import Path
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes

from telegram_bot.config import TOKEN, ALLOWED_CHATS, HERMES_OUTBOX_ENABLED
from telegram_bot.classifiers.content_classifier import classify

from telegram_bot.power_commands import (
    cmd_sleep, cmd_hibernate, cmd_shutdown, cmd_restart,
    cmd_confirm, cmd_cancel_power, cmd_powerstatus,
)
from telegram_bot.hermes_bridge import outbox_loop, ticket_create
from telegram_bot.system_monitor import cmd_alertas, monitor_loop
from telegram_bot.file_commands import cmd_ls, cmd_cat, cmd_tail, cmd_download, cmd_allowedpaths
from telegram_bot.kaos_commands import (
    cmd_kaospipeline, cmd_kaosstart, cmd_kaosstop,
    cmd_kaosagentes, cmd_kaoshealth, cmd_kaosscores,
)
from telegram_bot.cron_commands import cmd_cron

from processors.web_scraper import process_url
from processors.youtube_transcriber import process_youtube
from processors.image_processor import process_image
from processors.document_processor import process_document
from processors.audio_transcriber import process_audio

logging.basicConfig(level=logging.INFO)

SCRIPTS = Path(__file__).resolve().parent.parent / "_scripts"

def _box(msg: str, title: str = "🤖 KAOS") -> str:
    lines = msg.split("\n")
    w = max(len(l) for l in lines) + 2
    top = "╔" + "═" * (w + 2) + "╗"
    hdr = "║ " + title.ljust(w) + " ║"
    sep = "╠" + "═" * (w + 2) + "╣"
    body = "\n".join("║ " + l.ljust(w) + " ║" for l in lines)
    bot = "╚" + "═" * (w + 2) + "╝"
    return f"`{top}\n{hdr}\n{sep}\n{body}\n{bot}`"

def _load_dashboard_data() -> dict:
    try:
        path = SCRIPTS.parent / "dashboard" / "dashboard.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        return {}

def _load_token_usage() -> dict:
    try:
        path = SCRIPTS.parent / "cache" / "token-usage.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        return {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(_box(
        "📥 Ingesta: URLs, YouTube, imágenes, PDFs, audios\n\n"
        "📊 Dashboard:\n"
        "  /costos /status /dashboard\n\n"
        "⚡ Power:\n"
        "  /sleep /hibernate /shutdown /restart\n"
        "  /confirm /cancel /powerstatus\n\n"
        "🤖 KAOS:\n"
        "  /kaospipeline /kaosstart /kaosstop\n"
        "  /kaosagentes /kaoshealth /kaosscores\n\n"
        "🔔 Sistema:\n"
        "  /alertas /cron /ls /download\n\n"
        "❓ /ayuda — lista completa",
        "🤖 KAOS BOT"
    ), parse_mode="Markdown")

async def cmd_costos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tokens usados hoy/semana/mes por agente."""
    data = _load_token_usage()
    if not data:
        await update.message.reply_text("No hay datos de tokens aún. Usa agentes primero.")
        return
    tot = data.get("totals", {})
    daily = data.get("daily", {})
    today_str = __import__("datetime").date.today().isoformat()
    today_data = daily.get(today_str, {})
    msg = (
        f"💰 **Costos KAOS**\n\n"
        f"**Totales:**\n"
        f"  Llamadas: {tot.get('total_calls', 0)}\n"
        f"  Costo: ${tot.get('cost_usd', 0):.4f}\n"
        f"  Tokens prompt: {tot.get('prompt_tokens', 0):,}\n"
        f"  Tokens completion: {tot.get('completion_tokens', 0):,}\n\n"
        f"**Hoy ({today_str}):**\n"
        f"  Llamadas: {today_data.get('calls', 0)}\n"
        f"  Costo: ${today_data.get('cost_usd', 0):.4f}\n"
        f"  Tokens: {today_data.get('prompt_tokens', 0):,}\n\n"
    )
    per_agent = {}
    for s in data.get("sessions", []):
        a = s.get("agent", "unknown")
        if a not in per_agent:
            per_agent[a] = {"calls": 0, "cost": 0}
        per_agent[a]["calls"] += 1
        per_agent[a]["cost"] += s.get("cost_usd", 0)
    if per_agent:
        msg += "**Por agente:**\n"
        for agent, stats in sorted(per_agent.items(), key=lambda x: -x[1]["cost"]):
            msg += f"  {agent}: {stats['calls']} calls, ${stats['cost']:.4f}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enviar dashboard HTML completo como documento."""
    html_path = SCRIPTS.parent / "dashboard" / "index.html"
    if not html_path.exists():
        await update.message.reply_text("Dashboard no generado. Ejecuta: vault.py dashboard")
        return
    try:
        doc = io.BytesIO(html_path.read_bytes())
        doc.name = "kaos-dashboard.html"
        await update.message.reply_document(
            document=doc,
            filename="kaos-dashboard.html",
            caption="📊 Dashboard KAOS — métricas del vault"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:100]}")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Estado del sistema: pipeline, salud, calidad."""
    data = _load_dashboard_data()
    if not data:
        await update.message.reply_text("No hay datos de dashboard. Ejecuta: vault.py dashboard")
        return
    pipe = data.get("pipeline", {})
    health = data.get("health", {})
    qual = data.get("quality", {})
    msg = (
        f"📊 **KAOS Status**\n\n"
        f"**Pipeline:**\n"
        f"  Estado: {pipe.get('status', 'N/A')}\n"
        f"  Perfil: {pipe.get('profile', 'N/A')}\n\n"
        f"**Salud:**\n"
        f"  Overall: {health.get('overall', 'N/A')}\n"
        f"  Lint issues: {health.get('lint_issues', 'N/A')}\n"
        f"  Git clean: {'✅' if health.get('git_clean') else '❌'}\n\n"
        f"**Calidad:**\n"
        f"  Score: {qual.get('score', 'N/A')}/100\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **KAOS Bot — Comandos**\n\n"
        "**📊 Dashboard:**\n"
        "  /costos — tokens y gasto por agente\n"
        "  /status — estado del pipeline y salud\n"
        "  /dashboard — enviar dashboard HTML\n\n"
        "**⚡ Power Management:**\n"
        "  /sleep — suspender a RAM\n"
        "  /hibernate — hibernar equipo\n"
        "  /shutdown [N] — apagar en N min\n"
        "  /restart [N] — reiniciar en N min\n"
        "  /confirm — confirmar apagado\n"
        "  /cancel — cancelar apagado\n"
        "  /powerstatus — estado del PC\n\n"
        "**🤖 Control KAOS:**\n"
        "  /kaospipeline — estado del pipeline\n"
        "  /kaosstart <tema> — iniciar pipeline\n"
        "  /kaosstop — detener pipeline\n"
        "  /kaosagentes — estado de agentes\n"
        "  /kaoshealth — salud del sistema\n"
        "  /kaosscores — scores de calidad\n\n"
        "**🔔 Sistema:**\n"
        "  /alertas — monitoreo automático\n"
        "  /cron — tareas programadas\n\n"
        "**📁 Archivos:**\n"
        "  /ls <ruta> — listar directorio\n"
        "  /cat <ruta> — ver archivo\n"
        "  /tail <ruta> [N] — últimas N líneas\n"
        "  /download <ruta> — descargar archivo\n"
        "  /allowedpaths — rutas permitidas\n\n"
        "**📥 Ingesta:**\n"
        "  Envía URLs, YouTube, imágenes, PDFs, audios",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ALLOWED_CHATS:
        await update.message.reply_text("No autorizado")
        return

    msg = update.message
    content_type = classify(
        text=msg.text or msg.caption or "",
        mime_type=msg.document.mime_type if msg.document else "",
        has_photo=bool(msg.photo),
        has_video=bool(msg.video),
        has_document=bool(msg.document),
        has_audio=bool(msg.audio),
    )

    processors = {
        "youtube": lambda: process_youtube(msg.text or msg.caption or ""),
        "url": lambda: process_url(msg.text or ""),
        "image": lambda: process_image(msg),
        "pdf": lambda: process_document(msg),
        "document": lambda: process_document(msg),
        "text_file": lambda: process_document(msg),
        "audio": lambda: process_audio(msg),
        "text": lambda: process_url(msg.text or ""),
    }

    handler = processors.get(content_type)
    if not handler:
        await msg.reply_text("Tipo de contenido no soportado")
        return

    await msg.reply_text(f"Procesando {content_type}...")
    try:
        result = await asyncio.to_thread(handler)
        await msg.reply_text(f"Listo: {result[:200]}")
    except Exception as e:
        await msg.reply_text(f"Error: {str(e)[:200]}")

    ticket_create(
        title=f"[TG] {update.effective_user.first_name}: {msg.text or msg.caption or content_type}",
        tag="telegram-ingest"
    )


async def post_init(app: Application):
    """Start Hermes outbox poller and system monitor as background tasks."""
    loop = asyncio.get_event_loop()
    chat_id = int(os.environ.get("TELEGRAM_CHAT_ID", "1487561068"))

    if HERMES_OUTBOX_ENABLED:
        loop.create_task(outbox_loop(app, chat_id))
        logging.info("Hermes outbox loop scheduled")

    loop.create_task(monitor_loop(app, chat_id))
    logging.info("System monitor loop scheduled")


def main():
    if not TOKEN:
        print("TELEGRAM_BOT_TOKEN no configurado")
        return
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    # Ingesta handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", cmd_ayuda))
    app.add_handler(CommandHandler("help", cmd_ayuda))

    # Dashboard command handlers
    app.add_handler(CommandHandler("costos", cmd_costos))
    app.add_handler(CommandHandler("dashboard", cmd_dashboard))
    app.add_handler(CommandHandler("status", cmd_status))

    # Power management handlers
    app.add_handler(CommandHandler("sleep", cmd_sleep))
    app.add_handler(CommandHandler("hibernate", cmd_hibernate))
    app.add_handler(CommandHandler("shutdown", cmd_shutdown))
    app.add_handler(CommandHandler("restart", cmd_restart))
    app.add_handler(CommandHandler("confirm", cmd_confirm))
    app.add_handler(CommandHandler("cancel", cmd_cancel_power))
    app.add_handler(CommandHandler("powerstatus", cmd_powerstatus))

    # KAOS control handlers
    app.add_handler(CommandHandler("kaospipeline", cmd_kaospipeline))
    app.add_handler(CommandHandler("kaosstart", cmd_kaosstart))
    app.add_handler(CommandHandler("kaosstop", cmd_kaosstop))
    app.add_handler(CommandHandler("kaosagentes", cmd_kaosagentes))
    app.add_handler(CommandHandler("kaoshealth", cmd_kaoshealth))
    app.add_handler(CommandHandler("kaosscores", cmd_kaosscores))

    # System monitor
    app.add_handler(CommandHandler("alertas", cmd_alertas))

    # Cron
    app.add_handler(CommandHandler("cron", cmd_cron))

    # File browser
    app.add_handler(CommandHandler("ls", cmd_ls))
    app.add_handler(CommandHandler("cat", cmd_cat))
    app.add_handler(CommandHandler("tail", cmd_tail))
    app.add_handler(CommandHandler("download", cmd_download))
    app.add_handler(CommandHandler("allowedpaths", cmd_allowedpaths))

    # Message handler (catch-all for ingestion)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print("KAOS Bot iniciado (long polling) — 30+ comandos activos")
    app.run_polling()


if __name__ == "__main__":
    main()
