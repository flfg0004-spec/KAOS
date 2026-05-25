"""Telegram bot configuration."""
import os
from pathlib import Path

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1487561068")
ALLOWED_CHATS = {int(CHAT_ID)} if CHAT_ID else set()

RATE_LIMIT_PER_USER = 10  # max messages per minute
RATE_LIMIT_DAILY = 100    # max messages per day per user
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
PROCESS_TIMEOUT = 300     # 5 min max per item
