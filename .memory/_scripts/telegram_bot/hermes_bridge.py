"""Puente bidireccional entre Telegram Bot y Hermes Kanban.

Direcciones:
  Telegram -> Hermes: mensajes entrantes -> tickets kanban
  Hermes -> Telegram: tickets outbox -> mensajes Telegram
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

_LOG = logging.getLogger(__name__)

HERMES_BIN = "hermes"
KANBAN_POLL_INTERVAL = 30
OUTBOX_TAG = "telegram-outbox"

HERMES_AVAILABLE: Optional[bool] = None

def _hermes_available() -> bool:
    global HERMES_AVAILABLE
    if HERMES_AVAILABLE is not None:
        return HERMES_AVAILABLE
    try:
        r = subprocess.run([HERMES_BIN, "--version"], capture_output=True, text=True, timeout=5)
        HERMES_AVAILABLE = r.returncode == 0
    except Exception:
        HERMES_AVAILABLE = False
    return HERMES_AVAILABLE

def _hermes_run(*args: str) -> tuple[bool, str]:
    env = {**__import__("os").environ}
    try:
        r = subprocess.run([HERMES_BIN, *args], capture_output=True, text=True, timeout=15, env=env)
        return r.returncode == 0, r.stdout.strip()
    except Exception as e:
        return False, str(e)

def ticket_create(title: str, tag: str = "telegram") -> Optional[str]:
    if not _hermes_available():
        return None
    ok, out = _hermes_run("kanban", "create", "--json", title)
    if ok and out:
        try:
            data = json.loads(out)
            tid = data.get("id")
            if tid:
                _LOG.info("Hermes ticket created: %s (%s)", tid, title[:60])
                return tid
        except json.JSONDecodeError:
            pass
    _LOG.warning("Hermes ticket creation failed: %s", out[:200])
    return None

def ticket_comment(ticket_id: str, message: str) -> bool:
    if not _hermes_available():
        return False
    ok, _ = _hermes_run("kanban", "comment", ticket_id, message)
    return ok

def outbox_poll(limit: int = 5) -> list[dict]:
    if not _hermes_available():
        return []
    ok, out = _hermes_run("kanban", "list", "--json")
    if not ok or not out:
        return []
    try:
        tasks = json.loads(out)
        if isinstance(tasks, dict):
            tasks = tasks.get("tasks", tasks)
        ready = [t for t in (tasks or []) if t.get("status") == "ready"]
        return [{"id": t["id"], "title": t.get("title", ""), "message": t.get("body", "")} for t in ready[:limit]]
    except json.JSONDecodeError:
        return []

def outbox_complete(ticket_id: str) -> bool:
    if not _hermes_available():
        return False
    ok, _ = _hermes_run("kanban", "complete", ticket_id)
    return ok

def gateway_send(message: str) -> bool:
    from lib.hermes_router import send as _router_send
    return _router_send(message, channel="telegram")

def format_ticket(title: str, sender: str = "", content: str = "") -> str:
    msg = f"📋 **{title}**"
    if sender:
        msg += f"\n👤 {sender}"
    if content:
        msg += f"\n\n{content[:300]}"
    return msg

async def outbox_loop(app, chat_id: int):
    if not _hermes_available():
        _LOG.info("Hermes not available — outbox loop disabled")
        return
    _LOG.info("Hermes outbox loop started (poll every %ds)", KANBAN_POLL_INTERVAL)
    while True:
        try:
            tickets = outbox_poll()
            for t in tickets:
                asyncio.create_task(_send_outbox_ticket(app, t, chat_id))
        except Exception as e:
            _LOG.error("Outbox poll error: %s", e)
        await asyncio.sleep(KANBAN_POLL_INTERVAL)

async def _send_outbox_ticket(app, ticket: dict, chat_id: int):
    try:
        msg = format_ticket(ticket.get("title", "Hermes message"),
                           content=ticket.get("message", ""))
        await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        outbox_complete(ticket["id"])
        _LOG.info("Outbox ticket %s sent to Telegram", ticket["id"])
    except Exception as e:
        _LOG.error("Failed to send outbox ticket %s: %s", ticket.get("id"), e)
