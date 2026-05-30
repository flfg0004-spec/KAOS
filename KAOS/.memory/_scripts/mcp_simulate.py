#!/usr/bin/env python3
"""MCP server for simulate.py — Monte Carlo simulation engine.

Exposes 3 tools: simulate_evaluate, simulate_sensitivity, simulate_tornado.
JSON-RPC 2.0 over stdio. No external dependencies.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".tools"))
from simulate import SimulationEngine

TOOLS = [
    {
        "name": "simulate_evaluate",
        "description": "Run Monte Carlo evaluation on OKRs and return markdown results with probability of success per KR",
        "inputSchema": {
            "type": "object",
            "properties": {
                "okrs_json": {
                    "type": "string",
                    "description": "OKRs JSON string with format: {\"okrs\": [{\"objective\": \"...\", \"key_results\": [...]}]}",
                }
            },
            "required": ["okrs_json"],
        },
    },
    {
        "name": "simulate_sensitivity",
        "description": "Run sensitivity analysis on each OKR variable and return a markdown ranking of variable impact",
        "inputSchema": {
            "type": "object",
            "properties": {
                "okrs_json": {
                    "type": "string",
                    "description": "OKRs JSON string with format: {\"okrs\": [{\"objective\": \"...\", \"key_results\": [...]}]}",
                }
            },
            "required": ["okrs_json"],
        },
    },
    {
        "name": "simulate_tornado",
        "description": "Run tornado sensitivity analysis with elasticity across -30% to +30% perturbations, returns ASCII chart",
        "inputSchema": {
            "type": "object",
            "properties": {
                "okrs_json": {
                    "type": "string",
                    "description": "OKRs JSON string with format: {\"okrs\": [{\"objective\": \"...\", \"key_results\": [...]}]}",
                }
            },
            "required": ["okrs_json"],
        },
    },
]


def _respond(id_val, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_val}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def _format_evaluate(results):
    lines = []
    lines.append("## Monte Carlo Evaluation Results")
    lines.append("")
    for okr_result in results:
        lines.append(f"### {okr_result['objective']}")
        lines.append("")
        lines.append(f"**Combined Probability:** {okr_result['combined_probability']:.2%}")
        lines.append(f"**Verdict:** {okr_result['verdict']}")
        lines.append("")
        lines.append("| Key Result | Expected Value | P(Success) | CI 95% (lower) | CI 95% (upper) | Std Dev |")
        lines.append("|------------|---------------|------------|----------------|----------------|---------|")
        for kr in okr_result["key_results"]:
            lines.append(
                f"| {kr['name']} | {kr['expected_value']} | {kr['probability_success']:.2%} "
                f"| {kr['ci_95_lower']} | {kr['ci_95_upper']} | {kr['std']} |"
            )
        lines.append("")
    return "\n".join(lines)


def _format_sensitivity(analyses):
    lines = []
    lines.append("## Sensitivity Analysis — Variable Impact Ranking")
    lines.append("")
    for analysis in analyses:
        lines.append(f"### {analysis['objective']}")
        lines.append("")
        lines.append(f"**Baseline Probability:** {analysis['baseline_probability']:.2%}")
        lines.append("")
        for kr in analysis["key_results"]:
            lines.append(f"#### {kr['name']} (baseline: {kr['baseline_probability']:.2%})")
            lines.append("")
            lines.append("| Variable | Base Prob | Low Prob | High Prob | Impact |")
            lines.append("|----------|----------|----------|-----------|--------|")
            for var in kr["variables"]:
                lines.append(
                    f"| {var['name']} | {var['base_probability']:.2%} "
                    f"| {var['low_probability']:.2%} | {var['high_probability']:.2%} "
                    f"| {var['impact']:.4f} |"
                )
            lines.append("")
    return "\n".join(lines)


def _format_tornado(charts):
    return "\n\n".join(charts)


def _run_mcp():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = msg.get("method")
        req_id = msg.get("id")
        params = msg.get("params") or {}
        if method == "initialize":
            _respond(req_id, {
                "protocolVersion": "2026-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mcp-simulate", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _respond(req_id, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                engine = SimulationEngine()
                if tool_name == "simulate_evaluate":
                    okrs_data = json.loads(args["okrs_json"])
                    results = engine.evaluate_okrs(okrs_data)
                    text = _format_evaluate(results)
                    _respond(req_id, {"content": [{"type": "text", "text": text}]})
                elif tool_name == "simulate_sensitivity":
                    okrs_data = json.loads(args["okrs_json"])
                    okrs_list = okrs_data.get("okrs", []) if isinstance(okrs_data, dict) else okrs_data
                    analyses = [engine.sensitivity_analysis(okr) for okr in okrs_list]
                    text = _format_sensitivity(analyses)
                    _respond(req_id, {"content": [{"type": "text", "text": text}]})
                elif tool_name == "simulate_tornado":
                    okrs_data = json.loads(args["okrs_json"])
                    okrs_list = okrs_data.get("okrs", []) if isinstance(okrs_data, dict) else okrs_data
                    charts = []
                    for okr in okrs_list:
                        result = engine.tornado_analysis(okr)
                        chart = engine.generate_tornado_chart(result)
                        charts.append(chart)
                    text = _format_tornado(charts)
                    _respond(req_id, {"content": [{"type": "text", "text": text}]})
                else:
                    _respond(req_id, error={"code": -32601, "message": f"Tool not found: {tool_name}"})
            except Exception as e:
                _respond(req_id, error={"code": -32603, "message": str(e)})
        elif method == "prompts/list":
            _respond(req_id, {"prompts": []})
        else:
            _respond(req_id, error={"code": -32601, "message": f"Method not found: {method}"})


if __name__ == "__main__":
    _run_mcp()
