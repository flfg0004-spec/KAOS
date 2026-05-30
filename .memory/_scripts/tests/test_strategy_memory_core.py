import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from strategy_memory import StrategicMemoryBank


def _bank():
    return StrategicMemoryBank(db_path=":memory:")


def _context(overrides=None):
    ctx = {"industry": "cloud", "team_size": 5, "plan_type": "okr"}
    if overrides:
        ctx.update(overrides)
    return ctx


def test_store_and_recall_by_hash():
    bank = _bank()
    ctx = _context()
    content = {"okrs": [{"kr": "reduce latency", "target": "<200ms"}]}
    sid = bank.store(ctx, content, "okr", outcome_score=7.5)
    assert sid > 0
    results = bank.recall_similar(ctx, top_k=5)
    assert len(results) == 1
    assert results[0]["id"] == sid
    assert results[0]["outcome_score"] == 7.5


def test_recall_fallback_plan_type():
    bank = _bank()
    ctx1 = _context({"industry": "finance"})
    ctx2 = _context({"industry": "healthcare"})
    bank.store(ctx1, {"okrs": []}, "okr", outcome_score=6.0)
    bank.store(ctx2, {"okrs": []}, "okr", outcome_score=8.0)
    new_ctx = _context({"industry": "retail"})
    results = bank.recall_similar(new_ctx, top_k=5)
    assert len(results) >= 2
    assert all(r["plan_type"] == "okr" for r in results)


def test_recall_fallback_recent():
    bank = _bank()
    ctx1 = _context({"plan_type": "roadmap", "industry": "fintech"})
    ctx2 = _context({"plan_type": "foda", "industry": "edtech"})
    bank.store(ctx1, {"steps": []}, "roadmap")
    bank.store(ctx2, {"items": []}, "foda")
    new_ctx = {"plan_type": "unknown", "industry": "new"}
    results = bank.recall_similar(new_ctx, top_k=5)
    assert len(results) >= 2


def test_predict_outcome_with_scores():
    bank = _bank()
    ctx = _context()
    for score in [8.0, 6.0, 4.0, 9.0, 7.0]:
        bank.store(ctx, {"okrs": []}, "okr", outcome_score=score)
    prediction = bank.predict_outcome(ctx)
    assert prediction["probability_success"] is not None
    assert prediction["probability_success"] > 0
    assert prediction["based_on_n_strategies"] == 5
    assert prediction["avg_outcome_score"] is not None


def test_predict_outcome_no_scores():
    bank = _bank()
    ctx = _context()
    for _ in range(3):
        bank.store(ctx, {"okrs": []}, "okr")
    prediction = bank.predict_outcome(ctx)
    assert prediction["probability_success"] is None


def test_detect_patterns_high_failure():
    bank = _bank()
    ctx = _context()
    for score in [2.0, 3.0, 8.0]:
        bank.store(ctx, {"okrs": []}, "okr", outcome_score=score)
    patterns = bank.detect_patterns()
    assert len(patterns) >= 1
    match = [p for p in patterns if p["plan_type"] == "okr"]
    assert len(match) >= 1
    assert match[0]["failures"] >= 2
    assert match[0]["failure_rate"] >= 0.6


def test_detect_patterns_no_failure():
    bank = _bank()
    ctx = _context()
    for score in [8.0, 9.0, 7.5]:
        bank.store(ctx, {"okrs": []}, "okr", outcome_score=score)
    patterns = bank.detect_patterns()
    okr_patterns = [p for p in patterns if p["plan_type"] == "okr"]
    assert len(okr_patterns) == 0


def test_calibrate_adjusts_priors():
    bank = _bank()
    prior_before = bank.BETA_PRIORS.get("calidad_datos", (3, 3))
    feedback_data = {
        "feedback": [
            {"plan_type": "calidad_datos", "predicted_score": 5.0, "actual_score": 7.0}
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(feedback_data, f)
        fpath = f.name
    try:
        result = bank.calibrate(fpath)
        assert result["entries_processed"] == 1
        adj = result["adjustments"]["calidad_datos"]
        assert adj["prior_alpha"] == prior_before[0]
        assert adj["prior_beta"] == prior_before[1]
        assert adj["adjusted_alpha"] > prior_before[0]
        assert adj["adjusted_beta"] < prior_before[1]
    finally:
        Path(fpath).unlink(missing_ok=True)


def test_generate_prevention_suggestions():
    bank = _bank()
    ctx = _context()
    for score in [2.0, 3.0, 1.0]:
        bank.store(ctx, {"okrs": []}, "okr", outcome_score=score)
    suggestions = bank.generate_prevention_suggestions(ctx)
    assert len(suggestions) > 0
    high_risk = [s for s in suggestions if s["type"] == "high_risk"]
    assert len(high_risk) >= 1


def test_stats_empty_db():
    bank = _bank()
    s = bank.stats()
    assert s["total_strategies"] == 0
    assert s["total_patterns"] == 0
    assert s["by_plan_type"] == {}
    assert s["avg_outcome_score"] is None


def test_stats_populated_db():
    bank = _bank()
    ctx1 = _context({"industry": "cloud"})
    ctx2 = _context({"industry": "finance"})
    bank.store(ctx1, {"okrs": []}, "okr", outcome_score=8.0)
    bank.store(ctx2, {"okrs": []}, "roadmap", outcome_score=6.0)
    bank.store(ctx1, {"okrs": []}, "okr", outcome_score=7.0)
    s = bank.stats()
    assert s["total_strategies"] == 3
    assert s["by_plan_type"]["okr"] == 2
    assert s["by_plan_type"]["roadmap"] == 1
    assert s["avg_outcome_score"] == 7.0


def test_semantic_similarity_identical():
    bank = _bank()
    ctx = _context()
    sig = bank._context_to_signature(ctx)
    sim = bank.semantic_similarity(sig, sig)
    assert sim == 1.0


def test_semantic_similarity_similar():
    bank = _bank()
    ctx_a = _context({"industry": "cloud-gpu", "description": "high performance computing for AI workloads"})
    ctx_b = _context({"industry": "cloud-gpu", "description": "GPU cluster for machine learning training"})
    sig_a = bank._context_to_signature(ctx_a)
    sig_b = bank._context_to_signature(ctx_b)
    sim = bank.semantic_similarity(sig_a, sig_b)
    assert sim > 0.1


def test_semantic_similarity_different():
    bank = _bank()
    ctx_a = _context({"industry": "cloud-gpu"})
    ctx_b = _context({"industry": "healthtech", "focus": "compliance"})
    sig_a = bank._context_to_signature(ctx_a)
    sig_b = bank._context_to_signature(ctx_b)
    sim = bank.semantic_similarity(sig_a, sig_b)
    assert sim < 0.8


def test_recall_semantic_empty_db():
    bank = _bank()
    results = bank.recall_semantic(_context())
    assert len(results) == 0


def test_recall_semantic_finds_similar():
    bank = _bank()
    bank.store(_context({"industry": "cloud-gpu", "desc": "AI training"}), {"okrs": []}, "okr", outcome_score=8.0)
    bank.store(_context({"industry": "fintech", "desc": "payments"}), {"okrs": []}, "okr", outcome_score=6.0)
    results = bank.recall_semantic({"industry": "cloud-gpu", "desc": "machine learning"}, min_similarity=0.15)
    assert len(results) >= 1
    assert results[0]["similarity"] > 0


def test_cli_help():
    try:
        from strategy_memory import main as strategy_main
    except ImportError:
        import importlib
        mod = importlib.import_module("strategy_memory")
        strategy_main = mod.main
    import argparse
    try:
        strategy_main()
    except SystemExit as e:
        assert e.code in (0, 2)
    except argparse.Error:
        pass
