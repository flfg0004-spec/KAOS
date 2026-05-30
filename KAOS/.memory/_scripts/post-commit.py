#!/usr/bin/env python3
"""Post-commit hook: run fast tests in background, save report on failure."""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS = BASE / ".memory" / "_scripts"
REPORTS_DIR = BASE / ".memory" / "bridge" / "reports"
PYTHON = "py" if sys.platform == "win32" else "python3"

r = subprocess.run(
    [PYTHON, str(SCRIPTS / "tests" / "run.py"), "--fast"],
    capture_output=True, text=True, timeout=120,
)

if r.returncode != 0:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORTS_DIR / f"test-fail-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    report.write_text(
        f"# Test Failure Report\n\n"
        f"**Time**: {datetime.now().isoformat()}\n\n"
        f"```\n{r.stdout[:2000]}\n```\n"
        f"```\n{r.stderr[:1000]}\n```\n",
        encoding="utf-8",
    )
    print(f"⚠️ Tests failed. Report saved to {report}")
else:
    print("✅ Post-commit tests passed")
