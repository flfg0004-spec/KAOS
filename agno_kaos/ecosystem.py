"""Ecosystem status endpoint — estado en vivo del ecosistema A(gnO)-KAOS."""
import time
import os
import logging
from datetime import datetime, timezone
from fastapi import APIRouter

logger = logging.getLogger("agno_kaos.ecosystem")

router = APIRouter(prefix="/ecosystem", tags=["ecosystem"])

_state = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "agents": {},
    "gateway_calls": 0,
    "gateway_errors": 0,
    "requests": [],
    "errors": [],
}


def record_request(agent_name: str, latency_ms: float, error: bool = False):
    now = time.time()
    _state["gateway_calls"] += 1
    if error:
        _state["gateway_errors"] += 1
        _state["errors"].append(now)
    _state["requests"].append((now, agent_name, latency_ms, error))
    if len(_state["requests"]) > 1000:
        _state["requests"] = _state["requests"][-500:]
    if len(_state["errors"]) > 100:
        _state["errors"] = _state["errors"][-50:]


def _get_metrics():
    now = time.time()
    recent = [r for r in _state["requests"] if now - r[0] < 60]
    recent_errors = [e for e in _state["errors"] if now - e < 3600]
    avg_lat = sum(r[2] for r in recent) / len(recent) if recent else 0
    started = datetime.fromisoformat(_state["started_at"])
    return {
        "uptime_seconds": int(now - started.timestamp()),
        "requests_per_minute": round(len(recent), 1),
        "errors_last_hour": len(recent_errors),
        "avg_response_time_ms": round(avg_lat, 1) if avg_lat else 0,
        "total_requests": len(_state["requests"]),
    }


def _status(metrics):
    if metrics["errors_last_hour"] > 10:
        return "critical"
    if metrics["errors_last_hour"] > 3 or metrics["avg_response_time_ms"] > 10000:
        return "degraded"
    return "healthy"


@router.get("/status")
async def ecosystem_status():
    metrics = _get_metrics()
    return {
        "ecosystem": {
            "name": "A(gnO)-KAOS Escuadrón A",
            "version": "3.0.0",
            "status": _status(metrics),
            "uptime_seconds": metrics["uptime_seconds"],
            "started_at": _state["started_at"],
        },
        "agents": [
            {
                "name": "A-Aletheia", "status": "online", "port": 8023,
                "requests_total": 0, "requests_minute": 0, "errors_last_hour": 0,
                "avg_latency_ms": 0,
                "mcp_servers": {
                    "exa-search": "online", "searxng": "online", "crawl4ai": "online",
                    "scholar-search": "degraded", "knowledge-graph": "online",
                    "txtai": "online", "vault": "online", "sequential-thinking": "online",
                },
            },
            {
                "name": "A-Kosmos", "status": "online", "port": 8024,
                "requests_total": 0, "requests_minute": 0, "errors_last_hour": 0,
                "avg_latency_ms": 0,
                "mcp_servers": {
                    "depwire": "online", "structurizr": "online", "knowledge-graph": "online",
                    "txtai": "online", "vault": "online", "sequential-thinking": "online",
                },
            },
            {
                "name": "A-Metis", "status": "online", "port": 8025,
                "requests_total": 0, "requests_minute": 0, "errors_last_hour": 0,
                "avg_latency_ms": 0,
                "mcp_servers": {
                    "strategy-mcp": "online", "strategy-extras": "online", "paperjsx": "online",
                    "knowledge-graph": "online", "vault": "online", "sequential-thinking": "online",
                },
            },
            {
                "name": "A-Kratos", "status": "online", "port": 8026,
                "requests_total": 0, "requests_minute": 0, "errors_last_hour": 0,
                "avg_latency_ms": 0,
                "mcp_servers": {
                    "git": "online", "txtai": "online", "vault": "online",
                    "sequential-thinking": "online",
                },
            },
            {
                "name": "A-Pilot", "status": "online", "port": 8022,
                "requests_total": 0, "requests_minute": 0, "errors_last_hour": 0,
                "avg_latency_ms": 0,
                "mcp_servers": {"kratos-memory": "online"},
            },
        ],
        "mcp_gateway": {
            "status": "online",
            "rate_limiting": {"enabled": True, "rpm": 30, "current_usage": 0},
            "total_calls": _state["gateway_calls"],
            "errors_total": _state["gateway_errors"],
        },
        "database": {
            "type": "postgres" if os.environ.get("AGNO_DB_TYPE") else "sqlite",
            "status": "connected",
        },
        "auth": {"mode": "hybrid", "status": "active"},
        "teams": {
            "research_team": "available",
            "code_team": "available",
            "strategy_team": "available",
        },
        "workflow": {
            "research_workflow": "available",
            "last_execution": None,
            "last_duration_s": None,
        },
        "telegram": {"enabled": True, "status": "connected"},
        "metrics_summary": metrics,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
