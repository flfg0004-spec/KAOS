"""Run all knowledge tests directly."""
import os
import sys
import subprocess

os.chdir(os.path.join(os.path.dirname(__file__), ".memory", "_scripts"))

test_files = [
    "tests/test_knowledge_scorer.py",
    "tests/test_knowledge_synthesis.py",
]

cmd = [sys.executable, "-m", "pytest"] + test_files + ["-v", "--no-header", "-q"]
print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:500])
print(f"Return code: {result.returncode}")
sys.exit(result.returncode)
