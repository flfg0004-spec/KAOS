"""Tests for agent self-evaluation modules (kratos, aletheia, kosmos, kronos, metis, mnemosyne, bcg)."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.kratos_self_eval import kratos_self_eval
from lib.aletheia_self_eval import aletheia_self_eval
from lib.kosmos_self_eval import kosmos_self_eval
from lib.kronos_self_eval import kronos_self_eval
from lib.metis_self_eval import metis_self_eval
from lib.mnemosyne_self_eval import mnemosyne_self_eval
from lib.bcg_self_eval import bcg_self_eval


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


def test_kosmos_empty_output():
    result = kosmos_self_eval("kosmos", None)
    assert result["score"] == 0.0
    assert isinstance(result["dimensions"], dict)


def test_kosmos_good_analysis():
    output = {
        "content": "# Architecture Analysis\n## Components\n- Service A: REST API\n## Dependencies\n- Service A depends on DB\n## Recommendations\n- Add caching layer",
    }
    result = kosmos_self_eval("kosmos", output)
    assert result["score"] > 0.3


def test_kosmos_poor_analysis():
    output = {
        "content": "ok",
    }
    result = kosmos_self_eval("kosmos", output)
    assert result["score"] < 0.5
    assert result["dimensions"]["completitud"]["score"] < 0.5


def test_kosmos_contradiction():
    output = {
        "content": "Usar microservicio. También usar monolito en todo.",
    }
    result = kosmos_self_eval("kosmos", output)
    assert result["dimensions"]["consistencia"]["score"] < 1.0


def test_kronos_empty_output():
    result = kronos_self_eval("kronos", None)
    assert result["score"] == 0.0
    assert isinstance(result["dimensions"], dict)


def test_kronos_good_orchestration():
    output = {
        "status": "Pipeline executed with order: step1 first, then step2, step3 after that. Dependencies resolved. Retry on failure enabled. Resources optimized.",
    }
    result = kronos_self_eval("kronos", output)
    assert result["score"] > 0.3


def test_kronos_error_handling():
    output = {
        "status": "Timeout error: task timed out after 30s. Retry with graceful fallback.",
    }
    result = kronos_self_eval("kronos", output)
    assert result["dimensions"]["manejo_errores"]["score"] > 0.0


def test_metis_empty_output():
    result = metis_self_eval("metis", None)
    assert result["score"] == 0.0
    assert isinstance(result["dimensions"], dict)


def test_metis_good_content():
    output = {
        "content": "Strategy: expand into Latin America by Q3. Objective: 30% market share. Goal: 2x revenue. OKR: launch in 3 countries. Roadmap: Q1 research, Q2 pilot, Q3 launch. Vision: become regional leader.",
        "analysis": "Competitive analysis: main competitor is X Corp. Market gap in mid-tier segment. SWOT: strengths in brand, weakness in distribution.",
        "recommendations": "Recommend: prioritize Mexico first. Suggest: partner with local distributors. Priority: high. Impact: revenue growth. Effort: medium.",
        "risks": "Risk: currency volatility. Mitigation: hedge positions. Blocker: regulatory approval in Brazil.",
        "action_items": "Next step: sign LOI with distributor. Timeline: 2 weeks. Deliverable: partnership agreement.",
    }
    result = metis_self_eval("metis", output)
    assert result["score"] > 0.3


def test_metis_poor_content():
    output = {
        "content": "ok",
    }
    result = metis_self_eval("metis", output)
    assert result["score"] < 0.5


def test_mnemosyne_empty_output():
    result = mnemosyne_self_eval("mnemosyne", None)
    assert result["score"] == 0.0
    assert isinstance(result["dimensions"], dict)


def test_mnemosyne_good_content():
    output = {
        "content": "## Sources\nReference: Smith et al. 2023. DOI: 10.1000/xyz. URL: https://example.com\n## Structure\nCategory: AI Agents. Tags: #agent #memory. Wikilink: [[Kosmos]].\n## Coverage\nSection: Overview. Summary: This covers architectures. Todo: add benchmarks.",
        "sources": "source1, source2",
        "tags": "#agent",
        "structure": "taxonomy: agents, pipelines",
        "summary": "Practical insights for implementation.",
    }
    result = mnemosyne_self_eval("mnemosyne", output)
    assert result["score"] > 0.3


def test_mnemosyne_poor_content():
    output = {
        "content": "nada",
    }
    result = mnemosyne_self_eval("mnemosyne", output)
    assert result["score"] < 0.5


def test_bcg_empty_output():
    result = bcg_self_eval("bcg", None)
    assert result["score"] == 0.0
    assert isinstance(result["dimensions"], dict)


def test_bcg_good_content():
    output = {
        "content": "Metric: code coverage 85%. Score: 7/10. Evidence: test results attached. Data: 120 test cases passed. Criterion: industry standard 80%. Benchmark: baseline from sprint 1. Feedback: improvement needed in edge cases. Opportunity: add integration tests. Gap: missing negative tests. Consistent: aligned with quality goals. Matches previous evaluation. Action item: add 10 more tests. Next step: review by Friday. Fix: resolve flaky test.",
        "criteria": "standard benchmark",
        "feedback": "improvement opportunity gap",
        "scores": "metric score data",
        "actions": "action item fix",
    }
    result = bcg_self_eval("bcg", output)
    assert result["score"] > 0.3


def test_bcg_poor_content():
    output = {
        "content": "bien",
    }
    result = bcg_self_eval("bcg", output)
    assert result["score"] < 0.5
