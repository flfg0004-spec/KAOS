"""kosmos/pipeline.py — KosmosV2 Pipeline class.

Contains the KosmosPipelineV2 class orchestrating the 8-node pipeline,
plus the async entry point run_kosmos_pipeline().
"""

import json
import logging
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── B1: ExecutionSpan via OpenTelemetry (or fallback in-memory) ──
from lib.kosmos.otel import ExecutionSpan, export_spans

# ── S3.2: In-memory pipeline cache (avoids sentence-transformers dependency) ──
from lib.kosmos.cache import PipelineCache
from lib.kosmos._state import set_pipeline_cache
_PIPELINE_CACHE = PipelineCache(maxsize=500, ttl_seconds=1800)
set_pipeline_cache(_PIPELINE_CACHE)

# ── A2: Global txtai mutex (non-reentrant Lock, timeout 10s) ──
_TXTAI_LOCK = threading.Lock()

# ── Vault / project paths (adjusted for lib/kosmos/pipeline.py location) ──
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent  # .memory/_scripts/
_MEMORY_DIR = _SCRIPTS_DIR.parent  # .memory/
_VAULT_ROOT = _MEMORY_DIR.parent  # KAOS/
_PIPELINE_DIR = _MEMORY_DIR / "_pipeline"
_RAW_DIR = _PIPELINE_DIR / "raw"
_SCHEMA_DIR = _MEMORY_DIR / "schema"
_CACHE_DIR = _MEMORY_DIR / "cache"

# ── Ensure directory ──
_RAW_DIR.mkdir(parents=True, exist_ok=True)

from lib.kosmos.routing import resolve_routing, ROUTING_TABLE


class KosmosPipelineV2:
    """Pipeline de 8 nodos para KosmosV2.

    Cada nodo ejecuta una función específica y actualiza el estado.
    Los nodos son independientes y el pipeline continúa incluso si
    un nodo falla (graceful degradation).

    Uso:
        pipeline = KosmosPipelineV2(state, memory)
        result = pipeline.run_all()
    """

    def __init__(self, state: Dict[str, Any], memory: Any = None) -> None:
        """Initialize the pipeline.

        Args:
            state: Pipeline state dict with at least 'topic' key.
            memory: Optional ArchitectureMemoryL0 instance.
        """
        self.state: Dict[str, Any] = {**state}
        self.memory = memory
        self.node_results: Dict[str, Dict[str, Any]] = {}
        self.errors: Dict[str, str] = {}
        self.iteration = state.get("iteration", 0)

        # G2: Skip evaluation flag (pipeline vs external evaluation)
        self.skip_eval = state.get("skip_eval", False)

        # P1: Cache enabled flag
        self.cache_enabled = state.get("cache_enabled", True)
        self.topic_hash = self._make_topic_hash(state.get("topic", ""), state)

        # P2: Parallel execution flag (DAG optimization)
        self.parallel_enabled = state.get("parallel_enabled", True)

        # G4: Aletheia real verification flag
        self.aletheia_real = state.get("aletheia_real", True)

        # A4: Rate limiting flag (active by default)
        self.rate_limiter = state.get("rate_limiter", True)

        # S3.1: Thread safety locks for shared state
        self._state_lock = threading.RLock()
        self._results_lock = threading.RLock()
        self._errors_lock = threading.RLock()

        logger.info("KosmosPipelineV2 initialized (topic=%s, skip_eval=%s, cache=%s)",
                     state.get("topic", "N/A")[:50], self.skip_eval, self.cache_enabled)

    @staticmethod
    def _build_empty_summary(reason: str, start_time: datetime) -> Dict[str, Any]:
        """Build empty summary for skipped/rate-limited pipeline."""
        return {
            "pipeline": "KosmosV2",
            "status": "skipped",
            "reason": reason,
            "elapsed_seconds": round((datetime.now() - start_time).total_seconds(), 2),
            "nodes_executed": 0,
            "nodes_with_errors": 0,
            "errors": {"rate_limit": reason},
        }

    @staticmethod
    def _make_topic_hash(topic: str, state: dict = None) -> str:
        """Generate a deterministic cache key for a pipeline execution.

        Args:
            topic: The pipeline topic.
            state: Optional pipeline state to incorporate into the key.

        Returns:
            16-char hex hash string.
        """
        import hashlib
        key_dict = {"topic": topic, "pipeline": "KosmosV2", "version": 3}
        if state:
            key_dict["profile"] = state.get("profile", "desarrollo")
        raw = json.dumps(key_dict, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    # ── Public methods ──

    def run_contracts(self) -> Dict[str, Any]:
        """Ejecuta todos los contratos post-ADR (Fase 2).

        Inicializa ContractOrchestrator con L0 memory y ejecuta
        ``run_all_contracts()`` con el ADR generado y el estado actual.

        Returns:
            Dict con resultados de contratos, incluyendo summary de
            ContractOrchestrator.
        """
        logger.info("▶️ Ejecutando contratos Fase 2...")
        try:
            from lib.kosmos_contracts import ContractOrchestrator

            adr_data = self.state.get("adr", {})
            adr_text = adr_data.get("adr_text", "")
            adr_id = adr_data.get("adr_id", "ADR-XXX")

            if not adr_text:
                return {"status": "skipped", "reason": "No ADR text available"}

            aletheia_real = getattr(self, 'aletheia_real', False)
            orchestrator = ContractOrchestrator(memory_l0=self.memory, aletheia_real=aletheia_real)
            contracts_result = orchestrator.run_all_contracts(
                adr_text=adr_text,
                adr_id=adr_id,
                state=self.state,
            )

            summary = orchestrator.get_summary()

            # G5: Propagate corrective actions from contracts
            corrective_actions = contracts_result.get("corrective_actions", [])

            result = {
                "status": "completed",
                "contracts": contracts_result.get("contracts", {}),
                "summary": summary,
                "contract_statuses": orchestrator.get_contract_statuses(),
                "corrective_actions": corrective_actions,
            }

            logger.info("   Contracts: %s (%d corrective actions)",
                         summary.get("summary_text", ""), len(corrective_actions))
            return result

        except ImportError as exc:
            logger.warning("ContractOrchestrator not available: %s", exc)
            return {"status": "error", "error": f"Module not available: {exc}"}
        except Exception as exc:
            logger.warning("Contract execution failed: %s", exc)
            return {"status": "error", "error": str(exc)}

    def sync_with_txtai(self, adr_text: str, adr_id: str) -> str:
        """Indexa ADR en L1 (txtai) para búsqueda semántica inmediata.

        Usa ``vectorstore.update()`` para agregar el ADR al índice txtai
        con metadata (id, título, tags).

        Args:
            adr_text: Texto completo del ADR.
            adr_id: ID del ADR (ej. "ADR-019").

        Returns:
            Status string describing the indexing result.
        """
        # A2: Global txtai mutex — non-reentrant Lock with 10s timeout
        if not _TXTAI_LOCK.acquire(timeout=10):
            logger.warning("A2: txtai lock timeout (10s) — skipping L1 index")
            return "skipped: txtai busy"
        try:
            try:
                from lib.vectorstore import update as _vs_update

                # Extract title from ADR
                title_match = re.search(r'^#\s+(.+)$', adr_text, re.MULTILINE)
                title = title_match.group(1).strip() if title_match else adr_id

                # Extract tags
                tags_match = re.search(r'tags:\s*\[([^\]]+)\]', adr_text)
                tags_str = tags_match.group(1) if tags_match else "adr, architecture"

                # Build metadata-enhanced text for indexing
                meta_text = f"# {title}\n\n**ID**: {adr_id}\n**Tags**: {tags_str}\n\n{adr_text}"

                # Use vectorstore to update index
                l1_dir = _MEMORY_DIR / "_pipeline" / "raw" / "l1_index"
                l1_dir.mkdir(parents=True, exist_ok=True)
                temp_path = l1_dir / f"{adr_id.lower()}-adr.md"
                temp_path.write_text(meta_text, encoding="utf-8")

                # Call vectorstore.update with relative path
                rel_path = temp_path.relative_to(_MEMORY_DIR).as_posix()
                result = _vs_update(rel_path)

                logger.info("L1 sync for %s: %s", adr_id, result)
                return result

            except ImportError as exc:
                logger.warning("txtai not available for L1 sync: %s", exc)
                return "L1 unavailable: txtai not installed"
            except Exception as exc:
                logger.warning("L1 sync failed for %s: %s", adr_id, exc)
                return f"L1 sync error: {exc}"
        finally:
            _TXTAI_LOCK.release()

    def _populate_arch_graph(self, adr_id: str, topic: str, tags: list, related: list, adr_text: str) -> Dict[str, Any]:
        """Populate the ArchKnowledgeGraph with ADR data (Fase 3).

        Uses arch_graph.py to add nodes and edges representing the ADR
        and its relationships to components, patterns, and other ADRs.

        Returns:
            Dict with nodes_added, edges_added, status, coverage.
        """
        result: Dict[str, Any] = {
            "nodes_added": 0,
            "edges_added": 0,
            "status": {},
            "coverage": {},
        }
        try:
            from lib import arch_graph

            # Add ADR node
            add_node_result = arch_graph.add_node(
                node_id=adr_id,
                node_type="adr",
                properties={
                    "title": topic[:200],
                    "status": "proposed",
                    "tags": tags[:10],
                    "created": datetime.now().isoformat(),
                },
            )
            result["nodes_added"] += 1

            # Add edges for related ADRs
            for rel_adr in related[:10]:
                arch_graph.add_edge(
                    source_id=adr_id,
                    target_id=rel_adr.strip(),
                    edge_type="references",
                    properties={"type": "adr-reference"},
                )
                result["edges_added"] += 1

            # Detect component references from text and add implements edges
            if adr_text:
                component_patterns = re.findall(
                    r'(?:component|m[oó]dulo|servicio|service|api)\s+[`\"]*([A-Za-z0-9_\\-]+)',
                    adr_text, re.IGNORECASE
                )
                for comp in list(set(component_patterns))[:5]:
                    arch_graph.add_node(node_id=f"comp-{comp}", node_type="component", properties={"name": comp})
                    arch_graph.add_edge(source_id=adr_id, target_id=f"comp-{comp}", edge_type="implements")
                    result["nodes_added"] += 1
                    result["edges_added"] += 1

            # Query coverage
            try:
                coverage = arch_graph.query("adr_coverage")
                result["coverage"] = coverage if isinstance(coverage, dict) else {"raw": str(coverage)[:200]}
            except Exception:
                result["coverage"] = {"error": "coverage query failed"}

            result["status"] = arch_graph.status()
            logger.info("ArchKnowledgeGraph: %d nodes, %d edges added", result["nodes_added"], result["edges_added"])

        except Exception as exc:
            logger.warning("ArchKnowledgeGraph population failed (non-blocking): %s", exc)
            result["error"] = str(exc)[:200]

        return result

    def get_errors(self) -> Dict[str, str]:
        """Return all errors collected during pipeline execution.

        Returns:
            Dict mapping node name to error string.
        """
        return dict(self.errors)

    # ── P2: Parallel node execution ──

    def _run_parallel_nodes(self, node_batch: List[Tuple[str, Callable]], batch_name: str = "") -> None:
        """Execute a batch of independent nodes in parallel using ThreadPoolExecutor.

        P2 optimization: nodes that have no dependency on each other run
        concurrently, reducing total pipeline time from N levels to ~5.

        Args:
            node_batch: List of (node_name, node_method) tuples to run in parallel.
            batch_name: Optional name for logging.
        """
        if not node_batch:
            return
        if len(node_batch) == 1:
            # Single node — run synchronously (no thread overhead)
            name, method = node_batch[0]
            logger.info("⏩ Running %s (single, no thread overhead)", name)
            method()
            return

        logger.info("⏩ Running %d nodes in parallel [%s]", len(node_batch), batch_name)

        def _safe_run(name: str, method: Callable) -> None:
            """Run a node method with state lock protection (S3.1)."""
            try:
                method()
                with self._state_lock:
                    logger.info("   ✅ %s completed", name)
            except Exception as exc:
                with self._errors_lock:
                    self.errors[name] = str(exc)
                logger.warning("   ❌ %s failed: %s", name, exc)

        with ThreadPoolExecutor(max_workers=len(node_batch)) as executor:
            fut_map = {executor.submit(_safe_run, name, method): name for name, method in node_batch}
            for future in as_completed(fut_map):
                future.result()  # re-raise if _safe_run failed unexpectedly

    # ── D2: Node methods (delegating to nodes.py with lazy imports) ──

    def discover(self) -> Dict[str, Any]:
        """Nodo 1: Discover — escanea el código base."""
        from lib.kosmos.nodes import discover as _impl
        return _impl(self)

    def model(self) -> Dict[str, Any]:
        """Nodo 2: Model — genera modelo C4."""
        from lib.kosmos.nodes import model as _impl
        return _impl(self)

    def analyze(self) -> Dict[str, Any]:
        """Nodo 3: Analyze — análisis de impacto y health score."""
        from lib.kosmos.nodes import analyze as _impl
        return _impl(self)

    def quality(self) -> Dict[str, Any]:
        """Nodo 4: Quality — evaluación dimensional del output."""
        from lib.kosmos.nodes import quality as _impl
        return _impl(self)

    def visualize(self) -> Dict[str, Any]:
        """Nodo 5: Visualize — genera diagramas C4 obligatorios con validación."""
        from lib.kosmos.nodes import visualize as _impl
        return _impl(self)

    def document(self) -> Dict[str, Any]:
        """Nodo 6: Document — redacta el ADR completo y lo indexa en L1."""
        from lib.kosmos.nodes import document as _impl
        return _impl(self)

    def govern(self) -> Dict[str, Any]:
        """Nodo 7: Govern — población del Architecture Knowledge Graph."""
        from lib.kosmos.nodes import govern as _impl
        return _impl(self)

    def validate(self) -> Dict[str, Any]:
        """Nodo 8: Validate — verificación cross-referencia + reflexión + contratos F2."""
        from lib.kosmos.nodes import validate as _impl
        return _impl(self)

    @staticmethod
    def _validate_diagram(diagram_text: str, diagram_name: str) -> Dict[str, Any]:
        """Validate a Mermaid diagram for minimum quality requirements."""
        from lib.kosmos.nodes import _validate_diagram as _impl
        return _impl(diagram_text, diagram_name)

    @staticmethod
    def _generate_fallback_diagram(diagram_type: str, topic: str) -> str:
        """Generate a simplified fallback diagram when validation fails."""
        from lib.kosmos.nodes import _generate_fallback_diagram as _impl
        return _impl(diagram_type, topic)

    # ── Pipeline runner ──

    def run_all(self) -> Dict[str, Any]:
        """Execute all 8 pipeline nodes in sequence.

        Each node is executed with error isolation — if a node fails,
        the pipeline continues with the next node and logs the error.

        Returns:
            Complete pipeline state dict with all node results,
            error log, and metadata.
        """
        logger.info("=" * 60)
        logger.info("🚀 KosmosV2 Pipeline: Starting 8-node execution")
        logger.info("=" * 60)

        start_time = datetime.now()
        topic = self.state.get("topic", "")

        # A4: Rate limiting
        if hasattr(self, 'rate_limiter') and self.rate_limiter:
            try:
                from lib.kosmos.ratelimit import acquire_pipeline, release_pipeline
                self._release_rate = release_pipeline
                if not acquire_pipeline():
                    logger.warning("A4: Pipeline rate limit exceeded")
                    return self._build_empty_summary("rate_limited", start_time)
            except Exception as exc:
                logger.warning("A4: Rate limiter unavailable (non-blocking): %s", exc)

        # P1: Check cache (PipelineCache LRU+TTL, A1+A3 unified)
        if self.cache_enabled:
            cached = _PIPELINE_CACHE.get(self.topic_hash)
            if cached:
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info("P1: Cache HIT for topic '%s' (hash=%s, %.2fs)",
                            topic[:40], self.topic_hash, elapsed)
                self.state.update(cached.get("state", {}))
                self.node_results = cached.get("node_results", {})
                self.errors = cached.get("errors", {})
                summary = cached.get("summary", {})
                summary["cached"] = True
                summary["cache_hit"] = True
                summary["elapsed_seconds"] = round(elapsed, 2)
                summary["evaluation_mode"] = "cached"
                return summary

        # P2: Parallel DAG execution
        if self.parallel_enabled:
            with ExecutionSpan("batch_level_0", batch="Discover+Analyze"):
                self._run_parallel_nodes([
                    ("discover", self.discover),
                    ("analyze", self.analyze),
                ], batch_name="Level 0: Discover+Analyze")
            with ExecutionSpan("model", topic=topic[:50]):
                self.model()
            with ExecutionSpan("batch_level_2", batch="Quality+Visualize"):
                self._run_parallel_nodes([
                    ("quality", self.quality),
                    ("visualize", self.visualize),
                ], batch_name="Level 2: Quality+Visualize")
            with ExecutionSpan("document", topic=topic[:50]):
                self.document()
            with ExecutionSpan("batch_level_4", batch="Govern+Validate"):
                self._run_parallel_nodes([
                    ("govern", self.govern),
                    ("validate", self.validate),
                ], batch_name="Level 4: Govern+Validate")
        else:
            with ExecutionSpan("discover", topic=topic[:50]):
                self.discover()
            with ExecutionSpan("model", topic=topic[:50]):
                self.model()
            with ExecutionSpan("analyze", topic=topic[:50]):
                self.analyze()
            with ExecutionSpan("quality", topic=topic[:50]):
                self.quality()
            with ExecutionSpan("visualize", topic=topic[:50]):
                self.visualize()
            with ExecutionSpan("document", topic=topic[:50]):
                self.document()
            with ExecutionSpan("govern", topic=topic[:50]):
                self.govern()
            with ExecutionSpan("validate", topic=topic[:50]):
                self.validate()

        elapsed = (datetime.now() - start_time).total_seconds()

        # Build summary
        summary: Dict[str, Any] = {
            "pipeline": "KosmosV2",
            "topic": topic,
            "started_at": start_time.isoformat(),
            "elapsed_seconds": round(elapsed, 2),
            "nodes_executed": len([n for n in self.node_results.keys()]),
            "nodes_with_errors": len(self.errors),
            "errors": self.errors,
            "routing": {node: resolve_routing(node, self.state) for node in ROUTING_TABLE},
            "node_results": self.node_results,
            "parallel_enabled": self.parallel_enabled,
            "pipeline_levels": 5 if self.parallel_enabled else 8,
            "corrective_actions": self.node_results.get("validate", {}).get("corrective_actions", []),
            "spans": ExecutionSpan.get_spans(),
        }

        # B2: Export spans to JSONL file with daily rotation
        try:
            exported = export_spans()
            if exported:
                logger.debug("B2: Exported %d spans to file", exported)
        except Exception as exc:
            logger.warning("B2: Span export failed: %s", exc)

        # Extract key outputs for the state
        self.state["kosmos_output"] = summary
        self.state["kosmos_adr"] = self.node_results.get("document", {}).get("adr_text", "")
        self.state["kosmos_diagrams"] = self.node_results.get("visualize", {}).get("diagram_paths", [])
        self.state["kosmos_scores"] = self.node_results.get("quality", {}).get("scores", {})

        # G2: Flatten evaluation results into state for external consumption
        quality_result = self.node_results.get("quality", {})
        if quality_result.get("scores") and not quality_result.get("skip_eval"):
            self.state["kosmos_eval_v2"] = {
                "scores": quality_result["scores"],
                "weighted_score": quality_result.get("weighted_score", 0.0),
                "passed": quality_result.get("passed", False),
                "profile": quality_result.get("profile_used", "desarrollo"),
                "evidences": quality_result.get("evidences", {}),
            }
            logger.info("G2: kosmos_eval_v2 stored in state (composite=%.1f)",
                        quality_result.get("weighted_score", 0.0))

        # G2: Store reflection from validate node (already flattened)
        reflection_from_validate = self.node_results.get("validate", {}).get("reflection", {})
        if reflection_from_validate and not reflection_from_validate.get("skip_eval"):
            self.state["kosmos_reflection"] = reflection_from_validate
            logger.info("G2: kosmos_reflection stored in state (score=%s)",
                        reflection_from_validate.get("total_score", "N/A"))

        self.state["kosmos_errors"] = self.errors

        # G2: evaluation_mode flag
        summary["evaluation_mode"] = "pipeline" if not self.skip_eval else "external"

        # ── Fase 3: Post-pipeline autonomy ──
        fase3_result: Dict[str, Any] = {}
        try:
            from lib.kosmos_monitor import ArchitectureMonitor
            monitor = ArchitectureMonitor()
            health = monitor.full_scan()
            if hasattr(health, '__dataclass_fields__'):
                import dataclasses
                fase3_result["health"] = dataclasses.asdict(health)
            else:
                fase3_result["health"] = str(health)
        except Exception as exc:
            logger.warning("F3 monitor failed: %s", exc)
            fase3_result["health_error"] = str(exc)[:200]

        try:
            from lib.kosmos_dashboard import KosmosDashboard
            dash = KosmosDashboard(monitor=None, memory_l0=getattr(self, 'memory', None))
            dash_path = dash.generate()
            fase3_result["dashboard_path"] = str(dash_path) if dash_path else ""
        except Exception as exc:
            logger.warning("F3 dashboard failed: %s", exc)
            fase3_result["dashboard_error"] = str(exc)[:200]

        try:
            from lib.kosmos_kronos_feedback import KosmosKronosLoop
            loop = KosmosKronosLoop()
            kronos = loop.report_pipeline_health(summary)
            fase3_result["kronos_feedback"] = kronos
        except Exception as exc:
            logger.warning("F3 kronos failed: %s", exc)
            fase3_result["kronos_error"] = str(exc)[:200]

        summary["fase3"] = fase3_result
        self.state["kosmos_fase3"] = fase3_result
        logger.info("Fase 3: health=%s, dashboard=%s",
                    "ok" if "health" in fase3_result else "error",
                    "ok" if "dashboard_path" in fase3_result else "error")

        # P1: Store in cache (PipelineCache unified A3)
        if self.cache_enabled:
            cache_state = {
                "kosmos_adr": self.state.get("kosmos_adr", ""),
                "kosmos_diagrams": self.state.get("kosmos_diagrams", []),
                "kosmos_eval_v2": self.state.get("kosmos_eval_v2", {}),
                "kosmos_reflection": self.state.get("kosmos_reflection", {}),
                "kosmos_scores": self.state.get("kosmos_scores", {}),
                "adr": self.state.get("adr", {}),
            }
            cache_summary = {k: v for k, v in summary.items() if k not in ("fase3", "node_results")}
            _PIPELINE_CACHE.put(self.topic_hash, {
                "state": cache_state,
                "node_results": self.node_results,
                "errors": self.errors,
                "summary": cache_summary,
            })

        # A4: Release rate limiter slot
        if hasattr(self, '_release_rate'):
            try:
                self._release_rate()
            except Exception:
                pass

        logger.info("=" * 60)
        logger.info("✅ KosmosV2 Pipeline: Complete (%d nodes, %d errors, %.2fs)",
                    len(self.node_results), len(self.errors), elapsed)
        logger.info("=" * 60)

        return summary


# D2: Nodos definidos como métodos reales en la clase (no monkey-patches)
# Los métodos discover, model, etc. están definidos arriba en KosmosPipelineV2
# y usan import lazy de lib.kosmos.nodes internamente.

# ── Async high-level entry point ──

async def run_kosmos_pipeline(topic: str, context: dict = None) -> Dict[str, Any]:
    """High-level async entry point for the KosmosV2 pipeline.

    Initializes L0 memory, indexes ADRs (if first time), and runs
    the full 8-node pipeline.

    Args:
        topic: The architecture topic to analyze.
        context: Optional context dict with additional state.

    Returns:
        Complete pipeline result with scores, ADR, diagrams, reflections.
    """
    logger.info("run_kosmos_pipeline(topic='%s')", topic[:60])

    if context is None:
        context = {}

    # 1. Initialize L0 memory
    memory = None
    try:
        from lib.kosmos_memory import ArchitectureMemoryL0

        memory = ArchitectureMemoryL0()
        count = memory.index_all_adrs()
        logger.info("L0 memory initialized: %d ADRs indexed", count)
    except Exception as exc:
        logger.warning("L0 memory init failed (non-critical): %s", exc)

    # 2. Build initial state
    state: Dict[str, Any] = {
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "iteration": context.get("iteration", 0),
        "profile": context.get("profile", "desarrollo"),
        "tags": context.get("tags", ["adr", "architecture"]),
        "aletheia_output": context.get("aletheia_output", ""),
        **context,
    }

    # 3. Execute pipeline
    pipeline = KosmosPipelineV2(state, memory)
    result = pipeline.run_all()

    # 4. Build final output
    output: Dict[str, Any] = {
        "topic": topic,
        "pipeline_result": result,
        "adr": state.get("kosmos_adr", ""),
        "adr_id": state.get("adr", {}).get("adr_id", ""),
        "diagrams": state.get("kosmos_diagrams", []),
        "quality_scores": state.get("kosmos_scores", {}),
        "reflection": state.get("kosmos_reflection", {}),
        "errors": state.get("kosmos_errors", {}),
        "node_count": len(result.get("node_results", {})),
        "elapsed_seconds": result.get("elapsed_seconds", 0),
        "timestamp": datetime.now().isoformat(),
    }

    # Clean up memory
    if memory is not None:
        try:
            memory.close()
        except Exception:
            pass

    logger.info("run_kosmos_pipeline complete: adr=%s, diagrams=%d, errors=%d",
                output["adr_id"], len(output["diagrams"]), len(output["errors"]))

    return output


# ── Quick test ──
if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(level=_logging.INFO)

    print("=" * 60)
    print("KosmosV2 Pipeline — Self-Test")
    print("=" * 60)

    # Test 1: Routing table
    print("\n1️⃣  Routing Table:")
    for node, route in ROUTING_TABLE.items():
        print(f"   {node:12s} → {route['model']:16s} ({route['reason']})")

    # Test 2: Pipeline instantiation
    print("\n2️⃣  Pipeline Instantiation...")
    test_state = {
        "topic": "Sistema de Memoria Arquitectónica L0",
        "iteration": 0,
    }
    pipeline = KosmosPipelineV2(test_state)
    print("   ✅ Pipeline created")

    # Test 3: Discovery node (standalone)
    print("\n3️⃣  Discover node...")
    disc = pipeline.discover()
    print(f"   Files: {len(disc.get('files', []))}")
    print(f"   Imports: {len(disc.get('imports', {}))}")
    print(f"   Problems: {disc.get('problems', [])}")

    # Test 4: Model node
    print("\n4️⃣  Model node...")
    mdl = pipeline.model()
    dsl_lines = mdl.get("dsl", "").count("\n")
    print(f"   DSL: {dsl_lines} lines")
    print(f"   Containers: {len(mdl.get('containers', []))}")

    # Test 5: Analyze node
    print("\n5️⃣  Analyze node...")
    anl = pipeline.analyze()
    health = anl.get("health", {}).get("health_score", "N/A")
    print(f"   Health score: {health}")
    print(f"   Suggestions: {anl.get('suggestions', [])}")

    # Test 6: Quality node
    print("\n6️⃣  Quality node...")
    qual = pipeline.quality()
    print(f"   Weighted score: {qual.get('weighted_score', 'N/A')}")
    print(f"   Passed: {qual.get('passed', False)}")

    # Test 7: Visualize node
    print("\n7️⃣  Visualize node...")
    vis = pipeline.visualize()
    print(f"   Diagrams: {vis.get('diagram_paths', [])}")

    # Test 8: Document node
    print("\n8️⃣  Document node...")
    doc = pipeline.document()
    adr_preview = doc.get("adr_text", "")[:100].replace("\n", " ")
    print(f"   ADR ID: {doc.get('adr_id', 'N/A')}")
    print(f"   Preview: {adr_preview}...")

    # Test 9: Govern node
    print("\n9️⃣  Govern node...")
    gov = pipeline.govern()
    print(f"   Triples: {gov.get('triple_count', 0)}")

    # Test 10: Validate node
    print("\n🔟 Validate node...")
    val = pipeline.validate()
    print(f"   Suggestions: {val.get('suggestions', [])}")
    ref_count = len(val.get("validation", {}).get("adr_references_found", []))
    print(f"   ADR refs found: {ref_count}")

    # Test 11: run_all
    print("\n1️⃣1️⃣  Full pipeline run_all...")
    test_state2 = {"topic": "Sistema de Memoria Arquitectónica L0"}
    pipeline2 = KosmosPipelineV2(test_state2)
    full = pipeline2.run_all()
    print(f"   Nodes: {len(full.get('node_results', {}))}/8")
    print(f"   Errors: {len(full.get('errors', {}))}")
    print(f"   Time: {full.get('elapsed_seconds', 0):.2f}s")
    print(f"   ADR: {'✅' if pipeline2.state.get('kosmos_adr') else '❌'} generated")
    print(f"   Diagrams: {len(pipeline2.state.get('kosmos_diagrams', []))}")

    print("\n" + "=" * 60)
    print("✅ KosmosV2 Pipeline self-test complete")
    print("=" * 60)
