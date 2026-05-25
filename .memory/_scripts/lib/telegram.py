"""Telegram notifications — DEPRECATED, usa lib/hermes_router.py.

Mantenido como fallback directo a Telegram Bot API.
Las nuevas implementaciones deben importar hermes_router.send().
"""
from lib.hermes_router import send, send_boxed, notify_pipeline, notify_degradation, notify_service_down, notify_report

__all__ = ["send", "send_boxed", "notify_pipeline", "notify_degradation", "notify_service_down", "notify_report"]
