import argparse
import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TOOLS_DIR.parent / ".memory" / "_scripts"

sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from causal_graph import CausalModeler
from strategy_memory import StrategicMemoryBank


class CausalMemoryBridge:
    def __init__(self):
        self.modeler = CausalModeler()
        self.bank = StrategicMemoryBank()

    def bridge_analysis(self, context_text):
        causal = self.modeler.analyze(context_text)
        memory_context = {"context_preview": context_text[:300]}
        memory = self.bank.recall_similar(memory_context)
        return {
            "causal_analysis": {
                "node_count": causal["node_count"],
                "edge_count": causal["edge_count"],
                "nodes": {k: dict(v) for k, v in causal["nodes"].items()},
                "graph": {k: dict(v) for k, v in causal["graph"].items()},
                "leverage_points": causal.get("leverage_points", []),
            },
            "memory_recall": [
                {
                    "id": m["id"],
                    "plan_type": m["plan_type"],
                    "timestamp": m["timestamp"][:19] if m.get("timestamp") else None,
                    "outcome_score": m.get("outcome_score"),
                }
                for m in memory
            ],
            "node_count": causal["node_count"],
            "edge_count": causal["edge_count"],
            "similar_strategies_found": len(memory),
        }

    def store_causal_insight(self, context_text, causal_report_path=None):
        causal = self.modeler.analyze(context_text)
        if causal_report_path:
            report_path = Path(causal_report_path)
            if report_path.exists():
                extra = json.loads(report_path.read_text(encoding="utf-8"))
                if isinstance(extra, dict):
                    causal["external_report"] = extra
        context = {"context_preview": context_text[:300]}
        content = {
            "node_count": causal["node_count"],
            "edge_count": causal["edge_count"],
            "leverage_points": causal.get("leverage_points", []),
            "graph": {k: dict(v) for k, v in causal["graph"].items()},
            "nodes": {k: dict(v) for k, v in causal["nodes"].items()},
        }
        sid = self.bank.store(context, content, "causal_analysis")
        return {"stored_id": sid, "node_count": causal["node_count"]}

    def recall_similar_causal_contexts(self, context_text):
        causal = self.modeler.analyze(context_text)
        memory_context = {"context_preview": context_text[:300]}
        similar = self.bank.recall_similar(memory_context)
        enriched = []
        for s in similar:
            raw = s.get("content_json")
            if isinstance(raw, str):
                try:
                    s_content = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    s_content = {}
            else:
                s_content = raw or {}
            enriched.append({
                "id": s["id"],
                "plan_type": s["plan_type"],
                "timestamp": s.get("timestamp", "?")[:19],
                "node_count": s_content.get("node_count", 0),
                "edge_count": s_content.get("edge_count", 0),
                "outcome_score": s.get("outcome_score"),
            })
        return {
            "current_analysis": {
                "node_count": causal["node_count"],
                "edge_count": causal["edge_count"],
            },
            "similar_contexts": enriched,
        }

    def generate_enriched_report(self, context_text):
        causal = self.modeler.analyze(context_text)
        causal_md = self.modeler.generate_report(context_text)
        memory_context = {"context_preview": context_text[:300]}
        similar = self.bank.recall_similar(memory_context)
        lines = []
        lines.append("# Causal-Memory Enriched Report")
        lines.append("")
        lines.append("## Causal Analysis Summary")
        lines.append("")
        lines.append(f"- **Nodes detected**: {causal['node_count']}")
        lines.append(f"- **Edges detected**: {causal['edge_count']}")
        if causal.get("leverage_points"):
            lines.append(f"- **Leverage Points**: {len(causal['leverage_points'])}")
            for lp in causal["leverage_points"][:3]:
                lines.append(f"  - **{lp['node']}** (score: {lp['score']:.3f})")
        lines.append("")
        lines.append("## Memory Recall")
        lines.append("")
        lines.append(f"- **Similar past strategies found**: {len(similar)}")
        for s in similar[:5]:
            ts = s.get("timestamp", "")[:10] if s.get("timestamp") else "?"
            score = s.get("outcome_score", "N/A")
            lines.append(f"  - `id={s['id']}` type=`{s['plan_type']}` date={ts} score={score}")
        lines.append("")
        lines.append("## Full Causal Report")
        lines.append("")
        lines.append(causal_md)
        return "\n".join(lines)


def load_context(file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Causal-Memory Bridge — connects Causal Modeler with Strategic Memory Bank for enriched strategic analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  py -3 .tools/causal_memory_bridge.py analyze context.txt\n"
            "  py -3 .tools/causal_memory_bridge.py store context.txt --report causal_report.json\n"
            "  py -3 .tools/causal_memory_bridge.py recall context.txt\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Run causal analysis and memory recall jointly")
    analyze_parser.add_argument("context_file", help="Path to context text file")

    store_parser = subparsers.add_parser("store", help="Run causal analysis and store insight in memory bank")
    store_parser.add_argument("context_file", help="Path to context text file")
    store_parser.add_argument("--report", help="Path to existing causal report JSON to include")

    recall_parser = subparsers.add_parser("recall", help="Find causally similar contexts from memory")
    recall_parser.add_argument("context_file", help="Path to context text file")

    args = parser.parse_args()
    bridge = CausalMemoryBridge()

    if args.command == "analyze":
        text = load_context(args.context_file)
        result = bridge.bridge_analysis(text)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "store":
        text = load_context(args.context_file)
        result = bridge.store_causal_insight(text, args.report)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "recall":
        text = load_context(args.context_file)
        result = bridge.recall_similar_causal_contexts(text)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
