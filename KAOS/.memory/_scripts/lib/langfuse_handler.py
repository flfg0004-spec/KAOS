"""Langfuse tracing handler — extracted to avoid circular imports."""

import logging
import os

logger = logging.getLogger(__name__)

LANGFUSE_ENABLED = os.environ.get("LANGFUSE_PUBLIC_KEY", "") and os.environ.get("LANGFUSE_SECRET_KEY", "")
_LANGFUSE_HANDLER = None

if LANGFUSE_ENABLED:
    try:
        from langfuse.callback import CallbackHandler

        _LANGFUSE_HANDLER = CallbackHandler(
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            host=os.environ.get("LANGFUSE_HOST", "http://localhost:3000"),
        )
        logger.info("Langfuse tracing enabled")
    except Exception as e:
        logger.warning("Langfuse init failed: %s", e)


def get_handler():
    return _LANGFUSE_HANDLER
