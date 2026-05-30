"""kosmos_node_v2.py — Wrapper de compatibilidad.

Contenido refactorizado a kosmos/ submódulos (S1 endurecimiento).
Mantiene retrocompatibilidad para imports existentes.
"""

from lib.kosmos.pipeline import KosmosPipelineV2, run_kosmos_pipeline
from lib.kosmos.routing import ROUTING_TABLE, resolve_routing

__all__ = ["KosmosPipelineV2", "run_kosmos_pipeline", "resolve_routing", "ROUTING_TABLE"]
