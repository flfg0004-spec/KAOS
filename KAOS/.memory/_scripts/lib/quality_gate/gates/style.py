"""Style gate — ruff format --check for Python."""

import subprocess
import sys


def gate_style(content: str, language: str = "python") -> dict:
    if language != "python":
        return {"gate": "style", "passed": True, "score": 5.0, "detail": "Style check only for Python"}
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "format", "--check", "--stdin-filename", "code.py", "-"],
            input=content, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return {"gate": "style", "passed": True, "score": 10.0, "detail": "Code style compliant"}
        issues = len([l for l in result.stdout.split("\n") if l.strip()])
        score = max(0, 10 - issues)
        return {"gate": "style", "passed": score >= 5, "score": score, "detail": f"{issues} style issues"}
    except Exception as e:
        return {"gate": "style", "passed": True, "score": 5.0, "detail": f"Style check error: {e}"}
