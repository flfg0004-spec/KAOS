import sys
sys.path.insert(0, r"C:\Users\LeonX\Documents\KAOS\.memory\_scripts")

from lib.aether.config import (
    TASK_MODEL_MAP, MODEL_FALLBACK_CHAIN, MODEL_TIERS,
    COST_CAPS, COST_RATES, AGENT_TASK_MODEL,
)
from lib.aether import resolve_model
from lib.aether.ab_testing import ABTest
from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER
from lib.aether.observability import Timer
from lib.aether.quality_store import QualityStore


def test_config_keys():
    assert len(TASK_MODEL_MAP) >= 19
    assert set(MODEL_TIERS.keys()) == {"flash", "pro", "kimi", "mimo"}
    assert "go-mimo" in COST_RATES
    assert "mimo" in COST_CAPS
    assert "go-mimo" in MODEL_FALLBACK_CHAIN
    assert "default_task" in AGENT_TASK_MODEL["aletheia"]
    assert "default_model" in AGENT_TASK_MODEL["aletheia"]


def test_resolve_override():
    r1 = resolve_model(model_override="go-pro")
    assert r1["model"] == "go-pro"
    assert r1["tier"] == "override"


def test_resolve_research():
    r2 = resolve_model(task_type="research")
    assert r2["model"] in ("go-pro", "go-flash")


def test_resolve_agent_metis():
    r3 = resolve_model(agent="metis")
    assert r3["model"] in ("go-kimi-latest", "go-flash", "go-pro", "go-mimo")


def test_resolve_multimodal():
    r4 = resolve_model(has_images=True)
    assert r4["model"] in ("go-kimi-latest", "go-flash", "go-mimo")


def test_resolve_extract():
    r5 = resolve_model(task_type="extract")
    assert r5["model"] in ("go-mimo", "go-flash")


def test_resolve_default():
    r6 = resolve_model()
    assert r6["model"] == "go-gemini-flash"


def test_quality_store():
    qs = QualityStore()
    qs.record(
        model="go-mimo", task_type="code_simple", agent="kratos",
        scores={"correctness": 8, "coherence": 9},
        weighted_score=8.5, verdict="pass",
    )
    qs.record(
        model="go-mimo", task_type="code_simple", agent="kratos",
        scores={"correctness": 7, "coherence": 8},
        weighted_score=7.5, verdict="pass",
    )
    scores = qs.get_task_scores("code_simple")
    assert len(scores) > 0
    summary = qs.get_summary()
    assert summary["total_entries"] > 0


def test_circuit_breaker():
    cb = _ETHER_CIRCUIT_BREAKER
    assert cb is not None
    cb.record_success("go-mimo")
    assert cb.is_available("go-mimo")


def test_ab_test():
    ab = ABTest(task_type="research", control_model="go-pro", variant_model="go-mimo")
    assert ab is not None


def test_timer():
    import time
    with Timer() as t:
        time.sleep(0.01)
    assert t.elapsed_ms > 0
