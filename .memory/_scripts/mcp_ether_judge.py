#!/usr/bin/env python3
"""MCP tool: ether_judge — LLM-as-judge para agentes KAOS.

Invocación: py -3 mcp_ether_judge.py --prompt "..." --response "..."
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from lib.aether.judge import EtherJudge


def handle_ether_judge(params: dict) -> str:
    """Evalúa un output usando LLM-as-judge.

    Args:
        params: {
            "prompt": str (required),
            "response": str (required),
            "task_type": str (optional, default "general"),
            "judge_model": str (optional, default "go-pro"),
        }
    Returns: str (JSON)
    """
    prompt = params.get("prompt", "")
    response = params.get("response", "")
    task_type = params.get("task_type", "general")
    judge_model = params.get("judge_model", "go-pro")

    if not prompt or not response:
        return json.dumps({"error": "prompt and response are required"})

    judge = EtherJudge(judge_model=judge_model)
    result = judge.evaluate(prompt, response, task_type=task_type)
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EtherJudge — LLM-as-judge")
    parser.add_argument("--prompt", required=True, help="The original prompt")
    parser.add_argument("--response", required=True, help="The model response to evaluate")
    parser.add_argument("--task-type", default="general", help="Task type (general, code_gen, extract, etc.)")
    parser.add_argument("--judge-model", default="go-pro", help="Judge model (default: go-pro)")
    args = parser.parse_args()

    result = handle_ether_judge(
        {
            "prompt": args.prompt,
            "response": args.response,
            "task_type": args.task_type,
            "judge_model": args.judge_model,
        }
    )
    print(result)

