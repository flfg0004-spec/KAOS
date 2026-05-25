"""Comandos de navegación remota de archivos vía Telegram."""

import io
import logging
import os
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.config import ALLOWED_PATHS, MAX_FILE_SIZE

_LOG = logging.getLogger(__name__)

def _box(msg: str, title: str = "📁 FILES") -> str:
    lines = msg.split("\n")
    w = max(len(l) for l in lines) + 2
    top = "╔" + "═" * (w + 2) + "╗"
    hdr = "║ " + title.ljust(w) + " ║"
    sep = "╠" + "═" * (w + 2) + "╣"
    body = "\n".join("║ " + l.ljust(w) + " ║" for l in lines)
    bot = "╚" + "═" * (w + 2) + "╝"
    return f"`{top}\n{hdr}\n{sep}\n{body}\n{bot}`"

def _resolve_path(raw: str) -> Path | None:
    p = Path(raw).resolve()
    for allowed in ALLOWED_PATHS:
        try:
            p.relative_to(allowed)
            return p
        except ValueError:
            pass
    return None

async def cmd_ls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    target = args[0] if args else "."
    p = _resolve_path(target)
    if not p:
        await update.message.reply_text("❌ Ruta no permitida. Usa /allowedpaths para ver rutas accesibles.")
        return
    if not p.exists():
        await update.message.reply_text("❌ Ruta no existe.")
        return
    if p.is_file():
        await update.message.reply_text(f"📄 Es un archivo: `{p}`", parse_mode="Markdown")
        return

    try:
        entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        lines = []
        for e in entries[:50]:
            icon = "📁" if e.is_dir() else "📄"
            size = e.stat().st_size if e.is_file() else 0
            size_str = f" ({_fmt_size(size)})" if size else ""
            lines.append(f"{icon} `{e.name}`{size_str}")
        if len(entries) > 50:
            lines.append(f"... y {len(entries) - 50} más")
        await update.message.reply_text(
            _box("\n".join(lines) or "(vacío)", f"📁 {p.name}"),
            parse_mode="Markdown"
        )
    except PermissionError:
        await update.message.reply_text("❌ Permiso denegado.")

async def cmd_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Uso: /cat <ruta>")
        return
    p = _resolve_path(args[0])
    if not p or not p.is_file():
        await update.message.reply_text("❌ Archivo no encontrado o no permitido.")
        return
    try:
        text = p.read_text(encoding="utf-8", errors="replace")[:2000]
        await update.message.reply_text(f"```\n{text}\n```", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

async def cmd_tail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Uso: /tail <ruta> [N]")
        return
    n = 20
    if len(args) > 1:
        try:
            n = max(1, min(100, int(args[1])))
        except ValueError:
            pass
    p = _resolve_path(args[0])
    if not p or not p.is_file():
        await update.message.reply_text("❌ Archivo no encontrado o no permitido.")
        return
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").split("\n")
        tail = lines[-n:]
        text = "\n".join(tail)
        await update.message.reply_text(f"```\n{text}\n```", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

async def cmd_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Uso: /download <ruta>")
        return
    p = _resolve_path(args[0])
    if not p or not p.is_file():
        await update.message.reply_text("❌ Archivo no encontrado o no permitido.")
        return
    size = p.stat().st_size
    if size > MAX_FILE_SIZE:
        await update.message.reply_text(f"❌ Archivo demasiado grande ({_fmt_size(size)}). Máximo: {_fmt_size(MAX_FILE_SIZE)}")
        return
    try:
        doc = io.BytesIO(p.read_bytes())
        doc.name = p.name
        await update.message.reply_document(document=doc, filename=p.name)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

async def cmd_allowedpaths(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [str(p) for p in ALLOWED_PATHS]
    await update.message.reply_text(
        _box("\n".join(lines) or "No hay rutas configuradas", "📁 RUTAS PERMITIDAS"),
        parse_mode="Markdown"
    )

def _fmt_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}TB"
