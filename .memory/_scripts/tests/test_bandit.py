"""Tests for LinUCB contextual bandit — selection, update, persistence."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"

import numpy as np


def _clean_bandit_db():
    from lib.bandit import DB
    if DB.exists():
        DB.unlink()


def test_select_arm_returns_best():
    from lib.bandit import LinUCBBandit
    bandit = LinUCBBandit(alpha=0.1, n_features=3)
    features = np.array([0.5, 0.3, 0.2])
    arms = ["arm_a", "arm_b"]
    
    # Pre-train: arm_a gets rewards, arm_b doesn't
    for _ in range(10):
        bandit.update("arm_a", features, 1.0)
        bandit.update("arm_b", features, 0.0)
    
    selected = bandit.select_arm(features, arms)
    assert selected == "arm_a", f"Expected arm_a, got {selected}"


def test_update_changes_confidence():
    from lib.bandit import LinUCBBandit
    bandit = LinUCBBandit(alpha=0.2, n_features=4)
    features = np.array([0.8, 0.4, 1.0, 0.0])
    
    init_conf = bandit.get_confidence("test_arm")
    bandit.update("test_arm", features, 1.0)
    after_conf = bandit.get_confidence("test_arm")
    assert after_conf != init_conf, "Confidence should change after update"


def test_select_arm_returns_none_if_no_arms():
    from lib.bandit import LinUCBBandit
    bandit = LinUCBBandit()
    features = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
    assert bandit.select_arm(features, []) is None


def test_select_arm_returns_valid_arm():
    from lib.bandit import LinUCBBandit
    bandit = LinUCBBandit()
    features = np.array([0.8, 0.2, 1.0, 0.0, 0.1, 0.0])
    arm = bandit.select_arm(features, ["hash_x"])
    assert arm == "hash_x"


def test_extract_features():
    from lib.bandit import extract_features
    error_data = {
        "language": "python",
        "error": "TypeError: NoneType",
        "stack_trace": "File test.py line 1",
        "solution": "Check for None",
        "retrievals": 5,
        "ast_score": 0.8,
    }
    features = extract_features(error_data)
    assert len(features) == 6
    assert features[0] == 0.8  # python
    assert features[2] == 1.0  # has stack_trace
    assert features[5] == 1.0  # has solution


def test_extract_features_defaults():
    from lib.bandit import extract_features
    features = extract_features({"language": "unknown"})
    assert len(features) == 6
    assert features[0] == 0.2  # unknown lang


def test_persistence_save_load():
    from lib.bandit import LinUCBBandit, DB
    _clean_bandit_db()
    
    bandit = LinUCBBandit(alpha=0.2, n_features=3)
    features = np.array([0.5, 0.3, 0.2])
    bandit.update("persist_arm", features, 1.0)
    saved_conf = bandit.get_confidence("persist_arm")
    bandit.save(str(DB))
    
    new_bandit = LinUCBBandit(alpha=0.2, n_features=3)
    new_bandit.load(str(DB))
    loaded_conf = new_bandit.get_confidence("persist_arm")
    assert abs(loaded_conf - saved_conf) < 0.001, f"Confidence mismatch: {saved_conf} vs {loaded_conf}"


def test_persistence_multiple_arms():
    from lib.bandit import LinUCBBandit, DB
    _clean_bandit_db()
    
    bandit = LinUCBBandit(alpha=0.2, n_features=2)
    f1 = np.array([0.8, 0.2])
    f2 = np.array([0.3, 0.7])
    bandit.update("arm1", f1, 1.0)
    bandit.update("arm2", f2, 0.5)
    bandit.save(str(DB))
    
    loaded = LinUCBBandit(alpha=0.2, n_features=2)
    loaded.load(str(DB))
    assert loaded.get_confidence("arm1") > 0
    assert loaded.get_confidence("arm2") > 0


def test_reset():
    from lib.bandit import get_bandit, reset_bandit
    b1 = get_bandit()
    assert b1 is not None
    reset_bandit()
    b2 = get_bandit()
    assert b2 is not b1  # Different instance after reset
