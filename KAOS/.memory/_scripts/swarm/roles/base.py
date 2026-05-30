import abc
import logging
import sys

_LOG = logging.getLogger(__name__)


class BaseSwarmWorker(abc.ABC):
    """Abstract base for a swarm worker role."""

    def __init__(self):
        self._running = True

    @abc.abstractmethod
    def execute(self, context: dict) -> dict: ...

    def run_forever(self):
        """Read JSON commands from stdin, execute, write JSON result to stdout."""
        while self._running:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                import json

                cmd = json.loads(line.strip())
                result = self.execute(cmd)
                print(json.dumps(result), flush=True)
            except json.JSONDecodeError:
                print(json.dumps({"error": "invalid JSON"}), flush=True)
            except EOFError:
                break
            except KeyboardInterrupt:
                break

    def stop(self):
        self._running = False
