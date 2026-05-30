"""Unified curation pipeline orchestrator — replaces fragile agent_nodes delegation.

Phases are registered in order and can be individually gated by feature flags.
Shared cache (VaultGraph, txtai) initialized once per pipeline run.
Graceful degradation: each phase catches errors independently.
"""
import logging
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass, field
from pathlib import Path

from lib.config import VAULT_ROOT
from lib.feature_flags import is_enabled

logger = logging.getLogger(__name__)

_BASE = Path(__file__).resolve().parent.parent

_DOC_TIMEOUT = int(os.environ.get("CURATION_DOC_TIMEOUT", "30"))


@dataclass
class SharedCache:
    vault_graph: object | None = None
    txtai_available: bool = False
    pr_cache: dict = field(default_factory=dict)


@dataclass
class CurationState:
    paths: list[Path] = field(default_factory=list)
    scores: list[dict] = field(default_factory=list)
    score_avg: float = 0.0
    tier_distribution: dict = field(default_factory=dict)
    needs_synthesis: int = 0
    synthesis_results: list[dict] = field(default_factory=list)
    lint_issues: int = 0
    report: str = ""
    errors: list[str] = field(default_factory=list)
    dashboard_path: str = ""


_Phase = tuple[str, Callable, str]
_PHASES: list[_Phase] = []


def register_phase(name: str, fn: Callable, flag: str = ""):
    _PHASES.append((name, fn, flag))


def _init_with_timeout(fn, timeout=10):
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            logger.warning("Init timed out after %ds", timeout)
            return None


def _init_cache() -> SharedCache:
    cache = SharedCache()
    if os.environ.get("KAOS_TESTING") == "1":
        logger.info("KAOS_TESTING=1: skipping VaultGraph and txtai init")
        return cache
    try:
        from lib.graph_analysis import VaultGraph
        vg = _init_with_timeout(lambda: VaultGraph(), timeout=10)
        cache.vault_graph = vg
    except Exception as e:
        logger.warning("VaultGraph unavailable (degraded mode): %s", e)
    try:
        from lib.vectorstore import status as vs_status
        result = _init_with_timeout(vs_status, timeout=10)
        cache.txtai_available = result is not None and "not initialized" not in str(result)
    except Exception:
        pass
    return cache


def _phase_discover(state: CurationState, cache: SharedCache) -> CurationState:
    exclude = {"cache", "_pending", "_archive", "_scripts", "_pipeline", "dashboard"}
    root = VAULT_ROOT / "wiki"
    state.paths = [
        f for f in root.rglob("*.md")
        if not any(p in exclude for p in f.parts)
    ]
    logger.info("Discovered %d documents", len(state.paths))
    return state


def _phase_score(state: CurationState, cache: SharedCache) -> CurationState:
    if not state.paths:
        return state
    try:
        from lib.knowledge_scorer import score_document

        for p in state.paths:
            try:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    fut = pool.submit(score_document, p, vg=cache.vault_graph)
                    r = fut.result(timeout=_DOC_TIMEOUT)
                if "error" not in r:
                    state.scores.append(r)
            except TimeoutError:
                state.errors.append(f"score({p.name}): timeout after {_DOC_TIMEOUT}s")
            except Exception as e:
                state.errors.append(f"score({p.name}): {e}")

        if state.scores:
            scores_list = [s.get("score", 0) for s in state.scores]
            state.score_avg = round(sum(scores_list) / len(scores_list), 2)
            dist = {}
            needs = 0
            for s in state.scores:
                lvl = s.get("level", "RAW")
                dist[lvl] = dist.get(lvl, 0) + 1
                if s.get("score", 100) < 60:
                    needs += 1
            state.tier_distribution = dist
            state.needs_synthesis = needs
        logger.info("Scored %d docs, avg=%.1f, tiers=%s",
                     len(state.scores), state.score_avg, state.tier_distribution)
    except Exception as e:
        state.errors.append(f"score phase: {e}")
    return state


def _phase_synthesize(state: CurationState, cache: SharedCache) -> CurationState:
    from lib.config import KNOWLEDGE_SYNTHESIS_MAX_DOCS

    candidates = [s for s in state.scores if s.get("score", 100) < 60][:KNOWLEDGE_SYNTHESIS_MAX_DOCS]
    if not candidates:
        return state
    try:
        from lib.knowledge_synthesis import synthesize

        for c in candidates:
            try:
                path = c.get("path", "")
                if not path:
                    continue
                syn = synthesize(path, c, dry_run=False)
                state.synthesis_results.append(syn)
            except Exception as e:
                state.errors.append(f"synthesize({Path(path).name}): {e}")
        logger.info("Synthesized %d docs", len(state.synthesis_results))
    except Exception as e:
        state.errors.append(f"synthesize phase: {e}")
    return state


def _phase_lint(state: CurationState, cache: SharedCache) -> CurationState:
    try:
        from lib.lint import run as lint_run
        issues, _ = lint_run([])
        state.lint_issues = len(issues) if isinstance(issues, list) else 0
    except Exception as e:
        state.errors.append(f"lint: {e}")
    return state


def _phase_report(state: CurationState, cache: SharedCache) -> CurationState:
    try:
        from lib.knowledge_scorer import format_report, generate_dashboard
        if state.scores:
            state.report = format_report(state.scores)
            dash_path = _BASE.parent / "dashboard" / "knowledge-dashboard.html"
            generate_dashboard(state.scores, dash_path)
            state.dashboard_path = str(dash_path)
    except Exception as e:
        state.errors.append(f"report: {e}")
    return state


register_phase("discover", _phase_discover)
register_phase("score", _phase_score, "use_knowledge_scorer")
register_phase("synthesize", _phase_synthesize, "use_knowledge_synthesis")
register_phase("lint", _phase_lint)
register_phase("report", _phase_report)


def run_pipeline(state: CurationState | None = None) -> CurationState:
    if state is None:
        state = CurationState()
    try:
        cache = _init_cache()
    except MemoryError:
        logger.error("MemoryError during cache init — returning empty results")
        state.errors.append("cache_init: MemoryError")
        return state
    except Exception as e:
        logger.warning("Cache init failed, continuing without cache: %s", e)
        cache = SharedCache()
        state.errors.append(f"cache_init: {e}")
    for name, fn, flag in _PHASES:
        if flag and not is_enabled(flag):
            logger.info("Phase '%s' skipped (flag %s=OFF)", name, flag)
            continue
        try:
            state = fn(state, cache)
        except MemoryError:
            logger.error("MemoryError in phase '%s' — returning partial results", name)
            state.errors.append(f"{name}: MemoryError")
            break
        except Exception as e:
            logger.warning("Phase '%s' failed: %s", name, e)
            state.errors.append(f"{name}: {e}")
    return state


def mnemosyne_curation_node(state_dict: dict) -> dict:
    """Entry point for LangGraph agent_executor.mnemosyne_node()."""
    curation_state = CurationState()
    result = run_pipeline(curation_state)
    report = result.report or "# Mnemosyne Curation Report\n\n*No documents scored.*\n"
    return {
        **state_dict,
        "mnemosyne_output": report,
        "curation_metrics": {
            "knowledge_score_avg": result.score_avg,
            "knowledge_tier_distribution": result.tier_distribution,
            "knowledge_needs_synthesis": result.needs_synthesis,
            "synthesis_results": result.synthesis_results,
            "synthesis_count": len(result.synthesis_results),
            "lint_issues": result.lint_issues,
            "phases": [name for name, _, _ in _PHASES],
            "errors": result.errors,
        },
    }
