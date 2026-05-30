"""Tests for the verification chain (cross-agent quality verification)."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["KAOS_TESTING"] = "1"


def test_generate_claim_id():
    from verification_chain import generate_claim_id

    cid = generate_claim_id("Kosmos", "test-topic")
    assert cid.startswith("kosmos"), f"Expected 'kosmos...', got '{cid}'"
    assert "test-topic" in cid
    assert " " not in cid


def test_verify_output_structure():
    from verification_chain import verify_output

    v, path = verify_output("test-claim", "test_agent", "test_verifier", {"veracidad": 80})
    assert v["agent_origin"] == "test_agent"
    assert v["agent_verifier"] == "test_verifier"
    assert v["scores"]["veracidad"] == 80
    assert "evidence_hash" in v
    assert path.exists()
    assert path.suffix == ".json"
    path.unlink()


def test_run_verification_chain():
    from verification_chain import run_verification_chain

    outputs = {
        "aletheia": {"veracidad": 82, "coherencia": 76},
        "kosmos": {"completitud": 80, "utilidad": 78},
        "metis": {"veracidad": 85, "reproducibilidad": 72},
    }
    results = run_verification_chain(outputs)
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    for v in results:
        assert "agent_origin" in v
        assert "agent_verifier" in v
        assert "scores" in v


def test_chain_empty_outputs():
    from verification_chain import run_verification_chain

    results = run_verification_chain({})
    assert results == [], f"Expected empty list, got {results}"


def test_chain_skips_missing_agents():
    from verification_chain import run_verification_chain

    outputs = {"aletheia": {"veracidad": 90}}
    results = run_verification_chain(outputs)
    assert len(results) == 1
    assert results[0]["agent_origin"] == "aletheia"


def test_verify_output_includes_evaluations():
    from verification_chain import verify_output

    v, path = verify_output("eval-claim", "agent_a", "agent_b", {"veracidad": 85, "coherencia": 90})
    assert "evaluations" in v
    assert "veracidad" in v["evaluations"]
    assert "coherencia" in v["evaluations"]
    path.unlink()
