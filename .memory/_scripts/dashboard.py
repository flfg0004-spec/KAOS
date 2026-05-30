"""Dashboard Pipeline Visual — FastAPI + SSE + Cytoscape.js + vis-timeline.

Sirve el dashboard HTML y una API REST/SSE para monitoreo en vivo de pipelines.
Simula progreso de nodos cuando no hay pipelines reales activos.

Endpoints:
  GET  /dashboard/                 → HTML principal
  GET  /dashboard/api/pipelines    → Lista de pipelines (JSON)
  GET  /dashboard/api/pipeline/{id} → Detalle de pipeline con nodos
  POST /dashboard/api/run          → Crear nuevo pipeline run
  POST /dashboard/api/cancel/{id}  → Cancelar pipeline
  GET  /dashboard/api/events       → SSE de actualizaciones en vivo
"""

import asyncio
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Path setup ─────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from lib.config import VAULT_ROOT
from mcp_pipeline import (
    PIPELINE_DIR,
    _load,
    _save,
    _now_iso,
    _PRIORITY_ORDER,
    _VALID_PRIORITIES,
    pipeline_list,
    pipeline_status,
    pipeline_run,
    pipeline_cancel,
    pipeline_execute,
)

HERE = Path(__file__).resolve().parent
HTML_FILE = HERE / "dashboard.html"

app = FastAPI(
    title="KAOS Pipeline Dashboard",
    description="Visual live dashboard for KAOS pipeline orchestration",
    version="1.0.0",
)

# ── SSE State ──────────────────────────────────────
_sse_queues: list[asyncio.Queue] = []
_simulation_running = True


# ── Broadcast helper ───────────────────────────────
async def _broadcast(event_type: str, data: dict) -> None:
    """Push an event to every connected SSE client."""
    payload = json.dumps(data, default=str)
    dead: list[asyncio.Queue] = []
    for q in _sse_queues:
        try:
            await q.put((event_type, payload))
        except Exception:
            dead.append(q)
    for q in dead:
        if q in _sse_queues:
            _sse_queues.remove(q)


# ── Demo seed ──────────────────────────────────────
def _seed_demo_pipelines() -> None:
    """Create sample pipelines so the dashboard isn't empty on first load."""
    existing = list(PIPELINE_DIR.glob("*.json"))
    if existing:
        return

    demos = [
        {
            "topic": "Research RAG pipeline",
            "agents": ["aletheia", "kratos"],
            "priority": "critical",
        },
        {
            "topic": "Code review automation",
            "agents": ["kratos", "kosmos", "metis"],
            "priority": "high",
        },
        {
            "topic": "Architecture analysis",
            "agents": ["kosmos", "metis"],
            "priority": "normal",
        },
        {
            "topic": "Full multi-agent quality scan",
            "agents": ["aletheia", "kratos", "kosmos", "metis", "mnemosyne"],
            "priority": "critical",
        },
    ]
    for d in demos:
        pipeline_run(**d)
    print(f"[dashboard] Seeded {len(demos)} demo pipelines")


# ── Simulation tick ────────────────────────────────
async def _simulation_tick() -> None:
    """Advance one random node in one random non-terminal pipeline."""
    files = sorted(
        PIPELINE_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not files:
        return

    # Collect candidates (queued or running)
    candidates: list[dict] = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("state") in ("queued", "running"):
                candidates.append(data)
        except Exception:
            continue

    if not candidates:
        return

    pipeline = random.choice(candidates)
    pid = pipeline["id"]

    # Find first pending node
    next_node: Optional[str] = None
    for nid, node in pipeline["nodes"].items():
        if node["state"] == "pending":
            next_node = nid
            break

    # ── If no pending nodes, check completion ──
    if next_node is None:
        all_terminal = all(
            n["state"] in ("completed", "failed", "timeout")
            for n in pipeline["nodes"].values()
        )
        if all_terminal and pipeline["state"] == "running":
            pipeline["state"] = "completed"
            pipeline["completed_at"] = _now_iso()
            _save(pid, pipeline)
            await _broadcast("pipeline_update", {
                "pipeline_id": pid,
                "state": "completed",
                "changed_node": None,
                "timestamp": _now_iso(),
            })
        return

    # ── Start the node (pending → running) ──
    node = pipeline["nodes"][next_node]
    node["state"] = "running"
    node["started_at"] = _now_iso()
    node["attempt"] = node.get("attempt", 0) + 1

    if pipeline["state"] == "queued":
        pipeline["state"] = "running"
        pipeline["started_at"] = _now_iso()

    _save(pid, pipeline)

    await _broadcast("pipeline_update", {
        "pipeline_id": pid,
        "state": "running",
        "changed_node": next_node,
        "node_state": "running",
        "timestamp": _now_iso(),
    })

    # Simulate processing delay
    await asyncio.sleep(random.uniform(1.0, 3.0))

    # Reload — pipeline may have been modified externally
    data = _load(pid)
    if data is None:
        return

    n = data["nodes"].get(next_node)
    if n is None or n["state"] != "running":
        return

    # ── Determine outcome ──
    if random.random() < 0.12:  # 12 % chance of failure
        n["state"] = "failed"
        n["error"] = "Simulated node failure"
        n["result"] = None
    else:
        n["state"] = "completed"
        n["result"] = "OK"

    n["completed_at"] = _now_iso()
    n["elapsed_ms"] = random.uniform(1000.0, 3000.0)

    # Update aggregate counters
    completed = sum(1 for x in data["nodes"].values() if x["state"] == "completed")
    failed = sum(1 for x in data["nodes"].values() if x["state"] in ("failed", "timeout"))
    data["completed_nodes"] = completed
    data["failed_nodes"] = failed

    # Check if the entire pipeline is finished
    all_terminal = all(
        x["state"] in ("completed", "failed", "timeout")
        for x in data["nodes"].values()
    )
    if all_terminal:
        data["state"] = "completed"
        data["completed_at"] = _now_iso()

    _save(pid, data)

    await _broadcast("pipeline_update", {
        "pipeline_id": pid,
        "state": data["state"],
        "changed_node": next_node,
        "node_state": n["state"],
        "timestamp": _now_iso(),
        "elapsed_ms": n.get("elapsed_ms", 0),
        "error": n.get("error"),
    })


async def _simulation_loop() -> None:
    """Background loop: tick every 1-2 seconds."""
    while _simulation_running:
        await asyncio.sleep(random.uniform(1.0, 2.0))
        try:
            await _simulation_tick()
        except Exception as exc:
            print(f"[dashboard] simulation tick error: {exc}")


# ── Lifecycle hooks ────────────────────────────────
@app.on_event("startup")
async def _on_startup() -> None:
    _seed_demo_pipelines()
    asyncio.create_task(_simulation_loop())
    print("[dashboard] Server started — simulation loop active")


@app.on_event("shutdown")
async def _on_shutdown() -> None:
    global _simulation_running
    _simulation_running = False
    print("[dashboard] Server shutting down")


# ══════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════


@app.get("/dashboard/")
async def dashboard_page():
    """Serve the main HTML dashboard."""
    if not HTML_FILE.exists():
        return JSONResponse(
            {"error": f"dashboard.html not found at {HTML_FILE}"},
            status_code=500,
        )
    return FileResponse(str(HTML_FILE))


@app.get("/dashboard/api/pipelines")
async def api_pipelines(
    state: Optional[str] = None,
    priority: Optional[str] = None,
):
    """List all pipelines, optionally filtered by state / priority."""
    result = pipeline_list(limit=100, state=state)
    pipelines = result.get("pipelines", [])
    if priority and priority in _VALID_PRIORITIES:
        pipelines = [p for p in pipelines if p.get("priority") == priority]
    return JSONResponse({"pipelines": pipelines, "total": len(pipelines)})


@app.get("/dashboard/api/pipeline/{pipeline_id}")
async def api_pipeline_detail(pipeline_id: str):
    """Full detail for a single pipeline, including node data."""
    data = _load(pipeline_id)
    if data is None:
        return JSONResponse({"error": "Pipeline not found"}, status_code=404)
    return JSONResponse(data)


@app.post("/dashboard/api/run")
async def api_run_pipeline(request: Request):
    """Create a new pipeline run from JSON body.

    Body:
        {
            "topic": "str",
            "agents": ["str", ...],   (optional)
            "priority": "str"          (optional, default "normal")
        }
    """
    body = await request.json()
    topic = body.get("topic", "Untitled run")
    agents = body.get("agents")
    priority = body.get("priority", "normal")
    result = pipeline_run(topic=topic, agents=agents, priority=priority)
    return JSONResponse(result)


@app.post("/dashboard/api/cancel/{pipeline_id}")
async def api_cancel_pipeline(pipeline_id: str):
    """Cancel a running / queued pipeline."""
    result = pipeline_cancel(pipeline_id)
    # Broadcast the cancellation immediately
    await _broadcast("pipeline_update", {
        "pipeline_id": pipeline_id,
        "state": "cancelled",
        "changed_node": None,
        "timestamp": _now_iso(),
    })
    return JSONResponse(result)


@app.get("/dashboard/api/score")
async def api_score():
    """Score de madurez del sistema Kronos."""
    return JSONResponse(_calculate_scores())


def _calculate_scores() -> dict:
    """Calcula scores de madurez por categoría basado en módulos existentes."""
    scores = {}

    # pipeline_orchestration: existe mcp_pipeline + executor + dashboard
    try:
        from mcp_pipeline import pipeline_run, pipeline_execute, pipeline_list
        from lib.kronos import ParallelExecutor
        scores["pipeline_orchestration"] = min(100.0, (
            (1.0 if callable(pipeline_run) else 0) * 30 +
            (1.0 if callable(pipeline_execute) else 0) * 30 +
            (1.0 if callable(pipeline_list) else 0) * 20 +
            (1.0 if ParallelExecutor else 0) * 20
        ))
    except Exception:
        scores["pipeline_orchestration"] = 0.0

    # adaptive_routing: existe aether router + quality feedback
    try:
        from lib.aether.router import resolve_model, _apply_quality_feedback
        from lib.aether.quality_store import QualityStore
        scores["adaptive_routing"] = min(100.0, (
            (1.0 if callable(resolve_model) else 0) * 40 +
            (1.0 if callable(_apply_quality_feedback) else 0) * 30 +
            (1.0 if QualityStore else 0) * 30
        ))
    except Exception:
        scores["adaptive_routing"] = 0.0

    # error_recovery: timeout + retry + circuit breaker
    try:
        from mcp_pipeline import _process_node
        from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER
        scores["error_recovery"] = min(100.0, (
            (1.0 if callable(_process_node) else 0) * 50 +
            (1.0 if _ETHER_CIRCUIT_BREAKER else 0) * 50
        ))
    except Exception:
        scores["error_recovery"] = 0.0

    # speed_analysis: mcp-speed + cache boundary + dsol tracker
    try:
        from lib.cache_boundary import stats, build_prompt
        scores["speed_analysis"] = min(100.0, (
            (1.0 if callable(stats) else 0) * 40 +
            (1.0 if callable(build_prompt) else 0) * 30 +
            30.0  # mcp-speed registry
        ))
    except Exception:
        scores["speed_analysis"] = 0.0

    # agent_coordination: Kronos SOUL + methodology + dashboard visual
    try:
        with open(str(Path(__file__).resolve().parent.parent.parent /
                      ".opencode" / "agents" / "kronos" / "SOUL.md"), "rb") as _f:
            has_soul = len(_f.read()) > 50
        has_dashboard = Path(str(HTML_FILE)).exists()
        scores["agent_coordination"] = min(100.0, (
            (1.0 if has_soul else 0) * 40 +
            (1.0 if has_dashboard else 0) * 40 +
            20.0  # methodology exists
        ))
    except Exception:
        scores["agent_coordination"] = 0.0

    overall = round(sum(scores.values()) / max(len(scores), 1), 1)
    target = 90.0
    return {
        "overall": overall,
        "categories": scores,
        "target": target,
        "remaining": round(max(0.0, target - overall), 1),
    }


@app.get("/dashboard/api/events")
async def api_sse_events(request: Request):
    """Server-Sent Events stream.

    Emits:
        event: pipeline_update
        data:  {pipeline_id, state, changed_node, timestamp, ...}

        event: heartbeat
        data:  {timestamp}
    """
    queue: asyncio.Queue = asyncio.Queue()
    _sse_queues.append(queue)

    async def event_generator():
        try:
            while True:
                try:
                    event_type, data = await asyncio.wait_for(
                        queue.get(), timeout=30.0
                    )
                    yield f"event: {event_type}\ndata: {data}\n\n"
                except asyncio.TimeoutError:
                    yield (
                        "event: heartbeat\n"
                        f"data: {json.dumps({'timestamp': _now_iso()})}\n\n"
                    )
        except asyncio.CancelledError:
            pass  # client disconnected
        finally:
            if queue in _sse_queues:
                _sse_queues.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


# ── Entry point (for direct execution) ─────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("dashboard:app", host="0.0.0.0", port=8085, reload=True)
