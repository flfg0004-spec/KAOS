#!/usr/bin/env python3
"""Unified session runner — smoke, functional, audit profiles."""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def _run(script: str, *args, timeout: int = 120) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(BASE / script)] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def cmd_smoke(profile: str) -> bool:
    """2 min — quick post-output check."""
    print(f"Smoke check (profile: {profile})...")
    r = _run(".tools/verification_chain.py", profile, timeout=120)
    print(r.stdout)
    if r.stderr:
        print(r.stderr)
    ok = r.returncode == 0
    print(f"Smoke: {'PASS ✅' if ok else 'FAIL ❌'}")
    return ok


def cmd_functional(profile: str) -> dict:
    """15 min — full verification + scoring + session save."""
    print(f"Functional session (profile: {profile})...")

    # 1. Verification chain
    print("  Running verification chain...")
    subprocess.run(
        [sys.executable, str(BASE / ".tools/verification_chain.py"), profile],
        timeout=900,
    )

    # 2. Score engine
    print("  Running score engine...")
    r = _run(".tools/score_engine.py", "test", timeout=60)
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        data = {"composite": 0, "dimensions": {}, "error": r.stdout}
        print(f"  Score parse error: {r.stdout}")

    # 3. Save session
    sessions_dir = BASE / ".vault/quality/sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    session_file = sessions_dir / f"session-{stamp}.json"
    session_file.write_text(json.dumps(data, indent=2))
    print(f"  Session saved: {session_file.name}")
    print(f"  Composite: {data.get('composite', 'N/A')}")

    return data


def cmd_audit(profile: str):
    """60 min — full evaluation + weekly report."""
    print(f"Audit session (profile: {profile})...")
    cmd_functional(profile)
    print("  Generating weekly report...")
    r = _run(".tools/weekly_report.py", timeout=120)
    print(r.stdout)
    print("Audit complete ✅")


def main():
    parser = argparse.ArgumentParser(description="KAOS session runner")
    parser.add_argument("mode", choices=["smoke", "functional", "audit"])
    parser.add_argument("profile", nargs="?", default="desarrollo")
    args = parser.parse_args()

    modes = {"smoke": cmd_smoke, "functional": cmd_functional, "audit": cmd_audit}
    result = modes[args.mode](args.profile)
    sys.exit(0 if result is True or isinstance(result, dict) else 1)


if __name__ == "__main__":
    main()
