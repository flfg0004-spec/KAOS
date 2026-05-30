"""Tests for RSCB-MC contextual bandit — selection, update, persistence."""

import os, sys
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"

import numpy as np


def _clean_bandit_db():
    from lib.bandit import DB
    if DB.exists():
        DB.unlink()


def test_select_arm_returns_best():
    from lib.bandit import RSCBMCBandit
    bandit = RSCBMCBandit(alpha=0.1, risk_lambda=0.05, n_features=3)
    features = np.array([0.5, 0.3, 0.2])
    arms = ["arm_a", "arm_b"]
    
    for _ in range(10):
        bandit.update("arm_a", features, 1.0)
        bandit.update("arm_b", features, 0.0)
    
    selected = bandit.select_arm(features, arms)
    assert selected == "arm_a", f"Expected arm_a, got {selected}"


def test_update_changes_confidence():
    from lib.bandit import RSCBMCBandit
    bandit = RSCBMCBandit(alpha=0.2, risk_lambda=0.1, n_features=4)
    features = np.array([0.8, 0.4, 1.0, 0.0])
    
    init_conf = bandit.get_confidence("test_arm")
    bandit.update("test_arm", features, 1.0)
    after_conf = bandit.get_confidence("test_arm")
    assert after_conf != init_conf, "Confidence should change after update"


def test_select_arm_returns_none_if_no_arms():
    from lib.bandit import RSCBMCBandit
    bandit = RSCBMCBandit()
    features = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
    assert bandit.select_arm(features, []) is None


def test_select_arm_returns_valid_arm():
    from lib.bandit import RSCBMCBandit
    bandit = RSCBMCBandit()
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
    assert features[0] == 0.8
    assert features[2] == 1.0
    assert features[5] == 1.0


def test_extract_features_defaults():
    from lib.bandit import extract_features
    features = extract_features({"language": "unknown"})
    assert len(features) == 6
    assert features[0] == 0.2


def test_persistence_save_load():
    from lib.bandit import RSCBMCBandit, DB
    
    # Use a temp DB path to avoid Windows file locking conflicts
    import tempfile
    tmp_db = Path(tempfile.mktemp(suffix=".db"))
    
    bandit = RSCBMCBandit(alpha=0.2, risk_lambda=0.05, n_features=3)
    features = np.array([0.5, 0.3, 0.2])
    bandit.update("persist_arm", features, 1.0)
    saved_conf = bandit.get_confidence("persist_arm")
    bandit.save(str(tmp_db))
    
    new_bandit = RSCBMCBandit(alpha=0.2, risk_lambda=0.05, n_features=3)
    new_bandit.load(str(tmp_db))
    loaded_conf = new_bandit.get_confidence("persist_arm")
    assert abs(loaded_conf - saved_conf) < 0.001
    
    tmp_db.unlink(missing_ok=True)


def test_persistence_multiple_arms():
    from lib.bandit import RSCBMCBandit, DB
    import tempfile
    tmp_db = Path(tempfile.mktemp(suffix=".db"))
    
    bandit = RSCBMCBandit(alpha=0.2, risk_lambda=0.05, n_features=2)
    f1 = np.array([0.8, 0.2])
    f2 = np.array([0.3, 0.7])
    bandit.update("arm1", f1, 1.0)
    bandit.update("arm2", f2, 0.5)
    bandit.save(str(tmp_db))
    
    loaded = RSCBMCBandit(alpha=0.2, risk_lambda=0.05, n_features=2)
    loaded.load(str(tmp_db))
    assert loaded.get_confidence("arm1") > 0
    assert loaded.get_confidence("arm2") > 0
    
    tmp_db.unlink(missing_ok=True)


def test_reset():
    from lib.bandit import get_bandit, reset_bandit
    b1 = get_bandit()
    assert b1 is not None
    reset_bandit()
    b2 = get_bandit()
    assert b2 is not b1


def test_risk_penalty_prefers_stable_arms():
    """RSCB-MC should prefer arms with lower variance."""
    from lib.bandit import RSCBMCBandit
    bandit = RSCBMCBandit(alpha=0.1, risk_lambda=0.5, n_features=3)
    features = np.array([0.5, 0.3, 0.2])
    
    # Stable arm: always 0.8
    for _ in range(20):
        bandit.update("stable", features, 0.8)
    
    # Unstable arm: alternates 1.0 and 0.0 (high variance)
    for i in range(20):
        bandit.update("unstable", features, 1.0 if i % 2 == 0 else 0.0)
    
    # With high risk_lambda, stable should be preferred despite lower mean
    selected = bandit.select_arm(features, ["stable", "unstable"])
    assert selected == "stable", f"Expected stable (low variance), got {selected}"


def test_welford_variance():
    """Verify Welford's online algorithm produces correct variance."""
    from lib.bandit import RSCBMCBandit
    import numpy as np
    
    bandit = RSCBMCBandit(n_features=2)
    features = np.array([0.5, 0.5])
    
    values = [1.0, 0.0, 1.0, 0.0, 1.0]
    for v in values:
        bandit.update("test_welford", features, v)
    
    n = bandit.counts["test_welford"]
    mean = bandit.means["test_welford"]
    var = bandit.variances["test_welford"]
    
    expected_var = np.var(values, ddof=1)
    assert abs(var - expected_var) < 0.01, f"Welford variance {var:.4f} != numpy ddof=1 {expected_var:.4f}"
