"""Tests for lib.pdf_chart_engine — chart generation functions."""

import pytest
from lib.pdf_chart_engine import (
    create_bar_chart,
    create_gauge_chart,
    create_heatmap,
    create_line_chart,
    create_pie_chart,
    create_radar_chart,
    create_waterfall_chart,
    generate_chart,
)

# ── Valid data fixtures ──


def test_create_bar_chart():
    """Valid bar chart data returns a non-empty base64 string."""
    data = {"x": ["A", "B", "C"], "y": [10, 20, 15]}
    result = create_bar_chart(data, "Test Bar")
    assert isinstance(result, str)
    assert len(result) > 0


def test_create_bar_chart_missing_keys():
    """Missing 'x' or 'y' keys raises ValueError."""
    with pytest.raises(ValueError, match="create_bar_chart requires"):
        create_bar_chart({"x": ["A"]}, "Test")
    with pytest.raises(ValueError, match="create_bar_chart requires"):
        create_bar_chart({"y": [1]}, "Test")


def test_create_line_chart():
    """Valid line chart data returns a non-empty base64 string."""
    data = {"x": [1, 2, 3], "y": [10, 20, 15]}
    result = create_line_chart(data, "Test Line")
    assert isinstance(result, str)
    assert len(result) > 0


def test_create_line_chart_missing_keys():
    """Missing 'x' or 'y' keys raises ValueError."""
    with pytest.raises(ValueError, match="create_line_chart requires"):
        create_line_chart({"x": [1]}, "Test")
    with pytest.raises(ValueError, match="create_line_chart requires"):
        create_line_chart({"y": [1]}, "Test")


def test_create_pie_chart():
    """Valid pie chart data returns a non-empty base64 string."""
    data = {"labels": ["A", "B", "C"], "values": [30, 50, 20]}
    result = create_pie_chart(data, "Test Pie")
    assert isinstance(result, str)
    assert len(result) > 0


def test_create_pie_chart_missing_keys():
    """Missing 'labels' or 'values' keys raises ValueError."""
    with pytest.raises(ValueError, match="create_pie_chart requires"):
        create_pie_chart({"labels": ["A"]}, "Test")
    with pytest.raises(ValueError, match="create_pie_chart requires"):
        create_pie_chart({"values": [1]}, "Test")


class TestCreateRadarChart:
    """Tests for create_radar_chart — validation + valid path."""

    def test_valid(self):
        """Valid radar chart data returns a non-empty base64 string."""
        data = {"labels": ["Speed", "Quality", "Cost"], "values": [80, 90, 70]}
        result = create_radar_chart(data, "Test Radar")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_missing_values_key(self):
        """Missing 'values' key raises ValueError."""
        data = {"labels": ["A", "B"]}
        with pytest.raises(ValueError, match="create_radar_chart requires.*values.*labels"):
            create_radar_chart(data, "Test")

    def test_missing_labels_key(self):
        """Missing 'labels' key raises ValueError."""
        data = {"values": [1, 2, 3]}
        with pytest.raises(ValueError, match="create_radar_chart requires.*values.*labels"):
            create_radar_chart(data, "Test")


class TestCreateGaugeChart:
    """Tests for create_gauge_chart."""

    def test_valid(self):
        """Valid gauge chart data returns a non-empty base64 string."""
        result = create_gauge_chart(75.5, "Test Gauge")
        assert isinstance(result, str)
        assert len(result) > 0


class TestCreateHeatmap:
    """Tests for create_heatmap — validation + valid path."""

    def test_valid(self):
        """Valid heatmap data returns a non-empty base64 string."""
        data = {"z": [[1, 2], [3, 4]], "x": ["A", "B"], "y": ["X", "Y"]}
        result = create_heatmap(data, "Test Heatmap")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_missing_z_key(self):
        """Missing 'z' key raises ValueError."""
        data = {"x": ["A", "B"], "y": ["X", "Y"]}
        with pytest.raises(ValueError, match="create_heatmap requires.*z"):
            create_heatmap(data, "Test")


class TestCreateWaterfallChart:
    """Tests for create_waterfall_chart — validation + valid path."""

    def test_valid(self):
        """Valid waterfall chart data returns a non-empty base64 string."""
        data = {"x": ["Start", "Revenue", "Costs", "Profit"], "y": [0, 1000, -300, 700]}
        result = create_waterfall_chart(data, "Test Waterfall")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_missing_x_key(self):
        """Missing 'x' key raises ValueError."""
        data = {"y": [1, 2, 3]}
        with pytest.raises(ValueError, match="create_waterfall_chart requires.*x.*y"):
            create_waterfall_chart(data, "Test")

    def test_missing_y_key(self):
        """Missing 'y' key raises ValueError."""
        data = {"x": ["A", "B", "C"]}
        with pytest.raises(ValueError, match="create_waterfall_chart requires.*x.*y"):
            create_waterfall_chart(data, "Test")


class TestGenerateChart:
    """Tests for the generate_chart factory function."""

    def test_dispatch_bar(self):
        """Factory dispatches to create_bar_chart correctly."""
        data = {"x": ["A", "B"], "y": [10, 20]}
        result = generate_chart("bar", data, "Factory Bar")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_dispatch_gauge(self):
        """Factory dispatches to create_gauge_chart correctly."""
        result = generate_chart("gauge", {"value": 50}, "Factory Gauge")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unknown_type(self):
        """Unknown chart type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown chart type"):
            generate_chart("nonexistent", {}, "Unknown")
