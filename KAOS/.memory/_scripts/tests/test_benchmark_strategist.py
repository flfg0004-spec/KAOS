"""Tests for benchmark_strategist.py."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / ".tools"))
from benchmark_strategist import StrategistBenchmark


class TestStrategistBenchmark:
    def test_load_case_valid(self):
        b = StrategistBenchmark()
        case_data = {
            "problem": "X",
            "context": {},
            "human_decision": {"dimensions": {"clarity": 8}},
            "human_outcome": 7.5,
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(case_data, f)
            path = f.name
        case = b.load_case(path)
        assert "problem" in case
        assert "human_decision" in case
        assert case["problem"] == "X"
        assert case["human_decision"]["dimensions"]["clarity"] == 8
        assert case["human_outcome"] == 7.5
        Path(path).unlink()

    def test_load_case_not_found(self):
        b = StrategistBenchmark()
        try:
            b.load_case("/nonexistent/path.json")
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_evaluate_metis_decision_returns_scores(self):
        b = StrategistBenchmark()
        case = {
            "problem": "Increase market share by 20% in Q3",
            "context": {"industry": "tech", "team_size": 15, "okrs": ["launch feature"]},
        }
        result = b.evaluate_metis_decision(case)
        assert isinstance(result, dict)
        assert "dimensions" in result
        assert "composite_score" in result
        assert isinstance(result["composite_score"], (int, float))

    def test_evaluate_metis_decision_all_dimensions(self):
        b = StrategistBenchmark()
        expected = {"clarity", "measurability", "realism", "risk_awareness", "creativity", "actionability"}
        case = {
            "problem": "Expand to Latin America with a localized product",
            "context": {
                "goal": "30% growth",
                "target": "new markets",
                "metric": "revenue",
                "fecha": "2026-12",
                "riesgo": "currency fluctuation",
                "opcion": "partner model",
                "paso": "pilot in Mexico",
            },
        }
        result = b.evaluate_metis_decision(case)
        assert set(result["dimensions"].keys()) == expected
        for dim in expected:
            assert 1 <= result["dimensions"][dim] <= 10

    def test_compare_decisions_metis_wins(self):
        b = StrategistBenchmark()
        human = {
            "dimensions": {"clarity": 3, "measurability": 2, "realism": 4, "risk_awareness": 3, "creativity": 2, "actionability": 3},
            "composite_score": 2.8,
        }
        metis = {
            "dimensions": {"clarity": 8, "measurability": 7, "realism": 8, "risk_awareness": 6, "creativity": 7, "actionability": 8},
            "composite_score": 7.3,
        }
        result = b.compare_decisions(human, metis)
        assert result["overall"]["winner"] == "metis"
        assert result["overall"]["delta"] > 0

    def test_compare_decisions_human_wins(self):
        b = StrategistBenchmark()
        human = {
            "dimensions": {"clarity": 9, "measurability": 8, "realism": 9, "risk_awareness": 8, "creativity": 8, "actionability": 9},
            "composite_score": 8.5,
        }
        metis = {
            "dimensions": {"clarity": 4, "measurability": 3, "realism": 5, "risk_awareness": 3, "creativity": 4, "actionability": 4},
            "composite_score": 3.8,
        }
        result = b.compare_decisions(human, metis)
        assert result["overall"]["winner"] == "human"
        assert result["overall"]["delta"] < 0

    def test_compare_decisions_tie(self):
        b = StrategistBenchmark()
        human = {
            "dimensions": {"clarity": 6, "measurability": 6, "realism": 6, "risk_awareness": 6, "creativity": 6, "actionability": 6},
            "composite_score": 6.0,
        }
        metis = {
            "dimensions": {"clarity": 6, "measurability": 6, "realism": 6, "risk_awareness": 6, "creativity": 6, "actionability": 6},
            "composite_score": 6.0,
        }
        result = b.compare_decisions(human, metis)
        assert result["overall"]["winner"] == "tie"
        assert result["overall"]["delta"] == 0

    def test_generate_report_empty(self):
        b = StrategistBenchmark()
        report = b.generate_report([])
        assert isinstance(report, str)
        assert "Cases evaluated" in report
        assert "0" in report[:200]

    def test_generate_report_one_case(self):
        b = StrategistBenchmark()
        case_result = {
            "case_name": "Test Case",
            "comparison": {
                "overall": {"human_composite": 5.0, "metis_composite": 7.0, "delta": 2.0, "winner": "metis"},
                "dimensions": {"clarity": {"human": 5, "metis": 7, "delta": 2.0, "winner": "metis"}},
            },
        }
        report = b.generate_report([case_result])
        assert isinstance(report, str)
        assert "Test Case" in report
        assert "Metis" in report
        assert "Human" in report

    def test_cli_help(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[3] / ".tools" / "benchmark_strategist.py"), "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower()
