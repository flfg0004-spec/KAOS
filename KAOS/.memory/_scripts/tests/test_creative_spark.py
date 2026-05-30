"""Tests for creative_spark.py — Creative divergence engine."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("KAOS_TESTING", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / ".tools"))

from creative_spark import (
    DIVERGENCE_TEMPLATES,
    generate_options,
    evaluate_options,
    format_evaluation_report,
    EVALUATION_CRITERIA,
)


class TestGenerateOptions:
    def test_generate_options_returns_list(self):
        result = generate_options("How to improve team velocity", count=3)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_generate_options_min_count(self):
        result = generate_options("Test problem", count=0)
        assert len(result) >= 1

    def test_generate_options_max_count(self):
        max_templates = len(DIVERGENCE_TEMPLATES)
        result = generate_options("Test problem", count=max_templates + 10)
        assert len(result) == max_templates

    def test_generate_options_contains_expected_keys(self):
        result = generate_options("Test problem", count=1)
        option = result[0]
        assert "template" in option
        assert "name" in option
        assert "prompt" in option
        assert "description" in option
        assert "problem" in option
        assert "option_text" in option

    def test_generate_options_different_problems(self):
        r1 = generate_options("Problem A", count=1)
        r2 = generate_options("Problem B", count=1)
        assert r1[0]["problem"] == "Problem A"
        assert r2[0]["problem"] == "Problem B"

    def test_generate_options_all_templates_used(self):
        for _ in range(100):
            result = generate_options("Test", count=5)
            templates_used = {o["template"] for o in result}
            if len(templates_used) == 5:
                break
        assert len(templates_used) == 5


class TestEvaluateOptions:
    @pytest.fixture
    def sample_options_file(self):
        options = {
            "options": [
                {
                    "name": "First Principles",
                    "template": "first_principles",
                    "option_text": "Test option A",
                },
                {
                    "name": "Inversion",
                    "template": "inversion",
                    "option_text": "Test option B",
                },
            ]
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(options, f)
            f.flush()
            path = f.name

        yield path
        Path(path).unlink(missing_ok=True)

    def test_evaluate_options_returns_scores(self, sample_options_file):
        results = evaluate_options(sample_options_file)
        assert isinstance(results, list)
        assert len(results) == 2

    def test_evaluate_options_contains_criteria(self, sample_options_file):
        results = evaluate_options(sample_options_file)
        for r in results:
            assert "name" in r
            assert "scores" in r
            assert "average" in r
            assert "recommended" in r
            for criterion in EVALUATION_CRITERIA:
                assert criterion in r["scores"]

    def test_evaluate_options_ranked(self, sample_options_file):
        results = evaluate_options(sample_options_file)
        for i in range(len(results) - 1):
            assert results[i]["average"] >= results[i + 1]["average"]

    def test_evaluate_options_invalid_file(self):
        with pytest.raises(SystemExit):
            evaluate_options("nonexistent_file_xyz.json")


class TestFormatEvaluationReport:
    def test_format_report_empty(self):
        report = format_evaluation_report([])
        assert isinstance(report, str)
        assert "Evaluation Report" in report

    def test_format_report_with_results(self):
        results = [
            {
                "name": "First Principles",
                "scores": {"impact": 3.5, "effort": 2.0, "risk": 2.5, "vision_alignment": 4.0},
                "average": 3.0,
                "recommended": True,
                "option_text": "Test content",
            }
        ]
        report = format_evaluation_report(results)
        assert "First Principles" in report
        assert "3.0" in report
        assert "Recommended" in report

    def test_format_report_top_option(self, sample_results):
        report = format_evaluation_report(sample_results)
        assert sample_results[0]["name"] in report
        for r in sample_results:
            assert r["name"] in report

    @pytest.fixture
    def sample_results(self):
        return [
            {
                "name": "Option A",
                "scores": {"impact": 4.0, "effort": 3.0, "risk": 2.5, "vision_alignment": 4.5},
                "average": 3.5,
                "recommended": True,
                "option_text": "Content A",
            },
            {
                "name": "Option B",
                "scores": {"impact": 2.0, "effort": 4.0, "risk": 3.0, "vision_alignment": 2.5},
                "average": 2.875,
                "recommended": False,
                "option_text": "Content B",
            },
        ]


class TestCLI:
    def test_cli_help(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[3] / ".tools" / "creative_spark.py"), "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[3],
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()

    def test_cli_generate(self):
        import subprocess
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve().parents[3] / ".tools" / "creative_spark.py"),
                "generate", "--problem", "Test problem", "--count", "2",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[3],
        )
        assert result.returncode == 0
        assert "Test problem" in result.stdout

    def test_cli_generate_output_file(self):
        import subprocess
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[3] / ".tools" / "creative_spark.py"),
                    "generate", "--problem", "Test", "--count", "1", "--output", out_path,
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[3],
            )
            assert result.returncode == 0
            assert Path(out_path).exists()
            data = json.loads(Path(out_path).read_text(encoding="utf-8"))
            assert "options" in data
            assert len(data["options"]) == 1
        finally:
            Path(out_path).unlink(missing_ok=True)

    def test_cli_evaluate(self):
        import subprocess
        options_data = {
            "options": [
                {"name": "Test Option", "template": "analogy", "option_text": "Test"}
            ]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(options_data, f)
            options_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[3] / ".tools" / "creative_spark.py"),
                    "evaluate", "--options", options_path,
                ],
                capture_output=True,
                text=True, encoding="utf-8", errors="replace",
                cwd=Path(__file__).resolve().parents[3],
            )
            assert result.returncode == 0
            assert "Evaluation Report" in result.stdout
        finally:
            Path(options_path).unlink(missing_ok=True)
