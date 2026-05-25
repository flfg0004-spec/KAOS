"""Sandbox entrypoint — ejecuta código recibido via stdin JSON.

Protocolo:
  INPUT (stdin, JSON):
    {"code": "...", "language": "python", "timeout": 30}
  OUTPUT (stdout, JSON):
    {"stdout": "...", "stderr": "...", "exit_code": 0}

Uso desde KAOS:
  docker run --rm -i kaos-sandbox < task.json
"""

import json
import sys
import subprocess
import tempfile
import os


def execute_python(code: str, timeout: int = 30) -> dict:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        fpath = f.name

    try:
        result = subprocess.run(
            ["python", fpath],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tempfile.gettempdir(),
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timeout", "exit_code": -1}
    finally:
        os.unlink(fpath)


def main():
    raw = sys.stdin.read()
    try:
        task = json.loads(raw)
    except json.JSONDecodeError as e:
        result = {"stdout": "", "stderr": f"JSON parse error: {e}", "exit_code": -1}
        print(json.dumps(result))
        return

    code = task.get("code", "")
    language = task.get("language", "python")
    timeout = task.get("timeout", 30)

    if language == "python":
        result = execute_python(code, timeout)
    else:
        result = {"stdout": "", "stderr": f"Unsupported language: {language}", "exit_code": -1}

    print(json.dumps(result))


if __name__ == "__main__":
    main()
