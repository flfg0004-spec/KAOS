"""Researcher worker — invoca pipeline aletheia_node."""

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
    _LOG.info("Researcher processing: %s (dry_run=%s)", topic, dry_run)
    if dry_run:
        return {"status": "ok", "role": "researcher", "topic": topic, "result": "dry_run_ok"}
    try:
        from lib.agent_executor import aletheia_node

        state = {"topic": topic, "profile": "standard", "plan": {}, "iteration": 0, "critic_score": 0}
        result = aletheia_node(state)
        return {"status": "ok", "role": "researcher", "result": result}
    except Exception as e:
        return {"status": "error", "role": "researcher", "error": str(e)}


if __name__ == "__main__":
    from swarm.roles.base import BaseSwarmWorker

    class ResearcherWorker(BaseSwarmWorker):
        def execute(self, context):
            return run(context)

    ResearcherWorker().run_forever()
