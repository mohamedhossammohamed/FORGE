"""Performance tests: generation speed, memory at scale, and thread safety."""

import os
import time
import statistics
import pytest
from concurrent.futures import ThreadPoolExecutor

from forge.categories import CATEGORIES
from conftest import REFERENCE_SEED


# Categories known to be slow due to expensive computation
SLOW_GENERATORS = {"algebra_groups", "chess_mate", "diff_eq_rlc", "finance_math"}
VERY_SLOW_GENERATORS = {"algebra_groups"}  # Skip entirely for speed benchmarks


class TestGenerationSpeed:
    """Verify problem generation is within acceptable time bounds."""

    @pytest.mark.parametrize("category_name", CATEGORIES.keys())
    def test_generation_speed(self, category_name):
        """Each category should generate problems within time bounds."""
        if category_name in VERY_SLOW_GENERATORS:
            pytest.skip(f"{category_name} has extremely slow generation")
        cls = CATEGORIES[category_name]
        instance = cls(seed=REFERENCE_SEED)
        times = []
        n_problems = 20 if category_name in SLOW_GENERATORS else 100
        difficulties = [1, 3] if category_name in SLOW_GENERATORS else range(1, 6)
        iterations = 10 if category_name in SLOW_GENERATORS else 20

        for difficulty in difficulties:
            for iteration in range(iterations):
                start = time.perf_counter()
                instance.generate(difficulty, iteration)
                elapsed = time.perf_counter() - start
                times.append(elapsed)

        mean_time = statistics.mean(times)
        p99_idx = int(len(times) * 0.99)
        p99_time = sorted(times)[min(p99_idx, len(times) - 1)]

        # Slow generators get a more generous bound
        mean_limit = 5.0 if category_name in SLOW_GENERATORS else 2.0
        p99_limit = 15.0 if category_name in SLOW_GENERATORS else 5.0

        assert mean_time < mean_limit, (
            f"{category_name}: mean generation time {mean_time:.3f}s exceeds {mean_limit}s"
        )
        assert p99_time < p99_limit, (
            f"{category_name}: p99 generation time {p99_time:.3f}s exceeds {p99_limit}s"
        )


class TestMemoryAtScale:
    """Verify memory usage stays bounded during large generation runs."""

    @pytest.mark.slow
    def test_memory_at_scale(self):
        """Generate 10K problems total; memory growth must stay under 500MB."""
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil not installed")

        process = psutil.Process(os.getpid())
        baseline_mb = process.memory_info().rss / (1024 * 1024)

        for name, cls in CATEGORIES.items():
            instance = cls(seed=REFERENCE_SEED)
            for difficulty in range(1, 6):
                for iteration in range(80):  # 25 * 5 * 80 = 10,000
                    instance.generate(difficulty, iteration)

        peak_mb = process.memory_info().rss / (1024 * 1024)
        growth_mb = peak_mb - baseline_mb
        assert growth_mb < 500, (
            f"Memory growth {growth_mb:.1f}MB exceeds 500MB limit"
        )

    @pytest.mark.slow
    def test_no_degradation_at_scale(self):
        """Last 1000 problems must not be >20% slower than first 1000."""
        first_1000_times = []
        last_1000_times = []
        all_times = []

        count = 0
        for name, cls in CATEGORIES.items():
            instance = cls(seed=REFERENCE_SEED)
            for difficulty in range(1, 6):
                for iteration in range(80):
                    start = time.perf_counter()
                    instance.generate(difficulty, iteration)
                    elapsed = time.perf_counter() - start
                    all_times.append(elapsed)
                    count += 1

        first_1000_times = all_times[:1000]
        last_1000_times = all_times[-1000:]

        first_mean = statistics.mean(first_1000_times)
        last_mean = statistics.mean(last_1000_times)

        if first_mean > 0:
            degradation = (last_mean - first_mean) / first_mean
            assert degradation < 0.20, (
                f"Performance degraded by {degradation:.1%}: "
                f"first 1000 mean={first_mean:.4f}s, last 1000 mean={last_mean:.4f}s"
            )


class TestConcurrentGeneration:
    """Verify thread safety of problem generation.

    Since create_rng() now defaults to seed_python_random=False, the global
    stdlib random state is no longer mutated.  All randomness flows through
    per-instance NumPy RNGs, which are thread-safe.  These tests verify that
    concurrent generation produces identical results to sequential generation.
    """

    # Categories excluded from the broad concurrency sweep due to slow generation
    _SLOW = {"algebra_groups", "chess_mate", "diff_eq_rlc", "finance_math"}

    def test_concurrent_matches_sequential(self):
        """Concurrent generation must produce byte-identical results to sequential."""
        fast_categories = [
            name for name in CATEGORIES.keys() if name not in self._SLOW
        ]

        # --- sequential baseline ---
        sequential = {}
        for cat in fast_categories:
            cls = CATEGORIES[cat]
            instance = cls(seed=REFERENCE_SEED)
            for d in range(1, 4):
                for i in range(3):
                    p = instance.generate(d, i)
                    sequential[(cat, d, i)] = (p.question, str(p.answer))

        # --- concurrent generation ---
        def generate_one(category_name, difficulty, iteration):
            cls = CATEGORIES[category_name]
            instance = cls(seed=REFERENCE_SEED)
            p = instance.generate(difficulty, iteration)
            return p.question, str(p.answer)

        concurrent_results = {}
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {}
            for cat in fast_categories:
                for d in range(1, 4):
                    for i in range(3):
                        key = (cat, d, i)
                        futures[key] = executor.submit(generate_one, cat, d, i)
            for key, future in futures.items():
                concurrent_results[key] = future.result()

        # --- compare ---
        failures = []
        for key in sequential:
            seq_q, seq_a = sequential[key]
            con_q, con_a = concurrent_results[key]
            if seq_q != con_q or seq_a != con_a:
                cat, d, i = key
                failures.append(f"{cat} d={d} i={i}")

        assert not failures, (
            f"Concurrent generation diverged from sequential in {len(failures)} cases: "
            f"{failures[:10]}"
        )

    def test_concurrent_determinism_across_threads(self):
        """Two threads generating the same problem must produce identical output."""
        fast_categories = [
            name for name in CATEGORIES.keys() if name not in self._SLOW
        ][:5]  # subset for speed

        def generate_one(category_name, difficulty, iteration):
            cls = CATEGORIES[category_name]
            instance = cls(seed=REFERENCE_SEED)
            p = instance.generate(difficulty, iteration)
            return p.question, str(p.answer)

        failures = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for cat in fast_categories:
                for d in range(1, 4):
                    for i in range(3):
                        f1 = executor.submit(generate_one, cat, d, i)
                        f2 = executor.submit(generate_one, cat, d, i)
                        futures.append((f1, f2, cat, d, i))

            for f1, f2, cat, d, i in futures:
                q1, a1 = f1.result()
                q2, a2 = f2.result()
                if q1 != q2 or a1 != a2:
                    failures.append(f"{cat} d={d} i={i}")

        assert not failures, (
            f"Same-seed concurrent generation diverged in {len(failures)} cases: "
            f"{failures[:10]}"
        )

    def test_no_global_random_mutation(self):
        """create_rng() should not mutate the global stdlib random state."""
        import random as _random

        from forge.core.state import create_rng

        # Sanity check: seed_python_random=True MUST mutate state
        state_before_true = _random.getstate()
        create_rng(REFERENCE_SEED, 1, 0, seed_python_random=True)
        state_after_true = _random.getstate()
        assert state_before_true != state_after_true, (
            "Sanity check failed: seed_python_random=True should mutate state"
        )
        # Restore state for the main test
        _random.setstate(state_before_true)

        # Main test: default path must NOT mutate state
        for d in range(1, 6):
            for i in range(10):
                create_rng(REFERENCE_SEED, d, i)

        state_after = _random.getstate()

        assert state_before_true == state_after, (
            "create_rng(seed_python_random=False) mutated the global random state"
        )
