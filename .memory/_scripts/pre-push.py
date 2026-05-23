#!/usr/bin/env python3
"""pre-push: run vault.py lint and reject push if issues found.
Usage: python _scripts/pre-push.py (intended as git pre-push hook fallback)"""

import sys, subprocess, os, re

vault = os.path.join(os.path.dirname(__file__), "vault.py")
result = subprocess.run([sys.executable, vault, "lint"], capture_output=True, text=True)
print(result.stdout, end="")

report = os.path.join(os.path.dirname(__file__), "..", "schema", "lint-report.md")
try:
    content = open(report, encoding="utf-8").read()
    m = re.search(r"Total issues:\s*(\d+)", content)
    issues = int(m.group(1)) if m else 0
    if issues > 0:
        print(f"ERROR: Lint found {issues} issues. Push rejected.")
        sys.exit(1)
    print("Lint passed (0 issues). Push allowed.")
except FileNotFoundError:
    print("Warning: lint-report.md not found. Push allowed.")
    sys.exit(result.returncode)
