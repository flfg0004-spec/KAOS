"""CI Pipeline Runner — invoca LangGraph DAG headless for CI/CD."""
import json, sys, time
from datetime import datetime
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / ".memory" / "_scripts"
sys.path.insert(0, str(_SCRIPTS))

from lib.orchestrator import KAOSState, build_graph

RESULT_PATH = Path("pipeline-result.json")
EVAL_DIR = _SCRIPTS.parent / "_pipeline"


def run_pipeline(topic: str, profile: str = "desarrollo",
                 parallel: bool = False, timeout_s: int = 600) -> dict:
    graph = build_graph(with_parallel=parallel)
    state = KAOSState(topic=topic, profile=profile)
    start = time.time()
    config = {"configurable": {"thread_id": f"pipeline-{datetime.now().strftime('%Y%m%d-%H%M%S')}"}}
    result = graph.invoke(state, config=config)
    elapsed = round(time.time() - start, 1)

    ev = result.get("evaluation", {})
    return {
        "topic": topic,
        "profile": profile,
        "composite": ev.get("composite", 0),
        "system_health": ev.get("system_health", 0),
        "pipeline_score": ev.get("pipeline_score", 0),
        "critic_score": result.get("critic_score", 0),
        "critic_feedback": result.get("critic_feedback", ""),
        "iterations": result.get("iteration", 0),
        "agents_executed": [
            a for a in ["aletheia", "kosmos", "metis", "kratos", "mnemosyne"]
            if result.get(f"{a}_output")
        ],
        "duration_seconds": elapsed,
        "timestamp": datetime.now().isoformat(),
        "passed": ev.get("composite", 0) >= 50,
    }


def archive_artifacts(result: dict) -> list[Path]:
    artifacts = []
    for f in ["evaluation.json", "plan.json", "context.json"]:
        src = EVAL_DIR / f
        if src.exists():
            dst = Path(f"artifacts/{result['timestamp'][:10]}-{f}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text(encoding="utf-8"))
            artifacts.append(dst)
    return artifacts


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "auditar calidad del vault KAOS"
    profile = sys.argv[2] if len(sys.argv) > 2 else "desarrollo"
    result = run_pipeline(topic, profile)
    RESULT_PATH.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("passed") else 1)
