"""kosmos/_state.py — Estado global compartido para KosmosV2 (D1 hardening).

Este módulo NO importa nada del subpackage kosmos/ para evitar imports circulares.
Contiene referencias a objetos globales que necesitan ser accedidos desde
múltiples módulos del subpackage.

Uso:
    from lib.kosmos._state import get_pipeline_cache
    cache = get_pipeline_cache()
"""

from typing import Any

_PIPELINE_CACHE: Any = None


def set_pipeline_cache(cache: Any) -> None:
    """Set the global pipeline cache instance."""
    global _PIPELINE_CACHE
    _PIPELINE_CACHE = cache


def get_pipeline_cache() -> Any:
    """Get the global pipeline cache instance."""
    return _PIPELINE_CACHE


def pipeline_cache_stats() -> dict[str, Any]:
    """Get cache stats, or empty dict if not initialized."""
    cache = get_pipeline_cache()
    if cache is not None and hasattr(cache, 'stats'):
        return cache.stats()
    return {"size": 0, "maxsize": 0, "hit_rate": 0.0}
