"""Pipeline MCP Server — pipeline_status, pipeline_run, pipeline_cancel, pipeline_list."""

import json
import logging
import random
import time
import uuid
from datetime import datetime
from typing import Any, Optional

_LOG = logging.getLogger(__name__)

from lib.kronos import ParallelExecutor, TaskState
from lib.events import EventBus

# ── Shared executor pool ──────────────────────────
_EXECUTOR_POOL = None

def _get_executor(max_workers: int = 4):
    """Return a shared ThreadPoolExecutor (lazy-init)."""
    global _EXECUTOR_POOL
    if _EXECUTOR_POOL is None:
        from concurrent.futures import ThreadPoolExecutor
        _EXECUTOR_POOL = ThreadPoolExecutor(max_workers=max_workers)
        _LOG.info("Created shared executor pool (max_workers=%d)", max_workers)
    return _EXECUTOR_POOL
from lib.pipeline_store import (
    PIPELINE_DIR,
    PRIORITY_ORDER as _PRIORITY_ORDER,
    VALID_PRIORITIES as _VALID_PRIORITIES,
    DEFAULT_TIMEOUT as _DEFAULT_TIMEOUT,
    now_iso as _now_iso,
    load_pipeline as _load,
    save_pipeline as _save,
)

PIPELINE_DIR.mkdir(parents=True, exist_ok=True)


def _generate_id() -> str:
    return f"pipe_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


def pipeline_run(
    topic: str,
    agents: list[str] = None,
    profile: str = "standard",
    priority: str = "normal",
    model_override: str = None,
    timeout_seconds: int = _DEFAULT_TIMEOUT,
) -> dict:
    """Ejecuta un pipeline. Crea el run y devuelve su ID."""
    if agents is None:
        agents = ["aletheia", "kratos", "kosmos", "metis"]
    if isinstance(agents, list) and len(agents) == 0:
        return {"error": "agents list cannot be empty. Provide at least one agent."}

    if priority not in _VALID_PRIORITIES:
        return {"error": f"Invalid priority '{priority}'. Valid: critical, high, normal, low"}

    pipeline_id = _generate_id()
    now = _now_iso()

    nodes = {}
    for agent in agents:
        nodes[agent] = {
            "node_id": agent,
            "state": "pending",
            "started_at": None,
            "completed_at": None,
            "elapsed_ms": 0.0,
            "attempt": 0,
            "max_retries": 3,
            "timeout_seconds": timeout_seconds,
            "error": None,
            "result": None,
            "model_used": model_override,
            "cost_usd": 0.0,
        }

    data = {
        "id": pipeline_id,
        "topic": topic,
        "profile": profile,
        "priority": priority,
        "model_override": model_override,
        "state": "queued",
        "created_at": now,
        "started_at": None,
        "completed_at": None,
        "elapsed_ms": 0.0,
        "nodes": nodes,
        "total_nodes": len(nodes),
        "completed_nodes": 0,
        "failed_nodes": 0,
        "total_cost_usd": 0.0,
        "total_tokens": 0,
        "error": None,
    }

    _save(pipeline_id, data)
    EventBus.publish("pipeline_update", {
        "pipeline_id": pipeline_id,
        "state": "queued",
        "topic": topic,
        "priority": priority,
        "timestamp": _now_iso(),
    })
    return {"pipeline_id": pipeline_id, "state": "queued", "nodes": len(nodes), "priority": priority}


def pipeline_status(pipeline_id: str) -> dict:
    """Devuelve el estado actual de un pipeline."""
    data = _load(pipeline_id)
    if data is None:
        return {"error": f"Pipeline {pipeline_id} not found", "status": "unknown"}
    return {
        "pipeline_id": data["id"],
        "topic": data["topic"],
        "state": data["state"],
        "profile": data["profile"],
        "elapsed_ms": data["elapsed_ms"],
        "total_nodes": data["total_nodes"],
        "completed_nodes": data["completed_nodes"],
        "failed_nodes": data["failed_nodes"],
        "total_cost_usd": data["total_cost_usd"],
        "error": data["error"],
        "created_at": data["created_at"],
        "node_states": {
            nid: n["state"] for nid, n in data["nodes"].items()
        },
    }


def pipeline_cancel(pipeline_id: str) -> dict:
    """Cancela un pipeline en ejecución."""
    data = _load(pipeline_id)
    if data is None:
        return {"error": f"Pipeline {pipeline_id} not found"}
    if data["state"] in ("completed", "failed", "cancelled"):
        return {
            "pipeline_id": pipeline_id,
            "state": data["state"],
            "msg": f"Cannot cancel: pipeline is already {data['state']}",
        }

    data["state"] = "cancelled"
    data["completed_at"] = _now_iso()
    _save(pipeline_id, data)

    # Publish cancellation events for each node
    for nid in data.get("nodes", {}):
        EventBus.publish("node_update", {
            "pipeline_id": pipeline_id,
            "node_id": nid,
            "state": "cancelled",
            "timestamp": _now_iso(),
        })
    EventBus.publish("pipeline_update", {
        "pipeline_id": pipeline_id,
        "state": "cancelled",
        "timestamp": _now_iso(),
    })

    return {"pipeline_id": pipeline_id, "state": "cancelled", "msg": "Pipeline cancelled"}


def pipeline_list(limit: int = 10, state: str = None, sort_by_priority: bool = True) -> dict:
    """Lista pipelines recientes, opcionalmente filtrados por estado.

    Si sort_by_priority=True (default), critical primero → low último.
    """
    files = sorted(PIPELINE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    results = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if state and data.get("state") != state:
            continue
        results.append({
            "pipeline_id": data["id"],
            "topic": data["topic"],
            "state": data["state"],
            "priority": data.get("priority", "normal"),
            "profile": data.get("profile", "standard"),
            "total_nodes": data["total_nodes"],
            "completed_nodes": data["completed_nodes"],
            "total_cost_usd": data["total_cost_usd"],
            "created_at": data["created_at"],
        })

    if sort_by_priority:
        results.sort(key=lambda r: _PRIORITY_ORDER.get(r.get("priority", "normal"), 99))

    return {"pipelines": results[:limit], "total": len(results)}


# ── CLI entry point ────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: py -3 mcp_pipeline.py <run|status|cancel|list> [args...]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "run" and len(sys.argv) >= 3:
        agents = sys.argv[3].split(",") if len(sys.argv) > 3 else ["aletheia", "kratos"]
        result = pipeline_run(sys.argv[2], agents)
    elif cmd == "status" and len(sys.argv) >= 3:
        result = pipeline_status(sys.argv[2])
    elif cmd == "cancel" and len(sys.argv) >= 3:
        result = pipeline_cancel(sys.argv[2])
    elif cmd == "list":
        result = pipeline_list()
    else:
        print(f"Unknown command or missing args: {cmd}")
        sys.exit(1)

    print(json.dumps(result, indent=2, default=str))


def _update_node(pipeline_id: str, node_id: str, **updates) -> dict:
    """Actualiza el estado de un nodo en un pipeline."""
    data = _load(pipeline_id)
    if data is None:
        return {"error": f"Pipeline {pipeline_id} not found"}
    if node_id not in data["nodes"]:
        return {"error": f"Node {node_id} not found in pipeline"}

    node = data["nodes"][node_id]
    for k, v in updates.items():
        node[k] = v

    data["completed_nodes"] = sum(1 for n in data["nodes"].values() if n["state"] == "completed")
    data["failed_nodes"] = sum(1 for n in data["nodes"].values() if n["state"] in ("failed", "timeout"))
    data["total_cost_usd"] = sum(n.get("cost_usd", 0.0) for n in data["nodes"].values())
    _save(pipeline_id, data)
    return {"pipeline_id": pipeline_id, "node_id": node_id, "state": node["state"]}


def _process_node(pipeline_id: str, node_id: str, mock_delay: float = 0.0) -> dict:
    """Procesa un nodo con timeout y retry automático (exponential backoff).

    Args:
        pipeline_id: ID del pipeline.
        node_id: ID del nodo a procesar.
        mock_delay: Simula latencia de procesamiento (segundos). Si excede
                    timeout_seconds del nodo, se marca como timeout.

    Returns:
        Dict con resultado del procesamiento.
    """
    data = _load(pipeline_id)
    if data is None:
        return {"error": f"Pipeline {pipeline_id} not found"}
    if node_id not in data["nodes"]:
        return {"error": f"Node {node_id} not found"}

    node = data["nodes"][node_id]
    max_retries = node.get("max_retries", 3)
    timeout_seconds = node.get("timeout_seconds", _DEFAULT_TIMEOUT)

    node["started_at"] = _now_iso()
    node["state"] = "running"
    _save(pipeline_id, data)

    for attempt in range(max_retries + 1):
        node["attempt"] = attempt + 1
        _save(pipeline_id, data)

        # --- Timeout check (mock) ---
        if mock_delay > timeout_seconds:
            node["state"] = "timeout"
            node["error"] = f"Timeout after {mock_delay:.1f}s (limit: {timeout_seconds}s)"
            node["completed_at"] = _now_iso()
            _save(pipeline_id, data)
            return {
                "pipeline_id": pipeline_id,
                "node_id": node_id,
                "state": "timeout",
                "error": node["error"],
                "attempts": node["attempt"],
            }

        # Simulate processing (mock)
        import time as _time
        _time.sleep(min(mock_delay, 0.05))  # cap for real execution

        # --- Simulate random failure (for retry testing) ---
        # In real usage this would call the actual agent logic.
        # For mock: if mock_delay > 0, ~30% chance of failure per attempt.
        failed = False
        if mock_delay > 0 and random.random() < 0.3:
            failed = True

        if not failed:
            node["state"] = "completed"
            node["completed_at"] = _now_iso()
            node["result"] = f"OK (attempt {attempt + 1})"
            _save(pipeline_id, data)
            return {
                "pipeline_id": pipeline_id,
                "node_id": node_id,
                "state": "completed",
                "attempts": node["attempt"],
            }

        # --- Retry with exponential backoff ---
        if attempt < max_retries:
            wait = 2 ** attempt  # 1s, 2s, 4s
            node["error"] = f"Attempt {attempt + 1} failed, retrying in {wait}s..."
            _save(pipeline_id, data)
            _time.sleep(min(wait, 1.0))  # cap wait for tests
        else:
            node["state"] = "failed"
            node["error"] = f"All {max_retries + 1} attempts failed"
            node["completed_at"] = _now_iso()
            _save(pipeline_id, data)
            return {
                "pipeline_id": pipeline_id,
                "node_id": node_id,
                "state": "failed",
                "error": node["error"],
                "attempts": node["attempt"],
            }

    return {"error": "Unexpected exit from _process_node"}  # pragma: no cover


def _execute_node_task(pipeline_id: str, node_id: str, mock_delay: float = 0.0) -> dict:
    """Process a single node task WITHOUT pipeline-level save (thread-safe).

    Args:
        pipeline_id: ID del pipeline.
        node_id: ID del nodo a procesar.
        mock_delay: Simula latencia de procesamiento (segundos).

    Returns:
        Dict with final node state (no side effects on pipeline store).
    """
    data = _load(pipeline_id)
    if data is None:
        return {"node_id": node_id, "state": "failed", "error": "Pipeline not found"}

    node_template = data["nodes"].get(node_id, {})
    max_retries = node_template.get("max_retries", 3)
    timeout_seconds = node_template.get("timeout_seconds", _DEFAULT_TIMEOUT)

    # Work on a mutable copy — no shared state
    node = {
        "node_id": node_id,
        "state": "running",
        "started_at": _now_iso(),
        "completed_at": None,
        "elapsed_ms": 0.0,
        "attempt": 0,
        "max_retries": max_retries,
        "timeout_seconds": timeout_seconds,
        "error": None,
        "result": None,
    }
    _start = time.monotonic()
    EventBus.publish("node_update", {
        "pipeline_id": pipeline_id,
        "node_id": node_id,
        "state": "running",
        "timestamp": _now_iso(),
    })

    for attempt in range(max_retries + 1):
        node["attempt"] = attempt + 1

        # ── Timeout check ──
        if mock_delay > timeout_seconds:
            node["state"] = "timeout"
            node["error"] = f"Timeout after {mock_delay:.1f}s (limit: {timeout_seconds}s)"
            node["completed_at"] = _now_iso()
            node["elapsed_ms"] = (time.monotonic() - _start) * 1000
            EventBus.publish("node_update", {
                "pipeline_id": pipeline_id, "node_id": node_id,
                "state": "timeout", "error": node["error"],
                "timestamp": _now_iso(),
            })
            return node

        # Simulate processing
        time.sleep(min(mock_delay, 0.05))

        # Simulate random failure (30 % chance when mock_delay > 0)
        failed = bool(mock_delay > 0 and random.random() < 0.3)

        if not failed:
            node["state"] = "completed"
            node["completed_at"] = _now_iso()
            node["result"] = f"OK (attempt {attempt + 1})"
            node["elapsed_ms"] = (time.monotonic() - _start) * 1000
            EventBus.publish("node_update", {
                "pipeline_id": pipeline_id, "node_id": node_id,
                "state": "completed", "elapsed_ms": node["elapsed_ms"],
                "timestamp": _now_iso(),
            })
            return node

        # ── Retry with exponential backoff ──
        if attempt < max_retries:
            wait = 2 ** attempt  # 1s, 2s, 4s
            node["error"] = f"Attempt {attempt + 1} failed, retrying in {wait}s..."
            time.sleep(min(wait, 1.0))
        else:
            node["state"] = "failed"
            node["error"] = f"All {max_retries + 1} attempts failed"
            node["completed_at"] = _now_iso()
            node["elapsed_ms"] = (time.monotonic() - _start) * 1000
            EventBus.publish("node_update", {
                "pipeline_id": pipeline_id, "node_id": node_id,
                "state": "failed", "error": node["error"],
                "timestamp": _now_iso(),
            })
            return node

    return {"node_id": node_id, "state": "failed", "error": "Unexpected exit"}


def pipeline_execute(pipeline_id: str, mock_delay: float = 0.0) -> dict:
    """Execute all nodes in a pipeline using ParallelExecutor.

    Pipeline:
        1. Load pipeline from store
        2. Create tasks for each node (one per agent)
        3. Execute with ParallelExecutor.execute_all()
        4. Merge node results back into pipeline store
        5. Mark pipeline as "completed" or "failed"

    Args:
        pipeline_id: ID del pipeline a ejecutar.
        mock_delay: Latencia simulada por nodo (segundos).

    Returns:
        Dict con resumen de ejecución.
    """
    data = _load(pipeline_id)
    if data is None:
        return {"error": f"Pipeline {pipeline_id} not found"}
    if data["state"] in ("completed", "failed", "cancelled"):
        return {"pipeline_id": pipeline_id, "state": data["state"], "msg": "Already terminal"}

    # Mark pipeline as running
    data["state"] = "running"
    data["started_at"] = _now_iso()
    _save(pipeline_id, data)
    _LOG.info("Pipeline %s execution started (%d nodes)", pipeline_id, len(data["nodes"]))
    EventBus.publish("pipeline_update", {
        "pipeline_id": pipeline_id,
        "state": "running",
        "topic": data.get("topic", ""),
        "total_nodes": len(data["nodes"]),
        "timestamp": _now_iso(),
    })

    # Build one task per node
    tasks = []
    for node_id in data["nodes"]:
        node_conf = data["nodes"][node_id]
        tasks.append({
            "id": node_id,
            "fn": _execute_node_task,
            "args": (pipeline_id, node_id),
            "kwargs": {"mock_delay": mock_delay},
            "timeout": node_conf.get("timeout_seconds", _DEFAULT_TIMEOUT),
        })

    # Execute in parallel (shared pool)
    executor = ParallelExecutor(max_concurrent=len(tasks))
    results = executor.execute_all(tasks, executor=_get_executor())

    # Merge results into fresh pipeline state
    data = _load(pipeline_id)
    if data is None:
        return {"error": f"Pipeline {pipeline_id} lost during execution"}

    completed = 0
    failed = 0

    for r in results:
        nid = r.task_id
        if nid not in data["nodes"]:
            continue

        if r.state == TaskState.COMPLETED and isinstance(r.result, dict):
            data["nodes"][nid].update(r.result)
            if r.result.get("state") == "completed":
                completed += 1
            else:
                failed += 1
        else:
            # Executor-level failure (crash / timeout)
            data["nodes"][nid]["state"] = r.state.value
            data["nodes"][nid]["error"] = r.error or "Executor-level failure"
            data["nodes"][nid]["completed_at"] = _now_iso()
            failed += 1

    data["completed_nodes"] = completed
    data["failed_nodes"] = failed
    data["total_cost_usd"] = sum(
        n.get("cost_usd", 0.0) for n in data["nodes"].values()
    )
    data["state"] = "completed" if failed == 0 else "failed"
    data["completed_at"] = _now_iso()
    _save(pipeline_id, data)
    _LOG.info("Pipeline %s completed: state=%s, completed=%d, failed=%d",
              pipeline_id, data["state"], completed, failed)
    EventBus.publish("pipeline_update", {
        "pipeline_id": pipeline_id,
        "state": data["state"],
        "completed_nodes": completed,
        "failed_nodes": failed,
        "total_cost_usd": data["total_cost_usd"],
        "timestamp": _now_iso(),
    })

    return {
        "pipeline_id": pipeline_id,
        "state": data["state"],
        "completed": completed,
        "failed": failed,
        "total": len(results),
        "node_results": {r.task_id: r.state.value for r in results},
    }
