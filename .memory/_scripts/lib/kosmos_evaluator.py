"""Kosmos Evaluator — post-pipeline evaluation of agent outputs."""
import json, re, sys
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from lib.system_scanner import scan, health_score


EVAL_PATH = SCRIPTS.parent / "_pipeline" / "evaluation.json"

EVAL_CRITERIA = {
    "aletheia": {
        "min_lines": 20,
        "required_patterns": ["fuente", "source", "análisis", "analysis", "analisis",
                              "evidencia", "evidence", "resumen", "hallazgo", "conclus",
                              "recomend", "recommend"],
        "max_score": 90,
    },
    "kosmos": {
        "min_lines": 15,
        "required_patterns": ["adr", "architecture", "arquitectur", "recommendation",
                              "recomend", "diagram", "c4", "decisión", "decision"],
        "max_score": 90,
    },
    "metis": {
        "min_lines": 15,
        "required_patterns": ["strategy", "estrateg", "okr", "roadmap", "objetiv",
                              "goal", "kpi", "metric", "riesg", "risk", "mitig"],
        "max_score": 90,
    },
    "kratos": {
        "min_lines": 10,
        "required_patterns": ["implement", "código", "codigo", "code", "función",
                              "function", "clase", "class", "test", "error", "fix"],
        "max_score": 95,
    },
    "mnemosyne": {
        "min_lines": 5,
        "required_patterns": ["curation", "curacion", "calidad", "quality", "wikilink",
                              "referenc", "índice", "index", "consist"],
        "max_score": 90,
    },
}


def evaluate_output(text: str, agent: str) -> dict:
    """Evaluate a single agent output against criteria."""
    criteria = EVAL_CRITERIA.get(agent, EVAL_CRITERIA["kratos"])
    lines = text.strip().split("\n")
    line_count = len(lines)
    text_lower = text.lower()

    # Completeness score: count matched patterns (any of the alternatives counts)
    pattern_hits = sum(1 for p in criteria["required_patterns"] if p in text_lower)
    completeness = min(1.0, pattern_hits / max(1, len(criteria["required_patterns"]) / 2))  # generous: half match = full
    
    # Length score
    length_score = min(1.0, line_count / criteria["min_lines"])
    
    # Composite
    score = round((completeness * 0.6 + length_score * 0.4) * criteria["max_score"], 1)
    
    return {
        "agent": agent,
        "lines": line_count,
        "patterns_found": pattern_hits,
        "patterns_required": len(criteria["required_patterns"]),
        "completeness": round(completeness, 2),
        "score": score,
        "passed": score >= 40,
    }


def evaluate_pipeline_outputs(pipeline_dir: Path = None, state: dict = None) -> dict:
    """Scan pipeline outputs and evaluate each agent's work."""
    if pipeline_dir is None:
        pipeline_dir = SCRIPTS.parent / "_pipeline"
    
    AGENT_SUFFIXES = {
        "aletheia": "",
        "kosmos": "-adr",
        "metis": "-strategy",
        "kratos": "-code",
        "mnemosyne": "-curation",
    }
    
    evaluations = {}
    raw_dir = pipeline_dir / "raw"
    all_raw = list(raw_dir.glob("*.md")) if raw_dir.exists() else []
    
    for agent in ["aletheia", "kosmos", "metis", "kratos", "mnemosyne"]:
        # Prefer state output when available (pipeline context)
        state_output = state.get(f"{agent}_output", "") if state else ""
        if state_output and len(state_output.strip()) > 50:
            evaluations[agent] = evaluate_output(state_output, agent)
            continue
        
        suffix = AGENT_SUFFIXES[agent]
        candidates = list(pipeline_dir.glob(f"*{agent}*"))
        if suffix:
            candidates += [f for f in all_raw if f.stem.endswith(suffix)]
        else:
            candidates += [f for f in all_raw if not any(
                f.stem.endswith(s) for s in AGENT_SUFFIXES.values() if s
            )]
        
        text = ""
        for c in candidates:
            if c.exists():
                try:
                    text += c.read_text(encoding="utf-8", errors="replace") + "\n"
                except Exception:
                    pass
        
        if text.strip():
            evaluations[agent] = evaluate_output(text, agent)
        else:
            evaluations[agent] = {"agent": agent, "error": "no output found", "passed": False}
    
    return evaluations


def _build_composite(sys_score: float, pipeline: dict) -> float:
    pipeline_score = round(
        sum(e.get("score", 0) for e in pipeline.values() if "score" in e) /
        max(1, len([e for e in pipeline.values() if "score" in e])),
        1
    )
    return round((sys_score + pipeline_score) / 2, 1)


def evaluate_system(state: dict = None) -> dict:
    """Full system evaluation: system scan + pipeline evaluation.
    
    Args:
        state: Optional KAOSState dict — uses agent outputs if provided.
    """
    system = scan()
    sys_score = health_score(system)
    pipeline = evaluate_pipeline_outputs(state=state)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "system_health": sys_score,
        "system_components": {k: "ok" if "error" not in str(v) else "error" for k, v in system.items()},
        "pipeline_evaluation": pipeline,
        "pipeline_score": round(
            sum(e.get("score", 0) for e in pipeline.values() if "score" in e) /
            max(1, len([e for e in pipeline.values() if "score" in e])),
            1
        ),
        "composite": _build_composite(sys_score, pipeline),
    }
    
    EVAL_PATH.write_text(json.dumps(result, indent=2, default=str))
    return result


def run_evaluator(state: dict = None) -> dict:
    """Entry point for LangGraph evaluator node.
    
    Args:
        state: KAOSState dict from LangGraph (optional)
    
    Returns:
        Updated state with evaluation result
    """
    result = evaluate_system(state=state)
    if state is None:
        return result
    
    state["evaluation"] = result
    state["evaluation_score"] = result["composite"]
    return state


if __name__ == "__main__":
    import sys
    result = evaluate_system()
    print(json.dumps(result, indent=2, default=str))
    print(f"\n{'='*50}")
    print(f"System Health: {result['system_health']}/100")
    print(f"Pipeline Score: {result['pipeline_score']}/100")
    print(f"Composite: {result['composite']}/100")
    print(f"{'='*50}")
