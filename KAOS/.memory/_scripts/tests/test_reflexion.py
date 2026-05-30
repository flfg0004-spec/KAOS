"""Tests for Reflexion loop — quality evaluation, regeneration, iteration limits."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"
os.environ["LLM_DIRECT_ENABLED"] = "false"


def test_reflexion_node_no_output():
    """Reflexion should handle empty Kratos output gracefully."""
    from lib.orchestrator import reflexion_node
    state = {"topic": "test", "kratos_output": "", "reflexion_iteration": 0}
    result = reflexion_node(state)
    assert "reflexion_score" in result
    assert "reflexion_iteration" in result


def test_reflexion_node_short_output():
    """Short output (<100 chars) should produce low score."""
    from lib.orchestrator import reflexion_node
    state = {"topic": "test", "kratos_output": "short", "reflexion_iteration": 0}
    result = reflexion_node(state)
    assert result.get("reflexion_score", 0) == 0


def test_reflexion_good_code_advances():
    """Quality code should get complete decision."""
    from lib.orchestrator import reflexion_node
    good_code = """```python
def add(a: int, b: int) -> int:
    '''Add two numbers.'''
    return a + b

def test_add():
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
```"""
    state = {"topic": "test", "kratos_output": good_code, "reflexion_iteration": 0}
    result = reflexion_node(state)
    decision = result.get("kratos_decision", "")
    score = result.get("reflexion_score", 0)
    assert decision == "complete" or score > 0


def test_route_after_reflexion_complete():
    from lib.orchestrator import route_after_reflexion, KAOSState
    state = KAOSState(topic="test", kratos_decision="complete", reflexion_score=8.0, reflexion_iteration=2)
    route = route_after_reflexion(state)
    assert route == "advance"


def test_route_after_reflexion_needs_curation():
    from lib.orchestrator import route_after_reflexion, KAOSState
    state = KAOSState(topic="test", kratos_decision="needs_curation", reflexion_score=5.0, reflexion_iteration=1)
    route = route_after_reflexion(state)
    assert route == "refine"


def test_route_after_reflexion_max_iterations():
    from lib.orchestrator import route_after_reflexion, KAOSState
    state = KAOSState(topic="test", kratos_decision="needs_curation", reflexion_score=4.0, reflexion_iteration=3)
    route = route_after_reflexion(state)
    assert route == "advance", "Should advance after max iterations"


def test_route_after_reflexion_good_score():
    from lib.orchestrator import route_after_reflexion, KAOSState
    state = KAOSState(topic="test", kratos_decision="", reflexion_score=8.5, reflexion_iteration=1)
    route = route_after_reflexion(state)
    assert route == "advance", "Good score should advance regardless of decision"


def test_detect_language():
    from lib.orchestrator import _detect_language
    assert _detect_language("```python\nx=1\n```") == "python"
    assert _detect_language("```js\nx=1\n```") == "javascript"
    assert _detect_language("```ts\nx=1\n```") == "typescript"
    assert _detect_language("```rs\nx=1\n```") == "rust"
    assert _detect_language("no blocks") == "python"


def test_resolve_kratos_model_default():
    from lib.agent_executor import _resolve_kratos_model
    state = {"plan": {"complexity": "simple"}, "profile": "desarrollo"}
    model = _resolve_kratos_model(state)
    assert model in ("go-gemini-flash", "go-pro")


def test_reflexion_node_increments_iteration():
    from lib.orchestrator import reflexion_node
    long_code = (
        "```python\n"
        "def calculate(x: float, y: float) -> float:\n"
        '    """Calculate the sum of two numbers."""\n'
        "    return x + y\n\n"
        "def test_calculate():\n"
        "    assert calculate(1, 2) == 3\n"
        "    assert calculate(-1, 1) == 0\n"
        "    assert calculate(0, 0) == 0\n"
        "```"
    )
    state = {"topic": "test", "kratos_output": long_code, "reflexion_iteration": 0}
    result = reflexion_node(state)
    assert result["reflexion_iteration"] >= 1
