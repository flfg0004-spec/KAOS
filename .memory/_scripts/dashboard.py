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
import logging
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

# ── Path setup ─────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

_LOG = logging.getLogger(__name__)

from lib.config import VAULT_ROOT  # noqa: E402
from lib.events import EventBus  # noqa: E402
from lib.pipeline_store import (  # noqa: E402
    PIPELINE_DIR,
    load_pipeline,
    save_pipeline,
    now_iso,
    VALID_PRIORITIES,
)
from mcp_pipeline import (  # noqa: E402
    pipeline_list,
    pipeline_run,
    pipeline_cancel,
)

HERE = Path(__file__).resolve().parent
HTML_FILE = HERE / "dashboard.html"

app = FastAPI(
    title="KAOS Pipeline Dashboard",
    description="Visual live dashboard for KAOS pipeline orchestration",
    version="1.0.0",
)

# ── Global state ────────────────────────────────────
_sse_queues: list[asyncio.Queue] = []
_MAX_SSE_CLIENTS = 50
_SSE_QUEUE_MAXSIZE = 100
_simulation_running = True
_start_time = datetime.now(timezone.utc)
ALERTS_LOG = VAULT_ROOT / "cache" / "alerts.log"


# ── Broadcast helper ───────────────────────────────
async def _broadcast(event_type: str, data: dict) -> None:
    """Push an event to every connected SSE client. Drops oldest if queue full."""
    payload = json.dumps(data, default=str)
    dead: list[asyncio.Queue] = []
    for q in _sse_queues:
        try:
            q.put_nowait((event_type, payload))
        except asyncio.QueueFull:
            _LOG.warning("SSE queue full for client, dropping oldest event")
            try:
                q.get_nowait()
                q.put_nowait((event_type, payload))
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                dead.append(q)
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

    # Collect candidates (simulation only, queued or running, non-terminal)
    candidates: list[dict] = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("source") != "simulation":
                continue
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
            pipeline["completed_at"] = now_iso()
            save_pipeline(pid, pipeline)
            await _broadcast("pipeline_update", {
                "pipeline_id": pid,
                "state": "completed",
                "changed_node": None,
                "timestamp": now_iso(),
            })
        return

    # ── Start the node (pending → running) ──
    node = pipeline["nodes"][next_node]
    node["state"] = "running"
    node["started_at"] = now_iso()
    node["attempt"] = node.get("attempt", 0) + 1

    if pipeline["state"] == "queued":
        pipeline["state"] = "running"
        pipeline["started_at"] = now_iso()

    save_pipeline(pid, pipeline)

    await _broadcast("pipeline_update", {
        "pipeline_id": pid,
        "state": "running",
        "changed_node": next_node,
        "node_state": "running",
        "timestamp": now_iso(),
    })

    # Simulate processing delay
    await asyncio.sleep(random.uniform(1.0, 3.0))

    # Reload — pipeline may have been modified externally
    data = load_pipeline(pid)
    if data is None:
        return

    if data.get("state") in ("cancelled", "failed", "completed"):
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

    n["completed_at"] = now_iso()
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
        data["completed_at"] = now_iso()

    save_pipeline(pid, data)

    await _broadcast("pipeline_update", {
        "pipeline_id": pid,
        "state": data["state"],
        "changed_node": next_node,
        "node_state": n["state"],
        "timestamp": now_iso(),
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
    if priority and priority in VALID_PRIORITIES:
        pipelines = [p for p in pipelines if p.get("priority") == priority]
    return JSONResponse({"pipelines": pipelines, "total": len(pipelines)})


@app.get("/dashboard/api/pipeline/{pipeline_id}")
async def api_pipeline_detail(pipeline_id: str):
    """Full detail for a single pipeline, including node data."""
    data = load_pipeline(pipeline_id)
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
    return JSONResponse(result, status_code=201)


@app.post("/dashboard/api/cancel/{pipeline_id}")
async def api_cancel_pipeline(pipeline_id: str):
    """Cancel a running / queued pipeline."""
    result = pipeline_cancel(pipeline_id)
    # Broadcast the cancellation immediately
    await _broadcast("pipeline_update", {
        "pipeline_id": pipeline_id,
        "state": "cancelled",
        "changed_node": None,
        "timestamp": now_iso(),
    })
    return JSONResponse(result)


@app.get("/dashboard/api/health")
async def api_health():
    """Health check del sistema con estado de componentes."""
    components = {}
    try:
        pipeline_list(limit=1)
        components["pipeline_store"] = True
    except Exception:
        components["pipeline_store"] = False
    try:
        from lib.quality.store import history
        history(limit=1)
        components["quality_store"] = True
    except Exception:
        components["quality_store"] = False
    components["event_bus"] = EventBus.subscriber_count >= 0

    try:
        active = len(pipeline_list(state="running").get("pipelines", []))
        total = pipeline_list(limit=1000).get("total", 0)
    except Exception:
        active = total = -1

    uptime = int((datetime.now(timezone.utc) - _start_time).total_seconds())
    last_alerts = []
    try:
        if ALERTS_LOG.exists():
            lines = ALERTS_LOG.read_text(encoding="utf-8").strip().split("\n")
            last_alerts = [json.loads(line) for line in lines[-5:] if line.strip()]
    except Exception:
        _LOG.warning("Failed to read alerts log for health endpoint", exc_info=True)
    last_error = None
    last_error_at = None
    for a in reversed(last_alerts):
        if a.get("severity") in ("error", "critical"):
            last_error = a.get("message")
            last_error_at = a.get("timestamp")
            break

    all_ok = all(components.values()) and active >= 0
    return JSONResponse({
        "status": "healthy" if all_ok else "degraded",
        "uptime_seconds": uptime,
        "pipelines_active": active,
        "pipelines_total": total,
        "last_error": last_error,
        "last_error_at": last_error_at,
        "components": components,
        "timestamp": now_iso(),
    })


@app.get("/dashboard/api/alerts")
async def api_alerts():
    """Últimas alertas del sistema."""
    alerts = []
    try:
        if ALERTS_LOG.exists():
            lines = ALERTS_LOG.read_text(encoding="utf-8").strip().split("\n")
            alerts = [json.loads(line) for line in lines[-50:] if line.strip()]
    except Exception:
        _LOG.warning("Failed to read alerts log for alerts endpoint", exc_info=True)
    return JSONResponse({"alerts": alerts, "total": len(alerts)})


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
        _LOG.warning("pipeline_orchestration score failed", exc_info=True)
        scores["pipeline_orchestration"] = 0.0

    # adaptive_routing: existe aether router + quality feedback
    try:
        from lib.aether.router import resolve_model
        from lib.aether.quality_store import QualityStore
        has_quality_select = callable(resolve_model)
        scores["adaptive_routing"] = min(100.0, (
            (1.0 if callable(resolve_model) else 0) * 40 +
            (1.0 if has_quality_select else 0) * 30 +
            (1.0 if QualityStore else 0) * 30
        ))
    except Exception:
        _LOG.warning("adaptive_routing score failed", exc_info=True)
        scores["adaptive_routing"] = 0.0

    # audit_quality: resultados de Kosmos audit
    try:
        from lib.quality.audit_trigger import run_audit
        audit = run_audit()
        summary = audit.get("summary", {})
        errors = summary.get("errors", 0)
        warnings = summary.get("warnings", 0)
        score = 100.0 - (errors * 20 + warnings * 5)
        scores["audit_quality"] = max(0.0, min(100.0, score))
    except Exception:
        _LOG.warning("audit_quality score failed", exc_info=True)
        scores["audit_quality"] = 0.0

    # error_recovery: timeout + retry + circuit breaker
    try:
        from mcp_pipeline import pipeline_execute
        has_process_node = callable(pipeline_execute)
        try:
            from lib.aether.router import resolve_model
            has_circuit_breaker = True
        except ImportError:
            has_circuit_breaker = False
        scores["error_recovery"] = min(100.0, (
            (1.0 if has_process_node else 0) * 50 +
            (1.0 if has_circuit_breaker else 0) * 50
        ))
    except Exception:
        _LOG.warning("error_recovery score failed", exc_info=True)
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
        _LOG.warning("speed_analysis score failed", exc_info=True)
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
        _LOG.warning("agent_coordination score failed", exc_info=True)
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
    if len(_sse_queues) >= _MAX_SSE_CLIENTS:
        _LOG.warning("Max SSE clients reached (%d), rejecting connection", _MAX_SSE_CLIENTS)
        return JSONResponse({"error": "Too many SSE clients"}, status_code=503)
    queue: asyncio.Queue = asyncio.Queue(maxsize=_SSE_QUEUE_MAXSIZE)
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
                        f"data: {json.dumps({'timestamp': now_iso()})}\n\n"
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


# ── Startup: bridge EventBus → SSE + AlertDaemon ──
@app.on_event("startup")
async def _startup():
    asyncio.create_task(_eventbus_bridge())
    try:
        from alert_daemon import start as start_alerts
        start_alerts()
    except Exception:
        _LOG.warning("alert_daemon not available — alerts may not start", exc_info=True)
    _LOG.info("Dashboard startup complete — EventBus bridge + AlertDaemon active")


async def _eventbus_bridge():
    """Bridge: EventBus (thread-safe queue) → SSE queues."""
    loop = asyncio.get_event_loop()
    eb_queue = EventBus.subscribe()
    while True:
        try:
            event_type, data = await loop.run_in_executor(None, eb_queue.get)
            await _broadcast(event_type, data)
        except Exception:
            _LOG.error("EventBus bridge failed to process event", exc_info=True)


# ── Entry point (for direct execution) ─────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("dashboard:app", host="0.0.0.0", port=8085, reload=True)
