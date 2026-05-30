"""EtherJudge — LLM-as-judge standalone evaluator.

Invocado explícitamente, no automático.
Evalúa calidad de outputs en 6 dimensiones con rúbrica multi-dimensional.
"""

import json
import logging
from typing import Optional

_LOG = logging.getLogger(__name__)

DEFAULT_RUBRIC = {
    "helpfulness": {
        "weight": 0.15,
        "description": "Does the response address the user's actual need?",
    },
    "correctness": {
        "weight": 0.30,
        "description": "Is the factual information accurate and free of errors?",
    },
    "coherence": {
        "weight": 0.15,
        "description": "Is the response logically structured and well-organized?",
    },
    "completeness": {
        "weight": 0.20,
        "description": "Does the response cover all necessary aspects of the query?",
    },
    "conciseness": {
        "weight": 0.10,
        "description": "Is the response appropriately concise without missing key info?",
    },
    "format_adherence": {
        "weight": 0.10,
        "description": "Does the response follow the requested format?",
    },
}

TASK_RUBRICS = {
    "extract": {
        "correctness": 0.35,
        "format_adherence": 0.30,
        "completeness": 0.20,
        "coherence": 0.10,
        "helpfulness": 0.05,
        "conciseness": 0.00,
    },
    "code_gen": {
        "correctness": 0.40,
        "coherence": 0.20,
        "completeness": 0.15,
        "conciseness": 0.10,
        "helpfulness": 0.10,
        "format_adherence": 0.05,
    },
    "code_simple": {
        "correctness": 0.40,
        "coherence": 0.20,
        "completeness": 0.15,
        "conciseness": 0.15,
        "helpfulness": 0.10,
        "format_adherence": 0.00,
    },
    "code_agentic": {
        "correctness": 0.35,
        "completeness": 0.25,
        "coherence": 0.15,
        "helpfulness": 0.15,
        "conciseness": 0.10,
        "format_adherence": 0.00,
    },
    "research": {
        "correctness": 0.35,
        "completeness": 0.30,
        "coherence": 0.15,
        "helpfulness": 0.10,
        "conciseness": 0.10,
        "format_adherence": 0.00,
    },
    "analyze": {
        "correctness": 0.30,
        "completeness": 0.25,
        "coherence": 0.20,
        "helpfulness": 0.15,
        "conciseness": 0.10,
        "format_adherence": 0.00,
    },
    "synthesize": {
        "completeness": 0.30,
        "coherence": 0.25,
        "correctness": 0.20,
        "helpfulness": 0.15,
        "conciseness": 0.10,
        "format_adherence": 0.00,
    },
    "strategy": {
        "helpfulness": 0.30,
        "coherence": 0.25,
        "completeness": 0.20,
        "correctness": 0.15,
        "conciseness": 0.10,
        "format_adherence": 0.00,
    },
    "verify": {
        "correctness": 0.40,
        "completeness": 0.25,
        "coherence": 0.15,
        "conciseness": 0.10,
        "helpfulness": 0.10,
        "format_adherence": 0.00,
    },
    "cross_check": {
        "correctness": 0.40,
        "completeness": 0.25,
        "coherence": 0.15,
        "conciseness": 0.10,
        "helpfulness": 0.10,
        "format_adherence": 0.00,
    },
    "lint": {
        "correctness": 0.35,
        "format_adherence": 0.25,
        "completeness": 0.20,
        "coherence": 0.10,
        "conciseness": 0.10,
        "helpfulness": 0.00,
    },
    "health": {
        "correctness": 0.30,
        "completeness": 0.25,
        "coherence": 0.15,
        "format_adherence": 0.15,
        "conciseness": 0.10,
        "helpfulness": 0.05,
    },
    "hydrate": {
        "completeness": 0.35,
        "correctness": 0.25,
        "coherence": 0.15,
        "helpfulness": 0.15,
        "format_adherence": 0.10,
        "conciseness": 0.00,
    },
    "wikilinks": {
        "correctness": 0.35,
        "format_adherence": 0.25,
        "completeness": 0.20,
        "coherence": 0.10,
        "conciseness": 0.10,
        "helpfulness": 0.00,
    },
    "curation": {
        "completeness": 0.30,
        "correctness": 0.25,
        "coherence": 0.15,
        "format_adherence": 0.15,
        "conciseness": 0.10,
        "helpfulness": 0.05,
    },
    "adr": {
        "coherence": 0.25,
        "completeness": 0.25,
        "correctness": 0.20,
        "format_adherence": 0.15,
        "conciseness": 0.10,
        "helpfulness": 0.05,
    },
    "factual": {
        "correctness": 0.40,
        "completeness": 0.25,
        "coherence": 0.15,
        "conciseness": 0.10,
        "helpfulness": 0.10,
        "format_adherence": 0.00,
    },
    "diversity": {
        "helpfulness": 0.30,
        "completeness": 0.20,
        "coherence": 0.20,
        "correctness": 0.15,
        "conciseness": 0.10,
        "format_adherence": 0.05,
    },
    "general": {
        "helpfulness": 0.20,
        "correctness": 0.25,
        "coherence": 0.15,
        "completeness": 0.15,
        "conciseness": 0.15,
        "format_adherence": 0.10,
    },
}

JUDGE_PROMPT_TEMPLATE = """You are an expert LLM judge evaluating model outputs. Score the following response on 6 dimensions from 1-10.

## Task Context
The user asked the model to perform this task:
{task_type}

## User Prompt
{prompt}

## Model Response
{response}

## Scoring Rubric
{criteria_text}

## Instructions
- Score each dimension 1-10 (1=worst, 10=best)
- Be strict but fair — a score of 7 means "good but has room for improvement"
- Provide a brief explanation for each score

## Output Format
Return ONLY valid JSON:
```json
{{
  "scores": {{
    "helpfulness": 7,
    "correctness": 8,
    "coherence": 6,
    "completeness": 7,
    "conciseness": 9,
    "format_adherence": 10
  }},
  "verdict": "pass",
  "explanation": "<brief explanation>",
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1", "weakness2"]
}}
```
"""


class EtherJudge:
    """LLM-as-judge evaluator. Invocado explícitamente, no automático."""

    def __init__(self, judge_model: str = "go-pro"):
        self.judge_model = judge_model

    def evaluate(self, prompt: str, response: str, task_type: str = "general", criteria: dict = None) -> dict:
        """Evalúa un output contra criterios.

        Returns: {
            "scores": dict, "weighted_score": float,
            "verdict": "pass"|"warn"|"fail",
            "explanation": str, "strengths": [], "weaknesses": []
        }
        """
        rubric = criteria if criteria else TASK_RUBRICS.get(task_type, DEFAULT_RUBRIC)
        criteria_text = self._format_criteria(rubric)

        judge_prompt = JUDGE_PROMPT_TEMPLATE.format(
            task_type=task_type,
            prompt=prompt,
            response=response,
            criteria_text=criteria_text,
        )

        from lib.llm import agent_llm_call

        result = agent_llm_call(
            agent="ether_judge",
            prompt=judge_prompt,
            model_override=self.judge_model,
            task_type="verify",
            temperature=0.1,
        )

        try:
            json_str = self._extract_json(result)
            parsed = json.loads(json_str)

            weights = (
                rubric
                if all(isinstance(v, (int, float)) for v in rubric.values())
                else {k: v["weight"] for k, v in rubric.items()}
            )

            weighted = sum(parsed["scores"].get(dim, 0) * weights.get(dim, 0) / 10.0 for dim in weights)
            parsed["weighted_score"] = round(weighted, 2)

            if weighted >= 7.0:
                parsed["verdict"] = "pass"
            elif weighted >= 4.0:
                parsed["verdict"] = "warn"
            else:
                parsed["verdict"] = "fail"

            return parsed

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            _LOG.warning("EtherJudge: failed to parse judge output: %s", e)
            return {
                "scores": {},
                "weighted_score": 0.0,
                "verdict": "error",
                "explanation": f"Failed to parse judge response: {e}",
                "strengths": [],
                "weaknesses": [],
                "raw_judge_output": result,
            }

    def evaluate_batch(self, pairs: list[dict], task_type: str = "general") -> list[dict]:
        """Evalúa múltiples pares prompt/response."""
        results = []
        for pair in pairs:
            result = self.evaluate(
                prompt=pair["prompt"],
                response=pair["response"],
                task_type=pair.get("task_type", task_type),
            )
            results.append(result)
        return results

    def score_extraction(self, expected: dict, actual: dict) -> dict:
        """Métrica específica para tareas de extracción JSON."""
        expected_keys = set(expected.keys())
        actual_keys = set(actual.keys())

        precision = len(expected_keys & actual_keys) / max(len(actual_keys), 1)
        recall = len(expected_keys & actual_keys) / max(len(expected_keys), 1)
        f1 = 2 * precision * recall / max(precision + recall, 0.001)

        value_match = sum(1 for k in expected_keys & actual_keys if str(expected[k]) == str(actual[k])) / max(
            len(expected_keys & actual_keys), 1
        )

        return {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "value_accuracy": round(value_match, 3),
        }

    def score_code(self, prompt: str, code: str) -> dict:
        """Métrica específica para generación de código."""
        return self.evaluate(prompt, code, task_type="code_gen", criteria=TASK_RUBRICS["code_gen"])

    def _format_criteria(self, rubric: dict) -> str:
        lines = []
        for dim, config in rubric.items():
            if isinstance(config, dict):
                lines.append(f"- {dim} (weight={config.get('weight', 0):.0%}): {config.get('description', '')}")
            else:
                lines.append(f"- {dim}: {config}")
        return "\n".join(lines)

    def _extract_json(self, text: str) -> str:
        """Extrae JSON de un string que puede tener markdown wrapping."""
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()
