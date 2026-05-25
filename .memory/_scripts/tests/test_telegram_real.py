"""Test: Telegram bridge with real token from .env."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load .env from project root
from pathlib import Path
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def test_telegram_token_exists():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    assert token, "TELEGRAM_BOT_TOKEN not found in .env"
    assert len(token) > 10


def test_telegram_bridge_ready():
    from lib.telegram_bridge import TelegramBridge
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    bridge = TelegramBridge(token=token)
    status = bridge.status()
    assert status["available"] is True
    assert status["token_set"] is True
