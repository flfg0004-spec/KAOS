#!/usr/bin/env python3
"""MCP server + CLI: quantitative data analysis with pandas, numpy, scipy.

Dual-mode:
  CLI:  py -3 mcp_pandas.py <tool> [args]
  MCP:  stdio JSON-RPC server (start without args)

Tools: analyze_csv, correlation_matrix, trend_analysis, compare_groups, forecast_simple
All output is markdown for LLM consumption.
"""

import csv
import io
import json
import math
import os
import sys
from pathlib import Path

_HAS_PANDAS = False
try:
    import pandas as pd
    import numpy as np
    from scipy import stats as sp_stats
    _HAS_PANDAS = True
except ImportError:
    pd = np = sp_stats = None

_HAS_FASTMCP = False
try:
    from mcp.server.fastmcp import FastMCP
    _HAS_FASTMCP = True
except ImportError:
    FastMCP = None


def _require_pandas():
    if not _HAS_PANDAS:
        print("ERROR: pandas/numpy/scipy not installed. Run: pip install pandas numpy scipy", file=sys.stderr)
        sys.exit(1)


def _load_csv(path):
    _require_pandas()
    p = Path(path)
    if not p.exists():
        return None, f"ERROR: file not found: {path}"
    try:
        df = pd.read_csv(p, encoding="utf-8", engine="python")
    except Exception:
        try:
            df = pd.read_csv(p, encoding="latin-1", engine="python")
        except Exception as e:
            return None, f"ERROR: could not read CSV: {e}"
    if df.empty:
        return None, "ERROR: CSV is empty"
    return df, None


def _markdown_table(rows, headers):
    if not rows:
        return "_empty_"
    out = []
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    out.append("| " + " | ".join(headers) + " |")
    out.append(sep)
    for r in rows:
        vals = [str(v) if v is not None else "" for v in r]
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def analyze_csv(path):
    if not _HAS_PANDAS:
        return "ERROR: pandas/numpy/scipy not installed. Run: pip install pandas numpy scipy"
    df, err = _load_csv(path)
    if err:
        return err
    buf = io.StringIO()
    buf.write(f"## CSV Analysis: `{path}`\n\n")
    buf.write(f"**Rows:** {len(df)} | **Columns:** {len(df.columns)}\n\n")
    dtypes = df.dtypes.to_dict()
    type_rows = []
    for col, dt in dtypes.items():
        type_rows.append((col, str(dt)))
    buf.write("### Column Types\n\n")
    buf.write(_markdown_table(type_rows, ["Column", "Type"]))
    buf.write("\n\n")
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        buf.write("### Descriptive Statistics (numeric columns)\n\n")
        desc = df[num_cols].describe(percentiles=[0.25, 0.5, 0.75]).transpose()
        stat_rows = []
        for col in desc.index:
            r = desc.loc[col]
            stat_rows.append((
                col,
                _fmt(r.get("count", 0)),
                _fmt(r.get("mean", 0)),
                _fmt(r.get("std", 0)),
                _fmt(r.get("min", 0)),
                _fmt(r.get("25%", 0)),
                _fmt(r.get("50%", 0)),
                _fmt(r.get("75%", 0)),
                _fmt(r.get("max", 0)),
            ))
        buf.write(_markdown_table(stat_rows, [
            "Column", "Count", "Mean", "Std", "Min", "Q1", "Median", "Q3", "Max"
        ]))
        buf.write("\n\n")
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if cat_cols:
        buf.write("### Categorical Columns (top 5 values)\n\n")
        for col in cat_cols:
            top = df[col].value_counts().head(5)
            buf.write(f"**{col}:** {df[col].nunique()} unique values\n\n")
            val_rows = [(str(k), _fmt(v), _fmt(v / len(df) * 100) + "%") for k, v in top.items()]
            buf.write(_markdown_table(val_rows, ["Value", "Count", "%"]) + "\n\n")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        buf.write("### Missing Values\n\n")
        miss_rows = [(col, _fmt(missing[col]), _fmt(missing[col] / len(df) * 100) + "%") for col in missing.index]
        buf.write(_markdown_table(miss_rows, ["Column", "Missing", "%"]) + "\n\n")
    return buf.getvalue()


def correlation_matrix(path, columns=None):
    if not _HAS_PANDAS:
        return "ERROR: pandas/numpy/scipy not installed. Run: pip install pandas numpy scipy"
    df, err = _load_csv(path)
    if err:
        return err
    num_df = df.select_dtypes(include=[np.number])
    if num_df.empty:
        return "ERROR: no numeric columns found in CSV"
    if columns:
        valid = [c for c in columns if c in num_df.columns]
        if not valid:
            return f"ERROR: none of the specified columns exist or are numeric: {columns}"
        num_df = num_df[valid]
    corr = num_df.corr(method="pearson")
    buf = io.StringIO()
    buf.write(f"## Correlation Matrix: `{path}`\n\n")
    buf.write(f"**Columns:** {', '.join(corr.columns)}\n\n")
    headers = ["Column"] + list(corr.columns)
    rows = []
    for col in corr.columns:
        row = [col]
        for other in corr.columns:
            val = corr.loc[col, other]
            row.append(f"{val:.4f}")
        rows.append(row)
    buf.write(_markdown_table(rows, headers))
    buf.write("\n\n")
    pairs = []
    for i in range(len(corr.columns)):
        for j in range(i + 1, len(corr.columns)):
            pairs.append((corr.columns[i], corr.columns[j], corr.iloc[i, j]))
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    if pairs:
        buf.write("### Top Correlations\n\n")
        top_rows = [(a, b, f"{v:.4f}") for a, b, v in pairs[:10]]
        buf.write(_markdown_table(top_rows, ["Column A", "Column B", "Pearson r"]))
        buf.write("\n")
    return buf.getvalue()


def trend_analysis(data_json, period="monthly"):
    if not _HAS_PANDAS:
        return "ERROR: pandas/numpy/scipy not installed. Run: pip install pandas numpy scipy"
    try:
        data = json.loads(data_json) if isinstance(data_json, str) else data_json
    except (json.JSONDecodeError, TypeError) as e:
        return f"ERROR: invalid JSON: {e}"
    if not data or not isinstance(data, list):
        return "ERROR: data must be a JSON array of objects with 'date' and 'value' fields"
    try:
        df = pd.DataFrame(data)
        if "date" not in df.columns or "value" not in df.columns:
            return "ERROR: each entry must have 'date' and 'value' fields"
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
    except Exception as e:
        return f"ERROR: could not parse time series: {e}"
    if len(df) < 2:
        return "ERROR: need at least 2 data points"
    if period == "monthly":
        df["period"] = df["date"].dt.to_period("M").astype(str)
    elif period == "weekly":
        df["period"] = df["date"].dt.to_period("W").astype(str)
    elif period == "daily":
        df["period"] = df["date"].dt.to_period("D").astype(str)
    elif period == "quarterly":
        df["period"] = df["date"].dt.to_period("Q").astype(str)
    elif period == "yearly":
        df["period"] = df["date"].dt.to_period("Y").astype(str)
    else:
        df["period"] = df["date"].dt.to_period("M").astype(str)
    grouped = df.groupby("period", sort=True)["value"].mean().reset_index()
    vals = grouped["value"].values
    periods = grouped["period"].tolist()
    x = np.arange(len(vals))
    if len(vals) >= 2:
        slope, intercept, r_val, p_val, std_err = sp_stats.linregress(x, vals)
        trend_dir = "increasing" if slope > 0 else ("decreasing" if slope < 0 else "stable")
    else:
        slope = 0
        trend_dir = "insufficient_data"
    window = max(3, min(len(vals) // 3, 6))
    if len(vals) >= window:
        ma = pd.Series(vals).rolling(window=window, min_periods=1).mean().values
    else:
        ma = vals.copy()
    buf = io.StringIO()
    buf.write(f"## Trend Analysis ({period})\n\n")
    buf.write(f"**Trend:** {trend_dir} | **Slope:** {slope:.4f} | **Data points:** {len(vals)}\n\n")
    headers = ["Period", "Avg Value", "Change %", "Moving Avg", "Trend"]
    rows = []
    for i in range(len(periods)):
        chg = ""
        if i > 0 and vals[i - 1] != 0:
            chg = f"{((vals[i] - vals[i - 1]) / vals[i - 1] * 100):.2f}%"
        elif i == 0:
            chg = "—"
        trend_str = "↑" if (i > 0 and vals[i] > vals[i - 1]) else ("↓" if (i > 0 and vals[i] < vals[i - 1]) else "→")
        rows.append((
            periods[i],
            _fmt(vals[i]),
            chg,
            _fmt(ma[i]),
            trend_str,
        ))
    buf.write(_markdown_table(rows, headers))
    buf.write("\n")
    return buf.getvalue()


def compare_groups(path, group_col, value_col):
    if not _HAS_PANDAS:
        return "ERROR: pandas/numpy/scipy not installed. Run: pip install pandas numpy scipy"
    df, err = _load_csv(path)
    if err:
        return err
    if group_col not in df.columns:
        return f"ERROR: group column '{group_col}' not found"
    if value_col not in df.columns:
        return f"ERROR: value column '{value_col}' not found"
    if not pd.api.types.is_numeric_dtype(df[value_col]):
        return f"ERROR: value column '{value_col}' must be numeric"
    groups = df.groupby(group_col)[value_col]
    stats_df = groups.agg(["count", "mean", "std", "min", "max", "median"])
    stats_df = stats_df.dropna()
    anova = None
    unique_groups = df[group_col].dropna().unique()
    if len(unique_groups) >= 2:
        group_vals = [df[df[group_col] == g][value_col].dropna().values for g in unique_groups]
        valid = [g for g in group_vals if len(g) > 0]
        if len(valid) >= 2:
            try:
                f_stat, p_value = sp_stats.f_oneway(*valid)
                anova = (f"{f_stat:.4f}", f"{p_value:.4f}")
            except Exception:
                anova = None
    buf = io.StringIO()
    buf.write(f"## Group Comparison\n\n")
    buf.write(f"**Group by:** {group_col} | **Value:** {value_col}\n\n")
    if anova:
        buf.write(f"**ANOVA:** F={anova[0]}, p={anova[1]}\n\n")
    headers = ["Group", "Count", "Mean", "Std", "Min", "Max", "Median"]
    rows = []
    for grp_name, grp_stats in stats_df.iterrows():
        rows.append((
            str(grp_name),
            _fmt(grp_stats["count"]),
            _fmt(grp_stats["mean"]),
            _fmt(grp_stats["std"]),
            _fmt(grp_stats["min"]),
            _fmt(grp_stats["max"]),
            _fmt(grp_stats["median"]),
        ))
    buf.write(_markdown_table(rows, headers))
    buf.write("\n")
    return buf.getvalue()


def forecast_simple(data_json, periods=3):
    if not _HAS_PANDAS:
        return "ERROR: pandas/numpy/scipy not installed. Run: pip install pandas numpy scipy"
    try:
        data = json.loads(data_json) if isinstance(data_json, str) else data_json
    except (json.JSONDecodeError, TypeError) as e:
        return f"ERROR: invalid JSON: {e}"
    if not data or not isinstance(data, list):
        return "ERROR: data must be a JSON array of objects with 'date' and 'value' fields"
    try:
        df = pd.DataFrame(data)
        if "date" not in df.columns or "value" not in df.columns:
            return "ERROR: each entry must have 'date' and 'value' fields"
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
    except Exception as e:
        return f"ERROR: could not parse time series: {e}"
    if len(df) < 2:
        return "ERROR: need at least 2 data points for forecasting"
    vals = df["value"].values
    x = np.arange(len(vals))
    try:
        slope, intercept, r_val, p_val, std_err = sp_stats.linregress(x, vals)
    except Exception as e:
        return f"ERROR: regression failed: {e}"
    residuals = vals - (slope * x + intercept)
    residual_std = np.std(residuals) if len(residuals) > 1 else 0
    last_date = df["date"].max()
    freq = _infer_freq(df["date"])
    buf = io.StringIO()
    buf.write(f"## Simple Linear Forecast\n\n")
    buf.write(f"**Model:** y = {slope:.4f} * x + {intercept:.4f}\n")
    buf.write(f"**R²:** {r_val ** 2:.4f} | **Std Err:** {std_err:.4f}\n\n")
    headers = ["Period", "Forecast Value", "CI Lower (95%)", "CI Upper (95%)"]
    rows = []
    for i in range(1, periods + 1):
        next_x = len(vals) + i - 1
        pred = slope * next_x + intercept
        ci = 1.96 * residual_std if residual_std > 0 else 0
        next_date = _add_period(last_date, i, freq)
        rows.append((
            next_date.strftime("%Y-%m-%d"),
            _fmt(pred),
            _fmt(pred - ci),
            _fmt(pred + ci),
        ))
    buf.write(_markdown_table(rows, headers))
    buf.write("\n")
    if len(vals) >= 4:
        buf.write("### Model Diagnostics\n\n")
        diag_rows = [
            ("Slope", f"{slope:.4f}"),
            ("Intercept", f"{intercept:.4f}"),
            ("R-squared", f"{r_val ** 2:.4f}"),
            ("P-value", f"{p_val:.4e}"),
            ("Residual Std Dev", f"{residual_std:.4f}"),
        ]
        buf.write(_markdown_table(diag_rows, ["Metric", "Value"]))
        buf.write("\n")
    return buf.getvalue()


def _fmt(v):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "—"
    if isinstance(v, float):
        if abs(v) >= 10000 or (abs(v) > 0 and abs(v) < 0.01):
            return f"{v:.4e}"
        return f"{v:.4f}"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    return str(v)


def _infer_freq(dates):
    if len(dates) < 2:
        return "D"
    diffs = pd.Series(dates).diff().dropna()
    if len(diffs) == 0:
        return "D"
    mean_diff = diffs.mean()
    if mean_diff <= pd.Timedelta(days=2):
        return "D"
    if mean_diff <= pd.Timedelta(days=10):
        return "W"
    if mean_diff <= pd.Timedelta(days=50):
        return "M"
    if mean_diff <= pd.Timedelta(days=150):
        return "Q"
    return "Y"


def _add_period(dt, n, freq):
    import datetime
    if freq == "D":
        return dt + datetime.timedelta(days=n)
    if freq == "W":
        return dt + datetime.timedelta(weeks=n)
    if freq == "M":
        m = dt.month + n
        y = dt.year + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        return dt.replace(year=y, month=m)
    if freq == "Q":
        return dt + datetime.timedelta(days=90 * n)
    return dt + datetime.timedelta(days=365 * n)


TOOLS = [
    {
        "name": "analyze_csv",
        "description": "Load CSV and generate descriptive statistics (mean, median, std, min, max, quartiles) with auto type detection",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to CSV file"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "correlation_matrix",
        "description": "Calculate Pearson correlation matrix from a CSV file, optionally filtering by columns",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to CSV file"},
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of column names to include",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "trend_analysis",
        "description": "Analyze a time series JSON array for linear trend, percentage change, and moving average",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data_json": {
                    "type": "string",
                    "description": "JSON array of objects with 'date' and 'value' fields, e.g. [{\"date\":\"2024-01-01\",\"value\":100}]",
                },
                "period": {
                    "type": "string",
                    "description": "Aggregation period: daily, weekly, monthly, quarterly, yearly",
                    "default": "monthly",
                },
            },
            "required": ["data_json"],
        },
    },
    {
        "name": "compare_groups",
        "description": "Group by a categorical column and compute statistics per group (count, mean, std, min, max) with ANOVA",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to CSV file"},
                "group_col": {"type": "string", "description": "Column name to group by"},
                "value_col": {"type": "string", "description": "Numeric column name for statistics"},
            },
            "required": ["path", "group_col", "value_col"],
        },
    },
    {
        "name": "forecast_simple",
        "description": "Simple linear regression forecast from a time series JSON array",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data_json": {
                    "type": "string",
                    "description": "JSON array of objects with 'date' and 'value' fields",
                },
                "periods": {
                    "type": "integer",
                    "description": "Number of periods to forecast",
                    "default": 3,
                },
            },
            "required": ["data_json"],
        },
    },
]


# ── MCP Server (JSON-RPC over stdio) ─────────────────────────


def _respond(id_val, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_val}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def _run_mcp():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = msg.get("method")
        req_id = msg.get("id")
        params = msg.get("params") or {}
        if method == "initialize":
            _respond(req_id, {
                "protocolVersion": "2026-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mcp-pandas", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _respond(req_id, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                if tool_name == "analyze_csv":
                    result = analyze_csv(args.get("path", ""))
                    _respond(req_id, {"content": [{"type": "text", "text": result}]})
                elif tool_name == "correlation_matrix":
                    result = correlation_matrix(args.get("path", ""), args.get("columns"))
                    _respond(req_id, {"content": [{"type": "text", "text": result}]})
                elif tool_name == "trend_analysis":
                    result = trend_analysis(args.get("data_json", "[]"), args.get("period", "monthly"))
                    _respond(req_id, {"content": [{"type": "text", "text": result}]})
                elif tool_name == "compare_groups":
                    result = compare_groups(args.get("path", ""), args.get("group_col", ""), args.get("value_col", ""))
                    _respond(req_id, {"content": [{"type": "text", "text": result}]})
                elif tool_name == "forecast_simple":
                    result = forecast_simple(args.get("data_json", "[]"), int(args.get("periods", 3)))
                    _respond(req_id, {"content": [{"type": "text", "text": result}]})
                else:
                    _respond(req_id, error={"code": -32601, "message": f"Tool not found: {tool_name}"})
            except Exception as e:
                _respond(req_id, error={"code": -32603, "message": str(e)})
        elif method == "prompts/list":
            _respond(req_id, {"prompts": []})
        else:
            _respond(req_id, error={"code": -32601, "message": f"Method not found: {method}"})


# ── CLI mode ─────────────────────────────────────────────────


def _cli_help():
    print("""Usage:
  py -3 mcp_pandas.py <command> [args]

Commands:
  analyze_csv <path>
  correlation_matrix <path> [--columns col1,col2]
  trend_analysis --data <json> [--period monthly|weekly|daily|quarterly|yearly]
  compare_groups <path> --group <col> --value <col>
  forecast_simple --data <json> [--periods N]
  interactive              Start MCP server mode (stdio)
  --help                   Show this message

Examples:
  py -3 mcp_pandas.py analyze_csv data.csv
  py -3 mcp_pandas.py correlation_matrix data.csv --columns col1,col2
  py -3 mcp_pandas.py trend_analysis --data '[{"date":"2024-01","value":100}]' --period monthly
  py -3 mcp_pandas.py compare_groups data.csv --group category --value price
  py -3 mcp_pandas.py forecast_simple --data '[{"date":"2024-01","value":100}]' --periods 4
""")


def _cli_dispatch():
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        _cli_help()
        return
    cmd = args[0]
    if cmd == "interactive":
        _run_mcp()
        return
    if cmd == "analyze_csv":
        if len(args) < 2:
            print("ERROR: missing path argument", file=sys.stderr)
            sys.exit(1)
        print(analyze_csv(args[1]))
    elif cmd == "correlation_matrix":
        path = args[1] if len(args) > 1 else ""
        cols = None
        for i, a in enumerate(args):
            if a == "--columns" and i + 1 < len(args):
                cols = [c.strip() for c in args[i + 1].split(",")]
        if not path:
            print("ERROR: missing path argument", file=sys.stderr)
            sys.exit(1)
        print(correlation_matrix(path, cols))
    elif cmd == "trend_analysis":
        data = None
        period = "monthly"
        for i, a in enumerate(args):
            if a == "--data" and i + 1 < len(args):
                data = args[i + 1]
            if a == "--period" and i + 1 < len(args):
                period = args[i + 1]
        if not data:
            print("ERROR: --data is required", file=sys.stderr)
            sys.exit(1)
        print(trend_analysis(data, period))
    elif cmd == "compare_groups":
        path = args[1] if len(args) > 1 else ""
        group_col = None
        value_col = None
        for i, a in enumerate(args):
            if a == "--group" and i + 1 < len(args):
                group_col = args[i + 1]
            if a == "--value" and i + 1 < len(args):
                value_col = args[i + 1]
        if not path or not group_col or not value_col:
            print("ERROR: usage: compare_groups <path> --group <col> --value <col>", file=sys.stderr)
            sys.exit(1)
        print(compare_groups(path, group_col, value_col))
    elif cmd == "forecast_simple":
        data = None
        periods = 3
        for i, a in enumerate(args):
            if a == "--data" and i + 1 < len(args):
                data = args[i + 1]
            if a == "--periods" and i + 1 < len(args):
                periods = int(args[i + 1])
        if not data:
            print("ERROR: --data is required", file=sys.stderr)
            sys.exit(1)
        print(forecast_simple(data, periods))
    else:
        print(f"ERROR: unknown command: {cmd}", file=sys.stderr)
        _cli_help()
        sys.exit(1)


def main():
    _cli_dispatch()


if __name__ == "__main__":
    main()
