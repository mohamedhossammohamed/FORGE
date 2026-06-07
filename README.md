# FORGE: Formally Generated Reasoning Evaluation

**An open question about LLM evaluation, built as a tool.**

---

## The Hypothesis

This project starts from a contested scientific question: when a large language model solves a problem correctly, is it doing something that resembles reasoning over internalized structure, or is it pattern-matching against statistical regularities in its training data?

We do not know the answer. Neither does anyone else, with confidence.

**FORGE is an instrument designed to produce evidence that bears on this question — not to answer it.**

### What we hypothesize

We hypothesize that a model's performance profile across difficulty tiers — specifically the relationship between its interpolation score (easy/medium problems) and its extrapolation score (hard/expert problems) — is informative about whether it has internalized mathematical structure or is primarily retrieving from training distribution.

A model that scores well on easy problems and collapses on hard ones is consistent with sophisticated retrieval. A model that degrades gradually across tiers is consistent with something more like generalization. We do not claim this distinction is clean, or that FORGE scores prove either interpretation.

### Falsifiability

The hypothesis would be evidence against if models scoring highly on maximum difficulty tiers suffer catastrophic performance degradation when the mathematical structure of a problem is held constant but its surface framing is inverted. That would suggest reliance on surface pattern matching rather than internalized structure. We have not run this experiment systematically. It is a direction for future work.

---

## The Problem with Static Benchmarks

Existing benchmarks have well-documented structural problems:

- **Data contamination**: Static question banks are likely present in pre-training corpora, making it difficult to distinguish memorization from reasoning
- **Ceiling effects**: Multiple-choice formats are gameable; models exploit linguistic heuristics
- **LLM-as-judge evaluation**: Open-ended grading introduces its own hallucination and consistency problems
- **The complexity cliff**: Several papers have documented that model accuracy does not degrade gracefully at the boundary of training distribution — it collapses

FORGE addresses these by generating every problem procedurally at runtime from a seed. Verbatim contamination of generated questions is statistically near-impossible. Structural similarity to training data — problems that resemble the *type* of problem seen during training — cannot be ruled out and is a genuine limitation.

---

## The Nerfed Model Problem

AI labs face a quiet incentive problem. A model is released. It scores well on public benchmarks. The scores become part of the marketing. Then, quietly, the model is updated — safety tuning, cost optimization, behavior changes. The published scores no longer reflect what users are actually running.

Fixed benchmarks cannot distinguish between "the model got smarter" and "the model was tuned toward this specific benchmark distribution."

Because every FORGE run is governed by a published seed and every question is generated deterministically at runtime, a score is reproducible. Any researcher can rerun seed `42` six months from now against the same model endpoint and compare. If the score has shifted, the shift is documented.

Whether score changes over model versions reflect capability changes or distribution-specific tuning is something FORGE data may help investigate — though drawing firm conclusions would require controlled conditions we do not currently enforce.

**FORGE does not accuse anyone of nerfing. It makes the question more tractable.**

---

## How FORGE Works

### 25 Procedurally Generated Categories

Each category tests a distinct axis of theoretical internal world-models:

| # | Category | Difficulty Range | Human Time (Frontier) |
|---|----------|------------------|----------------------|
| 1 | Arithmetic Chain Composition | Kindergarten → Frontier | 15 mins |
| 2 | Polynomial Root Finding | High School → Frontier | 20 mins |
| 3 | Matrix Determinants | Undergraduate → Frontier | 45 mins |
| 4 | Jordan Normal Form | Undergraduate → Frontier | 60 mins |
| 5 | RLC Circuit Differential Equations | High School → Frontier | 30 mins |
| 6 | Boolean Logic Minimization | Undergraduate → Frontier | 10 mins |
| 7 | Chess Mate-in-N (Endgame) | Elementary → Frontier | 25 mins |
| 8 | Graph Theory: Shortest Path | High School → Frontier | 15 mins |
| 9 | Cryptographic Arithmetic (RSA) | Undergraduate → Frontier | 40 mins |
| 10 | Combinatorics: Stars and Bars | High School → Frontier | 10 mins |
| 11 | Information Theory: Entropy | Undergraduate → Frontier | 5 mins |
| 12 | Signal Processing: DFT | Undergraduate → Frontier | 20 mins |
| 13 | Game Theory: Nim States | Elementary → Frontier | 5 mins |
| 14 | Abstract Algebra: Group Orders | Undergraduate → Frontier | 15 mins |
| 15 | Systems of Linear Equations | High School → Frontier | 25 mins |
| 16 | Modular Exponentiation | Middle School → Frontier | 10 mins |
| 17 | Vector Calculus: Divergence | Undergraduate → Frontier | 15 mins |
| 18 | Geometry: Polygon Properties | Middle School → Frontier | 15 mins |
| 19 | Financial Mathematics | High School → Frontier | 10 mins |
| 20 | Probability: Bayesian Updating | Undergraduate → Frontier | 15 mins |
| 21 | Taylor Series Coefficients | Undergraduate → Frontier | 25 mins |
| 22 | Diophantine Equations | High School → Frontier | 15 mins |
| 23 | Formal Grammars | Undergraduate → Frontier | 20 mins |
| 24 | Quantum State Amplitudes | Undergraduate → Frontier | 30 mins |
| 25 | Algorithmic Trace Execution | Middle School → Frontier | 20 mins |

### Deterministic Generation

All problems are generated from a master seed using SHA-256 derived RNGs:
- Same seed → identical problems across runs, on any machine
- Different seeds → statistically distinct problems
- Verbatim generated questions have near-zero probability of existing in training corpora; structural similarity to training data is a separate concern and cannot be excluded

### Seed Security

FORGE uses a 256-bit hash space (SHA-256). The space of possible problem sets is large enough that exhaustive pre-computation is not feasible:

| Metric | Value |
|--------|-------|
| Possible problem sets | 2^256 ≈ 1.2 × 10^77 |
| Time to exhaust (1 trillion/sec) | ~3.7 × 10^51 years |
| Atom count in universe | ~10^80 |

**Best practices:**
- **For public benchmarks**: Use a random seed and publish it with your results
- **For contamination testing**: Use a seed that is not disclosed in advance
- **For reproducibility**: Document the seed alongside your score

If a lab knows your seed, they can pre-compute all problems. Keep seeds private for genuine evaluations.

### Computational Grading

All evaluation uses deterministic computational verification rather than LLM judges:
- **SymPy**: Symbolic equivalence for expressions, equations, and calculus
- **NumPy**: Matrix operations and numerical precision
- **python-chess**: Game state validation and legal move verification

This grading approach is computationally deterministic — the same input always produces the same grade, and the grading logic is inspectable. It is not perfect. SymPy has known edge cases with certain symbolic forms. Numeric tolerances are judgment calls. These limitations are documented in the Limitations section below.

### Scoring

**Per-category score** (extrapolation-weighted):

```
C_c = Σ(α^d · S_{c,d}) / Σ(α^d)
```

Where:
- `S_{c,d}` = accuracy for category `c` at difficulty `d`
- `α = 1.5` (extrapolation weight parameter)
- Higher difficulties contribute exponentially more to the score

**FORGE Score**: Mean of all per-category scores `C_c`.

**Complexity Cliff Index**: The first difficulty tier where accuracy drops more than 30% from the previous tier. This is an observation about where performance degrades — it is not a proof of anything about world models. It is a useful diagnostic number.

---

## Limitations

These are real limitations, not caveats. Read them before drawing conclusions from FORGE scores.

**Statistical power by mode:**

| Mode | Questions | 95% CI margin | Interpretation |
|------|-----------|---------------|----------------|
| `nano` | 5 | ±44% | Smoke test only. Not meaningful for comparison. |
| `quick` | 250 | ±6.2% | Useful for rough ordering. Not sufficient for fine distinctions. |
| `standard` | 2,500 | ±2.0% | Adequate for most research comparisons. |
| `full` | 10,000 | ±1.0% | High confidence. Expensive. |

Quick mode results on cheap models are not meaningful tests of the hypothesis. The statistical power is too low and the models are unlikely to be operating in the regime the hypothesis is about.

**Grading edge cases:**

- *SymPy*: Symbolic simplification can fail on certain trigonometric identities, piecewise functions, and expressions involving special functions. When SymPy cannot simplify a difference to zero, it returns False even if the expressions are mathematically equivalent. This produces false negatives.
- *Numeric tolerance*: The 1e-4 relative tolerance used in most numeric categories is a judgment call. Problems with very large or very small answers may grade incorrectly at this threshold.
- *Quantum amplitudes*: The answer parser handles ket notation, JSON arrays, and comma-separated complex values. Unusual formatting from models may not parse correctly, producing false negatives.
- *Chess*: Puzzle generation uses a minimax search over randomly placed endgame positions. The search is bounded (400 attempts per problem). In rare cases the fallback position is used. The grader accepts any move that forces mate in N, not just the canonical first move.
- *Formal grammars and algorithmic trace*: These categories involve string matching and execution trace comparison. Edge cases in whitespace handling and output formatting may affect grading.

**What FORGE does not control for:**

- Structural similarity between generated problems and training data. Procedural generation prevents verbatim contamination; it does not prevent a model from having seen many similar problems during training.
- Prompt sensitivity. The system prompt instructs models to output answers in a specific format. Models that do not follow this format will score lower regardless of whether they computed the correct answer.
- Reasoning token costs. Models that use extended thinking consume significantly more tokens per problem. Cost estimates in the UI are approximate.

---

## Observed Behaviors

**Shannon Entropy — log2 hallucination**

During evaluation on seed 42, qwen/qwen3-coder-flash produced confident multi-step entropy calculations using incorrect log2 values. Example: log2(107) computed as 6.7175 versus correct 6.7415 (error −0.024). The model used log2(a/b) = log2(a) − log2(b) with systematically wrong log2 values for integers 103, 107, 221, 309, 321, 332, 347. The reasoning trace showed no uncertainty at the point of error. FORGE's deterministic grader flagged all 10 entropy questions as incorrect. Raw response (first failure, truncated): "log2(50/321) = log2(50) - log2(321) = 5.6439 - 8.3219 = -2.6780" (actual: -2.6826).

---

## Known Issues

These are active limitations in the current implementation.

**Chess (category 7):** The minimax search for mate-in-4 and mate-in-5 positions can be slow because it searches without alpha-beta pruning. This is a performance issue, not a correctness issue. A future version should add pruning or use a tablebase.

**Quantum amplitudes (category 24):** The answer parser handles common output formats but will fail on unusual representations. This category has higher false-negative rates than others.

**Jordan Normal Form (category 4):** At difficulty 5, the generated matrices occasionally have degenerate eigenvalue structures that make the problem ambiguous. The grader handles the most common cases but may miss valid alternative forms.

**Statistical independence:** Problems within a category at the same difficulty level are generated from independent seeds, but the underlying mathematical structure follows the same parametric distribution. This is not full statistical independence and may affect confidence interval calculations.

---

## Installation

```bash
git clone https://github.com/mohamedhossammohamed/FORGE.git
cd FORGE

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

## Quick Start

### CLI

```bash
# Smoke test — 5 questions, ~30 seconds
python -m forge.cli run \
    --mode nano \
    --model gpt-4o \
    --api-base https://api.openai.com/v1 \
    --api-key sk-your-key-here

# Quick evaluation — 250 questions, ~5 minutes
python -m forge.cli run \
    --mode quick \
    --model gpt-4o \
    --api-base https://api.openai.com/v1 \
    --api-key sk-your-key-here \
    --seed 42

# Standard evaluation — 2,500 questions, ~1 hour
python -m forge.cli run \
    --mode standard \
    --model claude-3-5-sonnet \
    --api-base https://api.anthropic.com/v1 \
    --api-key your-key-here \
    --seed 42

# Run specific categories only
python -m forge.cli run \
    --mode quick \
    --categories arithmetic_chain,matrix_det,game_nim \
    --model gpt-4o \
    --api-base https://api.openai.com/v1 \
    --api-key sk-your-key-here

# List all categories
python -m forge.cli list-categories
```

### Web UI (Researcher Tool)

```bash
python -m forge.server
# Opens at http://localhost:7860/researcher.html
```

The researcher tool provides real-time progress, per-category breakdown, cliff index visualization, multi-model comparison, and snapshot export.

---

## Score Interpretation

| Metric | What it measures | What it does not prove |
|--------|-----------------|----------------------|
| **FORGE Score** | Weighted accuracy, emphasizing harder problems | That the model has an internal world-model |
| **Interpolation Score** | Accuracy on easy/medium tiers | That these problems were in training data |
| **Extrapolation Score** | Accuracy on hard/expert tiers | That these problems were absent from training data |
| **Cliff Index** | First tier where accuracy drops >30% | The cause of the drop |

A model with high interpolation and low extrapolation scores is consistent with retrieval-dominant behavior. A model that maintains accuracy across tiers is consistent with generalization. Neither interpretation is proven by the score alone.

---

## Run Modes

| Mode | Questions | Statistical Power | Est. Cost | Runtime |
|------|-----------|-------------------|-----------|---------|
| `nano` | 5 | Smoke test only | <$0.01 | ~30s |
| `quick` | 250 | Low (±6.2% ME) | ~$0.10 | ~5 mins |
| `standard` | 2,500 | Moderate (±2.0% ME) | ~$1.00 | ~1 hour |
| `full` | 10,000 | High (±1.0% ME) | ~$4.00 | ~4 hours |

---

## Adding a Category

FORGE is designed for extensibility. To add a new category:

1. Create `forge/categories/your_category.py`
2. Subclass `ForgeCategory`
3. Implement the required interface:

```python
from forge.core.generator import ForgeCategory, Problem

class YourCategory(ForgeCategory):

    @property
    def name(self) -> str:
        return "your_category"

    @property
    def display_name(self) -> str:
        return "Your Category Name"

    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"param1": value},
            2: {...},
            # ...
        }
        return params.get(difficulty, params[3])

    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        # Generate problem using rng — do not use any other randomness source
        return Problem(
            question="...",
            answer=...,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={...},
        )

    def grade(self, prediction: str, answer) -> bool:
        # Use SymPy, NumPy, or exact comparison — not string heuristics
        return prediction == answer
```

4. Register in `forge/categories/__init__.py`

### Design principles for categories

- **Procedural generation**: Every question must be generated from the RNG, not selected from a bank
- **Computational grading**: Use SymPy, NumPy, or domain-specific engines — not LLM judges or string heuristics
- **Parametric difficulty**: Difficulty must be controlled by explicit mathematical parameters, not problem selection
- **Document edge cases**: If your grader has known failure modes, document them in the category file

---

## Technical Architecture

```
forge-benchmark/
├── README.md
├── requirements.txt
├── forge/
│   ├── __init__.py
│   ├── core/
│   │   ├── generator.py       # Base class and shared generation interfaces
│   │   ├── grader.py          # Computational grading utilities
│   │   ├── runner.py          # Model API execution, timeout handling, scoring
│   │   └── state.py           # Seed management and deterministic hashing
│   ├── categories/
│   │   ├── __init__.py        # Category registry
│   │   └── [25 category files]
│   ├── cli.py                 # Typer command-line interface
│   ├── server.py              # FastAPI backend with SSE streaming
│   └── ui.py                  # Gradio interface (alternative to server)
└── configs/
    ├── mode_full.json
    ├── mode_standard.json
    └── mode_quick.json
```

---

## Contributing

Contributions that improve grading precision, add well-designed categories, or fix documented edge cases are welcome.

1. Fork the repository
2. Create a feature branch
3. Implement your change with tests for edge cases
4. Submit a pull request with a clear description of what the change fixes or adds

### Priority areas

- Alpha-beta pruning for chess puzzle generation (currently unbounded minimax)
- Additional mathematical domains (topology, number theory, classical mechanics)
- Improved quantum amplitude parsing for unusual model output formats
- Formal verification problems (SAT solving, model checking)

---

## Citation

```bibtex
@software{forge2025,
  title={FORGE: Formally Generated Reasoning Evaluation},
  author={Hossam, Mohamed},
  year={2025},
  url={https://github.com/mohamedhossammohamed/FORGE}
}
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built on SymPy, NumPy, python-chess, and the scientific Python ecosystem. Motivated by Apple ML Research's "Illusion of Thinking" paper and ongoing concerns about benchmark contamination in the field.

---

## Author

Built by [Mohamed Hossam](https://github.com/mohamedhossammohamed), first-year medical student, as an open question about LLM evaluation. Contributions welcome.

[@MohamedHz72007](https://x.com/MohamedHz72007)

---

*FORGE is an instrument for producing evidence, not asserting conclusions. The question it asks — whether models generalize or interpolate — does not yet have a clean answer. That is why the question is worth asking carefully.*
