"""Tests for lib.visual_dashboard — Plotly Quality Dashboard."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TIMESERIES_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".vault" / "quality" / "timeseries"


def _write_test_timeseries():
    TIMESERIES_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    for i in range(35):
        score = 50 + (i * 1.5) + (i % 5)
        lines.append(
            json.dumps(
                {
                    "date": f"2026-04-{22 + i:02d}" if 22 + i <= 30 else f"2026-05-{22 + i - 30:02d}",
                    "score": score,
                    "metrics": {
                        "confidence_matrix": min(25, 10 + i * 0.4),
                        "embeddings": min(15, 5 + i * 0.3),
                        "tests": min(15, 8 + i * 0.2),
                        "lint": min(15, 10 + i * 0.15),
                        "wikilinks": min(10, 6 + i * 0.1),
                        "connectivity": min(10, 3 + i * 0.2),
                        "freshness": min(10, 5 + i * 0.15),
                        "strategy": min(5, 2 + i * 0.1),
                    },
                }
            )
        )
    (TIMESERIES_DIR / "daily.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_test_verification_scores():
    data = {
        "scores": [
            {"agent": "aletheia", "composite": 72},
            {"agent": "kosmos", "composite": 85},
            {"agent": "metis", "composite": 63},
            {"agent": "mnemosyne", "composite": 78},
        ]
    }
    (TIMESERIES_DIR / "verification-scores.json").write_text(json.dumps(data), encoding="utf-8")


def _write_test_atdi():
    data = {"atdi_score": 18.5, "estimated_hours": 12.0, "severity": "medium"}
    (TIMESERIES_DIR / "pipeline-scores.json").write_text(json.dumps(data), encoding="utf-8")


def _cleanup():
    for f in ("daily.jsonl", "verification-scores.json", "pipeline-scores.json"):
        p = TIMESERIES_DIR / f
        if p.exists():
            p.unlink()


def test_generate_dashboard_creates_html():
    _write_test_timeseries()
    _write_test_verification_scores()
    _write_test_atdi()
    try:
        from lib.visual_dashboard import generate_quality_dashboard

        output = Path(os.path.dirname(__file__)) / "_test_quality_dashboard.html"
        generate_quality_dashboard(str(output))
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "KAOS Quality Dashboard" in content
        assert "plotly" in content.lower()
        assert "Tendencia" in content
        assert "score-badge" in content
        output.unlink(missing_ok=True)
    finally:
        _cleanup()


def test_empty_timeseries():
    _cleanup()
    from lib.visual_dashboard import generate_quality_dashboard

    output = Path(os.path.dirname(__file__)) / "_test_empty_dashboard.html"
    generate_quality_dashboard(str(output))
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "KAOS Quality Dashboard" in content
    assert "plotly" in content.lower()
    output.unlink(missing_ok=True)


def test_timeseries_chart_no_data():
    from lib.visual_dashboard import _build_timeseries_chart

    fig = _build_timeseries_chart([])
    assert fig is not None


def test_radar_chart_no_data():
    from lib.visual_dashboard import _build_radar_chart

    fig = _build_radar_chart({})
    assert fig is not None


def test_heatmap_no_data():
    from lib.visual_dashboard import _build_heatmap

    fig = _build_heatmap([])
    assert fig is not None


def test_atdi_bars():
    from lib.visual_dashboard import _build_atdi_bars

    fig = _build_atdi_bars({"atdi_score": 25, "estimated_hours": 10, "severity": "high"})
    assert fig is not None


def test_atdi_bars_empty():
    from lib.visual_dashboard import _build_atdi_bars

    fig = _build_atdi_bars({"atdi_score": 0, "estimated_hours": 0, "severity": "none"})
    assert fig is not None


def test_load_timeseries_empty():
    _cleanup()
    from lib.visual_dashboard import _load_timeseries

    records = _load_timeseries()
    assert records == []


def test_load_agent_scores_empty():
    _cleanup()
    from lib.visual_dashboard import _load_agent_scores

    scores = _load_agent_scores()
    assert scores == {}


def test_smoke_html_content():
    _write_test_timeseries()
    _write_test_verification_scores()
    _write_test_atdi()
    try:
        from lib.visual_dashboard import generate_quality_dashboard

        output = Path(os.path.dirname(__file__)) / "_test_smoke_dashboard.html"
        generate_quality_dashboard(str(output))
        html = output.read_text(encoding="utf-8")
        assert "plotly-3.0.1.min.js" in html
        assert "Tendencia de Calidad" in html
        assert "Desempeño por Agente" in html
        assert "Cobertura de Métricas" in html
        assert "Deuda Técnica" in html
        assert "score-badge" in html
        assert "ATDI" in html
        output.unlink(missing_ok=True)
    finally:
        _cleanup()


def test_default_output_path():
    _cleanup()
    from lib.visual_dashboard import generate_quality_dashboard

    result = generate_quality_dashboard()
    assert result
    output = Path(result)
    assert output.exists()
    assert output.name == "quality-dashboard.html"
    output.unlink(missing_ok=True)


def test_output_path_creates_parent_dirs():
    from lib.visual_dashboard import generate_quality_dashboard

    output = Path(os.path.dirname(__file__)) / "_nested_test" / "_dashboard.html"
    generate_quality_dashboard(str(output))
    assert output.exists()
    assert output.stat().st_size > 0
    output.unlink(missing_ok=True)
    output.parent.rmdir()


def test_corrupt_jsonl_lines():
    TIMESERIES_DIR.mkdir(parents=True, exist_ok=True)
    (TIMESERIES_DIR / "daily.jsonl").write_text(
        '{"date":"2026-05-20","score":50}\nnot json\n{"bad":\n',
        encoding="utf-8",
    )
    try:
        from lib.visual_dashboard import _load_timeseries

        records = _load_timeseries()
        assert len(records) == 1
    finally:
        _cleanup()


def test_dashboard_contains_noscript():
    _write_test_timeseries()
    try:
        from lib.visual_dashboard import generate_quality_dashboard

        output = Path(os.path.dirname(__file__)) / "_test_noscript.html"
        generate_quality_dashboard(str(output))
        html = output.read_text(encoding="utf-8")
        assert "<noscript>" in html
        output.unlink(missing_ok=True)
    finally:
        _cleanup()
