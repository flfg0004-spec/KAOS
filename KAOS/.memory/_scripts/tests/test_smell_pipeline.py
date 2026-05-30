"""Tests for lib.smell_pipeline — architecture smell detection."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_static_scan_empty():
    from lib.smell_pipeline import static_scan

    r = static_scan("")
    assert r == []


def test_static_scan_clean():
    from lib.smell_pipeline import static_scan

    r = static_scan('def foo():\n    """docstring"""\n    return 42')
    assert len(r) == 0


def test_static_scan_eval():
    from lib.smell_pipeline import static_scan

    r = static_scan("result = eval(data)")
    names = [s["name"] for s in r]
    assert "dangerous_eval" in names


def test_static_scan_silent_exception():
    from lib.smell_pipeline import static_scan

    r = static_scan("try:\n    pass\nexcept:\n    pass")
    names = [s["name"] for s in r]
    assert "silent_exception" in names


def test_static_scan_wildcard_import():
    from lib.smell_pipeline import static_scan

    r = static_scan("from os import *")
    names = [s["name"] for s in r]
    assert "wildcard_import" in names


def test_static_scan_hardcoded_secret():
    from lib.smell_pipeline import static_scan

    r = static_scan('api_key = "sk-1234567890"')
    names = [s["name"] for s in r]
    assert "hardcoded_secret" in names


def test_static_scan_todo():
    from lib.smell_pipeline import static_scan

    r = static_scan("# TODO: implement this later")
    names = [s["name"] for s in r]
    assert "unresolved_todo" in names


def test_static_scan_god_class():
    from lib.smell_pipeline import static_scan

    r = static_scan("This is a god class that does everything")
    names = [s["name"] for s in r]
    assert "god_class_reference" in names


def test_static_scan_circular_dependency():
    from lib.smell_pipeline import static_scan

    r = static_scan("circular dependency detected between modules A and B")
    names = [s["name"] for s in r]
    assert "circular_dependency" in names


def test_analyze_returns_dict():
    from lib.smell_pipeline import analyze

    r = analyze("clean code with no smells", task_type="general")
    assert "overall_score" in r
    assert "static_findings" in r
    assert "severity_breakdown" in r


def test_analyze_detects_critical():
    from lib.smell_pipeline import analyze

    r = analyze("uses eval() and except: pass and TODO and from x import *", task_type="code")
    assert r["static_count"] >= 3
    assert r["severity_breakdown"]["critical"] >= 1


def test_analyze_clean_score():
    from lib.smell_pipeline import analyze

    r = analyze("def hello():\n    return 'world'", task_type="general")
    assert r["overall_score"] >= 90


def test_severity_breakdown_keys():
    from lib.smell_pipeline import analyze

    r = analyze("eval() and except: pass", task_type="code")
    keys = set(r["severity_breakdown"].keys())
    assert keys.issuperset({"critical", "high", "medium", "low"})
