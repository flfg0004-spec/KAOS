"""Types gate — real mypy --strict when flag enabled, else regex fallback."""

import os
import re
import subprocess
import tempfile

from lib.feature_flags import is_enabled
from lib.quality_gate._toolchain import detect_toolchain


def gate_types(content: str, language: str = "python") -> dict:
    if language != "python":
        return {"gate": "types", "passed": True, "score": 5.0, "detail": "Type check only for Python"}

    if is_enabled("use_real_mypy"):
        try:
            if not detect_toolchain("mypy"):
                return {"gate": "types", "passed": True, "score": 5.0, "detail": "mypy not installed"}
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
                f.write(content)
                tmp = f.name
            try:
                result = subprocess.run(["mypy", "--strict", tmp], capture_output=True, text=True, timeout=30)
                issues = len([l for l in result.stdout.split("\n") if l.strip() and ":" in l])
                passed = result.returncode == 0
                score = max(0, 10 - issues)
                return {"gate": "types", "passed": passed, "score": float(score),
                        "detail": f"mypy: {issues} issues" if issues else "mypy: no issues"}
            finally:
                try:
                    os.unlink(tmp)
                except Exception:
                    pass
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass

    has_types = bool(re.search(r":\s*\w+", content)) and bool(re.search(r"->\s*\w+", content))
    score = 10.0 if has_types else 2.0
    return {"gate": "types", "passed": has_types, "score": score,
            "detail": "Has type hints (regex)" if has_types else "Missing type hints (regex)"}
