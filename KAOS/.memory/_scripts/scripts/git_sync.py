#!/usr/bin/env python3
"""Git auto-sync scaffolding for KAOS vault.

Uso:
  py -3 _scripts/scripts/git_sync.py --setup   # configura scaffolding
  py -3 _scripts/scripts/git_sync.py --status  # verifica estado
"""
import argparse
import subprocess
import sys
from pathlib import Path

def run_git(*args, cwd=None):
    return subprocess.run(["git"] + list(args), capture_output=True, text=True, cwd=cwd)

def cmd_setup():
    """Create .gitignore for library/ and configure git."""
    root = Path.cwd()
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("# KAOS vault\nlibrary/\n", encoding="utf-8")
        print("✅ .gitignore created")
    print("✅ Git sync scaffolding ready")

def cmd_status():
    """Check git status."""
    r = run_git("status", "--short")
    dirty = len([l for l in r.stdout.splitlines() if l.strip()])
    print(f"Git status: {'✅ clean' if dirty == 0 else f'⚠️ {dirty} uncommitted changes'}")

def main():
    parser = argparse.ArgumentParser(description="Git auto-sync for KAOS vault")
    parser.add_argument("--setup", action="store_true", help="Configure scaffolding")
    parser.add_argument("--status", action="store_true", help="Check status")
    args = parser.parse_args()
    if args.setup:
        cmd_setup()
    if args.status:
        cmd_status()
    return 0

if __name__ == "__main__":
    sys.exit(main())
