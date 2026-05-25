"""Telegram bot configuration."""
import os
from pathlib import Path

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1487561068")
ALLOWED_CHATS = {int(CHAT_ID)} if CHAT_ID else set()

RATE_LIMIT_PER_USER = 10
RATE_LIMIT_DAILY = 100
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
PROCESS_TIMEOUT = 300

# Power management
POWER_CONFIRM_TIMEOUT = 60

# File browser
ALLOWED_PATHS_ENV = os.environ.get("TELEGRAM_ALLOWED_PATHS", "")
ALLOWED_PATHS = [
    Path(p.strip())
    for p in ALLOWED_PATHS_ENV.split(";")
    if p.strip()
] if ALLOWED_PATHS_ENV else [
    Path.home() / "Documents" / "KAOS",
    Path.home() / "Documents",
]
ALLOWED_PATHS = [p.resolve() for p in ALLOWED_PATHS if p.exists()]

# System monitor
MONITOR_INTERVAL = int(os.environ.get("TELEGRAM_MONITOR_INTERVAL", "300"))
ALERT_COOLDOWN = int(os.environ.get("TELEGRAM_ALERT_COOLDOWN", "600"))

# Hermes
HERMES_BIN = os.environ.get("HERMES_BIN", "hermes")
HERMES_KANBAN_POLL_INTERVAL = int(os.environ.get("HERMES_KANBAN_POLL", "30"))
HERMES_ENABLED = os.environ.get("HERMES_ENABLED", "true").lower() == "true"
HERMES_CHANNEL = os.environ.get("HERMES_CHANNEL", "kaos-ci")

# Hermes outbox
HERMES_OUTBOX_ENABLED = os.environ.get("HERMES_OUTBOX_ENABLED", "true").lower() == "true"
