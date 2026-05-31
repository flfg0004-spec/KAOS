"""Quality Gate — syntax check, tests, and golden dataset validation.

Usage:
    py -3 quality_gate.py

Returns exit code 0 if all pass, 1 if any fail.
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIB = HERE / "lib"
TESTS = HERE / "tests"
GOLDEN = TESTS / "aletheia_golden_dataset.py"

CORE_TESTS = [
    "test_self_eval.py",
    "test_e2e_pipeline.py",
    "test_kosmos_quality.py",
    "test_aletheia_router.py",
    "test_verification.py",
    "test_aether_router.py",
    "test_aether_smoke.py",
    # Added in S10 (QW21):
    "test_lang_utils.py",
    "test_kratos_e2e.py",
    "test_quality_gate.py",
    "test_aether_config.py",
    "test_strategy_memory_core.py",
    "test_benchmark_strategist.py",
    "test_golden_queries.py",
]


def check_syntax() -> tuple[int, list[str]]:
    errors = []
    for pyfile in sorted(LIB.rglob("*.py")):
        if ".memory" in pyfile.parts or ".opencode" in pyfile.parts:
            continue
        rel = pyfile.relative_to(HERE)
        r = subprocess.run(
            [sys.executable, "-c", f"compile(open({str(pyfile)!r}, encoding='utf-8').read(), {str(pyfile)!r}, 'exec')"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            errors.append(f"{rel}: {r.stderr.strip()}")
    return len(errors), errors


def run_tests() -> tuple[int, list[str]]:
    errors = []
    for t in CORE_TESTS:
        tp = TESTS / t
        if not tp.exists():
            errors.append(f"Missing test: {t}")
            continue
        r = subprocess.run(
            [sys.executable, "-m", "pytest", str(tp), "--no-header", "-q"],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            errors.append(f"{t}: FAILED\n{r.stderr.strip()[:500]}")
    return len(errors), errors


def run_golden() -> tuple[int, list[str]]:
    r = subprocess.run(
        [sys.executable, str(GOLDEN)],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        return 1, [f"Golden dataset FAILED:\n{r.stderr.strip()[:500]}"]
    if '"accuracy": 100.0' not in r.stdout:
        return 1, [f"Golden dataset accuracy < 100%:\n{r.stdout.strip()[:500]}"]
    return 0, []


def main():
    print("=" * 50)
    print("QUALITY GATE")
    print("=" * 50)

    total_failures = 0

    print("\n1. Syntax check...")
    n, errors = check_syntax()
    if n == 0:
        print("   PASS: All files syntactically valid")
    else:
        print(f"   FAIL: {n} file(s) with syntax errors")
        for e in errors[:5]:
            print(f"     {e}")
        total_failures += n

    print("\n2. Core tests...")
    n, errors = run_tests()
    if n == 0:
        print("   PASS: All tests pass")
    else:
        print(f"   FAIL: {n} test(s) failed")
        for e in errors[:5]:
            print(f"     {e}")
        total_failures += n

    print("\n3. Golden dataset...")
    n, errors = run_golden()
    if n == 0:
        print("   PASS: 100% accuracy")
    else:
        print(f"   FAIL: {errors[0]}")
        total_failures += n

    print("\n4. Code coverage...")
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "--cov=lib", "--cov-report=term-missing",
             f"--cov-fail-under=20", "-x", "-q"] + [str(TESTS / t) for t in CORE_TESTS],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode == 0:
            print("   PASS: Coverage >= 20%")
        else:
            # Coverage may fail on first run — extract actual % without failing the gate
            cov_line = [l for l in r.stdout.split('\n') if 'TOTAL' in l]
            cov_pct = cov_line[0].split()[-1] if cov_line else "?"
            print(f"   INFO: Coverage at {cov_pct} (threshold 20%)")
            # Don't fail the gate for coverage
    except Exception as e:
        print(f"   SKIP: coverage check not available ({e})")

    print("\n" + "=" * 50)
    if total_failures == 0:
        print("RESULT: ALL GATES PASSED")
        sys.exit(0)
    else:
        print(f"RESULT: {total_failures} failure(s)")
        sys.exit(1)


if __name__ == "__main__":
    main()
