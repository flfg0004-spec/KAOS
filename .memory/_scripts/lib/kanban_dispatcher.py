"""Kanban Dispatcher — conecta Hermes Kanban con LangGraph Orchestrator.

Flujo:
  1. Poll `kanban list --json` → filtrar tickets "ready"
  2. Claim atómico (status → "running")
  3. Invoke LangGraph orchestrator con ticket como input
  4. Reportar progreso via kanban_comment
  5. Completar ticket al finalizar
"""

import asyncio
import json
import logging
import subprocess
import time
from typing import Optional

_LOG = logging.getLogger(__name__)

HERMES_BIN = "hermes"
POLL_INTERVAL = 30
CLAIM_TIMEOUT = 300


def _hermes(*args: str, timeout: int = 15) -> tuple[bool, str]:
    try:
        r = subprocess.run([HERMES_BIN, *args], capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout.strip()
    except Exception as e:
        return False, str(e)


def list_ready(limit: int = 5) -> list[dict]:
    ok, out = _hermes("kanban", "list", "--json")
    if not ok or not out:
        return []
    try:
        data = json.loads(out)
        tasks = data if isinstance(data, list) else data.get("tasks", data)
        return [t for t in (tasks or []) if t.get("status") == "ready"][:limit]
    except (json.JSONDecodeError, TypeError):
        return []


def claim(ticket_id: str) -> bool:
    ok, _ = _hermes("kanban", "claim", ticket_id)
    return ok


def comment(ticket_id: str, message: str) -> bool:
    ok, _ = _hermes("kanban", "comment", ticket_id, message)
    return ok


def complete(ticket_id: str) -> bool:
    ok, _ = _hermes("kanban", "complete", ticket_id)
    return ok


def create(title: str, body: str = "", tag: str = "") -> Optional[str]:
    args = ["kanban", "create", "--json"]
    if body:
        args.extend(["--body", body])
    ok, out = _hermes(*args, title=title)
    if ok and out:
        try:
            return json.loads(out).get("id")
        except json.JSONDecodeError:
            pass
    return None


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
            "profile": "desarrollo",
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
