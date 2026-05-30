"""CircuitBreaker unificado — per-model + per-provider con persistencia."""

import json
import logging
import os
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

from lib.aether.config import (
    ETHER_CIRCUIT_BREAKER_ENABLED,
    ETHER_CIRCUIT_RESET_TIMEOUT,
    ETHER_FAILURE_THRESHOLD,
    ETHER_HALF_OPEN_MAX,
)

_LOG = logging.getLogger(__name__)

MODEL_CB_CONFIG = {
    "go-flash": {"failure_threshold": 3, "reset_timeout": 300, "half_open_max": 1},
    "go-pro": {"failure_threshold": 3, "reset_timeout": 300, "half_open_max": 1},
    "go-kimi-latest": {"failure_threshold": 2, "reset_timeout": 600, "half_open_max": 1},
    "go-mimo": {"failure_threshold": 2, "reset_timeout": 300, "half_open_max": 1},
    "go-qwen": {"failure_threshold": 3, "reset_timeout": 300, "half_open_max": 1},
    "mimo-direct": {"failure_threshold": 2, "reset_timeout": 300, "half_open_max": 1},
}

CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / ".memory" / "cache"
_KAOS_TESTING = os.environ.get("KAOS_TESTING", "").lower() in ("1", "true")


def _match_model_config(model_name: str) -> dict | None:
    if model_name in MODEL_CB_CONFIG:
        return MODEL_CB_CONFIG[model_name]
    for prefix, cfg in MODEL_CB_CONFIG.items():
        if isinstance(prefix, str) and model_name.startswith(prefix):
            return cfg
    return None


def _default_cb_config() -> dict:
    return dict(MODEL_CB_CONFIG.get("go-flash", {"failure_threshold": 3, "reset_timeout": 300, "half_open_max": 1}))


class CircuitBreaker:
    """Circuit breaker per-model con persistencia.

    Estados: closed (normal) -> open (bloqueado) -> half-open (prueba) -> closed.
    Persiste estado en .memory/cache/circuit_breaker_aether.json con atomic writes.
    """

    def __init__(self, model_name="", failure_threshold=None, reset_timeout=None, half_open_max=None):
        self.model_name = model_name
        if model_name:
            cfg = _match_model_config(model_name)
            if cfg is not None:
                self.failure_threshold = cfg["failure_threshold"]
                self.reset_timeout = cfg["reset_timeout"]
                self.half_open_max = cfg["half_open_max"]
            else:
                self.failure_threshold = failure_threshold or ETHER_FAILURE_THRESHOLD
                self.reset_timeout = reset_timeout or ETHER_CIRCUIT_RESET_TIMEOUT
                self.half_open_max = half_open_max or ETHER_HALF_OPEN_MAX
        else:
            self.failure_threshold = failure_threshold or ETHER_FAILURE_THRESHOLD
            self.reset_timeout = reset_timeout or ETHER_CIRCUIT_RESET_TIMEOUT
            self.half_open_max = half_open_max or ETHER_HALF_OPEN_MAX
        self._state = {}
        self._lock = threading.Lock()
        self._persist_path = CACHE_DIR / "circuit_breaker_aether.json"
        self._load()

    def _load(self):
        if not ETHER_CIRCUIT_BREAKER_ENABLED:
            return
        if _KAOS_TESTING:
            self._persist_path = self._persist_path.with_suffix(".test.json")
            return
        if self._persist_path.exists():
            try:
                data = json.loads(self._persist_path.read_text(encoding="utf-8"))
                with self._lock:
                    self._state.update(data.get("state", {}))
            except Exception as e:
                _LOG.warning("CB: failed to load state: %s", e)

    def _save(self):
        if not ETHER_CIRCUIT_BREAKER_ENABLED or _KAOS_TESTING:
            return
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._persist_path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(
                    {
                        "state": self._state,
                        "updated": datetime.now(UTC).isoformat(),
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            tmp.replace(self._persist_path)
        except Exception as e:
            _LOG.warning("CB: failed to save state: %s", e)

    def _ensure(self, key):
        if key not in self._state:
            self._state[key] = {"failures": 0, "last_failure": 0.0, "state": "closed"}

    def _get_config(self, model):
        cfg = _match_model_config(model)
        if cfg is not None:
            return cfg
        return {
            "failure_threshold": self.failure_threshold,
            "reset_timeout": self.reset_timeout,
            "half_open_max": self.half_open_max,
        }

    def is_available(self, model):
        if not ETHER_CIRCUIT_BREAKER_ENABLED:
            return True
        cfg = self._get_config(model)
        with self._lock:
            self._ensure(model)
            s = self._state[model]
            if s["state"] == "closed":
                return True
            if s["state"] == "open":
                if time.time() - s["last_failure"] > cfg["reset_timeout"]:
                    s["state"] = "half-open"
                    s["failures"] = 0
                    self._save()
                    _LOG.info("CB: model=%s transitioned open->half-open", model)
                    return True
                return False
            return s["failures"] < cfg["half_open_max"]

    def record_success(self, model):
        if not ETHER_CIRCUIT_BREAKER_ENABLED:
            return
        with self._lock:
            self._ensure(model)
            before = self._state[model]["state"]
            self._state[model] = {"failures": 0, "last_failure": 0.0, "state": "closed"}
            if before != "closed":
                _LOG.info("CB: model=%s recovered (%s->closed)", model, before)
            self._save()

    def record_failure(self, model):
        if not ETHER_CIRCUIT_BREAKER_ENABLED:
            return
        cfg = self._get_config(model)
        with self._lock:
            self._ensure(model)
            s = self._state[model]
            s["failures"] += 1
            s["last_failure"] = time.time()
            if s["failures"] >= cfg["failure_threshold"]:
                s["state"] = "open"
                _LOG.warning(
                    "CB: OPEN for model=%s after %d failures (threshold=%d)",
                    model,
                    s["failures"],
                    cfg["failure_threshold"],
                )
            self._save()

    def is_open(self, provider_or_model):
        """Per-provider check (compatible con cost_optimizer.CircuitBreaker)."""
        if not ETHER_CIRCUIT_BREAKER_ENABLED:
            return False
        cfg = self._get_config(provider_or_model)
        with self._lock:
            self._ensure(provider_or_model)
            s = self._state[provider_or_model]
            if s["failures"] < cfg["failure_threshold"]:
                return False
            recent = [f for f in [s["last_failure"]] if time.time() - f < cfg["reset_timeout"]]
            return len(recent) >= cfg["failure_threshold"]

    def reset(self):
        """Limpia todo el estado del CB. Util para tests y recovery."""
        with self._lock:
            self._state = {}
            self._save()

    def get_status(self):
        with self._lock:
            return dict(self._state)


_ETHER_CIRCUIT_BREAKER = CircuitBreaker()
