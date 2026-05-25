"""Telegram Bridge — bot para consultar KAOS via Telegram.

Usa python-telegram-bot para recibir comandos y delegar a DeerFlowBridge.

Comandos:
  /investigate <tema> — invoca Aletheia
  /quality — muestra score de calidad actual
  /status — estado del sistema
  /search <query> — busca en el vault

Auto-deteccion: si python-telegram-bot no esta instalado, opera en modo mock.
"""

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger("telegram_bridge")

TELEGRAM_AVAILABLE = False
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


def _check_telegram() -> bool:
    global TELEGRAM_AVAILABLE
    if TELEGRAM_AVAILABLE:
        return True
    try:
        import telegram
        import telegram.ext
        TELEGRAM_AVAILABLE = True
        return True
    except ImportError:
        logger.warning("python-telegram-bot not installed")
        return False


class TelegramBridge:
    def __init__(self, token: str = ""):
        self.token = token or TELEGRAM_BOT_TOKEN
        self.app = None
        self.available = _check_telegram() and bool(self.token)

    async def _investigate(self, update, context):
        topic = " ".join(context.args) if context.args else "analisis general"
        try:
            from lib.deerflow_bridge import bridge as df_bridge
            import asyncio
            result = await df_bridge.execute({
                "type": "reasoning",
                "prompt": f"Investiga: {topic}",
                "id": f"tg-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            })
            output = result.get("output", result.get("stdout", str(result)))[:1500]
        except Exception as e:
            output = f"Error: {e}"
        await update.message.reply_text(f"*Investigacion: {topic}*\n\n{output}", parse_mode="Markdown")

    async def _quality(self, update, context):
        try:
            from lib.quality import calculate
            q = calculate()
            score = q.get("score", q.get("composite", "?"))
            await update.message.reply_text(f"Score de calidad: {score}/100")
        except Exception as e:
            await update.message.reply_text(f"Error obteniendo calidad: {e}")

    async def _status(self, update, context):
        try:
            from lib.deerflow_bridge import bridge as df_bridge
            s = df_bridge.status()
            status_lines = [
                f"DeerFlowBridge: {'real' if not s['mock_mode'] else 'mock'}",
                f"Sandbox URL: {s.get('sandbox_url', 'N/A')}",
            ]
            await update.message.reply_text("\n".join(status_lines))
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

    async def _search(self, update, context):
        query = " ".join(context.args) if context.args else "index"
        try:
            from lib.agno_gateway import _vault_search
            result = _vault_search(query)
            await update.message.reply_text(f"Resultados para '{query}':\n{result[:1500]}")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

    def start(self):
        if not self.available:
            logger.info("[MOCK] TelegramBridge — set TELEGRAM_BOT_TOKEN to activate")
            return {"status": "mock", "message": "TelegramBridge en modo mock. Configurar TELEGRAM_BOT_TOKEN"}

        from telegram.ext import Application, CommandHandler

        app = Application.builder().token(self.token).build()

        app.add_handler(CommandHandler("investigate", self._investigate))
        app.add_handler(CommandHandler("quality", self._quality))
        app.add_handler(CommandHandler("status", self._status))
        app.add_handler(CommandHandler("search", self._search))
        app.add_handler(CommandHandler("start", self._status))

        self.app = app
        logger.info("TelegramBridge starting polling...")
        app.run_polling()
        return {"status": "running"}

    def stop(self):
        if self.app:
            self.app.stop()

    def status(self) -> dict:
        return {
            "available": self.available,
            "token_set": bool(self.token),
            "running": self.app is not None,
        }


bridge = TelegramBridge()
