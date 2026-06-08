"""Tests for seed reproducibility, collision detection, and version stability."""

import pytest
from forge.categories import CATEGORIES
from forge.core.state import derive_seed
from conftest import (
    REFERENCE_SEED,
    generate_problem,
    make_prediction_from_answer,
)


class TestSeedDerivation:
    """Tests for the core seed derivation function."""

    def test_seed_derivation_deterministic(self):
        """Same inputs must always produce the same seed."""
        for base_seed in [0, 42, 2**32 - 1]:
            for difficulty in range(1, 6):
                for iteration in range(100):
                    s1 = derive_seed(base_seed, difficulty, iteration)
                    s2 = derive_seed(base_seed, difficulty, iteration)
                    assert s1 == s2, (
                        f"Non-deterministic: derive_seed({base_seed}, {difficulty}, "
                        f"{iteration}) returned {s1} then {s2}"
                    )

    def test_seed_derivation_unique(self):
        """Different (difficulty, iteration) pairs should produce different seeds."""
        seeds = set()
        for d in range(1, 6):
            for i in range(100):
                seeds.add(derive_seed(42, d, i))
        assert len(seeds) == 500, (
            f"Expected 500 unique seeds, got {len(seeds)} (collisions detected)"
        )

    def test_seed_derivation_varies_with_base(self):
        """Different base seeds should produce different derived seeds."""
        seeds_a = {derive_seed(42, d, i) for d in range(1, 6) for i in range(10)}
        seeds_b = {derive_seed(99, d, i) for d in range(1, 6) for i in range(10)}
        assert seeds_a != seeds_b, "Different base seeds produced identical seed sets"


SLOW_CATEGORIES = {"algebra_groups", "chess_mate", "diff_eq_rlc", "finance_math"}


class TestGenerationReproducibility:
    """Verify that generating the same problem twice yields byte-identical output."""

    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4, 5])
    @pytest.mark.parametrize("iteration", list(range(5)))
    def test_generation_reproducibility(self, forge_category, difficulty, iteration):
        name, cls, _ = forge_category
        if name in SLOW_CATEGORIES:
            pytest.skip(f"{name} has slow generation")
        instance1 = cls(seed=REFERENCE_SEED)
        instance2 = cls(seed=REFERENCE_SEED)
        p1 = instance1.generate(difficulty, iteration)
        p2 = instance2.generate(difficulty, iteration)
        assert p1.question == p2.question, f"Question diverged for {name}"
        assert str(p1.answer) == str(p2.answer), f"Answer diverged for {name}"
        assert p1.seed == p2.seed

    @pytest.mark.slow
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4, 5])
    @pytest.mark.parametrize("iteration", list(range(5, 20)))
    def test_generation_reproducibility_extended(self, forge_category, difficulty, iteration):
        """Extended reproducibility test with 100 seeds per category."""
        name, cls, _ = forge_category
        instance1 = cls(seed=REFERENCE_SEED)
        instance2 = cls(seed=REFERENCE_SEED)
        p1 = instance1.generate(difficulty, iteration)
        p2 = instance2.generate(difficulty, iteration)
        assert p1.question == p2.question, f"Question diverged for {name}"
        assert str(p1.answer) == str(p2.answer), f"Answer diverged for {name}"
        assert p1.seed == p2.seed


class TestSeedCollisionDetection:
    """Verify that different seeds produce different problems."""

    @pytest.mark.slow
    @pytest.mark.parametrize("category_name", CATEGORIES.keys())
    def test_seed_collision_detection(self, category_name):
        cls = CATEGORIES[category_name]
        instance = cls(seed=REFERENCE_SEED)
        seen = set()
        total = 0
        collisions = 0
        for difficulty in range(1, 6):
            for iteration in range(2000):  # 5 * 2000 = 10,000
                p = instance.generate(difficulty, iteration)
                key = (str(p.question), str(p.answer))
                if key in seen:
                    collisions += 1
                seen.add(key)
                total += 1
        collision_rate = collisions / total
        assert collision_rate < 0.0001, (
            f"Collision rate {collision_rate:.6%} exceeds 0.01% for {category_name}"
        )


class TestVersionStability:
    """Verify generated problems match the committed snapshot."""

    def test_version_stability(self, all_category_instances, snapshot_data):
        for name, instance in all_category_instances.items():
            assert name in snapshot_data, f"Missing snapshot for {name}"
            p = instance.generate(3, 0)
            expected = snapshot_data[name]
            assert p.question == expected["question"], (
                f"Question changed for {name}"
            )
            assert str(p.answer) == str(expected["answer"]), (
                f"Answer changed for {name}: "
                f"got {p.answer!r}, expected {expected['answer']!r}"
            )
