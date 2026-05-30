# ─── Webhook Adapter — KAOS ───────────────────────────────────────────
# Servidor HTTP mínimo que recibe POST en :8643/webhook
# Convierte el body del POST en un ticket kanban
# Responde 200 OK con el ticket ID
# Loggea cada request
# ──────────────────────────────────────────────────────────────────────
#
# Uso:
#   python webhook_adapter.py
#   curl -X POST http://localhost:8643/webhook \
#     -H "Content-Type: application/json" \
#     -d '{"title": "Bug crítico", "description": "Error en login"}'
#
# ──────────────────────────────────────────────────────────────────────

import json
import os
import sys
import uuid
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

# ─── Config ──────────────────────────────────────────────────────────
HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
PORT = int(os.getenv("WEBHOOK_PORT", "8643"))
KANBAN_FILE = os.getenv(
    "KANBAN_FILE",
    os.path.join(os.path.dirname(__file__), "..", "kanban", "tickets.json"),
)

# ─── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), "..", "cache", "webhook.log"),
            mode="a",
        ),
    ],
)
logger = logging.getLogger("webhook")


# ─── Ticket Generator ────────────────────────────────────────────────
def generate_ticket(payload: dict) -> dict:
    """Convierte un payload POST en un ticket kanban."""
    ticket = {
        "id": str(uuid.uuid4())[:8],
        "title": payload.get("title", "Untitled"),
        "description": payload.get("description", payload.get("body", "")),
        "status": "backlog",
        "priority": payload.get("priority", "medium"),
        "source": "webhook",
        "labels": payload.get("labels", []),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "assignee": payload.get("assignee", None),
    }

    # Normalizar prioridad
    valid_priorities = {"low", "medium", "high", "critical"}
    if ticket["priority"] not in valid_priorities:
        ticket["priority"] = "medium"

    return ticket


def save_ticket(ticket: dict) -> str:
    """Persiste el ticket en el archivo kanban."""
    tickets = []
    kanban_dir = os.path.dirname(KANBAN_FILE)
    if kanban_dir and not os.path.exists(kanban_dir):
        os.makedirs(kanban_dir, exist_ok=True)

    if os.path.exists(KANBAN_FILE):
        try:
            with open(KANBAN_FILE, "r", encoding="utf-8") as f:
                tickets = json.load(f)
        except (json.JSONDecodeError, Exception):
            tickets = []

    tickets.append(ticket)
    with open(KANBAN_FILE, "w", encoding="utf-8") as f:
        json.dump(tickets, f, indent=2, ensure_ascii=False)

    return ticket["id"]


# ─── HTTP Handler ────────────────────────────────────────────────────
class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            payload = {"body": raw_body.decode("utf-8", errors="ignore")}

        # ─── Generate ticket ─────────────────────────────────────────
        try:
            ticket = generate_ticket(payload)
            ticket_id = save_ticket(ticket)

            logger.info(
                f"POST /webhook -> ticket {ticket_id} | "
                f"title={ticket['title']!r} | "
                f"priority={ticket['priority']} | "
                f"size={content_length}b"
            )

            response = {
                "status": "ok",
                "ticket_id": ticket_id,
                "ticket": ticket,
            }
            self._respond(200, response)

        except Exception as e:
            logger.error(f"Failed to create ticket: {e}")
            self._respond(500, {"status": "error", "error": str(e)})

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {
                "status": "ok",
                "service": "webhook-adapter",
                "port": PORT,
            })
        else:
            self._respond(404, {"status": "error", "error": "not found"})

    def _respond(self, status_code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        logger.info(f"{self.client_address[0]} - {format % args}")


# ─── Main ────────────────────────────────────────────────────────────
def main():
    server = HTTPServer((HOST, PORT), WebhookHandler)
    logger.info(f"Webhook adapter listening on http://{HOST}:{PORT}/webhook")
    logger.info(f"Tickets will be saved to {KANBAN_FILE}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down webhook adapter...")
        server.shutdown()


if __name__ == "__main__":
    main()
