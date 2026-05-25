"""Tests for MemEx persistent Python scope — execution, persistence, cleanup."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_execute_simple():
    from lib.memex_scope import get_scope, reset_scope
    reset_scope()
    scope = get_scope("test_simple")
    result = scope.execute("x = 42")
    assert result["error"] is None
    assert scope.get("x") == 42


def test_persistence_between_calls():
    from lib.memex_scope import get_scope, reset_scope
    reset_scope()
    scope = get_scope("test_persist")
    scope.execute("data = [1, 2, 3]")
    result = scope.execute("total = sum(data)")
    assert result["error"] is None
    assert scope.get("total") == 6


def test_function_definition():
    from lib.memex_scope import get_scope, reset_scope
    reset_scope()
    scope = get_scope("test_func")
    scope.execute("def add(a, b): return a + b")
    result = scope.execute("c = add(3, 4)")
    assert result["error"] is None
    assert scope.get("c") == 7


def test_error_handling():
    from lib.memex_scope import get_scope, reset_scope
    reset_scope()
    scope = get_scope("test_error")
    result = scope.execute("1/0")
    assert result["error"] is not None
    assert result["error"]["type"] == "ZeroDivisionError"


def test_list_vars():
    from lib.memex_scope import get_scope, reset_scope
    reset_scope()
    scope = get_scope("test_list")
    scope.execute("a = 1; b = 'hello'; c = [1,2,3]")
    vars_list = scope.list_vars()
    names = [v["name"] for v in vars_list]
    assert "a" in names
    assert "b" in names
    assert "c" in names


def test_reset():
    from lib.memex_scope import get_scope, reset_scope
    reset_scope()
    scope = get_scope("test_reset")
    scope.execute("x = 99")
    assert scope.get("x") == 99
    reset_scope()
    new_scope = get_scope("test_reset_new")
    assert new_scope.get("x") is None


def test_status():
    from lib.memex_scope import get_scope, reset_scope
    reset_scope()
    scope = get_scope("test_status")
    scope.execute("a = 1; b = 2")
    s = scope.status()
    assert s["variables"] >= 2
    assert s["iteration"] >= 1


def test_stdout_capture():
    from lib.memex_scope import get_scope, reset_scope
    reset_scope()
    scope = get_scope("test_stdout")
    result = scope.execute("print('hello world')")
    assert "hello world" in result["stdout"]


def test_multiple_sessions():
    from lib.memex_scope import get_scope, reset_scope
    reset_scope()
    s1 = get_scope("session_a")
    s1.execute("val = 'from_a'")
    
    s2 = get_scope("session_b")
    s2.execute("val = 'from_b'")
    
    # Re-get session_a, should still have its value
    s1_again = get_scope("session_a")
    assert s1_again.get("val") == 'from_a'
