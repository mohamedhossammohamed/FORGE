"""Generate snapshot_seed42.json for version stability testing.

Run once and commit the output file:
    python tests/generate_snapshot.py
"""

import json
from pathlib import Path
from forge.categories import CATEGORIES

SEED = 42
DIFFICULTY = 3
ITERATION = 0


def main():
    snapshot = {}
    for name, cls in CATEGORIES.items():
        instance = cls(seed=SEED)
        p = instance.generate(DIFFICULTY, ITERATION)
        snapshot[name] = {
            "question": p.question,
            "answer": str(p.answer),
            "category": p.category,
            "difficulty": p.difficulty,
            "iteration": p.iteration,
            "seed": p.seed,
        }
        print(f"  {name}: answer={p.answer}")

    out_dir = Path(__file__).parent / "fixtures"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "snapshot_seed42.json"
    with open(out_path, "w") as f:
        json.dump(snapshot, f, indent=2)
    print(f"\nSnapshot written to {out_path}")


if __name__ == "__main__":
    main()
