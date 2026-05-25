"""Comandos de programación de tareas vía Hermes cron."""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.hermes_bridge import _hermes_run, _hermes_available

_LOG = logging.getLogger(__name__)

def _box(msg: str, title: str = "⏰ CRON") -> str:
    lines = msg.split("\n")
    w = max(len(l) for l in lines) + 2
    top = "╔" + "═" * (w + 2) + "╗"
    hdr = "║ " + title.ljust(w) + " ║"
    sep = "╠" + "═" * (w + 2) + "╣"
    body = "\n".join("║ " + l.ljust(w) + " ║" for l in lines)
    bot = "╚" + "═" * (w + 2) + "╝"
    return f"`{top}\n{hdr}\n{sep}\n{body}\n{bot}`"

async def cmd_cron(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _hermes_available():
        await update.message.reply_text("❌ Hermes no está disponible. Instala: `npm i -g hermes-agent`", parse_mode="Markdown")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            _box(
                "Comandos:\n"
                "  /cron list              — listar tareas\n"
                "  /cron add <schedule> <cmd> — agregar tarea\n"
                "  /cron remove <id>       — eliminar tarea\n"
                "  /cron pause <id>        — pausar tarea\n"
                "  /cron resume <id>       — reanudar tarea\n\n"
                "Ej: /cron add \"every day at 9am\" /kaoshealth",
                "⏰ CRON HELP"
            ),
            parse_mode="Markdown"
        )
        return

    subcmd = args[0].lower()

    if subcmd == "list":
        ok, out = _hermes_run("cron", "list")
        if ok and out:
            await update.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")
        else:
            await update.message.reply_text("No hay tareas programadas.")

    elif subcmd == "add":
        rest = " ".join(args[1:])
        if not rest:
            await update.message.reply_text("Uso: /cron add \"<schedule>\" <comando>")
            return
        parts = rest.split('"')
        schedule = ""
        command = rest
        if len(parts) >= 3:
            schedule = parts[1].strip()
            command = parts[2].strip()
        if not schedule or not command:
            await update.message.reply_text("Uso: /cron add \"every day at 9am\" /kaoshealth")
            return
        ok, out = _hermes_run("cron", "add", "--schedule", schedule, "--command", command)
        if ok:
            await update.message.reply_text(
                _box(f"✅ Tarea programada:\n📅 {schedule}\n🔧 {command}", "✅ CRON ADD"),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"❌ Error: {out[:200]}")

    elif subcmd == "remove":
        if len(args) < 2:
            await update.message.reply_text("Uso: /cron remove <id>")
            return
        ok, out = _hermes_run("cron", "remove", args[1])
        status = "✅ Tarea eliminada." if ok else f"❌ Error: {out[:200]}"
        await update.message.reply_text(status)

    elif subcmd == "pause":
        if len(args) < 2:
            await update.message.reply_text("Uso: /cron pause <id>")
            return
        ok, out = _hermes_run("cron", "pause", args[1])
        status = "✅ Tarea pausada." if ok else f"❌ Error: {out[:200]}"
        await update.message.reply_text(status)

    elif subcmd == "resume":
        if len(args) < 2:
            await update.message.reply_text("Uso: /cron resume <id>")
            return
        ok, out = _hermes_run("cron", "resume", args[1])
        status = "✅ Tarea reanudada." if ok else f"❌ Error: {out[:200]}"
        await update.message.reply_text(status)

    else:
        await update.message.reply_text(f"❌ Subcomando desconocido: {subcmd}")
