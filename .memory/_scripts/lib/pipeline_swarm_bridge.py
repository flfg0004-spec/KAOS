"""Bridge: pipeline → swarm workers vía JSON-RPC."""

import json
import logging
import subprocess
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent
_WORKERS_DIR = _SCRIPTS / "swarm"

_LOG = logging.getLogger(__name__)

ROLES = ["researcher", "architect", "strategist", "curator"]
WORKER_SCRIPT = {
    "researcher": "swarm.roles.researcher",
    "architect": "swarm.roles.architect",
    "strategist": "swarm.roles.strategist",
    "curator": "swarm.roles.curator",
}


def dispatch(role: str, topic: str, context: dict | None = None, timeout: int = 120) -> dict:
    """Dispatch a task to a swarm worker and return the result."""
    if role not in ROLES:
        return {"status": "error", "error": f"Unknown role: {role}"}

    payload = {"topic": topic}
    if context:
        payload.update(context)

    env = __import__("os").environ.copy()
    env["PYTHONPATH"] = str(_SCRIPTS)

    try:
        p = subprocess.Popen(
            ["py", "-3", "-m", WORKER_SCRIPT[role]],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        p.stdin.write(json.dumps(payload) + "\n")
        p.stdin.flush()
        p.stdin.close()  # EOF → worker exits run_forever loop

        out, err = p.communicate(timeout=timeout)
        result = json.loads(out.strip()) if out.strip() else {"status": "error", "error": "empty response"}
        result["role"] = role
        result["topic"] = topic
        return result
    except subprocess.TimeoutExpired:
        p.kill()
        return {"status": "error", "role": role, "topic": topic, "error": "timeout"}
    except Exception as e:
        return {"status": "error", "role": role, "topic": topic, "error": str(e)}


def dispatch_and_notify(role: str, topic: str, context: dict | None = None, timeout: int = 120) -> dict:
    """Dispatch and notify result to kanban."""
    result = dispatch(role, topic, context, timeout)

    status_icon = "✅" if result.get("status") == "ok" else "❌"
    title = f"{status_icon} {role}: {topic[:60]}"
    body = json.dumps(result, indent=2, ensure_ascii=False)

    try:
        subprocess.run(
            ["hermes", "kanban", "create", title, "--body", body[:500], "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as e:
        _LOG.warning("Kanban notify failed: %s", e)

    return result
