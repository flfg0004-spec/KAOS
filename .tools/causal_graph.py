"""Causal Modeler — Construye DAGs causales desde contexto textual.

Usage:
    py -3 .tools/causal_graph.py analyze <context_file>
    py -3 .tools/causal_graph.py leverage <context_file>
    py -3 .tools/causal_graph.py chain <context_file> --start <node>
    py -3 .tools/causal_graph.py --help
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path


class CausalModeler:
    def __init__(self):
        self.nodes = {}
        self.graph = {}

    def _add_node(self, name, kind, measure="", baseline=0.0):
        key = name.strip().lower()
        if key not in self.nodes:
            self.nodes[key] = {"kind": kind, "measure": measure, "baseline": baseline}
        if measure:
            self.nodes[key]["measure"] = measure
        if baseline:
            self.nodes[key]["baseline"] = baseline
        return key

    def _add_edge(self, source, target, polarity=1, delay="medium", strength=0.5):
        src = source.strip().lower()
        tgt = target.strip().lower()
        if src not in self.graph:
            self.graph[src] = {}
        self.graph[src][tgt] = {"polarity": polarity, "delay": delay, "strength": strength}

    def _parse_metrics(self, text):
        patterns = [
            r"([\w&]+(?:\s+[\w&]+){0,4})\s+is\s+at\s+(\d+(?:\.\d+)?)\s*%",
            r"([\w&]+(?:\s+[\w&]+){0,4})\s+currently\s+at\s+(\d+(?:\.\d+)?)\s*%",
            r"([\w&]+(?:\s+[\w&]+){0,4})\s+sits\s+at\s+(\d+(?:\.\d+)?)\s*%",
            r"([\w&]+(?:\s+[\w&]+){0,4})\s*:\s*(\d+(?:\.\d+)?)\s*%",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                value = float(match.group(2))
                self._add_node(name, "variable", measure="%", baseline=value)

    def _parse_actions(self, text):
        patterns = [
            r"(?:need to|should|must)\s+([\w&]+(?:\s+[\w&]+){0,4})",
            r"(?:required|necessary|critical)\s+to\s+([\w&]+(?:\s+[\w&]+){0,4})",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                self._add_node(name, "action")

    def _parse_outcomes(self, text):
        patterns = [
            r"(?:increase|decrease|improve|reduce|grow|boost|lowers?|hurts?|raises?|drops?)\s+([\w&]+(?:\s+[\w&]+){0,4})",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                self._add_node(name, "outcome")

    def _parse_causal_relations(self, text):
        positive_patterns = [
            r"([\w&]+(?:\s+[\w&]+){0,4})\s+(?:causes|leads?\s+to|drives|results?\s+in|triggers?|generates?|produces?|fosters?|enables?|increases?|improves?|boosts?|raises?)\s+([\w&]+(?:\s+[\w&]+){0,4})",
        ]
        for pattern in positive_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                source = match.group(1).strip()
                target = match.group(2).strip()
                self._add_node(source, "variable")
                self._add_node(target, "variable")
                self._add_edge(source, target, polarity=1)

        negative_patterns = [
            r"([\w&]+(?:\s+[\w&]+){0,4})\s+(?:but|while|however)\s+(?:[\w&]+\s+)?(?:decreases?|hurts?|reduces?|undermines?|blocks?|hinders?|negatively\s+impacts?)\s+([\w&]+(?:\s+[\w&]+){0,4})",
        ]
        for pattern in negative_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                source = match.group(1).strip()
                target = match.group(2).strip()
                self._add_node(source, "variable")
                self._add_node(target, "variable")
                self._add_edge(source, target, polarity=-1)

        delay_patterns = [
            r"([\w&]+(?:\s+[\w&]+){0,4})\s+(?:causes|leads?\s+to|drives|results?\s+in|increases?|improves?|boosts?)\s+([\w&]+(?:\s+[\w&]+){0,4})\s+after\s+(\w+)",
        ]
        for pattern in delay_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                source = match.group(1).strip()
                target = match.group(2).strip()
                raw_delay = match.group(3).strip().lower()
                if raw_delay in ("short", "quick", "rapid", "immediate"):
                    delay = "short"
                elif raw_delay in ("long", "slow", "gradual"):
                    delay = "long"
                else:
                    delay = "medium"
                self._add_node(source, "variable")
                self._add_node(target, "variable")
                self._add_edge(source, target, polarity=1, delay=delay)

    def build_from_context(self, context_text):
        self.nodes = {}
        self.graph = {}
        self._parse_metrics(context_text)
        self._parse_actions(context_text)
        self._parse_outcomes(context_text)
        self._parse_causal_relations(context_text)
        return {"nodes": dict(self.nodes), "graph": {k: dict(v) for k, v in self.graph.items()}}

    def find_leverage_points(self):
        out_degrees = {}
        for node_name in self.nodes:
            key = node_name
            out_degrees[key] = len(self.graph.get(key, {}))
        in_degrees = {}
        for src, targets in self.graph.items():
            for tgt in targets:
                in_degrees[tgt] = in_degrees.get(tgt, 0) + 1
        leverage = []
        for node_name in self.nodes:
            key = node_name
            out_deg = out_degrees.get(key, 0)
            in_deg = in_degrees.get(key, 0)
            if out_deg >= 2:
                leverage.append({
                    "node": key,
                    "out_degree": out_deg,
                    "in_degree": in_deg,
                    "score": out_deg / max(len(self.nodes), 1),
                })
        leverage.sort(key=lambda x: x["score"], reverse=True)
        return leverage

    def find_second_order_effects(self, action):
        key = action.strip().lower()
        if key not in self.graph:
            return []
        direct = set(self.graph[key].keys())
        second_order = {}
        for d in direct:
            if d in self.graph:
                for s_tgt, s_data in self.graph[d].items():
                    if s_tgt != key and s_tgt not in direct:
                        polarity_product = self.graph[key][d]["polarity"] * s_data["polarity"]
                        combined_strength = self.graph[key][d]["strength"] * s_data["strength"]
                        if s_tgt not in second_order or combined_strength > second_order[s_tgt]["strength"]:
                            second_order[s_tgt] = {
                                "via": d,
                                "polarity": polarity_product,
                                "strength": round(combined_strength, 3),
                                "hops": 2,
                            }
        return [{"target": k, **v} for k, v in sorted(second_order.items(), key=lambda x: x[1]["strength"], reverse=True)]

    def trace_chains(self, start, max_depth=4):
        key = start.strip().lower()
        if key not in self.nodes:
            return []
        chains = []

        def dfs(current, path, depth, visited):
            if depth > max_depth:
                return
            if depth > 0:
                chains.append(list(path))
            if current not in self.graph:
                return
            for neighbor in self.graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    dfs(neighbor, path, depth + 1, visited)
                    path.pop()
                    visited.discard(neighbor)

        dfs(key, [key], 0, {key})
        chains.sort(key=len, reverse=True)
        return chains

    def analyze(self, context_text):
        self.build_from_context(context_text)
        leverage = self.find_leverage_points()
        return {
            "nodes": {k: dict(v) for k, v in self.nodes.items()},
            "graph": {k: dict(v) for k, v in self.graph.items()},
            "leverage_points": leverage,
            "node_count": len(self.nodes),
            "edge_count": sum(len(t) for t in self.graph.values()),
        }

    def generate_report(self, context_text):
        analysis = self.analyze(context_text)
        lines = []
        lines.append("## Causal Analysis — Causal Modeler Report")
        lines.append("")
        lines.append(f"### Overview")
        lines.append(f"- **Nodes detected**: {analysis['node_count']}")
        lines.append(f"- **Edges detected**: {analysis['edge_count']}")
        lines.append("")

        lines.append(f"### Nodes by Kind")
        lines.append("")
        lines.append("| Node | Kind | Measure | Baseline |")
        lines.append("|------|------|---------|----------|")
        for name, ndata in sorted(analysis["nodes"].items()):
            kind = ndata.get("kind", "unknown")
            measure = ndata.get("measure", "")
            baseline = ndata.get("baseline", 0)
            baseline_str = f"{baseline}{measure}" if measure and baseline else str(baseline) if baseline else ""
            lines.append(f"| {name} | {kind} | {measure} | {baseline_str} |")
        lines.append("")

        if analysis["graph"]:
            lines.append(f"### Causal Graph Edges")
            lines.append("")
            lines.append("| Source | → Target | Polarity | Delay | Strength |")
            lines.append("|--------|----------|----------|-------|----------|")
            for src in sorted(analysis["graph"]):
                for tgt, edata in sorted(analysis["graph"][src].items()):
                    pol = "+" if edata["polarity"] > 0 else "−"
                    lines.append(f"| {src} | {tgt} | {pol} | {edata['delay']} | {edata['strength']} |")
            lines.append("")

        if analysis["leverage_points"]:
            lines.append(f"### Leverage Points")
            lines.append("")
            lines.append("| Node | Out-Degree | In-Degree | Leverage Score |")
            lines.append("|------|-----------|-----------|----------------|")
            for lp in analysis["leverage_points"]:
                lines.append(f"| {lp['node']} | {lp['out_degree']} | {lp['in_degree']} | {lp['score']:.3f} |")
            lines.append("")

            lines.append(f"### Recommended Interventions")
            lines.append("")
            for lp in analysis["leverage_points"][:3]:
                lines.append(f"- **{lp['node']}** (score: {lp['score']:.3f}) — high out-degree ({lp['out_degree']}), likely a high-impact lever")
            lines.append("")
        else:
            lines.append("### Leverage Points")
            lines.append("")
            lines.append("No leverage points detected (requires nodes with 2+ outgoing edges).")
            lines.append("")

        if analysis["graph"]:
            lines.append(f"### Second-Order Effects")
            lines.append("")
            lines.append("Checking action nodes for indirect effects...")
            lines.append("")
            for name, ndata in sorted(analysis["nodes"].items()):
                if ndata["kind"] == "action":
                    effects = self.find_second_order_effects(name)
                    if effects:
                        lines.append(f"- **{name}** → 2nd order effects:")
                        for eff in effects:
                            pol = "positive" if eff["polarity"] > 0 else "negative"
                            lines.append(f"  - {eff['target']} (via {eff['via']}, {pol}, strength={eff['strength']})")
                lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("_Generated by Causal Modeler (Week 3 — KAOS)_")
        return "\n".join(lines)


def load_context(file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def cmd_analyze(args):
    text = load_context(args.context_file)
    modeler = CausalModeler()
    report = modeler.generate_report(text)
    print(report)


def cmd_leverage(args):
    text = load_context(args.context_file)
    modeler = CausalModeler()
    modeler.build_from_context(text)
    leverage = modeler.find_leverage_points()
    print(json.dumps(leverage, indent=2, ensure_ascii=False))


def cmd_chain(args):
    text = load_context(args.context_file)
    modeler = CausalModeler()
    modeler.build_from_context(text)
    chains = modeler.trace_chains(args.start, max_depth=args.max_depth)
    if not chains:
        print(f"No chains found starting from '{args.start}'")
        return
    for chain in chains:
        print(" -> ".join(chain))


def main():
    parser = argparse.ArgumentParser(
        description="Causal Modeler — Build causal DAGs from strategic context text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  py -3 .tools/causal_graph.py analyze context.txt\n"
            "  py -3 .tools/causal_graph.py leverage context.txt\n"
            "  py -3 .tools/causal_graph.py chain context.txt --start market_share\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Generate full causal analysis report")
    analyze_parser.add_argument("context_file", help="Path to context text file")

    leverage_parser = subparsers.add_parser("leverage", help="Find leverage points in causal graph")
    leverage_parser.add_argument("context_file", help="Path to context text file")

    chain_parser = subparsers.add_parser("chain", help="Trace causal chains from a node")
    chain_parser.add_argument("context_file", help="Path to context text file")
    chain_parser.add_argument("--start", required=True, help="Starting node name")
    chain_parser.add_argument("--max-depth", type=int, default=4, help="Maximum chain depth (default: 4)")

    args = parser.parse_args()

    if args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "leverage":
        cmd_leverage(args)
    elif args.command == "chain":
        cmd_chain(args)


if __name__ == "__main__":
    main()
