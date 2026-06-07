# FORGE: Formally Generated Reasoning Evaluation

<p align="center">
<strong>Testing Understanding Over Interpolation</strong>
</p>

<p align="center">
<a href="#the-hypothesis">Hypothesis</a> •
<a href="#the-nerfed-model-problem">The Nerfed Model Problem</a> •
<a href="#how-forge-works">How It Works</a> •
<a href="#quickstart">Quickstart</a> •
<a href="#leaderboard">Leaderboard</a>
</p>

---

## The Hypothesis

Large language models—when performing well—may be operating with something functionally equivalent to an internal model of reality: a compressed, weighted representation of mathematical structure, physical law, and logical relationship embedded in their weights.

**FORGE does not assert an answer. It produces evidence.**

> A model's score on FORGE is evidence—not proof—of how deeply it has internalized mathematical and physical structure, as distinct from how much relevant training data it has seen.

---

## The Nerfed Model Problem

AI labs face a quiet incentive problem.

A model is released. It scores well on public benchmarks. The benchmark scores become part of the marketing. Then, quietly, the model is updated — safety tuning, cost optimization, behavior changes. The scores on the original benchmark no longer reflect what users are actually running.

There is currently no clean way to detect this. Fixed benchmarks cannot distinguish between "the model got smarter" and "the model was tuned toward this specific benchmark distribution." The question of whether a deployed model today matches the model that produced its published scores is largely unanswerable with existing tools.

**FORGE changes this.**

Because every FORGE run is governed by a public seed and every question is generated deterministically at runtime, a score is not just a number — it is a **reproducible experimental result**. Any researcher, journalist, or user can rerun seed `42` six months from now against the same model endpoint and compare. If the score has shifted, the shift is real and documented.

This makes FORGE **the first benchmark with a built-in longitudinal audit trail**.

Labs that publish FORGE scores alongside a seed and timestamp are making a verifiable commitment. Labs that avoid doing so are making a different kind of statement. Users and researchers can draw their own conclusions.

**FORGE does not accuse anyone of nerfing. It simply makes the question answerable for the first time.**

---

## The Problem with Static Benchmarks

| Problem | How FORGE Solves It |
|---------|---------------------|
| **Data Contamination** | 100% procedural generation. Zero substring collision with training data. |
| **Benchmark Saturation** | Parametric difficulty scaling prevents ceiling effects. |
| **LLM-as-Judge Bias** | Deterministic grading via SymPy, NumPy, python-chess. Zero LLM judges. |
| **The Complexity Cliff** | FORGE Cliff Index precisely measures where models fail. |
| **The Nerfed Model Problem** | Seed-based reproducibility creates an audit trail. |

---

## How FORGE Works

### 25 Procedurally Generated Categories

Each category probes a distinct axis of theoretical internal world-models:

| Domain | Categories |
|--------|------------|
| **Algebra & Number Theory** | Polynomial Roots, Diophantine Equations, Modular Exponentiation, Group Orders |
| **Linear Algebra** | Matrix Determinants, Jordan Normal Form, Systems of Equations, Vector Calculus |
| **Calculus & Analysis** | Taylor Series, Differential Equations, Divergence |
| **Discrete Math** | Combinatorics, Boolean Logic, Formal Grammars, Algorithmic Traces |
| **Applied Math** | Information Theory, Signal Processing, Financial Math, Bayesian Updating |
| **Game Theory & Logic** | Chess Mate-in-N, Nim States, Graph Theory |
| **Physics** | RLC Circuits, Quantum State Amplitudes |
| **Cryptography** | RSA Key Generation |

### Scoring Methodology

**FORGE Score** (extrapolation-weighted):

```
C_c = Σ(α^d · S_{c,d}) / Σ(α^d)    where α = 1.5
```

- **Interpolation Score**: Performance on Easy/Medium (likely in training data)
- **Extrapolation Score**: Performance on Hard/Expert (novel problems)
- **Cliff Index**: First difficulty tier where accuracy drops >30%

### Seed-Based Reproducibility

```python
# Same seed → Identical problems
seed = 42
category = ArithmeticChainCategory(seed=42)
problem = category.generate(difficulty=3, iteration=0)
# Always produces the same question, every time, on any machine
```

---

## Quickstart

### Installation

```bash
git clone https://github.com/mohamedhossammohamed/FORGE.git
cd FORGE
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run a Single Model

```bash
# Quick evaluation (~15 minutes, 250 questions)
python -m forge.cli run \
    --mode quick \
    --model gpt-4o \
    --api-base https://api.openai.com/v1 \
    --api-key sk-xxx \
    --seed 42
```

### Compare Multiple Models

```bash
# Launch web UI for multi-model comparison
python -m forge.ui
# Opens at http://localhost:7860
```

### CLI Options

```bash
python -m forge.cli run --help

Options:
  --mode [quick|standard|full]   Run mode (default: standard)
  --model TEXT                   Model name [required]
  --api-base TEXT                API base URL [required]
  --api-key TEXT                 API key [required]
  --seed INTEGER                 Random seed for reproducibility
  --categories TEXT              Comma-separated categories or 'all'
  --concurrency INTEGER          Max concurrent requests (default: 10)
```

---

## Score Interpretation

| Metric | What It Means |
|--------|---------------|
| **FORGE Score** | Weighted accuracy emphasizing harder problems. Higher = stronger internal world-model. |
| **Interpolation Score** | Performance on Easy/Medium. Likely similar to training data. |
| **Extrapolation Score** | Performance on Hard/Expert. Novel problems not in training data. |
| **Cliff Index** | First tier where accuracy drops >30%. Lower = earlier capability collapse. |

**Key Insight**: A model with high Interpolation but low Extrapolation is likely memorizing. A model maintaining high scores across both has evidence of generalized reasoning.

---

## Leaderboard

### How to Submit

1. Run FORGE with `--mode full --seed 42`
2. Save the JSON output
3. Open a GitHub Issue with:
   - Model name and version
   - API endpoint used
   - Seed and timestamp
   - Full JSON results

### Auditability

Every published score is **fully reproducible**:
- Same seed → Same questions → Same evaluation
- Any researcher can verify any published score
- Score drift over time is detectable and documented

---

## The Audit Trail

```
┌─────────────────────────────────────────────────────────────┐
│                    FORGE Audit Protocol                      │
├─────────────────────────────────────────────────────────────┤
│  1. Lab publishes: Model X, Seed 42, FORGE Score: 0.847     │
│  2. Timestamp: 2025-01-15                                   │
│  3. Six months later, anyone can run:                       │
│     $ python -m forge.cli run --model X --seed 42           │
│  4. If score ≠ 0.847, the change is documented              │
└─────────────────────────────────────────────────────────────┘
```

This is not an accusation. It is a **measurement tool**.

---

## Adding a Category

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
        return {
            1: {"param": value},
            # ...
        }
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        # Generate problem...
        return Problem(question=..., answer=..., ...)
    
    def grade(self, prediction: str, answer) -> bool:
        # Deterministic grading...
        return prediction == answer
```

---

## Technical Architecture

```
forge/
├── core/
│   ├── state.py       # SHA-256 deterministic seed management
│   ├── generator.py   # Abstract base class for categories
│   ├── grader.py      # Zero-LLM grading (SymPy, NumPy, chess)
│   └── runner.py      # Async API execution with scoring
├── categories/        # 25 procedurally generated categories
├── cli.py             # Typer command-line interface
└── ui.py              # Gradio web interface with multi-model comparison
```

---

## Citation

```bibtex
@software{forge2025,
  title={FORGE: Formally Generated Reasoning Evaluation},
  author={Mohamed Hossam},
  year={2025},
  url={https://github.com/mohamedhossammohamed/FORGE}
}
```

---

## Author

Built by [Mohamed Hossam](https://github.com/mohamedhossammohamed) · [@MohamedHz72007](https://x.com/MohamedHz72007)

---

<p align="center">
<strong>FORGE does not accuse anyone of anything.<br>
It simply makes the question answerable for the first time.</strong>
</p>
