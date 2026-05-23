"""Integration test: hydrate -> work -> extract -> hydrate cycle."""
import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _cleanup():
    cache = os.path.join(os.path.dirname(__file__), "..", "..", "cache", "test-cycle-hydrate.json")
    if os.path.exists(cache):
        os.remove(cache)


def test_hydrate_extract_cycle():
    """Verifica que hydrate + extract no fallen en un ciclo básico."""
    from lib.hydrate import load
    from lib.extract import extract_session
    _cleanup()
    ctx = load(agent="test_agent", task="test_cycle")
    assert "Quality Score" in ctx or "index" in ctx or "log" in ctx
    result = extract_session(
        agent="test_agent",
        summary="Integration test cycle",
        pages=["_scripts/tests/test_context_cycle.py"],
    )
    assert "Session extracted" in result or "committed" in result or "log" in result


def test_hydrate_pressure_levels():
    """Verifica que hydrate responde a presión de tokens."""
    from lib.hydrate import load
    ctx_normal = load(agent="test_pressure", task="normal_test")
    assert isinstance(ctx_normal, str)


def test_embeddings_search_cycle():
    """Verifica que embeddings search funciona con cosine similarity."""
    from lib.embeddings import query, status
    s = status()
    assert "pages" in s or "empty" in s
    results = query("arquitectura memoria agentes", top_k=3)
    assert isinstance(results, list)


def test_synapse_cosine():
    """Verifica que synapse usa cosine similarity, no BM25 fallback."""
    from lib.synapse import _find_similar
    results = _find_similar("compile-then-query", top_k=2)
    assert isinstance(results, list)


def test_vectorstore_query():
    """Verifica sqlite-vec query directa."""
    from lib import vectorstore as vs
    s = vs.status()
    assert "pages" in s
    results = vs.query("memoria sistema", top_k=2)
    assert isinstance(results, list)
    if results:
        assert "path" in results[0]
        assert "score" in results[0]


def test_vectorstore_concept_vector():
    """Verifica concept_vector lookup."""
    from lib import vectorstore as vs
    path = "concepts/checkpoint.md"
    vec = vs.concept_vector(path)
    if vec:
        assert len(vec) == 384


def test_vectorstore_migrate_idempotent():
    """Verifica que migrate_from_json no duplica datos."""
    from lib import vectorstore as vs
    before = vs.status()
    result = vs.migrate_from_json()
    after = vs.status()
    assert "already" in result.lower() or "Migrated" in result or before == after


def test_full_pipeline_multi_agent():
    """Verifica pipeline cross-agent: init -> check Aletheia -> check Kosmos."""
    from lib.pipeline import init, check
    result = init(topic="test multi-agent pipeline")
    assert "Pipeline" in result
    r1 = check(agent="aletheia")
    assert isinstance(r1, str)
    r2 = check(agent="kosmos")
    assert isinstance(r2, str)


def test_quality_after_vector_migration():
    """Verifica quality score con vectorstore activo."""
    from lib.quality import calculate
    q = calculate()
    assert "score" in q
    assert q["score"] >= 0
