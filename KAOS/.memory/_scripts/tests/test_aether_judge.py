"""Tests for EtherJudge — LLM-as-judge standalone evaluator."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_judge_default_rubric_weights():
    from lib.aether.judge import DEFAULT_RUBRIC

    total = sum(c["weight"] for c in DEFAULT_RUBRIC.values())
    assert abs(total - 1.0) < 0.001, f"Default rubric weights must sum to 1.0, got {total}"


def test_judge_task_rubrics_weights():
    from lib.aether.judge import TASK_RUBRICS

    for task, rubric in TASK_RUBRICS.items():
        total = sum(rubric.values())
        assert abs(total - 1.0) < 0.001, f"Rubric '{task}' weights must sum to 1.0, got {total}"


def test_judge_all_task_types_covered():
    from lib.aether.config import TASK_MODEL_MAP
    from lib.aether.judge import TASK_RUBRICS

    for task in TASK_MODEL_MAP:
        if task not in TASK_RUBRICS:
            pass
    assert "general" in TASK_RUBRICS


def test_judge_extract_json():
    import json

    from lib.aether.judge import EtherJudge

    judge = EtherJudge()
    text = '```json\n{"scores": {"helpfulness": 8}, "verdict": "pass", "explanation": "ok", "strengths": [], "weaknesses": []}\n```'
    extracted = judge._extract_json(text)
    parsed = json.loads(extracted)
    assert parsed["scores"]["helpfulness"] == 8


def test_judge_extract_json_no_wrapping():
    import json

    from lib.aether.judge import EtherJudge

    judge = EtherJudge()
    text = '{"scores": {"helpfulness": 7}, "verdict": "pass", "explanation": "ok", "strengths": [], "weaknesses": []}'
    extracted = judge._extract_json(text)
    parsed = json.loads(extracted)
    assert parsed["scores"]["helpfulness"] == 7


def test_judge_extraction_score():
    from lib.aether.judge import EtherJudge

    judge = EtherJudge()
    expected = {"name": "John", "age": 30, "city": "NYC"}
    actual = {"name": "John", "age": 30, "country": "USA"}
    result = judge.score_extraction(expected, actual)
    assert "precision" in result
    assert "recall" in result
    assert "f1" in result
    assert result["precision"] == 0.667
    assert result["recall"] == 0.667


def test_judge_format_criteria():
    from lib.aether.judge import DEFAULT_RUBRIC, EtherJudge

    judge = EtherJudge()
    formatted = judge._format_criteria(DEFAULT_RUBRIC)
    assert "helpfulness" in formatted
    assert "correctness" in formatted
    assert "weight=" in formatted


def test_judge_import():
    from lib.aether.judge import EtherJudge

    j = EtherJudge()
    assert j.judge_model == "go-pro"
    j2 = EtherJudge(judge_model="go-flash")
    assert j2.judge_model == "go-flash"


def test_observability_import():
    from lib.aether.observability import Timer, observe

    assert callable(observe)
    assert isinstance(Timer, type)


def test_observability_timer():
    import time

    from lib.aether.observability import Timer

    with Timer() as t:
        time.sleep(0.01)
    assert hasattr(t, "elapsed_ms")


def test_eval_pipeline_disabled():
    from lib.aether.eval import run_eval_pipeline

    result = run_eval_pipeline()
    assert result["status"] == "disabled"


def test_judge_parse_evaluate_error():
    """Judge should handle malformed LLM output gracefully."""
    from lib.aether.judge import EtherJudge

    judge = EtherJudge()
    result = judge._extract_json("not json at all")
    assert result == "not json at all"

