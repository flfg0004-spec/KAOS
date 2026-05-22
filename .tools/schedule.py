#!/usr/bin/env python3
"""Check scheduled tasks from dashboard and execute due ones."""

import subprocess
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

SCHEDULE = {
    "DistillRaw": {
        "freq": "daily",
        "cmd": [
            sys.executable,
            str(BASE / ".tools/distill.py"),
            "all",
            "--new-only",
        ],
    },
    "Distill": {
        "freq": "daily",
        "cmd": [
            sys.executable,
            str(BASE / ".memory/_scripts/vault.py"),
            "health",
            "--auto",
        ],
    },
    "Functional": {
        "freq": "daily",
        "cmd": [
            sys.executable,
            str(BASE / ".tools/session_runner.py"),
            "functional",
            "desarrollo",
        ],
    },
    "VaultHealth": {
        "freq": "weekly-sun",
        "cmd": [
            sys.executable,
            str(BASE / ".memory/_scripts/vault.py"),
            "health",
            "--auto",
        ],
    },
    "Verification": {
        "freq": "weekly-mon",
        "cmd": [
            sys.executable,
            str(BASE / ".tools/verification_chain.py"),
            "desarrollo",
        ],
    },
    "Audit": {
        "freq": "weekly-mon",
        "cmd": [
            sys.executable,
            str(BASE / ".tools/session_runner.py"),
            "audit",
            "desarrollo",
        ],
    },
}


def main():
    today = date.today()
    ran_any = False

    for name, task in SCHEDULE.items():
        should_run = False
        if task["freq"] == "daily":
            should_run = True
        elif task["freq"] == "weekly-mon" and today.weekday() == 0:
            should_run = True
        elif task["freq"] == "weekly-sun" and today.weekday() == 6:
            should_run = True

        if should_run:
            print(f"[{today}] Running {name}...")
            try:
                r = subprocess.run(task["cmd"], timeout=3600, capture_output=True, text=True)
                if r.returncode == 0:
                    print(f"  {name} ✅")
                else:
                    print(f"  {name} ❌ (exit {r.returncode})")
                    if r.stderr:
                        print(f"  stderr: {r.stderr[:500]}")
            except subprocess.TimeoutExpired:
                print(f"  {name} ⏰ timed out")
            ran_any = True

    if not ran_any:
        print(f"[{today}] No tasks due.")


if __name__ == "__main__":
    main()
