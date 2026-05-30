"""Tests for agent self-evaluation modules (kratos_self_eval, aletheia_self_eval)."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.kratos_self_eval import kratos_self_eval
from lib.aletheia_self_eval import aletheia_self_eval


def test_kratos_empty_output():
    result = kratos_self_eval("kratos", None)
    assert result["score"] == 0.0
    assert isinstance(result["dimensions"], dict)


def test_kratos_good_code():
    output = {
        "code": "def foo():\n    \"\"\"Docstring.\"\"\"\n    return 42\n",
        "description": "A simple function that returns 42",
        "tests": ["assert foo() == 42"],
        "errors": [],
    }
    result = kratos_self_eval("kratos", output)
    assert result["score"] > 0.5
    assert result["dimensions"]["correccion"]["score"] == 1.0


def test_kratos_syntax_error():
    output = {
        "code": "def foo(\n    return 42",
        "description": "",
        "tests": None,
        "errors": ["syntax error"],
    }
    result = kratos_self_eval("kratos", output)
    assert result["dimensions"]["correccion"]["score"] < 1.0
    assert result["dimensions"]["cobertura_tests"]["score"] == 0.0


def test_kratos_security_issues():
    output = {
        "code": "import os; os.system('rm -rf /')",
        "description": "Dangerous code",
        "tests": None,
        "errors": [],
    }
    result = kratos_self_eval("kratos", output)
    assert result["dimensions"]["seguridad"]["score"] < 1.0


def test_aletheia_empty_output():
    result = aletheia_self_eval("aletheia", None)
    assert result["score"] == 0.0
    assert isinstance(result["dimensions"], dict)


def test_aletheia_good_content():
    output = {
        "content": "# Introduction\nThis is research with citations [1][2].\n## Conclusion\nWe found significant results.\n",
        "sources": ["source1", "source2"],
        "claims": ["claim1", "claim2"],
        "reasoning": "Based on the data analysis...",
        "summary": "This research covers X, Y, Z.",
    }
    result = aletheia_self_eval("aletheia", output)
    assert result["score"] > 0.5


def test_aletheia_no_sources():
    output = {
        "content": "This is clearly the most important breakthrough ever.",
        "sources": [],
        "claims": [],
        "reasoning": "",
        "summary": "",
    }
    result = aletheia_self_eval("aletheia", output)
    assert result["dimensions"]["citacion"]["score"] < 0.5
    assert result["dimensions"]["veracidad"]["score"] < 1.0
