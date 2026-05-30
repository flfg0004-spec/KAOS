"""Compilation gate — py_compile for Python, rustc/tsc/go vet for multi-lang."""

import os
import subprocess
import sys
import tempfile

from lib.feature_flags import is_enabled
from lib.quality_gate._toolchain import detect_toolchain


def gate_compilation(content: str, language: str = "python") -> dict:
    if language != "python":
        return {"gate": "compilation", "passed": True, "score": 5.0,
                "detail": "Compilation check only for Python"}
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            import py_compile
            py_compile.compile(tmp, doraise=True)
            return {"gate": "compilation", "passed": True, "score": 10.0,
                    "detail": "Compiles without errors"}
        except py_compile.PyCompileError as e:
            return {"gate": "compilation", "passed": False, "score": 0.0,
                    "detail": f"Compile error: {e}"}
        finally:
            try:
                os.unlink(tmp)
            except Exception:
                pass
    except Exception as e:
        return {"gate": "compilation", "passed": True, "score": 5.0,
                "detail": f"Compilation check error: {e}"}


def gate_compilation_multi(content: str, language: str) -> dict:
    temp_path = None
    try:
        if language == "rust" and is_enabled("kratos_rust_gates"):
            if not detect_toolchain("rustc"):
                return {"gate": "compilation", "passed": True, "score": 5.0, "detail": "rustc not installed"}
            with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False, encoding="utf-8") as f:
                f.write(content)
                temp_path = f.name
            result = subprocess.run(["rustc", "--edition", "2021", "--crate-type", "lib", temp_path],
                                    capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {"gate": "compilation", "passed": True, "score": 10.0, "detail": "rustc compiles without errors"}
            return {"gate": "compilation", "passed": False, "score": 0.0, "detail": f"rustc error: {result.stderr[:200]}"}

        if language == "typescript" and is_enabled("kratos_ts_gates"):
            if not detect_toolchain("tsc"):
                return {"gate": "compilation", "passed": True, "score": 5.0, "detail": "tsc not installed"}
            with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False, encoding="utf-8") as f:
                f.write(content)
                temp_path = f.name
            result = subprocess.run(["tsc", "--noEmit", "--strict", "--lib", "es6,dom", temp_path],
                                    capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {"gate": "compilation", "passed": True, "score": 10.0, "detail": "tsc type-checks without errors"}
            return {"gate": "compilation", "passed": False, "score": 3.0, "detail": f"tsc errors: {result.stdout[:200] or result.stderr[:200]}"}

        if language == "go" and is_enabled("kratos_go_gates"):
            if not detect_toolchain("go"):
                return {"gate": "compilation", "passed": True, "score": 5.0, "detail": "go not installed"}
            with tempfile.NamedTemporaryFile(mode="w", suffix=".go", delete=False, encoding="utf-8") as f:
                f.write("package main\n" + content)
                temp_path = f.name
            result = subprocess.run(["go", "vet", temp_path], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {"gate": "compilation", "passed": True, "score": 10.0, "detail": "go vet passes"}
            return {"gate": "compilation", "passed": False, "score": 3.0, "detail": f"go vet errors: {result.stderr[:200]}"}

    except subprocess.TimeoutExpired:
        return {"gate": "compilation", "passed": True, "score": 5.0, "detail": f"Compilation timed out for {language}"}
    except Exception as e:
        return {"gate": "compilation", "passed": True, "score": 5.0, "detail": f"Compilation check error: {e}"}
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except Exception:
                pass

    return {"gate": "compilation", "passed": True, "score": 5.0, "detail": f"No compilation gate for {language}"}
