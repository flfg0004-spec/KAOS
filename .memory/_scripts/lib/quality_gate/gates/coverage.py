"""Coverage gate — real pytest --cov when flag enabled, else estimate.

Improvement (H3 Sprint 4):
- _find_project_tests() discovers real test_*.py / *_test.py files
- If real tests exist and use_real_coverage is enabled, run pytest --cov on them
- Fall back to tempfile-only if no real tests found
"""

import glob
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from lib.feature_flags import is_enabled


def _find_project_tests() -> list[str]:
    """Discover real test files in the project, excluding virtual environments."""
    test_files = (
        glob.glob("**/test_*.py", recursive=True)
        + glob.glob("**/*_test.py", recursive=True)
    )
    return [
        f for f in test_files
        if "site-packages" not in f
        and ".venv" not in f
        and "node_modules" not in f
        and "__pycache__" not in f
    ]


def gate_coverage(content: str = "", has_tests: bool = False) -> dict:
    if is_enabled("use_real_coverage") and content.strip():
        # Try real project tests first
        project_tests = _find_project_tests()
        if project_tests:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", *project_tests,
                     "--cov", "--cov-report=json", "--cov-fail-under=0", "-qq"],
                    capture_output=True, text=True, timeout=120
                )
                cov_json = Path("coverage.json")
                if cov_json.exists():
                    data = json.loads(cov_json.read_text(encoding="utf-8"))
                    cov_json.unlink(missing_ok=True)
                    pct = data.get("totals", {}).get("percent_covered", 0.0)
                    n_files = len(data.get("files", {}))
                else:
                    pct = 0.0
                    n_files = 0
                score = min(10.0, pct / 10.0)
                return {
                    "gate": "coverage", "passed": score >= 5.0,
                    "score": round(score, 1),
                    "detail": f"pytest --cov ({len(project_tests)} test files): "
                              f"{pct:.1f}% covered across {n_files} modules"
                }
            except Exception as e:
                return {"gate": "coverage", "passed": has_tests, "score": 7.0 if has_tests else 3.0,
                        "detail": f"Coverage real (project tests) failed: {e}"}

        # Fall back to tempfile-only coverage
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
                f.write(content)
                tmp = f.name
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", tmp, "--cov", "--cov-report=json",
                     "--cov-fail-under=0", "-qq"],
                    capture_output=True, text=True, timeout=60
                )
                cov_json = Path("coverage.json")
                if cov_json.exists():
                    data = json.loads(cov_json.read_text(encoding="utf-8"))
                    cov_json.unlink(missing_ok=True)
                    pct = data.get("totals", {}).get("percent_covered", 0.0)
                else:
                    pct = 0.0
                score = min(10.0, pct / 10.0)
                return {"gate": "coverage", "passed": score >= 5.0, "score": round(score, 1),
                        "detail": f"pytest --cov: {pct:.1f}% covered"}
            finally:
                try:
                    os.unlink(tmp)
                except Exception:
                    pass
        except Exception as e:
            return {"gate": "coverage", "passed": has_tests, "score": 7.0 if has_tests else 3.0,
                    "detail": f"Coverage real failed, fallback: {e}"}
    return {"gate": "coverage", "passed": has_tests, "score": 7.0 if has_tests else 3.0,
            "detail": "Has tests" if has_tests else "No tests detected"}
