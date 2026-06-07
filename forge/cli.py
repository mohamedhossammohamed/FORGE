"""
FORGE CLI - Command-line interface for running evaluations.

Uses Typer for type-safe command parsing and Rich for output formatting.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich import print as rprint

from .core.runner import ForgeRunner, ModelConfig, RunConfig
from .core.state import derive_seed
from .categories import CATEGORIES, CATEGORY_NAMES, get_category

app = typer.Typer(
    name="forge",
    help="FORGE: Formally Generated Reasoning Evaluation - Testing Understanding Over Interpolation",
    add_completion=False,
)
console = Console()


def load_run_config(mode: str, seed: int) -> RunConfig:
    """Load run configuration based on mode."""
    configs = {
        "nano": RunConfig(
            mode="nano",
            seed=seed,
            categories=["all"],
            questions_per_category=1,
            difficulty_distribution={3: 1},
            timeout=120,
        ),
        "quick": RunConfig(
            mode="quick",
            seed=seed,
            categories=["all"],
            questions_per_category=10,
            difficulty_distribution={3: 5, 4: 5},
            timeout=120,
        ),
        "standard": RunConfig(
            mode="standard",
            seed=seed,
            categories=["all"],
            questions_per_category=100,
            difficulty_distribution={1: 20, 2: 20, 3: 30, 4: 30},
            timeout=120,
        ),
        "full": RunConfig(
            mode="full",
            seed=seed,
            categories=["all"],
            questions_per_category=400,
            difficulty_distribution={1: 80, 2: 80, 3: 80, 4: 80, 5: 80},
            timeout=120,
        ),
    }
    return configs.get(mode, configs["nano"])


@app.command()
def run(
    mode: str = typer.Option(
        "nano", help="Run mode: nano (~30s), quick (~5min), standard (~1hr), full (~4hr)"
    ),
    categories: str = typer.Option("all", help="Comma-separated category names or 'all'"),
    seed: int = typer.Option(None, help="Random seed (random if not specified)"),
    model: str = typer.Option(..., help="Model name"),
    api_base: str = typer.Option(..., help="API base URL"),
    api_key: str = typer.Option(..., help="API key"),
    input_cost: float = typer.Option(4.0, help="Input cost per 1M tokens"),
    output_cost: float = typer.Option(15.0, help="Output cost per 1M tokens"),
    output: str = typer.Option(
        "results/latest.json", help="Output file path (latest.json always updated)"
    ),
    concurrency: int = typer.Option(10, help="Max concurrent API requests"),
):
    """Run FORGE evaluation on a model."""

    # Set seed
    if seed is None:
        import random

        seed = random.randint(0, 2**32 - 1)

    console.print(
        Panel(
            "[bold cyan]FORGE: Formally Generated Reasoning Evaluation[/bold cyan]\n"
            f"Testing Understanding Over Interpolation",
            title="Hypothesis",
            subtitle=f"Seed: {seed}",
        )
    )

    # Load config
    run_config = load_run_config(mode, seed)

    # Parse categories
    if categories == "all":
        category_list = CATEGORY_NAMES
    else:
        category_list = [c.strip() for c in categories.split(",")]
        for c in category_list:
            if c not in CATEGORIES:
                console.print(f"[red]Unknown category: {c}[/red]")
                raise typer.Exit(1)

    # Model config
    model_config = ModelConfig(
        name=model,
        api_base=api_base,
        api_key=api_key,
        input_cost_per_1m=input_cost,
        output_cost_per_1m=output_cost,
    )

    # Display configuration
    console.print(f"\n[bold]Configuration:[/bold]")
    console.print(f"  Mode: {mode}")
    console.print(f"  Categories: {len(category_list)}")
    console.print(f"  Questions per category: {run_config.questions_per_category}")
    console.print(f"  Total questions: {run_config.questions_per_category * len(category_list)}")
    console.print(f"  Difficulty distribution: {run_config.difficulty_distribution}")
    console.print(f"  Model: {model}")
    console.print()

    # Run evaluation
    async def run_evaluation():
        results = []
        start_time = time.time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Running {len(category_list)} categories...",
                total=len(category_list),
            )

            async with ForgeRunner(model_config, concurrency) as runner:
                cat_tasks = []
                for cat_name in category_list:
                    if cat_name not in CATEGORIES:
                        continue
                    category_cls = CATEGORIES[cat_name]
                    category = category_cls(seed)
                    cat_tasks.append(
                        runner.run_category(category, run_config.difficulty_distribution)
                    )

                for coro in asyncio.as_completed(cat_tasks):
                    result = await coro
                    results.append(result)
                    progress.advance(task)

        elapsed = time.time() - start_time

        # Compute final scores
        forge_score = ForgeRunner.compute_forge_score(results)
        interp, extra = ForgeRunner.compute_interpolation_extrapolation(results)

        # Find global cliff index
        cliff_indices = [r.cliff_index for r in results if r.cliff_index is not None]
        global_cliff = min(cliff_indices) if cliff_indices else None

        # Display results
        console.print("\n")
        display_results(results, forge_score, interp, extra, global_cliff, elapsed)

        # Save results
        save_results(
            output,
            run_config,
            model_config,
            results,
            forge_score,
            interp,
            extra,
            global_cliff,
            elapsed,
        )

        console.print(f"\n[green]Results saved to results/[/green]")

    asyncio.run(run_evaluation())


def display_results(results, forge_score, interp, extra, cliff_index, elapsed):
    """Display results in a formatted table."""

    # Summary panel
    summary = f"""
[bold cyan]FORGE Score (Extrapolation-Weighted):[/bold cyan] {forge_score:.4f}
[bold]Interpolation Score (Easy/Medium):[/bold] {interp:.4f}
[bold]Extrapolation Score (Hard/Expert):[/bold] {extra:.4f}
[bold]Complexity Cliff Index:[/bold] {f"Tier {cliff_index}" if cliff_index else "No cliff detected"}
[bold]Runtime:[/bold] {elapsed:.1f}s
"""
    console.print(Panel(summary, title="FORGE Results", border_style="cyan"))

    # Category breakdown
    table = Table(title="Category Breakdown")
    table.add_column("Category", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Correct", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Cliff", justify="right")

    for r in sorted(results, key=lambda x: x.category_score, reverse=True):
        table.add_row(
            r.display_name,
            f"{r.category_score:.4f}",
            str(r.correct),
            str(r.total_questions),
            f"Tier {r.cliff_index}" if r.cliff_index else "-",
        )

    console.print(table)


def save_results(
    output_path, run_config, model_config, results, forge_score, interp, extra, cliff_index, elapsed
):
    """Save results to a timestamped JSON file in results/ directory, plus results/latest.json."""
    data = {
        "forge_version": "0.1.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_config": {
            "mode": run_config.mode,
            "seed": run_config.seed,
            "questions_per_category": run_config.questions_per_category,
            "difficulty_distribution": run_config.difficulty_distribution,
        },
        "model": {
            "name": model_config.name,
            "api_base": model_config.api_base,
        },
        "scores": {
            "forge_score": forge_score,
            "interpolation_score": interp,
            "extrapolation_score": extra,
            "cliff_index": cliff_index,
        },
        "categories": [
            {
                "name": r.name,
                "display_name": r.display_name,
                "score": r.category_score,
                "correct": r.correct,
                "total": r.total_questions,
                "cliff_index": r.cliff_index,
                "accuracy_by_difficulty": {str(k): v for k, v in r.accuracy_by_difficulty.items()},
                "questions": [
                    {
                        "difficulty": q["difficulty"],
                        "iteration": q["iteration"],
                        "correct": q["correct"],
                        "input": q["question"],
                        "output": q["response"],
                        "extracted": q["extracted"],
                        "expected": str(q["expected"]),
                        "reasoning": q.get("reasoning", ""),
                        "elapsed": q.get("elapsed", 0),
                        "is_error": q.get("is_error", False),
                    }
                    for q in r.question_results
                ],
            }
            for r in results
        ],
        "runtime_seconds": elapsed,
    }

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    ts = time.strftime("%Y-%m-%dT%H-%M-%S", time.gmtime())
    model_slug = model_config.name.replace("/", "_")
    timestamped_path = results_dir / f"{ts}_{model_slug}.json"

    with open(timestamped_path, "w") as f:
        json.dump(data, f, indent=2)

    latest_path = results_dir / "latest.json"
    with open(latest_path, "w") as f:
        json.dump(data, f, indent=2)


@app.command()
def list_categories():
    """List all available categories."""
    table = Table(title="FORGE Categories")
    table.add_column("#", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Display Name")

    for i, (name, cls) in enumerate(CATEGORIES.items(), 1):
        table.add_row(str(i), name, cls.__name__.replace("Category", ""))

    console.print(table)


@app.command()
def info():
    """Display FORGE hypothesis and scoring methodology."""
    console.print(
        Panel(
            "[bold cyan]FORGE: Formally Generated Reasoning Evaluation[/bold cyan]\n\n"
            "[bold]Hypothesis:[/bold]\n"
            "Large language models—when performing well—may be operating with something\n"
            "functionally equivalent to an internal model of reality: a compressed, weighted\n"
            "representation of mathematical structure, physical law, and logical relationship\n"
            "embedded in their weights.\n\n"
            "[bold]Core Claim:[/bold]\n"
            "A model's score on FORGE is evidence—not proof—of how deeply it has internalized\n"
            "mathematical and physical structure, as distinct from how much relevant training\n"
            "data it has seen.\n\n"
            "[bold]Falsifiability:[/bold]\n"
            "The hypothesis would be disproven if models scoring highly on maximum difficulty\n"
            "tiers suffer catastrophic performance degradation when mathematical structure\n"
            "remains identical but semantic framing is inverted.\n\n"
            "[bold]Scoring:[/bold]\n"
            "C_c = Σ(α^d · S_{c,d}) / Σ(α^d)  where α=1.5 (extrapolation bias)\n"
            "FORGE Score = average of all C_c\n"
            "Cliff Index = first difficulty tier where accuracy drops >30%",
            title="About FORGE",
        )
    )


@app.command()
def visualize(
    results: str = typer.Option("results/latest.json", help="Path to results JSON file"),
    output_dir: str = typer.Option("forge_charts", help="Output directory for charts"),
    comparison_dir: Optional[str] = typer.Option(
        None, help="Directory with multiple results for comparison"
    ),
    formats: str = typer.Option("png,html,terminal", help="Comma-separated output formats"),
    terminal_only: bool = typer.Option(False, help="Only print terminal report (no files)"),
):
    """Generate visualizations from evaluation results."""
    from .visualize import visualize as run_visualize

    fmt_list = [f.strip() for f in formats.split(",")]
    if terminal_only:
        fmt_list = ["terminal"]

    console.print(
        Panel(
            "[bold cyan]FORGE Visualization Pipeline[/bold cyan]",
            title="Generating Charts",
        )
    )

    outputs = run_visualize(
        results_path=results,
        output_dir=output_dir,
        comparison_dir=comparison_dir,
        formats=fmt_list,
    )

    console.print()
    for fmt, out in outputs.items():
        if out:
            console.print(f"  [green]✓[/green] {fmt}: {out}")
    console.print()


if __name__ == "__main__":
    app()
