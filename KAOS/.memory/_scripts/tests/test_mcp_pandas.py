"""Tests for mcp_pandas.py — quantitative data analysis tools."""
import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import mcp_pandas

pytest.importorskip("pandas")
pytest.importorskip("numpy")
pytest.importorskip("scipy")


# ── Fixtures ───────────────────────────────────────────────────


@pytest.fixture
def csv_numeric():
    """CSV with three numeric columns for correlation / analysis tests."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("a,b,c\n1.0,2.0,3.0\n4.0,5.0,6.0\n7.0,8.0,9.0\n")
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def csv_categorical():
    """CSV with a categorical group column and a numeric value column."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("group,value\nA,10.0\nA,20.0\nB,30.0\nB,40.0\n")
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def csv_empty():
    """CSV with header row but zero data rows."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("a,b,c\n")
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def csv_no_numeric():
    """CSV with only string / categorical columns."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("name,desc\nfoo,bar\nbaz,qux\n")
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


# ── analyze_csv ────────────────────────────────────────────────


class TestAnalyzeCsv:
    def test_valid(self, csv_numeric):
        result = mcp_pandas.analyze_csv(csv_numeric)
        assert "Descriptive Statistics" in result
        assert "Column Types" in result
        assert "a" in result

    def test_not_found(self):
        result = mcp_pandas.analyze_csv("/nonexistent/path.csv")
        assert "ERROR" in result
        assert "not found" in result

    def test_empty(self, csv_empty):
        result = mcp_pandas.analyze_csv(csv_empty)
        assert "ERROR" in result
        assert "empty" in result.lower()


# ── correlation_matrix ─────────────────────────────────────────


class TestCorrelationMatrix:
    def test_valid(self, csv_numeric):
        result = mcp_pandas.correlation_matrix(csv_numeric)
        assert "Correlation Matrix" in result
        assert "Pearson" in result
        assert "a" in result

    def test_no_numeric(self, csv_no_numeric):
        result = mcp_pandas.correlation_matrix(csv_no_numeric)
        assert "ERROR" in result
        assert "no numeric columns" in result.lower()


# ── trend_analysis ─────────────────────────────────────────────


class TestTrendAnalysis:

    @property
    def _valid_data(self):
        return json.dumps([
            {"date": "2024-01-01", "value": 100},
            {"date": "2024-02-01", "value": 110},
            {"date": "2024-03-01", "value": 105},
        ])

    def test_valid(self):
        result = mcp_pandas.trend_analysis(self._valid_data)
        assert "Trend Analysis" in result
        assert "Slope" in result

    def test_invalid_json(self):
        result = mcp_pandas.trend_analysis("not valid json")
        assert "ERROR" in result
        assert "invalid json" in result.lower()

    def test_empty_array(self):
        result = mcp_pandas.trend_analysis("[]")
        assert "ERROR" in result
        assert "data must be" in result.lower()

    def test_insufficient_data(self):
        result = mcp_pandas.trend_analysis(
            '[{"date":"2024-01-01","value":100}]'
        )
        assert "ERROR" in result
        assert "at least 2" in result.lower()


# ── compare_groups ─────────────────────────────────────────────


class TestCompareGroups:
    def test_valid(self, csv_categorical):
        result = mcp_pandas.compare_groups(csv_categorical, "group", "value")
        assert "Group Comparison" in result
        assert "ANOVA" in result

    def test_missing_group_column(self, csv_categorical):
        result = mcp_pandas.compare_groups(
            csv_categorical, "nonexistent", "value"
        )
        assert "ERROR" in result
        assert "not found" in result

    def test_missing_value_column(self, csv_categorical):
        result = mcp_pandas.compare_groups(
            csv_categorical, "group", "nonexistent"
        )
        assert "ERROR" in result
        assert "not found" in result

    def test_non_numeric_value(self, csv_no_numeric):
        result = mcp_pandas.compare_groups(csv_no_numeric, "name", "desc")
        assert "ERROR" in result
        assert "numeric" in result.lower()


# ── forecast_simple ────────────────────────────────────────────


class TestForecastSimple:

    @property
    def _valid_data(self):
        return json.dumps([
            {"date": "2024-01-01", "value": 100},
            {"date": "2024-02-01", "value": 110},
            {"date": "2024-03-01", "value": 120},
            {"date": "2024-04-01", "value": 130},
        ])

    def test_valid(self):
        result = mcp_pandas.forecast_simple(self._valid_data)
        assert "Linear Forecast" in result
        assert "Model" in result

    def test_insufficient_data(self):
        result = mcp_pandas.forecast_simple(
            '[{"date":"2024-01-01","value":100}]'
        )
        assert "ERROR" in result
        assert "at least 2" in result.lower()

    def test_invalid_json(self):
        result = mcp_pandas.forecast_simple("{bad json}")
        assert "ERROR" in result
        assert "invalid json" in result.lower()
