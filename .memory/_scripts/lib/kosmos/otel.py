"""kosmos/otel.py — OpenTelemetry integration for KosmosV2 (KosmosV3 B1+B2+K2).

Proporciona ExecutionSpan reemplazado por OTel spans.
Si OpenTelemetry no está instalado, degrada gracefulmente a spans en memoria.

B1: Reemplazar ExecutionSpan con OTel spans (manteniendo compatibilidad)
B2: Export a console + archivo con rotación (7 días)
K2: Export dual OTel (OTLP HTTP + Console) + JSONL, setup_otel_exporter(), get_otel_status()
"""

import json
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Fallback: in-memory spans (same as original ExecutionSpan) ──

_FALLBACK_SPANS: List[Dict[str, Any]] = []
_FALLBACK_LOCK = threading.Lock()

# ── Try OTel import ──

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

    _OTEL_AVAILABLE = True
    _TRACER = trace.get_tracer("kosmosv2", "3.0.0")
except ImportError:
    _OTEL_AVAILABLE = False
    _TRACER = None


def setup_otel_exporter(endpoint: str = "http://localhost:4318/v1/traces",
                        use_console: bool = True) -> bool:
    """Configure OTel span exporter (K2).

    Sets up a TracerProvider with optional ConsoleSpanExporter
    and OTLP HTTP exporter (BatchSpanProcessor).

    Args:
        endpoint: OTLP HTTP endpoint (default ``http://localhost:4318/v1/traces``).
        use_console: Also export to console via ``ConsoleSpanExporter``.

    Returns:
        True if configured successfully, False if OTel not available.
    """
    if not _OTEL_AVAILABLE:
        logger.warning("K2: OpenTelemetry not installed, using fallback export")
        return False

    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor,
    )

    provider = TracerProvider()

    # Always add console exporter as fallback
    if use_console:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    # Add OTLP HTTP exporter if endpoint available
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info("K2: OTLP exporter configured for %s", endpoint)
    except ImportError:
        logger.info("K2: OTLP HTTP exporter not installed, console only")
    except Exception as exc:
        logger.warning("K2: OTLP config failed: %s", exc)

    trace.set_tracer_provider(provider)
    global _TRACER
    _TRACER = trace.get_tracer("kosmosv2", "3.0.0")
    return True


def is_otel_available() -> bool:
    """Check if OpenTelemetry is installed and available."""
    return _OTEL_AVAILABLE


# ── ExecutionSpan ──


class ExecutionSpan:
    """Execution span compatible with both OTel and in-memory fallback.

    Usage (same as before):
        with ExecutionSpan("discover", topic="..."):
            self.discover()

    Si OpenTelemetry está disponible, delega a OTel spans reales.
    Si no, usa la lista ``_FALLBACK_SPANS`` en memoria (misma API
    que el ExecutionSpan original en pipeline.py).
    """

    def __init__(self, name: str, **attrs: Any) -> None:
        self.name = name
        self.attrs = attrs
        self._span = None
        self._fallback_start = 0.0
        self._fallback_id = uuid.uuid4().hex[:8]

    def __enter__(self) -> "ExecutionSpan":
        if _OTEL_AVAILABLE and _TRACER:
            # B1: OTel real span
            self._span = _TRACER.start_span(self.name)
            for k, v in self.attrs.items():
                self._span.set_attribute(k, str(v)[:500])
        else:
            # B1: Fallback en memoria
            self._fallback_start = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._span is not None:
            # B1: Cerrar OTel span
            if exc_type:
                self._span.record_exception(exc_val)
                self._span.set_status(
                    trace.Status(trace.StatusCode.ERROR, str(exc_val))
                )
            self._span.end()
        else:
            # B1: Registrar en fallback en memoria (misma estructura que antes)
            duration_ms = round((time.time() - self._fallback_start) * 1000, 1)
            span: Dict[str, Any] = {
                "span_id": self._fallback_id,
                "name": self.name,
                "duration_ms": duration_ms,
                "success": exc_type is None,
                "timestamp": datetime.now().isoformat(),
            }
            span.update(self.attrs)
            if exc_type:
                span["error"] = (
                    f"{exc_type.__name__}: {exc_val}"
                    if exc_val
                    else exc_type.__name__
                )
            with _FALLBACK_LOCK:
                _FALLBACK_SPANS.append(span)

    @classmethod
    def get_spans(cls) -> List[Dict[str, Any]]:
        """Return accumulated fallback spans (thread-safe copy)."""
        with _FALLBACK_LOCK:
            return list(_FALLBACK_SPANS)

    @classmethod
    def clear_spans(cls) -> None:
        """Clear all accumulated fallback spans."""
        with _FALLBACK_LOCK:
            _FALLBACK_SPANS.clear()


# ── B2: Export a console + archivo con rotación ──


def _get_traces_dir() -> Path:
    """Get traces directory under .memory/_pipeline/traces, creating if needed.

    Uses lazy import from pipeline to avoid circular imports at load time.
    """
    from lib.kosmos.pipeline import _MEMORY_DIR

    traces_dir = _MEMORY_DIR / "_pipeline" / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)
    return traces_dir


def export_spans(use_otel: bool = True) -> int:
    """Export accumulated spans (K2: OTel + JSONL dual export).

    - When *use_otel* is True and OTel is available, the registered
      span processors handle export automatically (Console, OTLP, …).
    - Always falls back to JSONL file export for the in-memory
      fallback spans (graceful degradation).

    Args:
        use_otel: If True, also export via OTel if available.

    Returns:
        Number of spans exported (0 if none accumulated).
    """
    spans = ExecutionSpan.get_spans()
    if not spans:
        return 0

    # K2: OTel processor chain handles export automatically via
    # ExecutionSpan.__exit__ → span.end().  The block below is a
    # log checkpoint; real OTel export is event-driven through
    # the registered processors.
    if use_otel and _OTEL_AVAILABLE:
        try:
            logger.debug("K2: OTel exporter active (%d spans)", len(spans))
        except Exception as exc:
            logger.warning("K2: OTel export note failed: %s", exc)

    # Fallback JSONL export (always works)
    traces_dir = _get_traces_dir()
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = traces_dir / f"traces-{today}.jsonl"

    count = 0
    with open(filepath, "a", encoding="utf-8") as f:
        for span in spans:
            f.write(json.dumps(span, ensure_ascii=False, default=str) + "\n")
            count += 1

    ExecutionSpan.clear_spans()

    # Rotate: remove files older than 7 days
    _rotate_traces(traces_dir, days=7)

    # Log console summary
    export_sources = ["jsonl"]
    if use_otel and _OTEL_AVAILABLE:
        export_sources.append("otel")
    logger.info("K2: Exported %d spans (%s) to %s", count, "+".join(export_sources), filepath)

    return count


def _rotate_traces(traces_dir: Path, days: int = 7) -> None:
    """Remove trace files older than ``days`` days."""
    cutoff = datetime.now() - timedelta(days=days)
    for f in traces_dir.glob("traces-*.jsonl"):
        try:
            date_str = f.stem.replace("traces-", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff:
                f.unlink()
                logger.debug("B2: Rotated old trace %s", f.name)
        except (ValueError, OSError):
            pass


def get_trace_files() -> List[Path]:
    """Get sorted list of trace files (newest first)."""
    traces_dir = _get_traces_dir()
    return sorted(traces_dir.glob("traces-*.jsonl"), reverse=True)


def get_trace_summary() -> Dict[str, Any]:
    """Get summary of all trace files — file count and total spans.

    Returns:
        Dict with keys: trace_files (int), total_spans (int), latest_file (str|None).
    """
    files = get_trace_files()
    total_spans = 0
    for f in files:
        try:
            total_spans += sum(1 for _ in open(f, encoding="utf-8"))
        except OSError:
            pass
    return {
        "trace_files": len(files),
        "total_spans": total_spans,
        "latest_file": str(files[0]) if files else None,
    }


def get_otel_status() -> Dict[str, Any]:
    """Get OTel integration status for health endpoint (K2).

    Returns:
        Dict with available, exporter_configured, export_format,
        and cache_size from the LLM cache for observability context.
    """
    cache_size = 0
    try:
        from lib.kosmos.llm import _LLM_CACHE  # type: ignore[import]
        cache_size = len(_LLM_CACHE)
    except (ImportError, AttributeError):
        pass
    return {
        "available": _OTEL_AVAILABLE,
        "exporter_configured": _OTEL_AVAILABLE,
        "export_format": "otlp+jsonl" if _OTEL_AVAILABLE else "jsonl",
        "cache_size": cache_size,
    }
