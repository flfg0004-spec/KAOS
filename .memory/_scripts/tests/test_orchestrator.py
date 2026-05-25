"""Tests for LangGraph DAG (no API key required)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["LLM_DIRECT_ENABLED"] = "false"
os.environ["KAOS_TESTING"] = "1"


def test_dag_nodes_registered():
    from lib.orchestrator import build_graph
    g = build_graph(with_parallel=False)
    expected = {"planner", "aletheia", "kosmos", "metis",
                "kratos", "mnemosyne", "critic", "kosmos_evaluator"}
    actual = set(g.nodes.keys())
    missing = expected - actual
    assert not missing, f"Missing nodes: {missing}"


def test_dag_parallel_nodes_registered():
    from lib.orchestrator import build_graph
    g = build_graph(with_parallel=True)
    expected = {"planner", "aletheia", "kosmos", "metis",
                "kratos", "mnemosyne", "critic", "kosmos_evaluator"}
    actual = set(g.nodes.keys())
    assert expected.issubset(actual), f"Missing in parallel: {expected - actual}"


def test_routing_code_topic_to_kratos():
    from lib.orchestrator import route_after_strategy, KAOSState
    state = KAOSState(topic="implementar API REST con JWT")
    assert route_after_strategy(state) == "kratos"


def test_routing_research_topic_to_mnemosyne():
    from lib.orchestrator import route_after_strategy, KAOSState
    state = KAOSState(topic="teoria de grafos en ciencia de datos")
    assert route_after_strategy(state) == "mnemosyne"


def test_routing_has_code_keyword():
    from lib.orchestrator import _has_code_keywords
    assert _has_code_keywords("fix bug in parser")
    assert _has_code_keywords("implement API REST")
    assert not _has_code_keywords("historia del arte renacentista")


def test_critic_routing_advance():
    from lib.orchestrator import route_after_critic, KAOSState
    state = KAOSState(topic="test", critic_score=75, iteration=1)
    assert route_after_critic(state) == "advance"


def test_critic_routing_refine():
    from lib.orchestrator import route_after_critic, KAOSState
    state = KAOSState(topic="test", critic_score=30, iteration=1, kratos_output="# Code\nprint('test')")
    assert route_after_critic(state) == "refine"


def test_critic_routing_refine_max_iterations():
    from lib.orchestrator import route_after_critic, KAOSState
    state = KAOSState(topic="test", critic_score=30, iteration=3, kratos_output="# Code\nprint('test')")
    assert route_after_critic(state) == "advance"


def test_kaos_state_defaults():
    from lib.orchestrator import KAOSState
    s = KAOSState(topic="test", profile="standard")
    assert s["topic"] == "test"
    assert s.get("profile") == "standard"
    assert s.get("iteration", 0) == 0
    assert s.get("critic_score", 0) == 0


def test_planner_node_no_llm():
    from lib.agent_executor import planner_node
    state = {"topic": "implementar API REST", "profile": "desarrollo"}
    result = planner_node(state)
    assert "plan" in result
    assert result["has_code_subtasks"] is True
    assert result["iteration"] == 0


def test_planner_node_research_topic():
    from lib.agent_executor import planner_node
    state = {"topic": "filosofia estoica", "profile": "standard"}
    result = planner_node(state)
    plan = result.get("plan", {})
    assert plan.get("has_code") is False


def test_aletheia_node_no_llm():
    from lib.agent_executor import aletheia_node
    state = {"topic": "test", "plan": {"subtasks": []}}
    result = aletheia_node(state)
    assert "aletheia_output" in result
    assert "Prompt written to" in result["aletheia_output"]


def test_kosmos_node_no_llm():
    from lib.agent_executor import kosmos_node
    state = {"topic": "test", "aletheia_output": "research content"}
    result = kosmos_node(state)
    assert "kosmos_output" in result
    assert "ADR prompt written" in result["kosmos_output"]


def test_metis_node_no_llm():
    from lib.agent_executor import metis_node
    state = {"topic": "strategy test"}
    result = metis_node(state)
    assert "metis_output" in result
    assert "Strategy prompt written" in result["metis_output"]


def test_kratos_node_no_llm():
    from lib.agent_executor import kratos_node
    state = {"topic": "write a sorting function"}
    result = kratos_node(state)
    assert "kratos_output" in result
    assert "Code prompt written" in result["kratos_output"]
    assert result["kratos_decision"] == "needs_curation"


def test_mnemosyne_node_no_llm():
    from lib.agent_executor import mnemosyne_node
    state = {"topic": "curate outputs"}
    result = mnemosyne_node(state)
    assert "mnemosyne_output" in result
    assert "Curation prompt written" in result["mnemosyne_output"]


def test_parallel_build_graph():
    """Verifica que build_graph modo paralelo crea nodos específicos."""
    from lib.orchestrator import build_graph
    graph = build_graph(with_parallel=True)
    assert graph is not None
    nodes = list(graph.nodes.keys())
    assert "planner" in nodes
    assert "aletheia" in nodes
    assert "parallel_validate" in nodes, "Modo paralelo debe crear nodo parallel_validate"


def test_code_memory_hook_can_activate():
    """Verifica que el hook de CodeExperience se puede activar."""
    from lib.kratos_hook import init_code_memory_hook
    import builtins
    was_active = getattr(builtins, '_code_memory_hook_active', False)
    if not was_active:
        init_code_memory_hook()
    assert getattr(builtins, '_code_memory_hook_active', False)

def test_slugify():
    from lib.agent_executor import _slugify
    assert _slugify("Hello World!") == "hello-world"
    assert _slugify("API REST con JWT") == "api-rest-con-jwt"


def test_detect_complexity():
    from lib.agent_executor import _detect_complexity
    assert _detect_complexity("microservicio distribuido con kubernetes") == "alta"
    assert _detect_complexity("script simple de python") == "simple"
    assert _detect_complexity("API REST con autenticacion") == "moderada"


def test_detect_subtasks():
    from lib.agent_executor import _detect_subtasks
    subtasks = _detect_subtasks("implementar API REST con pruebas unitarias")
    ids = [s["id"] for s in subtasks]
    assert "code" in ids
    assert "test" in ids
    subtasks2 = _detect_subtasks("filosofia antigua")
    assert len(subtasks2) == 1
    assert subtasks2[0]["id"] == "research"


def test_critic_node_no_llm():
    from lib.orchestrator import critic_node
    state = {
        "topic": "test",
        "aletheia_output": "# Research\nContent here\n",
        "kosmos_output": "# ADR\nArchitecture\n",
        "metis_output": "# Strategy\nOKRs\n",
        "kratos_output": "# Code\nImplementation\n",
        "mnemosyne_output": "# Curation\nQuality check\n",
        "iteration": 0,
    }
    import os
    os.environ["LLM_DIRECT_ENABLED"] = "false"
    result = critic_node(state)
    assert "critic_score" in result
    assert result["iteration"] == 1
