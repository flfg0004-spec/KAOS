"""Tests for lib.forecasting — score forecasting."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_status():
    from lib.forecasting import status

    s = status()
    assert "available" in s
    assert "data_points" in s
    assert "min_required" in s
    assert s["min_required"] == 5


def test_forecast_insufficient_data():
    from lib.forecasting import forecast_by_agent

    r = forecast_by_agent(days=1, forecast_horizon=7)
    assert r["status"] == "insufficient_data" or r["status"] == "success"


def test_moving_average_short():
    from lib.forecasting import moving_average

    r = moving_average([1, 2, 3], window=5)
    assert r == [1, 2, 3]


def test_moving_average_normal():
    from lib.forecasting import moving_average

    r = moving_average([1, 2, 3, 4, 5], window=3)
    assert len(r) == 5
    assert r[-1] == 4.0  # (3+4+5)/3


def test_moving_average_window_1():
    from lib.forecasting import moving_average

    r = moving_average([1, 2, 3], window=1)
    assert r == [1, 2, 3]


def test_summary():
    from lib.forecasting import summary

    r = summary(days=1)
    assert "status" in r
