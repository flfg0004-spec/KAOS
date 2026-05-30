"""System health metrics — consolidates Aether subsystem state."""
import json
import logging
from datetime import date
from pathlib import Path

_LOG = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent.parent

def get_system_health():
    health = {
        "timestamp": str(date.today()),
        "quality": _get_quality_metrics(),
        "tracker": _get_tracker_metrics(),
        "circuit_breaker": _get_cb_metrics(),
        "audit": _get_audit_results(),
    }
    health["overall_score"] = _compute_score(health)
    return health

def _get_quality_metrics():
    try:
        from lib.aether.quality_store import QualityStore
        qs = QualityStore()
        summary = qs.get_summary()
        return {
            "total_entries": summary.get("total_entries", 0),
            "avg_score": summary.get("avg_score", 0),
            "models_tracked": len(summary.get("per_model", {})),
            "status": "ok",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def _get_tracker_metrics():
    try:
        from lib.aether.tracker import EtherTracker
        t = EtherTracker()
        stats = t.get_stats()
        return {
            "total_calls": stats.get("total_calls", 0),
            "total_cost_usd": round(stats.get("total_cost_usd", 0), 4),
            "total_tokens": stats.get("total_tokens", 0),
            "sessions": stats.get("total_sessions", 0),
            "status": "ok",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def _get_cb_metrics():
    try:
        from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER
        status = _ETHER_CIRCUIT_BREAKER.get_status()
        states = set(s.get("state", "closed") for s in status.values())
        failures = sum(s.get("failures", 0) for s in status.values())
        if "open" in states:
            state = "open"
        elif "half-open" in states:
            state = "half-open"
        else:
            state = "closed"
        return {
            "state": state,
            "failures": failures,
            "available": state == "closed",
            "status": "ok",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def _get_audit_results():
    hooks_dir = BASE / ".vault" / "quality" / "hooks"
    if not hooks_dir.exists():
        return {"status": "no_data", "message": "No audit hooks found"}
    try:
        files = sorted(hooks_dir.glob("*.json"), reverse=True)
        recent = []
        for f in files[:5]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                recent.append({
                    "file": f.name,
                    "timestamp": data.get("timestamp", ""),
                    "summary": data.get("summary", {}),
                })
            except Exception:
                continue
        return {"status": "ok", "recent_audits": recent}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def _compute_score(health):
    score = 50.0
    if health["quality"].get("status") == "ok":
        score += 10
    if health["tracker"].get("status") == "ok":
        score += 10
    if health["circuit_breaker"].get("status") == "ok":
        score += 10
    if health["audit"].get("status") == "ok":
        score += 10
    return min(100.0, score)

if __name__ == "__main__":
    import json
    h = get_system_health()
    print(json.dumps(h, indent=2, default=str))
