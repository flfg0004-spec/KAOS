"""Aether observability — LangFuse tracing integration with fallback.

- Habilitado por defecto (ETHER_LANGFUSE_ENABLED=true)
- Acceptance sampling configurable por tier
- Trace enrichment (prompt_size, cache_hit_ratio, resolved_by, tier, agent)
- Fallback logging a JSONL cuando LangFuse no disponible
- Health check endpoint
- Timer context manager mejorado
"""

import json
import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path

from lib.aether.config import ETHER_LANGFUSE_ENABLED

_LOG = logging.getLogger(__name__)
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "http://127.0.0.1:3000")

_lf = None

# ── Acceptance Sampling ─────────────────────────────────────────
# Fracción de trazas a enviar por tier. Evita sobrecargar LangFuse
# con llamadas baratas o experimentales.
SAMPLE_RATES = {
    "flash": 0.1,  # Solo 10% de las trazas flash
    "pro": 0.5,  # 50% de pro
    "kimi": 0.8,  # 80% de kimi
    "mimo": 0.3,  # 30% de mimo
}

# ── Fallback Path ───────────────────────────────────────────────
_FALLBACK_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / ".memory" / "cache"
_FALLBACK_LOG_PATH = _FALLBACK_DIR / "langfuse-fallback.jsonl"
_FALLBACK_MAX_LINES = 1000

# ── Health tracking ─────────────────────────────────────────────
_trace_counter = 0
_last_successful_trace: str | None = None


def _get_langfuse():
    """Inicializa LangFuse client con graceful degradation."""
    global _lf
    if not ETHER_LANGFUSE_ENABLED:
        return None
    if _lf is not None:
        return _lf
    try:
        from langfuse import Langfuse

        _lf = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
        )
        _LOG.info("LangFuse tracing enabled — host=%s", LANGFUSE_HOST)
        return _lf
    except ImportError:
        _LOG.debug("langfuse not installed — tracing disabled")
        return None
    except Exception as e:
        _LOG.debug("langfuse init failed: %s — tracing disabled", e)
        return None


def _log_fallback(trace_data: dict):
    """Persiste un trace en el archivo fallback JSONL.

    Cuando LangFuse no está disponible, los traces se guardan como
    JSON Lines en ``.memory/cache/langfuse-fallback.jsonl``.

    El archivo se rota automáticamente al superar ``_FALLBACK_MAX_LINES``
    líneas: se renombra a ``.bak`` y se empieza uno nuevo.

    Args:
        trace_data: Dict con datos del trace a persistir.
    """
    try:
        _FALLBACK_DIR.mkdir(parents=True, exist_ok=True)

        # Rotar si excede el límite
        if _FALLBACK_LOG_PATH.exists():
            lines = _FALLBACK_LOG_PATH.read_text(encoding="utf-8").strip().split("\n")
            if len([l for l in lines if l]) >= _FALLBACK_MAX_LINES:
                bak = _FALLBACK_LOG_PATH.with_suffix(".jsonl.bak")
                _FALLBACK_LOG_PATH.replace(bak)
                _LOG.debug("Fallback log rotated → %s", bak.name)

        with open(_FALLBACK_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace_data, ensure_ascii=False, default=str) + "\n")
    except Exception as e:
        _LOG.debug("Fallback log write failed: %s", e)


def _should_sample(model: str, tier: str | None = None) -> bool:
    """Determina si un trace debe ser muestreado según acceptance sampling.

    Usa random para la decisión de muestreo probabilístico.

    Args:
        model: Nombre del modelo (ej. "go-flash").
        tier: Tier explícito. Si es None, se infiere del modelo.

    Returns:
        True si el trace debe ser registrado.
    """
    import random

    if tier is None:
        if "mimo" in model:
            tier = "mimo"
        elif "kimi" in model:
            tier = "kimi"
        elif model in ("go-pro",):
            tier = "pro"
        else:
            tier = "flash"

    rate = SAMPLE_RATES.get(tier, 0.1)
    return random.random() < rate


def observe(
    func_name,
    model,
    agent,
    task_type,
    prompt_size,
    latency_ms,
    success,
    error=None,
    prompt_tokens=0,
    completion_tokens=0,
    quality_score=None,
    # Nuevos campos de enriquecimiento
    cache_hit_ratio=None,
    resolved_by=None,
    tier=None,
):
    """Registra trace en LangFuse si está habilitado.

    Incluye acceptance sampling configurable por tier y enriquecimiento
    de trazas con metadata de routing y calidad. Si LangFuse no está
    disponible, los traces se persisten localmente via ``_log_fallback``.

    Args:
        func_name: Nombre de la función.
        model: Modelo usado.
        agent: Agente (nunca vacío — se fuerza a "unknown" si es necesario).
        task_type: Tipo de tarea.
        prompt_size: Tamaño del prompt en tokens.
        latency_ms: Latencia en milisegundos.
        success: Si la llamada fue exitosa.
        error: Mensaje de error (si falló).
        prompt_tokens: Tokens de prompt.
        completion_tokens: Tokens de completion.
        quality_score: Score de calidad (opcional).
        cache_hit_ratio: Ratio de cache hit (0.0-1.0, opcional).
        resolved_by: Cómo se resolvió el routing (opcional).
        tier: Tier del modelo (flash/pro/kimi/mimo, opcional).

    Returns:
        trace_id (str) o None.
    """
    global _trace_counter, _last_successful_trace

    # Asegurar que agent nunca está vacío
    agent = agent or "unknown"

    # Inferir tier si no se proporcionó
    if tier is None:
        if "mimo" in model:
            tier = "mimo"
        elif "kimi" in model:
            tier = "kimi"
        elif model in ("go-pro",):
            tier = "pro"
        else:
            tier = "flash"

    # Construir payload completo del trace
    trace_data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "func_name": func_name,
        "model": model,
        "tier": tier,
        "agent": agent,
        "task_type": task_type,
        "prompt_size": prompt_size,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "latency_ms": round(latency_ms, 2),
        "success": success,
        "error": error,
        "quality_score": quality_score,
        "cache_hit_ratio": cache_hit_ratio,
        "resolved_by": resolved_by or "",
        "version": "aether",
    }

    # Intentar enviar a LangFuse
    lf = _get_langfuse()
    if lf is None:
        # Fallback: persistir localmente (sin sampling — todo se guarda)
        _log_fallback(trace_data)
        return None

    # Acceptance sampling (solo cuando LangFuse está disponible)
    if not _should_sample(model, tier):
        return None

    try:
        trace = lf.trace(
            name=func_name,
            input={
                "agent": agent,
                "task_type": task_type,
                "prompt_size": prompt_size,
                "resolved_by": resolved_by or "",
                "tier": tier,
            },
            metadata={
                "model": model,
                "success": success,
                "quality_score": quality_score,
                "cache_hit_ratio": cache_hit_ratio,
                "version": "aether",
            },
            output=({"error": error, "quality_score": quality_score} if error else {"quality_score": quality_score}),
        )
        trace.generation(
            name=f"llm_{model}",
            model=model,
            usage={
                "input": prompt_tokens,
                "output": completion_tokens,
                "total": prompt_tokens + completion_tokens,
            },
            latency=latency_ms / 1000.0,
        )
        _trace_counter += 1
        _last_successful_trace = trace_data["timestamp"]
        return trace.id
    except Exception as e:
        _LOG.debug("langfuse trace failed: %s — falling back to JSONL", e)
        _log_fallback(trace_data)
        return None


def _get_fallback_log_size() -> int:
    """Número de líneas en el archivo de fallback."""
    try:
        if _FALLBACK_LOG_PATH.exists():
            text = _FALLBACK_LOG_PATH.read_text(encoding="utf-8")
            return len([l for l in text.strip().split("\n") if l])
    except Exception:
        pass
    return 0


def _get_trace_count_last_hour() -> int:
    """Número de trazas exitosas en la última hora.

    Para un conteo preciso se leería el archivo de fallback;
    aquí usamos el contador en memoria (se resetea al reiniciar).
    """
    return _trace_counter


def health_check() -> dict:
    """Reporta el estado del sistema de observabilidad.

    Returns:
        dict con:
        - langfuse_available: bool
        - langfuse_host: str
        - fallback_log_size: int (líneas en el archivo fallback)
        - last_successful_trace: str | None (timestamp ISO)
        - traces_last_hour: int
    """
    lf = _get_langfuse()
    return {
        "langfuse_available": lf is not None,
        "langfuse_host": LANGFUSE_HOST,
        "fallback_log_size": _get_fallback_log_size(),
        "last_successful_trace": _last_successful_trace,
        "traces_last_hour": _get_trace_count_last_hour(),
    }


class Timer:
    """Context manager para medir latencia de llamadas LLM.

    Uso:
        with Timer() as timer:
            result = llm_call(...)
        print(f"Latency: {timer.elapsed_ms:.0f}ms")
    """

    def __enter__(self):
        self.start = time.time()
        self.elapsed_ms = 0.0
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.time() - self.start) * 1000
