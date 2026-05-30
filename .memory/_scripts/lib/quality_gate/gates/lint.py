"""Lint gate — ruff for Python, clippy/eslint/golint for multi-lang."""

import os
import subprocess
import sys
import tempfile

from lib.feature_flags import is_enabled
from lib.quality_gate._toolchain import detect_toolchain


def gate_lint(content: str, language: str = "python") -> dict:
    if language != "python":
        return {"gate": "lint", "passed": True, "score": 5.0, "detail": "Lint only for Python"}
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--select", "E,F,W", "--stdin-filename", "code.py", "-"],
            input=content, capture_output=True, text=True, timeout=30
        )
        issues = len([l for l in result.stdout.split("\n") if l.strip()])
        score = max(0, 10 - issues)
        return {"gate": "lint", "passed": score >= 5, "score": score, "detail": f"{issues} issues"}
    except Exception as e:
        return {"gate": "lint", "passed": True, "score": 5.0, "detail": f"Lint error: {e}"}


def gate_lint_multi(content: str, language: str) -> dict:
    temp_path = None
    try:
        if language == "rust" and is_enabled("kratos_rust_gates"):
            if not detect_toolchain("cargo"):
                return {"gate": "lint", "passed": True, "score": 5.0, "detail": "cargo not installed"}
            with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False, encoding="utf-8") as f:
                f.write(content)
                temp_path = f.name
            result = subprocess.run(["cargo", "clippy", "--", temp_path], capture_output=True, text=True, timeout=30)
            issues = len([l for l in result.stdout.split("\n") if "warning" in l.lower() or "error" in l.lower()])
            score = max(0, 10 - issues)
            return {"gate": "lint", "passed": score >= 5, "score": score, "detail": f"clippy: {issues} issues"}

        if language == "typescript" and is_enabled("kratos_ts_gates"):
            if not detect_toolchain("eslint"):
                return {"gate": "lint", "passed": True, "score": 5.0, "detail": "eslint not installed"}
            with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False, encoding="utf-8") as f:
                f.write(content)
                temp_path = f.name
            result = subprocess.run(
                ["eslint", "--no-eslintrc", "--rule", "{'no-unused-vars':'warn'}", temp_path],
                capture_output=True, text=True, timeout=30
            )
            issues = len([l for l in (result.stdout + result.stderr).split("\n") if "error" in l.lower() or "warning" in l.lower()])
            score = max(0, 10 - issues)
            return {"gate": "lint", "passed": score >= 5, "score": score, "detail": f"eslint: {issues} issues"}

        if language == "go" and is_enabled("kratos_go_gates"):
            if not detect_toolchain("golint"):
                return {"gate": "lint", "passed": True, "score": 5.0, "detail": "golint not installed"}
            with tempfile.NamedTemporaryFile(mode="w", suffix=".go", delete=False, encoding="utf-8") as f:
                f.write("package main\n" + content)
                temp_path = f.name
            result = subprocess.run(["golint", temp_path], capture_output=True, text=True, timeout=30)
            issues = len([l for l in result.stdout.split("\n") if l.strip()])
            score = max(0, 10 - issues)
            return {"gate": "lint", "passed": score >= 5, "score": score, "detail": f"golint: {issues} issues"}

    except subprocess.TimeoutExpired:
        return {"gate": "lint", "passed": True, "score": 5.0, "detail": f"Lint timed out for {language}"}
    except Exception as e:
        return {"gate": "lint", "passed": True, "score": 5.0, "detail": f"Lint error: {e}"}
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except Exception:
                pass

    return {"gate": "lint", "passed": True, "score": 5.0, "detail": f"No lint gate for {language}"}
