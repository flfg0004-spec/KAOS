"""Kronos Self-Evaluation — measures orchestration and pipeline quality across 5 dimensions."""

import logging
import re

_LOG = logging.getLogger(__name__)


def _check_scheduling(text: str) -> dict:
    patterns = {
        "order": r"(?:orden|order|secuencia|sequence|primero|first|luego|then|después|after)",
        "dependencies": r"(?:dependenc|dependency|espera|wait|before|antes|precondición)",
        "parallel": r"(?:paralel|parallel|simultáneo|concurrent|simultaneous)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_efficiency(text: str) -> dict:
    patterns = {
        "resources": r"(?:recurso|resource|memoria|memory|cpu|tiempo|time|idle|ocios)",
        "concurrency": r"(?:max_concurrent|workers|hilo|thread|pool|paralel)",
        "optimization": r"(?:optimiz|optimiza|improve|mejora|eficien|efficient)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_error_handling(text: str) -> dict:
    patterns = {
        "timeout": r"(?:timeout|tiempo.*espera|timed? out)",
        "retry": r"(?:retry|reintent|reintentar|intentar.*nuev|try.*again)",
        "error": r"(?:error|fail|failed|fallo|fallid|exception|excepción)",
        "graceful": r"(?:graceful|elegant|robust|robustez|fallback|resilien)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_traceability(text: str) -> dict:
    patterns = {
        "logging": r"(?:log|logging|registr|traz|trace|debug)",
        "state": r"(?:state|estado|status|pending|running|completed|failed)",
        "reporting": r"(?:report|informe|notify|notific|alerta|alert|dashboard)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def _check_scalability(text: str) -> dict:
    patterns = {
        "multi": r"(?:multi|varios|multiple|múltiple|n.*pipeline|varios.*agente)",
        "load": r"(?:carga|load|balanceo|balanc|distribución|distribut)",
        "capacity": r"(?:capacidad|capacity|escal|scal|crecimient|grow|expand)",
    }
    found = {}
    for key, pat in patterns.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        found[key] = len(matches)
    return found


def kronos_self_eval(agent: str, output: dict) -> dict:
    output = output or {}
    tasks = output.get("tasks", [])
    results = output.get("results", [])
    status = output.get("status", "")
    history = output.get("history", [])
    suggestions = output.get("suggestions", "")

    text = status or suggestions or ""
    for r in results:
        if isinstance(r, dict):
            text += " " + r.get("error", "") + " " + r.get("state", "")
    for t in tasks:
        if isinstance(t, dict):
            text += " " + t.get("id", "") + " " + t.get("name", "")

    if not text and not tasks and not results:
        return {
            "agent": agent,
            "score": 0.0,
            "dimensions": {
                "correccion_scheduling": {"score": 0.0, "justificacion": "No tasks or results provided"},
                "eficiencia_orquestacion": {"score": 0.0, "justificacion": "No tasks or results provided"},
                "manejo_errores": {"score": 0.0, "justificacion": "No tasks or results provided"},
                "trazabilidad": {"score": 0.0, "justificacion": "No tasks or results provided"},
                "escalabilidad": {"score": 0.0, "justificacion": "No tasks or results provided"},
            },
        }

    scheduling = _check_scheduling(text)
    efficiency = _check_efficiency(text)
    error_info = _check_error_handling(text)
    trace_info = _check_traceability(text)
    scale_info = _check_scalability(text)

    total_sched = sum(scheduling.values())
    correccion_scheduling = min(1.0, 0.3 + 0.1 * min(total_sched, 7))
    if scheduling.get("order", 0) > 1:
        correccion_scheduling = min(1.0, correccion_scheduling + 0.15)
    if scheduling.get("dependencies", 0) > 0:
        correccion_scheduling = min(1.0, correccion_scheduling + 0.15)

    total_eff = sum(efficiency.values())
    eficiencia_orquestacion = min(1.0, 0.3 + 0.1 * min(total_eff, 6))
    if efficiency.get("concurrency", 0) > 0:
        eficiencia_orquestacion = min(1.0, eficiencia_orquestacion + 0.2)
    if efficiency.get("optimization", 0) > 0:
        eficiencia_orquestacion = min(1.0, eficiencia_orquestacion + 0.15)

    manejo_errores = 0.5
    if error_info.get("timeout", 0) > 0:
        manejo_errores += 0.1
    if error_info.get("retry", 0) > 0:
        manejo_errores += 0.15
    if error_info.get("graceful", 0) > 0:
        manejo_errores += 0.15
    if error_info.get("error", 0) > 0:
        manejo_errores = max(0.3, manejo_errores - 0.1 * min(error_info.get("error", 0), 5))
    manejo_errores = max(0.0, min(1.0, manejo_errores))

    total_trace = sum(trace_info.values())
    trazabilidad = min(1.0, 0.2 + 0.1 * min(total_trace, 8))
    if trace_info.get("logging", 0) > 1:
        trazabilidad = min(1.0, trazabilidad + 0.15)
    if trace_info.get("state", 0) > 0:
        trazabilidad = min(1.0, trazabilidad + 0.15)
    if trace_info.get("reporting", 0) > 0:
        trazabilidad = min(1.0, trazabilidad + 0.1)
    if isinstance(history, list) and len(history) > 0:
        trazabilidad = min(1.0, trazabilidad + 0.1)

    total_scale = sum(scale_info.values())
    escalabilidad = min(1.0, 0.2 + 0.1 * min(total_scale, 6))
    if scale_info.get("multi", 0) > 0:
        escalabilidad = min(1.0, escalabilidad + 0.2)
    if scale_info.get("load", 0) > 0:
        escalabilidad = min(1.0, escalabilidad + 0.15)
    if scale_info.get("capacity", 0) > 0:
        escalabilidad = min(1.0, escalabilidad + 0.15)

    score = round((correccion_scheduling + eficiencia_orquestacion + manejo_errores + trazabilidad + escalabilidad) / 5, 2)

    return {
        "agent": agent,
        "score": score,
        "dimensions": {
            "correccion_scheduling": {
                "score": correccion_scheduling,
                "justificacion": (
                    f"order={scheduling.get('order', 0)}, "
                    f"dependencies={scheduling.get('dependencies', 0)}, "
                    f"parallel={scheduling.get('parallel', 0)}"
                ),
            },
            "eficiencia_orquestacion": {
                "score": eficiencia_orquestacion,
                "justificacion": (
                    f"resources={efficiency.get('resources', 0)}, "
                    f"concurrency={efficiency.get('concurrency', 0)}, "
                    f"optimization={efficiency.get('optimization', 0)}"
                ),
            },
            "manejo_errores": {
                "score": manejo_errores,
                "justificacion": (
                    f"timeout={error_info.get('timeout', 0)}, "
                    f"retry={error_info.get('retry', 0)}, "
                    f"errors={error_info.get('error', 0)}, "
                    f"graceful={error_info.get('graceful', 0)}"
                ),
            },
            "trazabilidad": {
                "score": trazabilidad,
                "justificacion": (
                    f"logging={trace_info.get('logging', 0)}, "
                    f"state={trace_info.get('state', 0)}, "
                    f"reporting={trace_info.get('reporting', 0)}, "
                    f"history_len={len(history) if isinstance(history, list) else 0}"
                ),
            },
            "escalabilidad": {
                "score": escalabilidad,
                "justificacion": (
                    f"multi_pipeline={scale_info.get('multi', 0)}, "
                    f"load_balancing={scale_info.get('load', 0)}, "
                    f"capacity={scale_info.get('capacity', 0)}"
                ),
            },
        },
    }
