"""Architecture Smell Detection Pipeline — static analysis + LLM-as-a-Judge."""

import logging
import re

logger = logging.getLogger("smell_pipeline")

_HAS_DEEPEVAL = False
try:
    from deepeval.metrics import GEval
    from deepeval.test_case import LLMTestCase

    _HAS_DEEPEVAL = True
except ImportError:
    pass

SMELL_PATTERNS = {
    "architecture": [
        {"pattern": r"(god class|god object|blob)", "name": "god_class_reference", "severity": "high"},
        {"pattern": r"(circular\s*depend|cyclic\s*depend)", "name": "circular_dependency", "severity": "critical"},
        {"pattern": r"(shotgun\s*surg|ripple.*change)", "name": "shotgun_surgery", "severity": "high"},
    ],
    "code_quality": [
        {"pattern": r"(eval\(|exec\()", "name": "dangerous_eval", "severity": "critical"},
        {"pattern": r"(except\s*:\s*pass|except Exception:\s*pass)", "name": "silent_exception", "severity": "medium"},
        {"pattern": r"(TODO|FIXME|HACK|XXX)", "name": "unresolved_todo", "severity": "low"},
    ],
    "dependency": [
        {"pattern": r"(import\s+\*\s*$|from\s+\S+\s+import\s+\*)", "name": "wildcard_import", "severity": "medium"},
        {"pattern": r"(hardcod.*key|api_key\s*=)", "name": "hardcoded_secret", "severity": "critical"},
    ],
    "documentation": [
        {"pattern": r"^\s*def\s+\w+\(.*\):\s*\n(?!\s*\"\"\")", "name": "missing_docstring", "severity": "low"},
    ],
}


def static_scan(text: str) -> list:
    findings = []
    for category, patterns in SMELL_PATTERNS.items():
        for p in patterns:
            matches = list(re.finditer(p["pattern"], text, re.MULTILINE))
            for m in matches:
                line_num = text[: m.start()].count("\n") + 1
                findings.append(
                    {
                        "name": p["name"],
                        "severity": p["severity"],
                        "category": category,
                        "line": line_num,
                        "match": m.group()[:80],
                    }
                )
    return findings


def _llm_judge(text: str, task_type: str = "general") -> dict:
    if not _HAS_DEEPEVAL:
        return {"smell_count": 0, "issues": [], "note": "deepeval not available"}
    rubrics = {
        "architecture": "Analyze for: god objects, circular deps, layer violations",
        "code": "Analyze for: error handling gaps, security issues, performance",
        "strategy": "Analyze for: missing analysis, unsupported claims, vague recommendations",
    }
    try:
        rubric = rubrics.get(task_type, rubrics["architecture"])
        geval = GEval(name="smell_detection", criteria=rubric)
        test_case = LLMTestCase(input=rubric, actual_output=text)
        geval.measure(test_case)
        return {
            "smell_count": 1 if geval.score < 0.7 else 0,
            "quality_score": round(geval.score * 100, 1),
            "issues": [],
            "note": "llm_judge",
        }
    except Exception as e:
        return {"smell_count": 0, "issues": [], "note": f"llm_judge_error: {e}"}


def analyze(agent_output: str, task_type: str = "general") -> dict:
    static_findings = static_scan(agent_output)
    llm_result = _llm_judge(agent_output, task_type)
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in static_findings:
        sev = f["severity"]
        if sev in severity_counts:
            severity_counts[sev] += 1
    penalty = (
        severity_counts["critical"] * 15
        + severity_counts["high"] * 10
        + severity_counts["medium"] * 5
        + severity_counts["low"] * 2
    )
    llm_penalty = (1 - llm_result.get("quality_score", 100) / 100) * 20 if llm_result.get("quality_score") else 0
    overall_score = max(0, min(100, 100 - penalty - llm_penalty))
    return {
        "overall_score": round(overall_score, 1),
        "static_findings": static_findings,
        "static_count": len(static_findings),
        "severity_breakdown": severity_counts,
        "llm_assessment": llm_result,
        "has_critical": severity_counts["critical"] > 0,
        "has_high": severity_counts["high"] > 0,
    }
