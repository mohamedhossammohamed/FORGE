# FORGE: Formally Generated Reasoning Evaluation

**Testing Understanding Over Interpolation**

---

## The Hypothesis

Large language models—when performing well—may be operating with something functionally equivalent to an internal model of reality: a compressed, weighted representation of mathematical structure, physical law, and logical relationship embedded in their weights. This remains a highly contested scientific claim.

**FORGE does not assert an answer, but rather serves as an operational instrument meticulously designed to produce clean, contamination-free evidence that bears directly on this question.**

### Core Claim

> A model's score on FORGE is evidence—not proof—of how deeply it has internalized mathematical and physical structure, as distinct from how much relevant training data it has seen.

### Falsifiability Statement

The hypothesis would be robustly disproven if models scoring highly on maximum difficulty tiers suffer catastrophic performance degradation when mathematical isomorphic structure remains identical but semantic framing is inverted—proving reliance on surface-level pattern matching rather than internalized circuits.

---

## The Problem with Static Benchmarks

Existing benchmarks suffer from structural failures:

- **Data Contamination**: Static question banks are inevitably ingested during pre-training, inflating scores through memorization rather than reasoning
- **Ceiling Effects**: Models game multiple-choice formats and exploit linguistic heuristics
- **LLM-as-Judge Bias**: Open-ended evaluations introduce hallucination and subjective bias
- **The Complexity Cliff**: Models exhibit catastrophic accuracy collapse—not graceful degradation—when pushed slightly beyond training distribution (Apple's "Illusion of Thinking")

**FORGE resolves this by mathematically ensuring zero substring collision with any existing pre-training dataset. Every generated problem is mathematically unique.**

---

## The Nerfed Model Problem

AI labs face a quiet incentive problem.

A model is released. It scores well on public benchmarks. The benchmark scores become part of the marketing. Then, quietly, the model is updated — safety tuning, cost optimization, behavior changes. The scores on the original benchmark no longer reflect what users are actually running.

There is currently no clean way to detect this. Fixed benchmarks cannot distinguish between "the model got smarter" and "the model was tuned toward this specific benchmark distribution." The question of whether a deployed model today matches the model that produced its published scores is largely unanswerable with existing tools.

FORGE changes this.

Because every FORGE run is governed by a public seed and every question is generated deterministically at runtime, a score is not just a number — it is a reproducible experimental result. Any researcher, journalist, or user can rerun seed `42` six months from now against the same model endpoint and compare. If the score has shifted, the shift is real and documented.

This makes FORGE the first benchmark with a built-in longitudinal audit trail.

Labs that publish FORGE scores alongside a seed and timestamp are making a verifiable commitment. Labs that avoid doing so are making a different kind of statement. Users and researchers can draw their own conclusions.

**FORGE does not accuse anyone of nerfing. It simply makes the question answerable for the first time.**

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
- Same seed → Identical problems across runs
- Different seeds → Mathematically unique problems
- Verbatim generated questions have near-zero probability of existing in training corpora

### Seed Security

FORGE uses a **256-bit hash space** (SHA-256), making pre-computation physically impossible:

| Metric | Value |
|--------|-------|
| Possible problem sets | 2^256 ≈ 1.2 × 10^77 |
| Time to exhaust (1 trillion/sec) | ~3.7 × 10^51 years |
| Atom count in universe | ~10^80 |

**Best practices:**
- **For public benchmarks**: Use a random seed and publish it with your results
- **For contamination testing**: Use a secret seed that AI labs cannot know in advance
- **For reproducibility**: Document the seed alongside your score

If an AI lab knows your seed, they can pre-compute all problems. Keep seeds secret for genuine evaluations.

### Zero-LLM Grading

All evaluation is performed through exact computational verification:
- **SymPy**: Symbolic equivalence for expressions, equations, and calculus
- **NumPy**: Matrix operations and numerical precision
- **python-chess**: Game state validation and legal move verification
- **No LLM judges**: Eliminates subjective bias and hallucination

### Scoring Methodology

**FORGE Aggregate Score** (weighted geometric mean with extrapolation bias):

```
C_c = Σ(α^d · S_{c,d}) / Σ(α^d)
```

Where:
- `S_{c,d}` = accuracy for category `c` at difficulty `d`
- `α = 1.5` (extrapolation weight parameter)
- Higher difficulties contribute exponentially more to the score

**Complexity Cliff Index**: The exact difficulty tier where accuracy drops >30% from the previous tier, quantifying the "Illusion of Thinking" phenomenon.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/forge-benchmark.git
cd forge-benchmark

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Quick Start

### CLI Usage

```bash
# Run quick evaluation (250 questions, ~15 mins)
python -m forge.cli run \
    --mode quick \
    --model gpt-4o \
    --api-base https://api.openai.com/v1 \
    --api-key sk-your-key-here

# Run standard evaluation (2500 questions, ~3-4 hours)
python -m forge.cli run \
    --mode standard \
    --model claude-3-5-sonnet \
    --api-base https://api.anthropic.com/v1 \
    --api-key your-key-here

# Run specific categories
python -m forge.cli run \
    --mode quick \
    --categories arithmetic_chain,matrix_det,game_nim \
    --model gpt-4o \
    --api-base https://api.openai.com/v1 \
    --api-key sk-your-key-here

# List all categories
python -m forge.cli list-categories

# View hypothesis and scoring info
python -m forge.cli info
```

### Gradio UI

```bash
# Launch web interface
python -m forge.ui
```

Opens a local web interface with:
- Model configuration inputs
- Run mode selector
- Seed with randomize button
- Real-time progress tracking
- Results dashboard with FORGE Score, Interpolation/Extrapolation scores, and Cliff Index

---

## Score Interpretation

| Metric | Meaning |
|--------|---------|
| **FORGE Score** | Weighted accuracy emphasizing harder problems. High score = strong internal world-model |
| **Interpolation Score** | Performance on Easy/Medium tiers. Likely similar to training data distributions |
| **Extrapolation Score** | Performance on Hard/Expert tiers. Tasks statistically impossible in training data |
| **Cliff Index** | First difficulty tier where accuracy drops >30%. Low cliff = early capability collapse |

**Key Insight**: A model with high Interpolation but low Extrapolation scores is likely memorizing. A model maintaining high scores across both is evidence of generalized reasoning circuits.

---

## Run Modes

| Mode | Questions | Statistical Power | Est. Cost | Runtime |
|------|-----------|-------------------|-----------|---------|
| `--mode quick` | 250 | Low | <$1.00 | ~15 mins |
| `--mode standard` | 2,500 | Moderate (95% CI, ±9.8% ME) | ~$10.00 | 3-4 hours |
| `--mode full` | 10,000 | High (95% CI, ±5% ME) | ~$40.00 | 12-16 hours |

---

## Adding a Category

FORGE is designed for extensibility. To add a new category:

1. Create `forge/categories/your_category.py`
2. Subclass `ForgeCategory`
3. Implement required methods:

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
        # Return parameters for each difficulty level (1-5)
        params = {
            1: {"param1": value, ...},
            2: {...},
            # ...
        }
        return params.get(difficulty, params[3])
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        # Generate problem using rng
        # ...
        
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
        # Grade using exact computational verification
        # Use ForgeGrader methods or custom logic
        return prediction == answer
```

4. Register in `forge/categories/__init__.py`

### Design Principles for Categories

- **Procedural Generation**: Every question must be generated from a seed, not selected from a bank
- **Deterministic Grading**: Use SymPy, NumPy, or game engines—never LLM judges
- **Parametric Scaling**: Difficulty must be controlled by mathematical parameters
- **Edge Case Handling**: Document and handle floating-point issues, degenerate cases, etc.

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
│   │   ├── grader.py          # Deterministic grading logic
│   │   ├── runner.py          # Model API execution, timeout handling
│   │   └── state.py           # Seed management and deterministic hashing
│   ├── categories/
│   │   ├── __init__.py        # Category registry with auto-discovery
│   │   └── [25 category files]
│   ├── cli.py                 # Typer command-line interface
│   └── ui.py                  # Gradio frontend interface
└── configs/
    ├── mode_full.json
    ├── mode_standard.json
    └── mode_quick.json
```

---

## Contributing

We welcome contributions that expand the category registry or improve grading precision.

1. Fork the repository
2. Create a feature branch
3. Implement your category following the design principles
4. Add tests for edge cases
5. Submit a pull request

### Priority Areas

- Additional mathematical domains (Topology, Number Theory, etc.)
- Physics simulations (Classical Mechanics, Electromagnetism)
- Formal verification problems (SAT solving, Model Checking)
- Optimization problems (Linear Programming, Constraint Satisfaction)

---

## Citation

If you use FORGE in your research, please cite:

```bibtex
@software{forge2024,
  title={FORGE: Formally Generated Reasoning Evaluation},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/forge-benchmark}
}
```

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Inspired by Apple ML Research's "Illusion of Thinking" and concerns about benchmark contamination
- Built on SymPy, NumPy, python-chess, and the scientific Python ecosystem
- Designed for integration with Hugging Face lm-evaluation-harness

---

## Author

Built by [Mohamed Hossam](https://github.com/mohamedhossammohamed) · [@MohamedHz72007](https://x.com/MohamedHz72007)

---

**FORGE is an instrument for producing evidence, not asserting conclusions. It asks whether models truly understand mathematical structure, or merely recognize its statistical shadow in training data.**
