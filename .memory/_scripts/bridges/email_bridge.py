# ─── Email Bridge — KAOS ──────────────────────────────────────────────
# Stub de integración SMTP/IMAP para envío y recepción de correo.
# Configurable vía variables de entorno en ~/.hermes/.env
# ──────────────────────────────────────────────────────────────────────
# Uso:
#   from email_bridge import EmailBridge
#   bridge = EmailBridge()
#   bridge.send_email("user@example.com", "Asunto", "Cuerpo")
#   messages = bridge.poll_inbox()
# ──────────────────────────────────────────────────────────────────────
import os
import json
import logging
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

logger = logging.getLogger("email_bridge")


class EmailBridge:
    """Bridge de correo configurable vía .env.

    Variables de entorno esperadas (en ~/.hermes/.env):
        EMAIL_SMTP_HOST     — servidor SMTP (ej: smtp.gmail.com)
        EMAIL_SMTP_PORT     — puerto SMTP (ej: 587)
        EMAIL_IMAP_HOST     — servidor IMAP (ej: imap.gmail.com)
        EMAIL_IMAP_PORT     — puerto IMAP (ej: 993)
        EMAIL_USER          — usuario/correo
        EMAIL_PASS          — contraseña o app password
        EMAIL_FROM          — dirección From (opcional, default = EMAIL_USER)
    """

    def __init__(self):
        self.smtp_host = os.getenv("EMAIL_SMTP_HOST", "")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.imap_host = os.getenv("EMAIL_IMAP_HOST", "")
        self.imap_port = int(os.getenv("EMAIL_IMAP_PORT", "993"))
        self.user     = os.getenv("EMAIL_USER", "")
        self.password = os.getenv("EMAIL_PASS", "")
        self.from_addr = os.getenv("EMAIL_FROM", self.user)

        self._connected = False

    # ─── SMTP: Send ──────────────────────────────────────────────────
    def send_email(self, to: str, subject: str, body: str,
                   html: Optional[str] = None) -> dict:
        """Envía un correo electrónico vía SMTP.

        Args:
            to:        Dirección de destino.
            subject:   Asunto del correo.
            body:      Cuerpo en texto plano.
            html:      Cuerpo en HTML (opcional).

        Returns:
            dict con {success: bool, message_id: str or None, error: str or None}
        """
        if not self.smtp_host or not self.user:
            logger.warning("SMTP no configurado — define EMAIL_SMTP_HOST y EMAIL_USER en .env")
            return {"success": False, "message_id": None, "error": "SMTP not configured"}

        try:
            msg = MIMEMultipart("alternative")
            msg["From"]    = self.from_addr
            msg["To"]      = to
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))
            if html:
                msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.user, self.password)
                result = server.sendmail(self.from_addr, [to], msg.as_string())

            logger.info(f"Email sent to {to}: {subject}")
            return {"success": True, "message_id": msg["Message-ID"], "error": None}

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return {"success": False, "message_id": None, "error": str(e)}

    # ─── IMAP: Poll ──────────────────────────────────────────────────
    def poll_inbox(self, limit: int = 10, mark_seen: bool = False) -> list[dict]:
        """Lee los últimos correos de la bandeja de entrada vía IMAP.

        Args:
            limit:     Número máximo de mensajes a retornar.
            mark_seen: Si True, marca los mensajes como leídos.

        Returns:
            Lista de dicts con {id, from, subject, date, body_preview}
        """
        if not self.imap_host or not self.user:
            logger.warning("IMAP no configurado — define EMAIL_IMAP_HOST y EMAIL_USER en .env")
            return []

        try:
            with imaplib.IMAP4_SSL(self.imap_host, self.imap_port) as mail:
                mail.login(self.user, self.password)
                mail.select("INBOX")

                status, data = mail.search(None, "ALL")
                if status != "OK":
                    return []

                ids = data[0].split()
                if not ids:
                    return []

                # Últimos N mensajes
                ids = ids[-limit:]

                messages = []
                for mid in ids:
                    status, data = mail.fetch(mid, "(RFC822)")
                    if status != "OK":
                        continue

                    raw_email = data[0][1]
                    parsed = email.message_from_bytes(raw_email)

                    body_preview = ""
                    if parsed.is_multipart():
                        for part in parsed.walk():
                            if part.get_content_type() == "text/plain":
                                body_preview = part.get_payload(decode=True).decode(
                                    "utf-8", errors="ignore"
                                )[:200]
                                break
                    else:
                        body_preview = parsed.get_payload(decode=True).decode(
                            "utf-8", errors="ignore"
                        )[:200]

                    messages.append({
                        "id": mid.decode(),
                        "from": parsed.get("From", ""),
                        "subject": parsed.get("Subject", ""),
                        "date": parsed.get("Date", ""),
                        "body_preview": body_preview,
                    })

                    if mark_seen:
                        mail.store(mid, "+FLAGS", "\\Seen")

                return messages

        except Exception as e:
            logger.error(f"Failed to poll inbox: {e}")
            return []

    # ─── Health ───────────────────────────────────────────────────────
    def check_config(self) -> dict:
        """Verifica qué servicios están configurados."""
        return {
            "smtp_configured": bool(self.smtp_host and self.user),
            "imap_configured": bool(self.imap_host and self.user),
            "user": self.user or "(not set)",
        }


# ─── CLI quick test ──────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bridge = EmailBridge()
    config_status = bridge.check_config()
    print(json.dumps(config_status, indent=2))

    if config_status["smtp_configured"]:
        print("SMTP configurado — puedes llamar send_email()")
    if config_status["imap_configured"]:
        print("IMAP configurado — puedes llamar poll_inbox()")
    if not config_status["smtp_configured"] and not config_status["imap_configured"]:
        print("⚠ Email no configurado. Define EMAIL_* en ~/.hermes/.env para activar.")
