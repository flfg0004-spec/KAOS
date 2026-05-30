"""Kanban Dispatcher — conecta Hermes Kanban con LangGraph Orchestrator.

Flujo:
  1. Poll `kanban list --json` → filtrar tickets "ready"
  2. Claim atómico (status → "running")
  3. Invoke LangGraph orchestrator con ticket como input
  4. Reportar progreso via kanban_comment
  5. Completar ticket al finalizar

Fallback local: si Hermes no está disponible, usa cola local JSON.
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

_LOG = logging.getLogger(__name__)

HERMES_BIN = "hermes"
POLL_INTERVAL = 30
CLAIM_TIMEOUT = 300
FALLBACK_FILE = Path(__file__).resolve().parent.parent.parent / ".memory" / "cache" / "kanban_queue.json"


def _hermes(*args: str, timeout: int = 15, title: str = "") -> tuple[bool, str]:
    try:
        cmd = [HERMES_BIN, *args]
        if title:
            cmd.append(title)
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout.strip()
    except Exception as e:
        return False, str(e)


def _hermes_available() -> bool:
    try:
        r = subprocess.run([HERMES_BIN, "--version"], capture_output=True, text=True, timeout=3)
        return r.returncode == 0
    except Exception:
        return False


# ── Fallback local queue ──────────────────────────────────────


def _read_fallback() -> list[dict]:
    if FALLBACK_FILE.exists():
        try:
            return json.loads(FALLBACK_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _write_fallback(tickets: list[dict]):
    FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    FALLBACK_FILE.write_text(json.dumps(tickets, indent=2, ensure_ascii=False), encoding="utf-8")


def list_ready(limit: int = 5) -> list[dict]:
    if _hermes_available():
        ok, out = _hermes("kanban", "list", "--json")
        if ok and out:
            try:
                data = json.loads(out)
                tasks = data if isinstance(data, list) else data.get("tasks", data)
                return [t for t in (tasks or []) if t.get("status") == "ready"][:limit]
            except (json.JSONDecodeError, TypeError):
                pass
    tickets = _read_fallback()
    return [t for t in tickets if t.get("status") == "ready"][:limit]


def claim(ticket_id: str) -> bool:
    if _hermes_available():
        ok, _ = _hermes("kanban", "claim", ticket_id)
        if ok:
            return True
    tickets = _read_fallback()
    for t in tickets:
        if t.get("id") == ticket_id:
            t["status"] = "running"
            _write_fallback(tickets)
            return True
    return False


def comment(ticket_id: str, message: str) -> bool:
    if _hermes_available():
        ok, _ = _hermes("kanban", "comment", ticket_id, message)
        return ok
    tickets = _read_fallback()
    for t in tickets:
        if t.get("id") == ticket_id:
            t.setdefault("comments", []).append({"msg": message, "ts": datetime.now().isoformat()})
            _write_fallback(tickets)
            return True
    return False


def complete(ticket_id: str) -> bool:
    if _hermes_available():
        ok, _ = _hermes("kanban", "complete", ticket_id)
        if ok:
            return True
    tickets = _read_fallback()
    tickets = [t for t in tickets if t.get("id") != ticket_id]
    _write_fallback(tickets)
    return True


def create(title: str, body: str = "", tag: str = "") -> Optional[str]:
    ticket_id = f"local_{int(time.time())}_{len(title) % 1000}"
    if _hermes_available():
        args = ["kanban", "create", "--json"]
        if body:
            args.extend(["--body", body])
        ok, out = _hermes(*args, title=title)
        if ok and out:
            try:
                return json.loads(out).get("id")
            except json.JSONDecodeError:
                pass
    tickets = _read_fallback()
    new_ticket = {
        "id": ticket_id,
        "title": title,
        "body": body,
        "tag": tag,
        "status": "ready",
        "created_at": datetime.now().isoformat(),
        "comments": [],
    }
    tickets.append(new_ticket)
    _write_fallback(tickets)
    return ticket_id


def dispatch_ticket(ticket: dict) -> bool:
    tid = ticket.get("id", "")
    title = ticket.get("title", "")
    body = ticket.get("body", "")

    if not claim(tid):
        _LOG.warning("Failed to claim ticket %s", tid)
        return False

    comment(tid, "🔄 Ticket reclamado por orquestador KAOS")

    try:
        from lib.orchestrator import build_graph

        state = {
            "topic": body or title,
            "ticket_id": tid,
            "profile": "standard",
        }

        graph = build_graph()
        result = graph.invoke(state)

        score = result.get("critic_score", result.get("evaluation_score", 0))
        comment(tid, f"✅ Pipeline completado\n📊 Score: {score}/100")
        complete(tid)

        from lib.hermes_router import notify_pipeline
        notify_pipeline(topic=title, score=score, duration_s=0, passed=True)
        return True

    except Exception as e:
        _LOG.error("Ticket %s failed: %s", tid, e)
        comment(tid, f"❌ Error: {str(e)[:200]}")
        return False


async def dispatcher_loop():
    _LOG.info("Kanban dispatcher loop started (poll every %ds)", POLL_INTERVAL)
    while True:
        try:
            tickets = list_ready()
            for t in tickets:
                _LOG.info("Dispatching ticket %s: %s", t.get("id"), t.get("title", "")[:60])
                dispatch_ticket(t)
        except Exception as e:
            _LOG.error("Dispatcher error: %s", e)
        await asyncio.sleep(POLL_INTERVAL)
