"""Curator worker — invoca pipeline mnemosyne_node."""

import logging
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_SCRIPTS))

_LOG = logging.getLogger(__name__)


def run(context) -> dict:
    if isinstance(context, str):
        import json

        context = json.loads(context)
    if not isinstance(context, dict):
        context = {"topic": str(context)}
    topic = context.get("topic", "unknown")
    dry_run = context.get("dry_run", False)
    _LOG.info("Curator processing: %s (dry_run=%s)", topic, dry_run)
    if dry_run:
        return {"status": "ok", "role": "curator", "topic": topic, "result": "dry_run_ok"}
    try:
        from lib.agent_executor import mnemosyne_node

        state = {"topic": topic, "profile": "curacion", "plan": {}, "iteration": 0, "critic_score": 0}
        result = mnemosyne_node(state)
        return {"status": "ok", "role": "curator", "result": result}
    except Exception as e:
        return {"status": "error", "role": "curator", "error": str(e)}


if __name__ == "__main__":
    from swarm.roles.base import BaseSwarmWorker

    class CuratorWorker(BaseSwarmWorker):
        def execute(self, context):
            return run(context)

    CuratorWorker().run_forever()
