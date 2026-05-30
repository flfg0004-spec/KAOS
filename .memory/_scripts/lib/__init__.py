# KAOS Memory Vault — Python library

# KosmosV2 modules
from .kosmos_memory import ArchitectureMemoryL0, ArchitectureMemoryL1, index_adrs_sync
from .kosmos_node_v2 import KosmosPipelineV2, run_kosmos_pipeline, resolve_routing, ROUTING_TABLE
from .kosmos_evaluator_v2 import DimensionalEvaluator, evaluate_all_dimensions, EvaluationResult
from .kosmos_reflect import ReflectionEngine, ReflectionReport

# KosmosV2 Fase 2: Contracts
from .kosmos_contracts import (
    AdherenceReport,
    OKRValidationResult,
    ADRImpactNotification,
    CurationFeedback,
    FactualVerification,
    KosmosKratosContract,
    KosmosMetisContract,
    KosmosMnemosyneContract,
    KosmosAletheiaContract,
    ContractOrchestrator,
    ADHERENCE_CRITERIA,
)

# KosmosV2 Fase 3: Autonomy
from .kosmos_monitor import ArchitectureMonitor, DebtTracker, ArchitectureHealthReport
from .kosmos_dashboard import KosmosDashboard
from .kosmos_kronos_feedback import KosmosKronosLoop, PipelineHealthReport
from . import arch_graph

# KosmosV2 S1: Submódulos refactorizados
from .kosmos import (
    KosmosPipelineV2,
    resolve_routing,
    ROUTING_TABLE,
    run_kosmos_pipeline,
)

# Backward compatibility exports
from .kosmos_evaluator_v2 import evaluate_system, run_evaluator
