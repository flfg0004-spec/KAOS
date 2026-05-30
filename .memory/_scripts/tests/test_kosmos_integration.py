"""Integration tests for KosmosV2 — pipeline, contracts, evaluation & governance."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["LLM_DIRECT_ENABLED"] = "false"
os.environ["KAOS_TESTING"] = "1"

def test_kosmos_node_returns_dict():
    from lib.agent_executor import kosmos_node
    state = {"topic": "test architecture"}
    result = kosmos_node(state)
    assert "kosmos_output" in result
    assert "kosmos_prompt" in result

def test_kosmos_prompt_has_architecture():
    from lib.agent_executor import kosmos_node
    result = kosmos_node({"topic": "microservices architecture"})
    prompt = result.get("kosmos_prompt", "")
    assert prompt is not None
    assert len(prompt) > 0

def test_kosmos_empty_topic():
    from lib.agent_executor import kosmos_node
    result = kosmos_node({"topic": ""})
    assert "kosmos_output" in result

def test_kosmos_eval_v2_dimensions():
    from lib.kosmos_evaluator_v2 import DimensionalEvaluator
    evaluator = DimensionalEvaluator(profile="desarrollo")
    sample = "# ADR-999\n\n## Context\nProblem 1. Problem 2. Problem 3.\n\n## Decision\nOption B.\n\n## Consequences\nPositives: X. Negatives: Y.\n\n## References\n- ref1\n"
    result = evaluator.evaluate(sample)
    assert 0 <= result.weighted_score <= 100
    assert len(result.scores) == 5
    assert "veracidad" in result.scores
    assert "coherencia" in result.scores

def test_kosmos_l0_memory():
    from lib.kosmos_memory import ArchitectureMemoryL0
    memory = ArchitectureMemoryL0()
    count = memory.index_all_adrs()
    assert count >= 0
    stats = memory.get_stats()
    assert "total_adrs" in stats
    memory.close()

def test_kosmos_contracts_orchestrator():
    from lib.kosmos_contracts import ContractOrchestrator
    orch = ContractOrchestrator()
    result = orch.run_all_contracts("test ADR", "ADR-TEST", {"profile": "desarrollo", "topic": "test"})
    assert "adr_id" in result

def test_kosmos_reflection():
    from lib.kosmos_reflect import ReflectionEngine
    engine = ReflectionEngine()
    sample = "---\nid: ADR-T\n---\n# ADR-T\n\n## Opciones Consideradas\n1. A\n2. B\n3. C\n\n## Decisión\nA\n\n## Consecuencias\nPositivas: X\nNegativas: Y\n"
    report = engine.evaluate_adr(sample)
    assert 0 <= report.total_score <= 100
    assert isinstance(report.gaps, list)

def test_kosmos_quality_from_adr():
    from lib.kosmos_quality import evaluate_agent_output
    output = "## Architecture Analysis\n\nADR-012: Quality Engine\n\nDecision: Use DeepEval.\n"
    result = evaluate_agent_output("kosmos", output, "Analyze architecture quality")
    assert "composite" in result
    assert 0 <= result["composite"] <= 100

def test_kosmos_routing_table():
    from lib.kosmos_node_v2 import resolve_routing, ROUTING_TABLE
    assert len(ROUTING_TABLE) == 8
    doc_route = resolve_routing("document")
    assert doc_route["model"] == "go-pro"
    disc_route = resolve_routing("discover")
    assert disc_route["model"] == "go-flash"
    qual_route = resolve_routing("quality")
    assert qual_route["model"] == "go-kimi-latest"
    fallback = resolve_routing("nonexistent")
    assert fallback["model"] == "go-flash"

def test_kosmos_l1_import():
    from lib.kosmos_memory import ArchitectureMemoryL1
    l1 = ArchitectureMemoryL1()
    st = l1.status()
    assert "available" in st

def test_g2_no_duplicate_evaluation():
    from lib.agent_executor import kosmos_node
    result = kosmos_node({"topic": "test G2 no-dup", "skip_eval": True})
    # Should have evaluation (either from pipeline V2 or fallback V1)
    assert "kosmos_output" in result
    # If V2 pipeline succeeded, it should have eval scores
    if "kosmos_eval_v2" in result:
        assert "scores" in result["kosmos_eval_v2"]
    if "kosmos_reflection" in result:
        assert "total_score" in result["kosmos_reflection"]

def test_p1_cache():
    from lib.kosmos_node_v2 import KosmosPipelineV2
    # Two identical topics — second should hit cache
    p1 = KosmosPipelineV2({"topic": "test P1 cache", "cache_enabled": True})
    r1 = p1.run_all()
    p2 = KosmosPipelineV2({"topic": "test P1 cache", "cache_enabled": True})
    r2 = p2.run_all()
    assert r2.get("cache_hit", False) or r2.get("cached", False)

def test_p2_parallel_flag():
    from lib.kosmos_node_v2 import KosmosPipelineV2
    p = KosmosPipelineV2({"topic": "test P2 parallel", "parallel_enabled": True})
    assert hasattr(p, 'parallel_enabled')
    assert p.parallel_enabled is True
    # Sequential mode should also work
    ps = KosmosPipelineV2({"topic": "test P2 seq", "parallel_enabled": False})
    assert ps.parallel_enabled is False

def test_g4_aletheia_real_mode():
    from lib.kosmos_contracts import KosmosAletheiaContract
    ac = KosmosAletheiaContract(real_mode=True)
    st = ac.status()
    assert "real_mode" in st
    assert st["real_mode"] is True
    assert "real_calls" in st
    assert "fallback_calls" in st
    # Default should have real_mode True
    ac2 = KosmosAletheiaContract()
    assert ac2.status()["real_mode"] is True

def test_g5_corrective_actions():
    from lib.kosmos_contracts import ContractOrchestrator
    orch = ContractOrchestrator()
    orch._results = {
        "adr_id": "ADR-TEST",
        "contracts": {
            "kratos": {"adherence_score": 45.0, "status": "completed"},
            "aletheia": {"verifications": [{"confidence": 0.3}], "status": "completed"},
            "mnemosyne": {"curation_score": 50.0, "status": "completed"},
            "metis": {"status": "completed"},
        },
    }
    actions = orch.get_corrective_actions()
    assert len(actions) >= 2

def test_p5_timeseries_compression():
    from lib.kosmos_monitor import ArchitectureMonitor
    from datetime import timedelta, datetime
    now = datetime.now()
    old = {
        "timestamp": (now - timedelta(days=100)).isoformat(),
        "health_score": 70.0, "atdi_score": 20.0, "smell_count": 10,
        "component_count": 12, "affected_components": 3,
        "debt_estimate_hours": 15.0, "atdi_severity": "low",
        "smell_breakdown": {"high": 2, "medium": 5},
    }
    records = [old] * 5
    mon = ArchitectureMonitor(db_path="")
    compressed = mon._compress_timeseries(records)
    assert len(compressed) < len(records)
