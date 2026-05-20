"""
KAOS Post-Output Hook v2 — Orquestación completa del pipeline
Detecta cambios y ejecuta: ingest → distill → synapse → embed → lint
Invocar: py .tools/post_output_hook.py (desde post-commit hook o manual)
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SESSION_RUNNER = BASE / ".tools" / "session_runner.py"
DISTILL_ENGINE = BASE / ".tools" / "distill.py"
INGEST_ENGINE = BASE / ".tools" / "ingest.py"
LOG_PATH = BASE / ".memory" / "wiki" / "log.md"
PYTHON = "py" if sys.platform == "win32" else "python3"


def _log(msg: str) -> None:
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n## [{datetime.now().isoformat()[:10]}] post-hook | {msg}\n")


def get_changed_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", ".memory/"],
        capture_output=True, text=True, cwd=BASE
    )
    if result.returncode != 0:
        return []
    return [f.strip() for f in result.stdout.split("\n") if f.strip()]


def classify_file(path: str) -> tuple[str, str]:
    if path.startswith(".memory/ingest/"):
        return "ingest", "ingest"
    if path.startswith(".memory/raw/"):
        return "raw", "distill"
    if path.startswith(".memory/wiki/"):
        return "wiki", "synapse"
    if path.startswith(".memory/schema/"):
        return "schema", "kosmos"
    return "other", "unknown"


def run_subprocess(script: Path, args: list[str], desc: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [PYTHON, str(script)] + args,
            capture_output=True, text=True, timeout=120
        )
        success = result.returncode == 0
        output = result.stdout[:300] + result.stderr[:100]
        return success, output
    except subprocess.TimeoutExpired:
        return False, f"Timeout: {desc}"
    except Exception as e:
        return False, f"Error: {e}"


def run_ingest_pipeline() -> bool:
    """Process ingest queue → raw/."""
    success, output = run_subprocess(INGEST_ENGINE, ["queue"], "ingest queue check")
    if success:
        _log(f"ingest queue: {output[:100]}")
    return success


def run_distill_pipeline() -> bool:
    """raw/ → wiki/ concepts + sources."""
    success, output = run_subprocess(DISTILL_ENGINE, ["all"], "distill")
    if success:
        _log(f"distill: {output[:100]}")
        return True
    else:
        _log(f"⚠️ distill issues: {output[:100]}")
        return False


def run_synapse_pipeline() -> bool:
    """Cross-link concepts semantically."""
    result = subprocess.run(
        [PYTHON, str(BASE / ".memory/_scripts/vault.py"), "synapse", "index"],
        capture_output=True, text=True, cwd=BASE, timeout=60
    )
    if result.returncode == 0:
        _log(f"synapse: {result.stdout[:100]}")
        return True
    return False


def run_lint_pipeline() -> bool:
    """Verify vault integrity."""
    result = subprocess.run(
        [PYTHON, str(BASE / ".memory/_scripts/vault.py"), "lint"],
        capture_output=True, text=True, cwd=BASE, timeout=60
    )
    ok = "0 issues" in result.stdout
    _log(f"lint: {'✅' if ok else '⚠️'}")
    return ok


def run_smoke_check() -> tuple[bool, str]:
    result = subprocess.run(
        [PYTHON, str(SESSION_RUNNER), "smoke", "desarrollo"],
        capture_output=True, text=True
    )
    return result.returncode == 0, result.stdout


def main():
    changed = get_changed_files()
    if not changed:
        print("No changes detected in .memory/")
        return

    print(f"KAOS Post-Hook v2 — {len(changed)} archivos cambiados")

    has_ingest = False
    has_raw = False
    has_wiki = False

    for path in changed:
        zone, _ = classify_file(path)
        print(f"  {path} → {zone}")
        if zone == "ingest":
            has_ingest = True
        elif zone == "raw":
            has_raw = True
        elif zone == "wiki":
            has_wiki = True

    # Pipeline stages
    if has_ingest:
        print("Stage 1/4: Ingest queue...")
        run_ingest_pipeline()

    if has_raw:
        print("Stage 2/4: Distilling raw → wiki...")
        run_distill_pipeline()

    if has_raw or has_wiki:
        print("Stage 3/4: Running synapse cross-linking...")
        run_synapse_pipeline()

    # Always run lint + smoke at end
    print("Stage 4/4: Quality checks...")
    lint_ok = run_lint_pipeline()
    smoke_ok, smoke_out = run_smoke_check()

    if lint_ok and smoke_ok:
        _log(f"post-hook complete: {len(changed)} files, health ok")
        print("Post-hook: ✅ complete")
    else:
        _log(f"⚠️ post-hook: {len(changed)} files, health DEGRADED")
        print(f"Post-hook: ⚠️ lint={'ok' if lint_ok else 'fail'}, smoke={'ok' if smoke_ok else 'fail'}")


if __name__ == "__main__":
    main()
