"""Agent output quality evaluation — DeepEval + heuristic fallback."""
import json, logging
from datetime import datetime
from pathlib import Path

from lib.file_lock import locked_read, locked_update

logger = logging.getLogger("quality.agent")

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TIMESERIES_DIR = VAULT_ROOT / ".vault" / "quality" / "timeseries"
SIGNALS_DIR = VAULT_ROOT / ".memory" / "bridge" / "signals"
TIMESERIES_FILE = TIMESERIES_DIR / "verification-scores.json"

try:
    from lib.config import QUALITY_THRESHOLD_CRIT, QUALITY_THRESHOLD_WARN

    SCORE_THRESHOLD_WARN = QUALITY_THRESHOLD_WARN
    SCORE_THRESHOLD_CRIT = QUALITY_THRESHOLD_CRIT
except ImportError:
    SCORE_THRESHOLD_WARN = 80
    SCORE_THRESHOLD_CRIT = 60

try:
    from deepeval.metrics import FaithfulnessMetric, GEval, TaskCompletionMetric
    from deepeval.test_case import LLMTestCase
    _HAS_DEEPEVAL = True
except ImportError:
    _HAS_DEEPEVAL = False


def _heuristic_fallback(text: str) -> dict:
    text = text or ""
    if len(text.strip()) < 100:
        return {
            "veracidad": 0, "coherencia": 0, "completitud": 0,
            "reproducibilidad": 0, "utilidad": 0,
            "insufficient_data": True,
        }
    lines = text.strip().split("\n")
    words = text.split()
    has_titles = "##" in text
    has_lists = "  - " in text or "* " in text
    completitud = 0
    if has_titles:
        completitud += 40
    if has_lists:
        completitud += 20
    if len(text) > 200:
        completitud += 40
    has_wikilinks = "[[" in text and "]]" in text
    return {
        "veracidad": min(100, int(len(words) * 0.5 + 10)),
        "coherencia": min(100, len(lines) * 5 + 20) if text else 0,
        "completitud": completitud,
        "reproducibilidad": (60 + (30 if has_wikilinks else 0) + (10 if len(text) > 50 else 0)),
        "utilidad": min(100, len(words) // 2 + 20) if text else 0,
        "insufficient_data": False,
    }


def evaluate_agent_output(agent: str, output: str, task_prompt: str = "", context: list = None) -> dict:
    if not _HAS_DEEPEVAL or not task_prompt:
        dims = _heuristic_fallback(output)
        composite = sum(dims.values()) / max(1, len(dims))
        return {"composite": round(composite, 1), "real_metrics": False, **{k: round(v, 1) for k, v in dims.items()}}
    try:
        test_case = LLMTestCase(input=task_prompt, actual_output=output, context=context or [])
        metrics = {"task_completion": TaskCompletionMetric(threshold=0.7), "faithfulness": FaithfulnessMetric()}
        if agent == "kosmos":
            metrics["geval"] = GEval(
                name="architecture_coherence",
                criteria="Determine if the architectural analysis is coherent and complete",
            )
        results = {}
        for name, metric in metrics.items():
            try:
                metric.measure(test_case)
                results[name] = metric.score
            except Exception as e:
                logger.warning(f"DeepEval {name} failed for {agent}: {e}")
                results[name] = 0.0
        dims = _heuristic_fallback(output)
        composite = (sum(results.values()) / max(1, len(results))) * 100 if results else sum(dims.values()) / 5
        return {
            "composite": round(composite, 1),
            "real_metrics": True,
            **{k: round(v * 100, 1) for k, v in results.items()},
            **{k: round(v, 1) for k, v in dims.items()},
        }
    except Exception as e:
        logger.warning(f"DeepEval failed for {agent}: {e}, using fallback")
        dims = _heuristic_fallback(output)
        composite = sum(dims.values()) / 5
        return {"composite": round(composite, 1), "real_metrics": False, **{k: round(v, 1) for k, v in dims.items()}}


def record(agent: str, output: str, topic: str = "", pipeline_id: str = "", task_prompt: str = "") -> dict:
    scores = evaluate_agent_output(agent, output, task_prompt)
    timestamp = datetime.now().isoformat()
    entry = {
        "agent": agent,
        "topic": topic[:80] if topic else "",
        "pipeline_id": pipeline_id,
        "timestamp": timestamp,
        **{k: v for k, v in scores.items()},
    }
    TIMESERIES_DIR.mkdir(parents=True, exist_ok=True)
    data = locked_update(
        TIMESERIES_FILE,
        lambda d: {**d, "scores": (d.get("scores", []) + [entry])[-10000:]},
        default={"scores": []},
    )
    logger.info(
        f"[QUALITY] {agent}: composite={scores['composite']:.1f}/100 (real={scores.get('real_metrics', False)})"
    )
    if scores["composite"] < SCORE_THRESHOLD_CRIT:
        SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
        signal = {"type": "quality_critical", "agent": agent, "score": scores["composite"], "timestamp": timestamp}
        signal_file = SIGNALS_DIR / f"quality_{agent}_{datetime.now().strftime('%H%M%S')}.json"
        signal_file.write_text(json.dumps(signal), encoding="utf-8")
    return entry


def latest(limit: int = 10) -> list:
    try:
        data = locked_read(TIMESERIES_FILE)
        return data.get("scores", [])[-limit:]
    except Exception:
        return []


def record_gap_feedback(topic: str, total_gaps: int, confirmed: int, rejected: int) -> dict:
    entry = {
        "agent": "aletheia",
        "type": "gap_feedback",
        "topic": topic[:80] if topic else "",
        "total_gaps": total_gaps,
        "confirmed": confirmed,
        "rejected": rejected,
        "timestamp": datetime.now().isoformat(),
    }
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
    signal_file = SIGNALS_DIR / f"gap_feedback_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    signal_file.write_text(json.dumps(entry), encoding="utf-8")
    logger.info("[GAP-FEEDBACK] %s: %d/%d confirmed", topic[:40], confirmed, total_gaps)
    return entry


def summary() -> dict:
    scores = latest(100)
    if not scores:
        return {"total": 0, "avg_composite": 0, "agents": {}}
    agents = {}
    for s in scores:
        a = s["agent"]
        if a not in agents:
            agents[a] = {"count": 0, "total_composite": 0}
        agents[a]["count"] += 1
        agents[a]["total_composite"] += s["composite"]
    avg_composite = sum(s["composite"] for s in scores if "composite" in s) / len(scores)
    return {
        "total": len(scores),
        "avg_composite": round(avg_composite, 1),
        "real_metrics": any(s.get("real_metrics", False) for s in scores),
        "agents": {
            a: {"avg_composite": round(d["total_composite"] / d["count"], 1), "count": d["count"]}
            for a, d in agents.items()
        },
    }
