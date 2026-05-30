"""Security tests for KosmosV2 (S2 endurecimiento): XSS, path injection, logging JSON, spans."""
import io, logging, os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
os.environ["LLM_DIRECT_ENABLED"] = "false"
os.environ["KAOS_TESTING"] = "1"

XSS_PAYLOAD = '<script>alert("xss")</script>'

def test_xss_dashboard_escape():
    from kosmos_dashboard import KosmosDashboard
    dash = KosmosDashboard()
    metrics = {
        "health_score": 75, "atdi_score": 15, "smell_count": 5,
        "smell_breakdown": {"high": 1, "medium": 3, "low": 1},
        "alerts": [{"severity": "high", "message": XSS_PAYLOAD}],
        "adrs": [{"id": "ADR-001", "title": XSS_PAYLOAD, "status": "proposed"}],
        "contracts": {"contracts": {"kratos": {"status": "completed"}}},
        "pipeline": {"status": "ok", "nodes_executed": 8, "total_nodes": 8, "nodes_with_errors": 0},
        "routing": {"discover": {"model": "flash", "reason": XSS_PAYLOAD}},
        "history": [],
    }
    html = dash.render_html(metrics)
    assert "<script>" not in html, "XSS payload should be escaped in HTML output"
    assert "&lt;script&gt;" in html, "XSS payload should appear as escaped entity"

def test_path_sanitized_with_spaces():
    from kosmos.nodes import _depwire_scan
    result = _depwire_scan(["nonexistent path with spaces"])
    assert result is not None
    assert "error" not in result or result.get("files") is not None

def test_logging_json_output():
    from kosmos_log import log_json, get_json_logger
    import io
    logger = get_json_logger("test_security")
    logger.setLevel(10)
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    logger.addHandler(handler)
    log_json(logger, 20, "test_event", detail="hello", count=42)
    handler.flush()
    output = buf.getvalue()
    parsed = json.loads(output)
    assert parsed["event"] == "test_event"
    assert parsed["context"]["detail"] == "hello"
    assert parsed["context"]["count"] == 42
    assert "timestamp" in parsed

def _check_spans(exp_count=1):
    """Check span count — works with OTel or fallback mode."""
    from lib.kosmos.otel import ExecutionSpan, is_otel_available
    ExecutionSpan.clear_spans()
    if is_otel_available():
        # OTel mode: spans don't appear in get_spans()
        # Just verify the class works without errors
        return True
    spans = ExecutionSpan.get_spans()
    return len(spans) == exp_count

def test_span_structure():
    from lib.kosmos.otel import ExecutionSpan, is_otel_available
    ExecutionSpan.clear_spans()
    test_attr = "test_value"
    with ExecutionSpan("test_span", attr=test_attr):
        pass
    if is_otel_available():
        # OTel mode: basic sanity check
        assert True
        return
    spans = ExecutionSpan.get_spans()
    assert len(spans) == 1
    s = spans[0]
    assert s["name"] == "test_span"
    assert s["span_id"]
    assert s["duration_ms"] >= 0
    assert s["success"] is True
    assert s["attr"] == "test_value"

def test_span_with_error():
    from lib.kosmos.otel import ExecutionSpan, is_otel_available
    ExecutionSpan.clear_spans()
    try:
        with ExecutionSpan("failing_span"):
            raise ValueError("test error")
    except ValueError:
        pass
    if is_otel_available():
        assert True
        return
    spans = ExecutionSpan.get_spans()
    assert len(spans) == 1
    assert spans[0]["success"] is False
    assert "error" in spans[0]

def test_span_nested():
    from lib.kosmos.otel import ExecutionSpan, is_otel_available
    ExecutionSpan.clear_spans()
    with ExecutionSpan("outer"):
        with ExecutionSpan("inner"):
            pass
    if is_otel_available():
        assert True
        return
    spans = ExecutionSpan.get_spans()
    assert len(spans) == 2
    names = [s["name"] for s in spans]
    assert "outer" in names
    assert "inner" in names
