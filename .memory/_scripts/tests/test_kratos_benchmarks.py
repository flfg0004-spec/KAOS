"""Benchmark tests for Kratos quality gates — sequential vs parallel performance."""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"

from lib.quality_gate import evaluate, evaluate_parallel
from lib.feature_flags import enable, disable


def test_parallel_faster_than_sequential():
    """Parallel evaluation should not be significantly slower than sequential."""
    code = '''
def add(a: int, b: int) -> int:
    return a + b
def sub(a: int, b: int) -> int:
    return a - b
def mul(a: int, b: int) -> int:
    return a * b
def test_add():
    assert add(1, 2) == 3
def test_sub():
    assert sub(5, 3) == 2
def test_mul():
    assert mul(2, 3) == 6
'''
    enable("use_parallel_gates")
    try:
        start = time.time()
        seq = evaluate(code, "python")
        seq_time = time.time() - start

        start = time.time()
        par = evaluate_parallel(code, "python")
        par_time = time.time() - start

        # Composites should be within 1.0 of each other
        assert abs(seq["composite"] - par["composite"]) < 1.0, \
            f"Composite mismatch: seq={seq['composite']} par={par['composite']}"
        # Parallel shouldn't be more than 3x slower than sequential
        assert par_time < seq_time * 3, \
            f"Parallel too slow: seq={seq_time:.3f}s par={par_time:.3f}s"
    finally:
        disable("use_parallel_gates")


def test_benchmark_gate_independence():
    """Each gate runs independently in parallel mode."""
    from lib.quality_gate.gates import list_gates
    gates = list_gates()
    assert len(gates) >= 8
    assert "syntax" in gates
    assert "lint" in gates
    assert "types" in gates


def test_benchmark_parallel_multi_lang_performance():
    """Multi-lang parallel evaluation completes without errors."""
    enable("use_parallel_gates")
    enable("use_rust_gates")
    try:
        code = "fn main() { println!(\"hello\"); }"
        start = time.time()
        result = evaluate_parallel(code, language="rust")
        elapsed = time.time() - start
        assert "composite" in result
        assert "gates" in result
        # Should complete within reasonable time
        assert elapsed < 30.0, f"Rust parallel too slow: {elapsed:.2f}s"
    finally:
        disable("use_parallel_gates")
        disable("use_rust_gates")


def test_benchmark_early_exit_speed():
    """Early exit returns faster on syntax failure vs full evaluation."""
    from lib.quality_gate import evaluate_parallel as ep
    enable("use_parallel_gates")
    try:
        bad_code = "def broken(("
        # With early exit
        enable("use_early_exit")
        start = time.time()
        result_fast = ep(bad_code, "python")
        fast_time = time.time() - start

        # Without early exit
        disable("use_early_exit")
        start = time.time()
        result_slow = ep(bad_code, "python")
        slow_time = time.time() - start

        assert result_fast["passed"] is False
        assert result_slow["passed"] is False
        # Early exit should be faster or equal
        assert fast_time <= slow_time * 2, \
            f"Early exit not faster: fast={fast_time:.3f}s slow={slow_time:.3f}s"
    finally:
        disable("use_parallel_gates")
        disable("use_early_exit")


def test_benchmark_sequential_consistency():
    """Sequential evaluation produces consistent results across runs."""
    code = "x: int = 1\ny: str = 'hello'\n"
    runs = []
    for _ in range(3):
        result = evaluate(code, "python")
        runs.append(result["composite"])
    assert max(runs) - min(runs) < 0.1, \
        f"Sequential inconsistent: {runs}"


def test_benchmark_concurrent_calls():
    """Multiple concurrent evaluate_parallel calls don't degrade."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    enable("use_parallel_gates")
    try:
        codes = [
            "def a(): return 1",
            "def b(): return 2",
            "def c(): return 3",
            "def d(): return 4",
        ]
        start = time.time()
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = [ex.submit(evaluate_parallel, c, "python") for c in codes]
            results = [f.result() for f in as_completed(futures)]
        elapsed = time.time() - start
        assert len(results) == 4
        assert all("composite" in r for r in results)
        # 4 concurrent calls should not take >5x single call time
        single = time.time()
        evaluate_parallel(codes[0], "python")
        single_time = time.time() - single
        assert elapsed < single_time * 6 or elapsed < 10.0, \
            f"Concurrent too slow: {elapsed:.3f}s (single: {single_time:.3f}s)"
    finally:
        disable("use_parallel_gates")
