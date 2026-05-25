"""Comandos de Kanban vía Telegram — listar, ver y crear tareas."""

import json
import logging

from telegram import Update
from telegram.ext import ContextTypes

from lib.format import boxify as _box
from lib.kanban_dispatcher import _hermes as hermes_run

_LOG = logging.getLogger(__name__)


async def cmd_kanban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(_box(
            "Comandos kanban:\n"
            "  /kanban list         — tareas ready/running/done\n"
            "  /kanban show <id>    — detalle de tarea\n"
            "  /kanban create <título> — crear tarea\n"
            "  /kanban stats        — conteos por estado",
            "📋 KANBAN HELP"
        ), parse_mode="Markdown")
        return

    subcmd = args[0].lower()

    if subcmd == "list":
        ok, out = hermes_run("kanban", "list", "--json")
        if not ok or not out:
            await update.message.reply_text("No hay tareas o kanban no disponible.")
            return
        try:
            data = json.loads(out)
            tasks = data if isinstance(data, list) else data.get("tasks", data)
            if not tasks:
                await update.message.reply_text("Kanban vacío.")
                return
            lines = []
            for t in tasks[:15]:
                sid = t.get("id", "?")[:12]
                status = t.get("status", "?")
                title = t.get("title", "?")[:50]
                icon = {"ready": "🟡", "running": "🔄", "done": "✅", "blocked": "🔴", "triage": "📥"}
                lines.append(f"{icon.get(status, '⚪')} `{sid}` {title} [{status}]")
            if len(tasks) > 15:
                lines.append(f"... y {len(tasks) - 15} más")
            await update.message.reply_text(_box("\n".join(lines), "📋 KANBAN"), parse_mode="Markdown")
        except json.JSONDecodeError:
            await update.message.reply_text(f"```\n{out[:1000]}\n```", parse_mode="Markdown")

    elif subcmd == "show":
        if len(args) < 2:
            await update.message.reply_text("Uso: /kanban show <id>")
            return
        ok, out = hermes_run("kanban", "show", args[1])
        await update.message.reply_text(f"```\n{out[:1500]}\n```", parse_mode="Markdown") if ok else \
            await update.message.reply_text("Tarea no encontrada.")

    elif subcmd == "create":
        title = " ".join(args[1:]) if len(args) > 1 else ""
        if not title:
            await update.message.reply_text("Uso: /kanban create <título>")
            return
        ok, out = hermes_run("kanban", "create", "--json", title)
        if ok and out:
            try:
                tid = json.loads(out).get("id", "?")
                await update.message.reply_text(_box(f"✅ Tarea creada: `{tid}`\n📌 {title}", "📋 KANBAN CREATE"),
                                                parse_mode="Markdown")
            except json.JSONDecodeError:
                await update.message.reply_text(f"✅ Creada: {out[:200]}")
        else:
            await update.message.reply_text(f"❌ Error: {out[:200]}")

    elif subcmd == "stats":
        ok, out = hermes_run("kanban", "list", "--json")
        if not ok or not out:
            await update.message.reply_text("No disponible.")
            return
        try:
            data = json.loads(out)
            tasks = data if isinstance(data, list) else data.get("tasks", data)
            counts = {}
            for t in (tasks or []):
                s = t.get("status", "unknown")
                counts[s] = counts.get(s, 0) + 1
            lines = [f"{k}: {v}" for k, v in sorted(counts.items())]
            await update.message.reply_text(_box("\n".join(lines) or "(vacío)", "📊 KANBAN STATS"),
                                            parse_mode="Markdown")
        except json.JSONDecodeError:
            await update.message.reply_text("Error parsing kanban data.")
