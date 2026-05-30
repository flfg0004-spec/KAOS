"""Alert Daemon — escucha EventBus y registra alertas de pipelines fallidos."""

import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from lib.config import VAULT_ROOT
from lib.events import EventBus

_LOG = logging.getLogger(__name__)
ALERTS_LOG = VAULT_ROOT / "cache" / "alerts.log"


def _write_alert(severity: str, source: str, message: str):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "source": source,
        "message": message,
    }
    ALERTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ALERTS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    _LOG.warning("ALERT [%s] %s: %s", severity, source, message)


def _alert_loop():
    """Background thread: escucha EventBus y escribe alertas."""
    q = EventBus.subscribe()
    _LOG.info("AlertDaemon started, listening for events...")
    while True:
        try:
            event_type, data = q.get(timeout=30)
            if event_type == "pipeline_update":
                state = data.get("state", "")
                pid = data.get("pipeline_id", "?")
                if state == "failed":
                    _write_alert("error", "pipeline", f"Pipeline {pid} failed")
                elif state == "cancelled":
                    _write_alert("warning", "pipeline", f"Pipeline {pid} cancelled")
                elif state == "completed":
                    failed = data.get("failed_nodes", 0)
                    if failed > 0:
                        _write_alert("warning", "pipeline",
                                     f"Pipeline {pid} completed with {failed} failed nodes")
            elif event_type == "alert":
                _write_alert(
                    data.get("severity", "info"),
                    data.get("source", "system"),
                    data.get("message", ""),
                )
        except Exception:
            pass


def start():
    """Inicia el alert daemon en un thread daemon."""
    t = threading.Thread(target=_alert_loop, daemon=True)
    t.start()
    _LOG.info("AlertDaemon thread started")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _LOG.info("AlertDaemon starting (standalone)...")
    start()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        _LOG.info("AlertDaemon stopped")
