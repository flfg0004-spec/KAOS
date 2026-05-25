"""KAOS Telegram Bot — long polling multi-modal ingestion + dashboard commands."""

import asyncio
import io
import json
import logging
import os
from pathlib import Path
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes

from telegram_bot.config import TOKEN, ALLOWED_CHATS
from telegram_bot.classifiers.content_classifier import classify

from processors.web_scraper import process_url
from processors.youtube_transcriber import process_youtube
from processors.image_processor import process_image
from processors.document_processor import process_document
from processors.audio_transcriber import process_audio

logging.basicConfig(level=logging.INFO)

SCRIPTS = Path(__file__).resolve().parent.parent / "_scripts"

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
    await update.message.reply_text(
        "🤖 KAOS Bot\n\n"
        "📥 Ingesta de contenido:\n"
        "  Envía links, YouTube, imágenes, PDFs, audios\n\n"
        "📊 Dashboard commands:\n"
        "  /costos — tokens usados hoy/semana/mes por agente\n"
        "  /dashboard — enviar dashboard HTML completo\n"
        "  /modelos — desglose por modelo (paginado)\n"
        "  /sesiones — últimas sesiones activas\n"
        "  /agentes — breakdown por agente\n"
        "  /status — estado del sistema\n"
        "  /ayuda — esta lista\n"
    )

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
        "**Dashboard:**\n"
        "  /costos — tokens y gasto por agente\n"
        "  /status — estado del pipeline y salud\n"
        "  /dashboard — enviar dashboard HTML\n"
        "  /modelos — desglose por modelo\n"
        "  /agentes — breakdown por agente\n"
        "  /sesiones — últimas sesiones activas\n\n"
        "**Ingesta:**\n"
        "  Envía URLs, YouTube, imágenes, PDFs\n\n"
        "**Sistema:**\n"
        "  /ayuda — esta lista\n"
        "  /start — mensaje de bienvenida",
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


def main():
    if not TOKEN:
        print("TELEGRAM_BOT_TOKEN no configurado")
        return
    app = Application.builder().token(TOKEN).build()
    # Ingesta handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", cmd_ayuda))
    app.add_handler(CommandHandler("help", cmd_ayuda))
    # Dashboard command handlers
    app.add_handler(CommandHandler("costos", cmd_costos))
    app.add_handler(CommandHandler("dashboard", cmd_dashboard))
    app.add_handler(CommandHandler("status", cmd_status))
    # Message handler (catch-all for ingestion)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    print("KAOS Bot iniciado (long polling) — dashboard commands activos")
    app.run_polling()


if __name__ == "__main__":
    main()
