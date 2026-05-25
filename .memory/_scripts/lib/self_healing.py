"""Self-healing graph — deteccion y recuperacion automatica de fallos.

Decision Estrategica (Principio 6):
  Sistema que se recupera solo de fallos. Circuit breakers por agente,
  reconexion automatica, backoff exponencial. Alerta si persiste >3 fallos.

Mecanismo:
  - CircuitBreaker por agente: closed (ok) → open (fallando) → half-open (probando)
  - Reconexion con backoff: 1s, 2s, 4s, 8s, max 30s
  - Reset automatico tras periodo de exito
  - Log de todos los eventos para debugging
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("self_healing")

SIGNALS_DIR = Path(__file__).resolve().parent.parent.parent / ".memory" / "bridge" / "signals"
HEALING_LOG = SIGNALS_DIR / "healing-events.json"

MAX_FAILURES = 3
RESET_TIMEOUT = 60
BACKOFF_BASE = 1


class CircuitBreaker:
    def __init__(self, name: str):
        self.name = name
        self.state = "closed"  # closed, open, half-open
        self.failures = 0
        self.last_failure = 0
        self.last_success = 0
        self.backoff = BACKOFF_BASE

    def record_success(self):
        self.failures = 0
        self.state = "closed"
        self.last_success = time.time()
        self.backoff = BACKOFF_BASE

    def record_failure(self) -> bool:
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= MAX_FAILURES:
            self.state = "open"
            _log_event(self.name, f"circuit OPEN after {self.failures} failures")
            return True  # signal escalation
        self.state = "half-open"
        return False

    def _next_retry(self) -> float:
        return self.last_failure + min(self.backoff, 30)
        self.backoff = min(self.backoff * 2, 30)

    def can_try(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() >= self._next_retry():
                self.state = "half-open"
                _log_event(self.name, "circuit HALF-OPEN (attempting recovery)")
                return True
            return False
        return True  # half-open: allow single attempt

    def status(self) -> dict:
        return {
            "name": self.name,
            "state": self.state,
            "failures": self.failures,
            "last_failure": datetime.fromtimestamp(self.last_failure).isoformat()
                if self.last_failure else None,
            "backoff_seconds": self.backoff,
        }


class SelfHealingGraph:
    def __init__(self):
        self.circuits: dict[str, CircuitBreaker] = {}

    def get(self, name: str) -> CircuitBreaker:
        if name not in self.circuits:
            self.circuits[name] = CircuitBreaker(name)
        return self.circuits[name]

    def record_success(self, name: str):
        self.get(name).record_success()
        _log_event(name, f"circuit CLOSED (recovered)")

    def record_failure(self, name: str) -> bool:
        breaker = self.get(name)
        escalated = breaker.record_failure()
        if escalated:
            _log_event(name, f"ESCALATED after {breaker.failures} failures")
        return escalated

    def status_all(self) -> dict[str, dict]:
        return {n: c.status() for n, c in self.circuits.items()}

    def escalate(self, agent: str, error: str):
        """Escala un fallo: guarda senal para revision humana."""
        SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
        signal = {
            "type": "healing_escalation",
            "agent": agent,
            "error": str(error)[:200],
            "timestamp": datetime.now().isoformat(),
        }
        path = SIGNALS_DIR / f"healing-escalation-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        path.write_text(json.dumps(signal, indent=2))
        logger.warning(f"[HEALING] Escalated {agent}: {str(error)[:100]}")


def _log_event(agent: str, event: str):
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "agent": agent,
        "event": event,
        "timestamp": datetime.now().isoformat(),
    }
    if HEALING_LOG.exists():
        try:
            data = json.loads(HEALING_LOG.read_text(encoding="utf-8"))
        except Exception:
            data = {"events": []}
    else:
        data = {"events": []}

    data["events"].append(entry)
    data["events"] = data["events"][-1000:]
    HEALING_LOG.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info(f"[HEALING] {agent}: {event}")


healer = SelfHealingGraph()
