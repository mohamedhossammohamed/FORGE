# FORGE — Research Log

Documented findings from FORGE evaluation runs. Each entry includes what was found,
reproduction details, honest interpretation, and implications for the hypothesis.

---

## Finding 1: Shannon Entropy — log2 Hallucination

**Date:** Observed during seed 42 evaluation
**Seed:** 42
**Model:** qwen/qwen3-coder-flash
**Category:** Shannon Entropy (info_entropy)

### What was found

The model produced confident multi-step entropy calculations using incorrect log2 values.
Example: log2(107) computed as 6.7175 versus correct 6.7415 (error −0.024). The model
used the identity log2(a/b) = log2(a) − log2(b) with systematically wrong log2 values
for integers 103, 107, 221, 309, 321, 332, 347.

The reasoning trace showed no uncertainty at the point of error. The model expressed
the wrong values with the same confidence as correct intermediate steps.

FORGE's deterministic grader flagged all 10 entropy questions as incorrect.

### Raw response (first failure, truncated)

```
log2(50/321) = log2(50) - log2(321) = 5.6439 - 8.3219 = -2.6780
```

Actual: −2.6826

### Honest interpretation

This is consistent with the model having memorized approximate log2 values for some
integers rather than computing them. It does not prove the model cannot reason —
it shows that for this specific operation, the model's internal representations are
not precise enough to produce correct multi-step results.

This finding supports the hypothesis that some model "reasoning" may be closer to
retrieval of approximate values. However, a single model on a single seed is not
sufficient evidence to draw firm conclusions.

### Implications

- FORGE's deterministic grading correctly identified the failure
- The model's confidence in wrong answers is itself informative
- This category may be useful for distinguishing models that compute versus retrieve

---

## Finding 2: Shannon Entropy — Cross-Model Non-Monotonic Failure

**Date:** Observed during cross-model evaluation
**Seed:** 17017656696087371159
**Mode:** nano (5 questions, Shannon Entropy difficulty 3)
**Models tested:** 8 frontier models

### What was found

Five models passed: DeepSeek V4 Pro, GPT-5.5, Claude Opus 4.7, Nemotron 550B, MiniMax M3.

Three models failed on the same entropy question (expected answer: 2.7037):

| Model | Extracted | Error | Failure type |
|-------|-----------|-------|--------------|
| Claude Opus 4.8 | 2.7038 | +0.0001 | Borderline tolerance |
| Claude Opus 4.6 | 2.7036 | −0.0001 | Borderline tolerance |
| Claude Sonnet 4.6 | 2.7056 | +0.0019 | Incorrect logarithm |

Notably, Opus 4.7 passes while 4.6 and 4.8 fail — a **non-monotonic pattern** across
versions. Newer is not always better.

Sonnet 4.6 is the only model with a demonstrably wrong logarithm: ln(0.072650) computed
as −2.6439 versus correct −2.6226. The other two failures are borderline tolerance cases
where the extracted value is within rounding error of the correct answer.

### Honest interpretation

The non-monotonic pattern (4.7 passes, 4.6 and 4.8 fail) suggests that version-to-version
performance on specific problems is not guaranteed to improve monotonically. This is
consistent with the hypothesis that models may change their internal approaches between
versions, sometimes losing precision on specific operations.

The borderline tolerance failures (4.6 and 4.8) suggest that the 1e-4 tolerance threshold
may be too tight for this category, or that floating-point extraction from model output
introduces small rounding differences that are not meaningful.

### Implications

- The FORGE hypothesis about monotonic degradation across difficulty tiers may not hold
  at the version level — models can improve on hard problems while regressing on specific
  easy ones
- Tolerance thresholds for Shannon Entropy may need review
- The non-monotonic finding is itself valuable evidence about model behavior

---

## Finding 3: Polynomial Roots — Contamination Vulnerability

**Date:** Identified during audit
**Category:** Polynomial Roots (polynomial_roots)

### What was found

The polynomial roots category has a problem space of approximately 62.8 million unique
questions. With a collision threshold of 7,930 (the number of problems generated in a
full run), exhaustive pre-computation is feasible on consumer hardware.

A motivated party could:
1. Generate all 62.8M possible questions for a given seed
2. Store them in a lookup table
3. Achieve perfect scores without any reasoning

This breaks the core anti-contamination claim for this category.

### Honest interpretation

This is a fundamental limitation of the category's parameter space, not a bug in the
generation code. The category was designed with polynomial coefficients that can take
a limited range of integer values, resulting in a finite and enumerable problem space.

### What needs to happen

Parameter expansion is required before this category can be certified. Options include:
- Increasing coefficient ranges
- Adding higher-degree polynomials
- Introducing irrational coefficients
- Removing the category if expansion is insufficient

### Status: [FLAGGED] — scores excluded from main FORGE score

---

## Finding 4: RSA Arithmetic — Feasibility Concern

**Date:** Identified during audit
**Category:** Cryptographic Arithmetic (crypto_rsa)

### What was found

The RSA arithmetic category involves large prime operations (modular exponentiation with
large moduli) that language models are not designed to perform mentally. Models must
perform multi-digit multiplication and modular reduction across many steps.

### Honest interpretation

This category may be testing the model's ability to generate correct computational tokens
rather than its reasoning ability. A model that scores well on RSA may simply be better
at token-level arithmetic, not at understanding cryptographic principles.

This is inconsistent with the FORGE hypothesis, which is about whether models have
internalized mathematical structure, not whether they can perform large-number arithmetic.

### What needs to happen

The category needs redesign to test reasoning about RSA (e.g., "given these parameters,
what is the security implications?") rather than computation of RSA operations. Alternatively,
it may need to be removed.

### Status: [FLAGGED] — under review for redesign or removal

---

## Finding 5: Boolean Minimization — Grader Bug

**Date:** Identified during testing
**Category:** Boolean Logic Minimization (boolean_kmap)

### What was found

At difficulty 4-5, SymPy's `simplify_logic` function raises a TypeError on certain complex
Boolean expressions. This causes the grader to fail on problems that the model may have
answered correctly.

### Honest interpretation

This is a grader bug, not a model limitation. The grading logic cannot handle certain
expressions that SymPy's simplification engine does not support.

### What needs to happen

The grader needs a fallback path for expressions that `simplify_logic` cannot handle.
Options include truth-table comparison or manual canonical form conversion.

### Status: [RESEARCH] — fix in progress

---

## Finding 6: Chess Mate-in-N — Generation Constraints

**Date:** Identified during testing
**Category:** Chess Mate-in-N (chess_mate)

### What was found

The minimax search for mate-in-4 and mate-in-5 positions is slow because it searches
without alpha-beta pruning. At high difficulty levels, the generation pool is constrained
because few endgame positions produce forced mates at exactly the requested depth.

### Honest interpretation

This limits the true procedural uniqueness of problems at high difficulty. If the pool
of valid positions is small, different seeds may produce similar or identical puzzles.

### What needs to happen

Alpha-beta pruning should be added to speed up search. A tablebase lookup could provide
known-correct positions for high-difficulty puzzles.

### Status: [RESEARCH] — rewrite in progress

---

## Reproduction Notes

To reproduce any finding:
1. Set the seed to the value specified above
2. Run the specified mode against the specified model
3. Compare results to the documented output

All findings are deterministic given the same seed, model, and API endpoint.
Differences in model versions or API implementations may produce different results.
