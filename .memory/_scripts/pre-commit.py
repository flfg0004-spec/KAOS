#!/usr/bin/env python3
"""Pre-commit hook for KAOS: lint + coverage + API key check.

Installed as .git/hooks/pre-commit (symlink to this file).
Runs before each commit and rejects if:
- Lint issues > 0
- Coverage < 100%
- API keys detected in staged files
"""

import subprocess
import sys
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
SCRIPTS = os.path.join(BASE, ".memory", "_scripts")
VAULT_PY = os.path.join(SCRIPTS, "vault.py")
PYTHON = "py" if sys.platform == "win32" else "python3"

errors = []

print("=== KAOS Pre-commit Hook ===")

# 1. Lint check
print("\n[1/3] Running lint...")
r = subprocess.run([PYTHON, VAULT_PY, "lint", "run"], capture_output=True, text=True)
output = r.stdout.strip() or r.stderr.strip()
print(output)
if "0 issues" not in output:
    errors.append(f"Lint found issues: {output[:100]}")

# 2. Coverage check
print("\n[2/3] Checking coverage...")
r = subprocess.run([PYTHON, VAULT_PY, "lint", "coverage"], capture_output=True, text=True)
output = r.stdout.strip() or r.stderr.strip()
print(output.split("\n")[0])
if "100.0%" not in output:
    errors.append(f"Coverage not at 100%")

# 3. API key check on staged files
print("\n[3/3] Scanning for exposed API keys...")
r = subprocess.run(
    ["git", "diff", "--cached", "--name-only"],
    capture_output=True, text=True
)
staged = r.stdout.strip().split("\n")
key_patterns = [
    (r'sk-[a-zA-Z0-9]{20,}', "OpenAI-style API key"),
    (r'[Aa][Pp][Ii]_[Kk][Ee][Yy].{0,10}["\']', "API_KEY assignment"),
    (r'6fa7bd38-4bb9-4667', "EXA_API_KEY (hardcoded)"),
    (r'f4155bb6cad0b4cd', "OBSIDIAN_API_KEY (hardcoded)"),
]
found_keys = False
for f in staged:
    if not f or not os.path.exists(f):
        continue
    if f.endswith((".py", ".json", ".yml", ".yaml", ".toml", ".md", ".ps1")):
        content = open(f, encoding="utf-8", errors="replace").read()
        for pattern, desc in key_patterns:
            if re.search(pattern, content):
                print(f"  ⚠️  {f}: possible {desc}")
                found_keys = True
if found_keys:
    errors.append("API keys detected in staged files")

# Result
if errors:
    print(f"\n❌ Pre-commit FAILED: {'; '.join(errors)}")
    print("Fix issues and commit again.")
    sys.exit(1)
else:
    print("\n✅ Pre-commit passed")
    sys.exit(0)
