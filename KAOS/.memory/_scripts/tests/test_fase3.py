"""Tests for FASE 3: Auto-ADR, Self-healing, Auto-tuning DSOL."""

import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.auto_adr import AutoADRDetector, AdrProposal
from lib.self_healing import SelfHealingGraph, CircuitBreaker
from lib.auto_tuning import cache_hit_rate, optimize_budget, status


# ── Auto-ADR Tests ─────────────────────────────────────────

def test_adr_proposal_creation():
    prop = AdrProposal(
        title="Test ADR",
        context="Test context",
        decision="Test decision",
        consequences=["+ Positive", "- Negative"],
        risk_level="minor",
    )
    assert prop.title == "Test ADR"
    assert prop.risk_level == "minor"
    assert prop.status == "proposed"


def test_adr_proposal_markdown():
    prop = AdrProposal(
        title="Test ADR",
        context="Test context",
        decision="Test decision",
        consequences=["+ Positive", "- Negative"],
        risk_level="minor",
    )
    md = prop.to_markdown(12)
    assert "# ADR-012: Test ADR" in md
    assert "## Contexto" in md
    assert "## Decision" in md
    assert "## Consecuencias" in md
    assert "+ Positive" in md
    assert "- Negative" in md


def test_detector_no_proposal_for_good_scores():
    detector = AutoADRDetector()
    result = detector.record_score("aletheia", 95, "good topic")
    assert result is None


def test_detector_proposal_after_3_failures():
    detector = AutoADRDetector()
    detector.record_score("kratos", 70, "topic")
    detector.record_score("kratos", 65, "topic2")
    result = detector.record_score("kratos", 55, "topic3")
    assert result is not None
    assert "kratos" in result.title.lower()


def test_detector_generates_risk_level():
    detector = AutoADRDetector()
    detector.record_score("aletheia", 70, "t1")
    detector.record_score("aletheia", 65, "t2")
    low_result = detector.record_score("aletheia", 70, "t3")

    detector2 = AutoADRDetector()
    detector2.record_score("aletheia", 50, "t1")
    detector2.record_score("aletheia", 45, "t2")
    critical_result = detector2.record_score("aletheia", 30, "t3")
    assert critical_result is not None and critical_result.risk_level == "critical"


# ── Self-healing Tests ─────────────────────────────────────

def test_circuit_breaker_starts_closed():
    cb = CircuitBreaker("test")
    assert cb.state == "closed"
    assert cb.can_try() is True


def test_circuit_opens_after_3_failures():
    cb = CircuitBreaker("test")
    cb.record_failure()
    cb.record_failure()
    escalated = cb.record_failure()
    assert cb.state == "open"
    assert escalated is True
    assert cb.failures == 3


def test_circuit_recovers_on_success():
    cb = CircuitBreaker("test")
    cb.record_failure()
    cb.record_success()
    assert cb.state == "closed"
    assert cb.failures == 0


def test_healing_graph_manages_multiple():
    hg = SelfHealingGraph()
    hg.record_failure("aletheia")
    hg.record_failure("kosmos")
    status = hg.status_all()
    assert "aletheia" in status
    assert "kosmos" in status
    assert status["aletheia"]["state"] == "half-open"
    assert status["aletheia"]["failures"] == 1


def test_healing_escalation():
    hg = SelfHealingGraph()
    hg.escalate("kratos", "test error")
    from pathlib import Path
    signals_dir = Path(__file__).resolve().parent.parent.parent / ".memory" / "bridge" / "signals"
    signals = list(signals_dir.glob("healing-escalation-*.json"))
    assert len(signals) > 0


# ── Auto-tuning DSOL Tests ─────────────────────────────────

def test_cache_hit_rate_no_data():
    rate = cache_hit_rate()
    assert isinstance(rate, float)
    assert 0 <= rate <= 100


def test_optimize_budget_runs():
    result = optimize_budget()
    assert "previous_budget" in result
    assert "new_budget" in result
    assert "cache_hit_rate" in result
    assert "changes" in result


def test_tuning_status():
    s = status()
    assert "cache_hit_rate" in s
    assert "weekly_cost" in s
    assert "targets" in s
    assert "budget" in s
