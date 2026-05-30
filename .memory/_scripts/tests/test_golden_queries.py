"""Tests for golden strategy queries — validates semantic recall with MRR."""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from strategy_memory import StrategicMemoryBank

GOLDEN_PATH = Path(__file__).resolve().parent / "golden_strategy_queries.json"


def _load_golden():
    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("queries", data.get("entries", []))


def _compute_mrr(results, relevant_ids):
    """Mean Reciprocal Rank @ K"""
    relevant = set(str(i) for i in (relevant_ids or []))
    for rank, r in enumerate(results, 1):
        if str(r.get("id")) in relevant:
            return 1.0 / rank
    return 0.0


def test_golden_file_exists():
    assert GOLDEN_PATH.exists()
    data = _load_golden()
    assert len(data) > 0


def test_golden_queries_have_required_fields():
    for q in _load_golden():
        assert "query" in q, f"Missing query field"
        has_ids = "relevant_ids" in q or "context" in q
        assert has_ids, f"Missing relevant_ids or context in: {q.get('query', '?')[:40]}"


def test_golden_recall_returns_results():
    bank = StrategicMemoryBank(db_path=":memory:")
    for q in _load_golden()[:3]:
        ctx = q.get("context", {"industry": "test", "plan_type": "okr"})
        results = bank.recall_semantic(ctx, top_k=5)
        assert isinstance(results, list)


def test_golden_recall_mrr():
    """MRR@5 debe ser ≥ 0.5 en golden dataset (baseline without txtai)."""
    queries = _load_golden()
    bank = StrategicMemoryBank(db_path=":memory:")

    id_context_map = {}
    for q in queries:
        ctx = q.get("context", {})
        for rid in q.get("relevant_ids", []):
            if rid not in id_context_map:
                id_context_map[rid] = dict(ctx)

    stored_ids = {}
    for sid, ctx in id_context_map.items():
        content = {"okrs": [{"name": f"KR_{sid}", "target": 100}]}
        stored_id = bank.store(ctx, content, ctx.get("plan_type", "okr"), outcome_score=7.0)
        stored_ids[sid] = stored_id

    mrr_sum = 0.0
    valid_queries = 0
    for q in queries:
        ctx = q.get("context", {})
        if not ctx:
            continue
        results = bank.recall_semantic(ctx, top_k=5)
        mapped_ids = [stored_ids.get(rid) for rid in q.get("relevant_ids", [])]
        mrr = _compute_mrr(results, mapped_ids)
        mrr_sum += mrr
        valid_queries += 1

    avg_mrr = mrr_sum / max(valid_queries, 1)
    assert avg_mrr >= 0.5, f"MRR@5 = {avg_mrr:.3f} < 0.5 (baseline without txtai)"


def test_golden_recall_exact_matches_first():
    """Hash exacto debe rankear primero."""
    bank = StrategicMemoryBank(db_path=":memory:")
    bank.store(
        {"industry": "cloud", "plan_type": "okr"},
        {"okrs": [{"name": "test", "target": 100}]},
        "okr",
    )
    bank.store(
        {"industry": "fintech", "plan_type": "okr"},
        {"okrs": [{"name": "test2", "target": 200}]},
        "okr",
    )
    results = bank.recall_semantic({"industry": "cloud", "plan_type": "okr"}, top_k=5)
    assert len(results) > 0
    assert results[0]["id"] == 1, f"Expected id=1 (exact hash match) first, got id={results[0]['id']}"


def test_golden_queries_json_valid():
    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, (list, dict))
