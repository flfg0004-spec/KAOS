"""kosmos_log.py — Logging estructurado JSON para KosmosV2 (S2 endurecimiento).

Proporciona:
- log_json(): logging estructurado con timestamp, logger, level, event, context
- get_json_logger(): acceso a logger por nombre
- ExecutionSpan (re-exportado para conveniencia): context manager para tracing
"""

import json
import logging
import threading
from datetime import datetime
from typing import Any, Dict

_lock = threading.Lock()

def get_json_logger(name: str) -> logging.Logger:
    """Get or create a logger."""
    return logging.getLogger(name)

def log_json(logger: logging.Logger, level: int, event: str, **context: Any) -> None:
    """Log a structured JSON message.

    Args:
        logger: Logger instance.
        level: logging level (logging.INFO, .WARNING, .ERROR).
        event: Event name (e.g. 'node_start', 'pipeline_complete').
        **context: Key-value pairs for structured data.
    """
    try:
        safe_context: Dict[str, Any] = {}
        for k, v in context.items():
            if not isinstance(v, (int, float, bool)):
                safe_context[k] = str(v)[:500]
            else:
                safe_context[k] = v
        record = {
            "timestamp": datetime.now().isoformat(),
            "logger": logger.name,
            "level": logging.getLevelName(level),
            "event": event,
            "context": safe_context,
        }
        with _lock:
            logger.log(level, json.dumps(record, ensure_ascii=False))
    except Exception:
        logger.log(level, "[json_log_fallback] %s: %s", event, str(context.get("detail", ""))[:200])
