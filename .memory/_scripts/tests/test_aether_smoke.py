"""Smoke tests for aether consolidated package."""

import sys

sys.path.insert(0, r"C:\Users\LeonX\Documents\KAOS\.memory\_scripts")

from lib.aether.config import (
    TASK_MODEL_MAP,
    MODEL_FALLBACK_CHAIN,
    MODEL_TIERS,
    COST_CAPS,
    COST_RATES,
    AGENT_TASK_MODEL,
)
from lib.aether import resolve_model
from lib.aether.ab_testing import ABTest
from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER
from lib.aether.observability import Timer
from lib.aether.quality_store import QualityStore

errors = []


def check(desc, cond):
    if not cond:
        errors.append(f"FAIL: {desc}")


# ── Config tests ──
check("19+ task types", len(TASK_MODEL_MAP) >= 19)
check("4 tiers", set(MODEL_TIERS.keys()) == {"flash", "pro", "kimi", "mimo"})
check("MiMo in cost rates", "go-mimo" in COST_RATES)
check("MiMo in cost caps", "mimo" in COST_CAPS)
check("MiMo in fallback chain", "go-mimo" in MODEL_FALLBACK_CHAIN)
check(
    "Agent has default_task+default_model",
    "default_task" in AGENT_TASK_MODEL["aletheia"] and "default_model" in AGENT_TASK_MODEL["aletheia"],
)

# ── Router tests ──
r1 = resolve_model(model_override="go-pro")
check("override works", r1["model"] == "go-pro" and r1["tier"] == "override")

r2 = resolve_model(task_type="research")
check("research -> pro", r2["model"] == "go-pro" and r2["thinking"] == "high")

r3 = resolve_model(agent="metis")
check("metis default -> strategy -> kimi", r3["model"] == "go-kimi-latest")

r4 = resolve_model(has_images=True)
check("multimodal routes", r4["model"] in ("go-kimi-latest", "go-flash", "go-mimo"))

r5 = resolve_model(task_type="extract")
check("extract -> mimo or flash", r5["model"] in ("go-mimo", "go-flash"))

r6 = resolve_model()
check("absolute default -> flash", r6["model"] == "go-flash")

# ── QualityStore tests ──
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
qs.record(
    model="go-flash", task_type="code_simple", agent="kratos",
    scores={"correctness": 6, "coherence": 7},
    weighted_score=6.5, verdict="pass",
)

scores = qs.get_task_scores("code_simple")
check("QualityStore has scores", len(scores) > 0)

summary = qs.get_summary()
check("Summary has entries", summary["total_entries"] > 0)

# ── CircuitBreaker tests ──
cb = _ETHER_CIRCUIT_BREAKER
check("CB initialized", cb is not None)
cb.record_success("go-mimo")
check("CB handles MiMo", cb.is_available("go-mimo"))

# ── ABTest tests ──
ab = ABTest(task_type="research", control_model="go-pro", variant_model="go-mimo")
check("ABTest initializes", ab is not None)

# ── Timer test ──
import time

with Timer() as t:
    time.sleep(0.01)
check("Timer measures ms", t.elapsed_ms > 0)

# ── Results ──
total = 22
passed = total - len(errors)
print(f"\n{'=' * 50}")
print("AETHER SMOKE TEST RESULTS")
print(f"{'=' * 50}")
print(f"Tests: {passed}/{total} passed")
if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  ❌ {e}")
    sys.exit(1)
else:
    print("✅ ALL TESTS PASSED")
    sys.exit(0)
