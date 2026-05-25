"""
KAOS Dashboard Pipeline — expone métricas del vault como Pipeline de Open WebUI.

Lee dashboard.json y expone herramientas que OWUI puede usar para mostrar
el estado del sistema KAOS en el panel admin.
"""

import json
import os
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("KAOS_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
DASHBOARD_PATH = VAULT_ROOT / ".memory" / "dashboard" / "dashboard.json"
EVALUATION_PATH = VAULT_ROOT / ".memory" / "_pipeline" / "evaluation.json"


class Pipeline:
    def __init__(self):
        self.name = "kaos-dashboard"

    async def on_startup(self):
        pass

    async def on_shutdown(self):
        pass

    async def inlet(self, body: dict, user: dict) -> dict:
        return body

    async def outlet(self, body: dict, user: dict) -> dict:
        enriched = await self._enrich(body)
        return enriched

    async def _enrich(self, body: dict) -> dict:
        body["kaos"] = self._load_kaos_metrics()
        return body

    def _load_kaos_metrics(self) -> dict:
        metrics = {"status": "unavailable", "timestamp": datetime.now().isoformat()}

        if DASHBOARD_PATH.exists():
            try:
                data = json.loads(DASHBOARD_PATH.read_text(encoding="utf-8"))
                vault = data.get("vault", {})
                health = data.get("health", {})
                sessions = data.get("session_analytics", {})
                metrics.update({
                    "status": "ok",
                    "vault_files": vault.get("total_md", 0),
                    "wiki_concepts": vault.get("by_directory", {}).get("wiki", 0),
                    "health_overall": health.get("overall", "N/A"),
                    "lint_issues": health.get("lint_issues", 0),
                    "git_clean": health.get("git_clean", False),
                    "total_sessions": sessions.get("total_sessions", 0),
                    "total_messages": sessions.get("total_messages", 0),
                    "avg_duration_min": sessions.get("avg_duration_min", 0),
                })
            except Exception as e:
                metrics["error"] = str(e)

        if EVALUATION_PATH.exists():
            try:
                ev = json.loads(EVALUATION_PATH.read_text(encoding="utf-8"))
                metrics["pipeline_score"] = ev.get("composite", ev.get("pipeline_score", 0))
                metrics["system_health"] = ev.get("system_health", 0)
            except Exception:
                pass

        return metrics
