"""Tests for lib.strategy_analytics — BCG/OKR tracking and trends."""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def _clean_timeseries():
    """Ensure clean state for tests."""
    from lib.strategy_analytics import TIMESERIES_DIR
    f = TIMESERIES_DIR / "strategy.jsonl"
    if f.exists():
        f.unlink()


def test_track_bcg():
    from lib.strategy_analytics import track_bcg
    _clean_timeseries()
    state = {
        "topic": "test topic",
        "bcg_score": 8.5,
        "bcg_passed": True,
        "bcg_details": {
            "dimensions": {
                "structure": {"score": 4},
                "synthesis": {"score": 3},
                "rigor": {"score": 4},
            }
        },
        "okr_quality": {"score_100": 85, "passed": True, "total_okrs": 3},
    }
    track_bcg(state)
    from lib.strategy_analytics import TIMESERIES_DIR
    f = TIMESERIES_DIR / "strategy.jsonl"
    assert f.exists()
    content = f.read_text()
    assert "test topic" in content
    assert "8.5" in content


def test_get_trend_empty():
    from lib.strategy_analytics import get_trend
    _clean_timeseries()
    trend = get_trend(days=30)
    assert trend["data_points"] == 0
    assert trend["direction"] == "stable"


def test_get_trend_with_data():
    from lib.strategy_analytics import track_bcg, get_trend
    _clean_timeseries()
    for i in range(3):
        track_bcg({
            "topic": f"topic {i}",
            "bcg_score": 7.0 + i,
            "bcg_passed": True,
            "bcg_details": {"dimensions": {}},
            "okr_quality": {"score_100": 70 + i * 5, "passed": True, "total_okrs": 2},
        })
    trend = get_trend(days=30)
    assert trend["data_points"] >= 3
    assert "bcg" in trend["scores"][0]
    assert "okr" in trend["scores"][0]


def test_get_summary():
    from lib.strategy_analytics import get_summary, track_bcg
    _clean_timeseries()
    track_bcg({
        "topic": "test", "bcg_score": 8.0, "bcg_passed": True,
        "bcg_details": {"dimensions": {}},
        "okr_quality": {"score_100": 80, "passed": True, "total_okrs": 2},
    })
    summary = get_summary()
    assert "latest_bcg" in summary
    assert "trend" in summary
    assert "recommendation" in summary


def test_track_bcg_persists_dimensions():
    from lib.strategy_analytics import track_bcg
    from lib.strategy_analytics import TIMESERIES_DIR
    _clean_timeseries()
    track_bcg({
        "topic": "dim test",
        "bcg_score": 7.5,
        "bcg_passed": True,
        "bcg_details": {
            "dimensions": {
                "structure": {"score": 4},
                "ambiguity_handling": {"score": 3},
                "synthesis": {"score": 5},
            }
        },
        "okr_quality": {"score_100": 75, "passed": True, "total_okrs": 1},
    })
    f = TIMESERIES_DIR / "strategy.jsonl"
    last_line = f.read_text().strip().split("\n")[-1]
    data = json.loads(last_line)
    assert "dimension_scores" in data
    assert data["dimension_scores"]["structure"] == 4
    assert data["dimension_scores"]["synthesis"] == 5
