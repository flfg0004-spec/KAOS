"""KAOS Telegram Bot — long polling multi-modal ingestion."""

import asyncio
import logging
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "KAOS Ingest Bot\n\n"
        "Envía cualquier contenido:\n"
        "• Links web → ingesta con análisis\n"
        "• YouTube → transcripción + resumen\n"
        "• Imágenes → descripción + OCR\n"
        "• PDFs/DOCX → extracción de texto\n"
        "• Audios → transcripción\n"
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
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    print("KAOS Bot iniciado (long polling)...")
    app.run_polling()


if __name__ == "__main__":
    main()
