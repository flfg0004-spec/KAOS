"""EventBus — singleton thread-safe pub/sub para el sistema de eventos KAOS.

Uso:
    from lib.events import EventBus, EVENT_TYPES

    EventBus.publish("pipeline_update", {"pipeline_id": "pipe_...", "state": "queued"})
    queue = EventBus.subscribe()
    event_type, data = queue.get()
"""

import logging
import queue
import threading
from typing import Any

_LOG = logging.getLogger(__name__)

# ── Tipos de evento soportados ─────────────────────
EVENT_TYPES = frozenset({
    "pipeline_update",
    "node_update",
    "system_health",
    "alert",
})


class _EventBus:
    """EventBus singleton — thread-safe pub/sub con colas asíncronas."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._queues: list[queue.Queue] = []

    # ── Publish ─────────────────────────────────────────
    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        """Publica un evento a todos los suscriptores.

        Args:
            event_type: Tipo de evento (debe estar en EVENT_TYPES).
            data: Diccionario con datos del evento.
        """
        if event_type not in EVENT_TYPES:
            _LOG.warning("EventBus: unknown event type '%s' (ignored)", event_type)
            return

        dead: list[queue.Queue] = []
        with self._lock:
            for q in self._queues:
                try:
                    q.put_nowait((event_type, data))
                except Exception:
                    dead.append(q)
            for q in dead:
                if q in self._queues:
                    self._queues.remove(q)

        _LOG.debug("EventBus: published %s — %s", event_type, data)

    # ── Subscribe ───────────────────────────────────────
    def subscribe(self) -> queue.Queue:
        """Crea una nueva cola de suscripción.

        Returns:
            queue.Queue que recibe tuplas (event_type: str, data: dict).
            El consumidor debe llamar a q.get() (bloqueante).
        """
        q: queue.Queue = queue.Queue()
        with self._lock:
            self._queues.append(q)
        return q

    # ── Unsubscribe ─────────────────────────────────────
    def unsubscribe(self, q: queue.Queue) -> None:
        """Elimina una cola de suscriptores."""
        with self._lock:
            if q in self._queues:
                self._queues.remove(q)

    # ── Stats ────────────────────────────────────────────
    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._queues)


# ── Singleton ──────────────────────────────────────
EventBus = _EventBus()
