"""Kronos — Agente Orquestador (Fase 1: Consultiva).

Analiza pipelines completados y sugiere mejoras de routing.
Sin capacidad de modificar el DAG — solo lectura y recomendaciones.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from lib.config import VAULT_ROOT

_LOG = logging.getLogger(__name__)

PIPELINE_DIR = VAULT_ROOT / "_pipeline"
EVAL_PATH = PIPELINE_DIR / "evaluation.json"
PLAN_PATH = PIPELINE_DIR / "plan.json"
STATUS_PATH = PIPELINE_DIR / "status.md"
LOG_PATH = PIPELINE_DIR / "log.md"
CONTEXT_PATH = PIPELINE_DIR / "context.json"


def pipeline_status() -> dict:
    info = {"status": "idle", "topic": "", "agents": []}
    if not STATUS_PATH.exists():
        return info
    try:
        text = STATUS_PATH.read_text(encoding="utf-8")
        sm = re.search(r"\*\*status\*\*:\s*(\S+)", text)
        if sm:
            info["status"] = sm.group(1)
        tm = re.search(r"\*\*topic\*\*:\s*(.+?)$", text, re.MULTILINE)
        if tm:
            info["topic"] = tm.group(1).strip()
        for m in re.finditer(r"\| \d+ \| (\w+) \| (.+?) \|", text):
            info["agents"].append({"name": m.group(1), "status": m.group(2).strip()})
    except Exception:
        pass
    return info


def evaluation_read() -> dict:
    if EVAL_PATH.exists():
        try:
            return json.loads(EVAL_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def plan_read() -> dict:
    if PLAN_PATH.exists():
        try:
            return json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def pipeline_history(limit: int = 10) -> list[dict]:
    if not LOG_PATH.exists():
        return []
    try:
        lines = LOG_PATH.read_text(encoding="utf-8").strip().split("\n")
        entries = []
        for line in lines[-limit:]:
            m = re.match(r"\[(.+?)\] (.+)", line)
            if m:
                entries.append({"timestamp": m.group(1), "message": m.group(2)})
        return entries
    except Exception:
        return []


def memory_search(query: str, top_k: int = 5) -> list[dict]:
    try:
        from lib.code_memory import search
        return search(query, top_k=top_k)
    except Exception:
        return []


def suggest_routing() -> str:
    ev = evaluation_read()
    plan = plan_read()
    status = pipeline_status()
    history = pipeline_history(5)

    lines = ["## Análisis de Kronos — Diagnóstico de Routing", ""]
    lines.append(f"**Pipeline:** {status.get('status', 'N/A')}")
    lines.append(f"**Tema:** {status.get('topic', 'N/A')}")
    lines.append("")

    score = ev.get("composite", ev.get("pipeline_score", 0))
    health = ev.get("system_health", 0)
    lines.append(f"**Score compuesto:** {score}/100")
    lines.append(f"**Salud del sistema:** {health}/100")
    lines.append("")

    agents = status.get("agents", [])
    if agents:
        lines.append("**Agentes en pipeline:**")
        for a in agents:
            lines.append(f"- {a['name']}: {a['status']}")

    complexity = plan.get("complexity", "desconocida")
    subtasks = plan.get("subtasks", [])
    lines.append("")
    lines.append(f"**Complejidad:** {complexity}")
    if subtasks:
        lines.append(f"**Sub-tareas:** {len(subtasks)}")
        for s in subtasks:
            lines.append(f"- {s.get('id', '?')}: {s.get('name', '?')}")

    if history:
        lines.append("")
        lines.append("**Historial reciente:**")
        for h in history:
            lines.append(f"- [{h['timestamp']}] {h['message']}")

    suggestions = []
    if score < 60:
        suggestions.append("Score bajo (<60). Recomiendo: (a) agregar iteración de critic loop, "
                          "(b) verificar que todos los agentes recibieron contexto completo")
    if complexity in ("alta", "moderada") and not plan.get("has_code"):
        suggestions.append("Tarea compleja sin subtareas de código. Considerar dividir en "
                          "sub-tasks más pequeñas para mejor paralelización.")
    if score > 80 and not plan.get("parallelizable", False):
        suggestions.append("Score alto en tarea secuencial. Evaluar si próximas tareas similares "
                          "pueden beneficiarse de ejecución paralela.")

    if suggestions:
        lines.append("")
        lines.append("**Sugerencias:**")
        for s in suggestions:
            lines.append(f"- 💡 {s}")

    return "\n".join(lines)


def analyze_pipeline(topic: str = "") -> str:
    status = pipeline_status()
    ev = evaluation_read()

    report = ["# Análisis de Pipeline por Kronos", ""]
    report.append(f"**Tema:** {topic or status.get('topic', 'N/A')}")
    report.append(f"**Estado:** {status.get('status', 'N/A')}")
    report.append(f"**Score:** {ev.get('composite', ev.get('pipeline_score', 'N/A'))}")
    report.append(f"**Salud:** {ev.get('system_health', 'N/A')}")
    report.append("")
    report.append("**Agentes:**")
    for a in status.get("agents", []):
        report.append(f"  {a['name']}: {a['status']}")
    report.append("")
    report.append("**Historial de ejecución:**")
    for h in pipeline_history(8):
        report.append(f"  [{h['timestamp']}] {h['message']}")
    report.append("")
    report.append("---")
    report.append(suggest_routing())

    return "\n".join(report)
