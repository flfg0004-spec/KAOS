"""Contextual Bandit LinUCB for CodeExperience confidence scoring.

Replaces simple confidence increment/decrement with 
LinUCB (Linear Upper Confidence Bound) for optimal 
exploration vs exploitation trade-off.
"""
import numpy as np
import json
import sqlite3
from typing import Dict, List, Optional
from pathlib import Path

DB = (Path(__file__).resolve().parent.parent.parent / ".memory" / "cache" / "code_experiences.db")


class LinUCBBandit:
    """Contextual bandit for code solution selection.
    
    Each 'arm' is a solution pattern (error_hash).
    Each 'context' is a feature vector describing the current error.
    
    Alpha controls exploration (higher = more exploration).
    
    State persists to SQLite via save()/load() — survives restarts.
    """
    
    def __init__(self, alpha: float = 0.2, n_features: int = 6):
        self.alpha = alpha
        self.n_features = n_features
        self.A: Dict[str, np.ndarray] = {}  # arm -> d x d matrix
        self.b: Dict[str, np.ndarray] = {}  # arm -> d x 1 vector
        
    def _init_arm(self, arm: str):
        if arm not in self.A:
            self.A[arm] = np.identity(self.n_features)
            self.b[arm] = np.zeros((self.n_features, 1))
    
    def select_arm(self, features: np.ndarray, available_arms: List[str]) -> Optional[str]:
        """Select arm with highest Upper Confidence Bound.
        
        Args:
            features: Context feature vector (n_features,)
            available_arms: List of arm IDs to choose from
            
        Returns:
            Selected arm ID, or None if no arms
        """
        if not available_arms:
            return None
        
        features = features.reshape(-1, 1)
        best_arm = None
        best_ucb = -float('inf')
        
        for arm in available_arms:
            self._init_arm(arm)
            A_inv = np.linalg.inv(self.A[arm])
            theta = A_inv @ self.b[arm]
            
            # UCB = theta^T * x + alpha * sqrt(x^T * A^{-1} * x)
            ucb = float(theta.T @ features) + self.alpha * float(np.sqrt(
                float(features.T @ A_inv @ features)
            ))
            
            if ucb > best_ucb:
                best_ucb = ucb
                best_arm = arm
        
        return best_arm
    
    def save(self, db_path: str = ""):
        """Persist bandit state to SQLite.
        
        Args:
            db_path: Path to SQLite DB (defaults to code_experiences.db)
        """
        path = Path(db_path) if db_path else DB
        try:
            conn = sqlite3.connect(str(path))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bandit_state (
                    arm_id TEXT PRIMARY KEY,
                    a_matrix TEXT NOT NULL,
                    b_vector TEXT NOT NULL
                )
            """)
            for arm in self.A:
                a_json = json.dumps(self.A[arm].tolist())
                b_json = json.dumps(self.b[arm].tolist())
                conn.execute(
                    "INSERT OR REPLACE INTO bandit_state (arm_id, a_matrix, b_vector) VALUES (?, ?, ?)",
                    (arm, a_json, b_json)
                )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def load(self, db_path: str = ""):
        """Restore bandit state from SQLite.
        
        Args:
            db_path: Path to SQLite DB (defaults to code_experiences.db)
        """
        path = Path(db_path) if db_path else DB
        try:
            conn = sqlite3.connect(str(path))
            rows = conn.execute("SELECT arm_id, a_matrix, b_vector FROM bandit_state").fetchall()
            for arm, a_json, b_json in rows:
                self.A[arm] = np.array(json.loads(a_json))
                self.b[arm] = np.array(json.loads(b_json))
            conn.close()
        except Exception:
            pass

    def update(self, arm: str, features: np.ndarray, reward: float):
        """Update arm parameters with observed reward.
        
        Auto-persists to SQLite after update.
        
        Args:
            arm: Arm ID that was selected
            features: Context feature vector at selection time
            reward: 1.0 for success, 0.0 for failure
        """
        self._init_arm(arm)
        x = features.reshape(-1, 1)
        self.A[arm] += x @ x.T
        self.b[arm] += reward * x
        self.save()  # Persist after each update
    
    def get_confidence(self, arm: str) -> float:
        """Get current estimated confidence (theta norm) for an arm."""
        if arm not in self.A:
            return 0.5
        A_inv = np.linalg.inv(self.A[arm])
        theta = A_inv @ self.b[arm]
        return float(1 / (1 + np.exp(-np.linalg.norm(theta))))


def extract_features(error: Dict) -> np.ndarray:
    """Extract feature vector from error data.
    
    Features:
        0: language (one-hot: python=0.8, rust=0.6, js=0.4, other=0.2)
        1: error_length (normalized: min(length/500, 1.0))
        2: has_stack_trace (binary: 0 or 1)
        3: ast_match_score (0.0 to 1.0)
        4: retrieval_count_norm (normalized: min(count/20, 1.0))
        5: has_solution_diff (binary: 0 or 1)
    """
    lang_map = {"python": 0.8, "rust": 0.6, "javascript": 0.4, "typescript": 0.3}
    lang = lang_map.get(error.get("language", ""), 0.2)
    
    return np.array([
        lang,
        min(len(error.get("error", "")) / 500, 1.0),
        1.0 if error.get("stack_trace") else 0.0,
        error.get("ast_score", 0.0),
        min(error.get("retrievals", 0) / 20, 1.0),
        1.0 if error.get("solution") else 0.0,
    ])


# Global singleton
_bandit = None

def get_bandit() -> LinUCBBandit:
    global _bandit
    if _bandit is None:
        _bandit = LinUCBBandit(alpha=0.2, n_features=6)
        _bandit.load()  # Restore persisted state
    return _bandit

def reset_bandit():
    global _bandit
    _bandit = None


if __name__ == "__main__":
    bandit = LinUCBBandit(alpha=0.3, n_features=6)
    
    # Simulate 3 arms with different rewards
    arms = ["hash1", "hash2", "hash3"]
    features = np.array([0.8, 0.4, 1.0, 0.0, 0.1, 0.0])
    
    print("=== LinUCB Bandit Test ===")
    for trial in range(20):
        selected = bandit.select_arm(features, arms)
        # Simulate reward: arm1 always good, arm2 50%, arm3 always bad
        reward = 1.0 if selected == "hash1" else (0.5 if selected == "hash2" else 0.0)
        bandit.update(selected, features, reward)
        print(f"Trial {trial+1:2d}: selected {selected}, reward {reward}")
    
    print(f"\nFinal confidences:")
    for arm in arms:
        print(f"  {arm}: {bandit.get_confidence(arm):.3f}")
    print(f"\n✅ Bandit should prefer hash1 > hash2 > hash3")
