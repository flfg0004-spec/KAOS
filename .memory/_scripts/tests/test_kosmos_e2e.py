"""Tests E2E reales para KosmosV2 — validan pipeline completo con output real."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["LLM_DIRECT_ENABLED"] = "false"
os.environ["KAOS_TESTING"] = "1"

SAMPLE_TOPIC = "Sistema de Memoria Arquitectónica basado en SQLite FTS5"

def test_e2e_adr_generation():
    """E2E: Pipeline completo genera ADR válido con todos los campos requeridos."""
    from lib.kosmos_node_v2 import KosmosPipelineV2
    p = KosmosPipelineV2({"topic": SAMPLE_TOPIC, "parallel_enabled": False, "cache_enabled": False})
    result = p.run_all()
    assert result["nodes_executed"] == 8, f"Expected 8 nodes, got {result['nodes_executed']}"
    assert result["nodes_with_errors"] == 0, f"Errors: {result['errors']}"
    adr_text = p.state.get("kosmos_adr", "")
    assert adr_text, "ADR text is empty"
    assert "id:" in adr_text, "ADR missing id in frontmatter"
    assert "title:" in adr_text, "ADR missing title in frontmatter"
    assert "status:" in adr_text, "ADR missing status in frontmatter"
    assert "## Contexto" in adr_text or "## Context" in adr_text, "ADR missing Context section"
    assert "## Decisi" in adr_text, "ADR missing Decision section"
    assert "## Consecuencias" in adr_text or "## Consequences" in adr_text, "ADR missing Consequences section"

def test_e2e_c4_diagrams():
    """E2E: Pipeline genera diagramas C4 válidos en disco."""
    from lib.kosmos_node_v2 import KosmosPipelineV2
    p = KosmosPipelineV2({"topic": SAMPLE_TOPIC, "parallel_enabled": False, "cache_enabled": False})
    p.run_all()
    diagrams = p.state.get("kosmos_diagrams", [])
    assert len(diagrams) >= 2, f"Expected ≥2 diagrams, got {len(diagrams)}"
    for d_path in diagrams:
        assert os.path.exists(d_path), f"Diagram not found: {d_path}"
        content = open(d_path, encoding="utf-8").read()
        assert "graph" in content or "flowchart" in content, f"Diagram has no graph/flowchart header: {d_path}"
        node_count = content.count("[") 
        assert node_count >= 4, f"Diagram has only {node_count} nodes (< 4 required): {d_path}"
        assert "-->" in content, f"Diagram has no relationships (-->): {d_path}"

def test_e2e_contracts_executed():
    """E2E: Pipeline ejecuta contratos F2 y produce resultados válidos."""
    from lib.kosmos_node_v2 import KosmosPipelineV2
    p = KosmosPipelineV2({"topic": SAMPLE_TOPIC, "parallel_enabled": False, "cache_enabled": False})
    result = p.run_all()
    validate = result.get("node_results", {}).get("validate", {})
    contracts = validate.get("contracts", {})
    assert contracts, "Contracts section is empty"
    statuses = contracts.get("contract_statuses", {})
    assert len(statuses) >= 2, f"Expected ≥2 contracts, got {len(statuses)}"
    corrective = validate.get("corrective_actions", [])
    if corrective:
        for action in corrective:
            assert "type" in action, "Corrective action missing 'type'"
            assert "severity" in action, "Corrective action missing 'severity'"
            assert "message" in action, "Corrective action missing 'message'"

def test_e2e_pipeline_with_cache():
    """E2E: Cache de pipeline funciona — segunda ejecución es cache hit."""
    from lib.kosmos_node_v2 import KosmosPipelineV2
    topic = "test E2E cache"
    p1 = KosmosPipelineV2({"topic": topic, "cache_enabled": True, "parallel_enabled": False})
    r1 = p1.run_all()
    p2 = KosmosPipelineV2({"topic": topic, "cache_enabled": True, "parallel_enabled": False})
    r2 = p2.run_all()
    assert r2.get("cache_hit", False) or r2.get("cached", False), "Second run should be cache hit"
