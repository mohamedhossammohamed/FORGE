# FORGE Test Suite

Comprehensive computational validation suite for the FORGE benchmark. No API calls, no model dependencies — all tests validate generation, grading, and infrastructure logic.

## Quick Start

```bash
# Install dev dependencies
pip install -e ".[dev]"
pip install psutil pytest-timeout

# Run all fast tests
pytest tests/ -v

# Run specific test file
pytest tests/test_grader.py -v

# Skip slow tests (collision detection, memory tests)
pytest tests/ -v -m "not slow"

# Run only slow tests
pytest tests/ -v -m "slow"
```

## Test Files

| File | What it covers |
|------|----------------|
| `conftest.py` | Shared fixtures (`forge_category`, `all_category_instances`), helper functions (`generate_problem`, `assert_grade_correct`, `make_wrong_answer`) |
| `test_reproducibility.py` | Seed determinism, byte-identical generation, collision detection (<0.01%), version stability against committed snapshot |
| `test_grader.py` | Self-consistency (answer → grade → True), wrong answer rejection (wrong → grade → False), tolerance boundaries |
| `test_generation.py` | Problem structure validation (required keys, types), difficulty scaling monotonicity |
| `test_edge_cases.py` | Boundary inputs per category (zero values, singular matrices, global phase invariance, etc.) |
| `test_performance.py` | Generation speed (<2s mean, <5s p99), memory at scale (<500MB for 10K problems), thread safety |

## The Snapshot File

`fixtures/snapshot_seed42.json` is the canonical reference for version stability testing. It records the exact `question` and `answer` for every category at `(seed=42, difficulty=3, iteration=0)`.

**Do not modify this file manually.** If generation logic changes intentionally, regenerate it:

```bash
python tests/generate_snapshot.py
```

Then commit the updated file. Any unintentional change to generation logic will cause `test_version_stability` to fail.

## Adding a Test for a New Category

When adding a new category to `forge/categories/`, update these files:

1. **`test_generation.py`**: Add an entry to `COMPLEXITY_METRIC_KEYS` with the difficulty param key that scales.

2. **`test_edge_cases.py`**: Add a `TestYourCategoryEdgeCases` class with boundary tests:
   ```python
   class TestYourCategoryEdgeCases:
       def test_correct_answer_accepted(self):
           assert_grade_correct("your_category", "expected_prediction", canonical_answer)

       def test_wrong_answer_rejected(self):
           assert_grade_wrong("your_category", "wrong_prediction", canonical_answer)

       def test_edge_case_boundary(self):
           # Test specific boundary conditions
           ...
   ```

3. **`conftest.py`**: If your category has a special answer format, update `make_prediction_from_answer()` and `make_wrong_answer()`.

4. **Regenerate snapshot**: `python tests/generate_snapshot.py`

## Expected Runtime

- Fast tests (`-m "not slow"`): ~2-4 minutes
- Slow tests (`-m "slow"`): ~5-10 minutes
- Full suite: ~10-15 minutes

All tests are purely computational — no network access or API keys required.

## Markers

- `@pytest.mark.slow` — Tests that take >30 seconds (collision detection, memory tests). Deselect with `-m "not slow"`.

## Important: `seed_python_random` Defaults to `False`

As of the current version, `create_rng()` no longer seeds Python's stdlib `random` module by default. This was changed for thread safety — `random.seed()` mutates global state and breaks concurrent generation.

**If your category uses `random.choice()`, `random.randint()`, or any other stdlib `random` function**, you must explicitly pass `seed_python_random=True` to `self.get_rng()`:

```python
# In your category's generate() method:
rng = self.get_rng(difficulty, iteration, seed_python_random=True)
```

Categories that only use `rng.integers()`, `rng.random()`, `rng.choice()` (NumPy RNG methods) are unaffected. Check your implementation before submitting a new category.
