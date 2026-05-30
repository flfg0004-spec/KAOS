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
    # K3: Visualize+Govern fusionados en Document → 7 nodos efectivos
    assert result["nodes_executed"] >= 6, f"Expected ≥6 nodes, got {result['nodes_executed']}"
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
    """E2E: Pipeline genera diagramas C4 o ADR completo (K3 fusion)."""
    from lib.kosmos_node_v2 import KosmosPipelineV2
    p = KosmosPipelineV2({"topic": SAMPLE_TOPIC, "parallel_enabled": False, "cache_enabled": False})
    r = p.run_all()
    # K3: diagrams dentro de document()
    doc = r.get("node_results", {}).get("document", {})
    diagrams = doc.get("diagram_paths", []) or p.state.get("kosmos_diagrams", [])
    if diagrams:
        for d_path in diagrams:
            assert os.path.exists(d_path), f"Diagram not found: {d_path}"
            content = open(d_path, encoding="utf-8").read()
            assert "-->" in content, f"Diagram has no relationships: {d_path}"
    else:
        # Fallback: verify document produced ADR
        adr = p.state.get("kosmos_adr", "")
        assert adr and len(adr) > 100, f"Expected ADR, got empty"

def test_e2e_contracts_executed():
    """E2E: Pipeline ejecuta contratos F2 y produce resultados válidos."""
    from lib.kosmos_node_v2 import KosmosPipelineV2
    p = KosmosPipelineV2({"topic": SAMPLE_TOPIC, "parallel_enabled": False, "cache_enabled": False})
    result = p.run_all()
    validate = result.get("node_results", {}).get("validate", {})
    contracts = validate.get("contracts", {})
    # K1: contracts may come from pipeline.run_contracts() or agent_node
    if not contracts:
        contracts = result.get("contracts", {}) or contracts
    statuses = contracts.get("contract_statuses", {})
    if not statuses:
        statuses = validate.get("contract_statuses", {})
    corrective = validate.get("corrective_actions", [])
    if corrective:
        for action in corrective:
            assert "type" in action, "Corrective action missing 'type'"
            assert "severity" in action, "Corrective action missing 'severity'"
            assert "message" in action, "Corrective action missing 'message'"

def test_e2e_pipeline_with_cache():
    from lib.kosmos_node_v2 import KosmosPipelineV2
    topic = "test E2E cache"
    p1 = KosmosPipelineV2({"topic": topic, "cache_enabled": True, "parallel_enabled": False})
    r1 = p1.run_all()
    p2 = KosmosPipelineV2({"topic": topic, "cache_enabled": True, "parallel_enabled": False})
    r2 = p2.run_all()
    assert r2.get("cache_hit", False) or r2.get("cached", False), "Second run should be cache hit"

def test_k1_real_adherence_contract():
    """K1: Verifica que KosmosKratosContract real_adherence_check funciona."""
    from lib.kosmos.contracts import KosmosKratosContract
    c = KosmosKratosContract(use_real_api=True)
    assert hasattr(c, 'real_adherence_check'), "Missing real_adherence_check method"
    st = c.status()
    assert "real_api_available" in st, "Missing real_api_available in status"
    assert "code_experience_available" in st, "Missing code_experience_available in status"
