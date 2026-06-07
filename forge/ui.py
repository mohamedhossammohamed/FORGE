"""
FORGE UI - Gradio web interface for running evaluations.

Provides an interactive interface for configuring and running FORGE evaluations
with real-time progress tracking and result visualization.
Supports multi-model comparison and leaderboard generation.
"""

import asyncio
import json
import time
from typing import Optional
from dataclasses import dataclass, field

import gradio as gr

from .core.runner import ForgeRunner, ModelConfig, RunConfig
from .core.state import derive_seed
from .categories import CATEGORIES, CATEGORY_NAMES, get_category


def create_ui():
    """Create the Gradio interface for FORGE."""

    with gr.Blocks(
        title="FORGE: Formally Generated Reasoning Evaluation",
    ) as app:
        # State for storing multiple models
        models_state = gr.State([])
        results_state = gr.State({})

        gr.Markdown(
            """
            # FORGE: Formally Generated Reasoning Evaluation
            ### Testing Understanding Over Interpolation
            
            **Hypothesis:** Large language models may be operating with something functionally 
            equivalent to an internal model of reality. FORGE is a procedurally generated, 
            computationally graded evaluation instrument designed to test whether LLMs generalize 
            through internal world-models or succeed via sophisticated interpolation over 
            memorized training data.
            """
        )

        with gr.Tabs():
            # Tab 1: Single Model Evaluation
            with gr.TabItem("Single Model"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("## Model Configuration")

                        model_name = gr.Textbox(
                            label="Model Name",
                            placeholder="e.g., gpt-4o, claude-3-5-sonnet",
                            value="gpt-4o",
                        )

                        api_base = gr.Textbox(
                            label="API Base URL",
                            placeholder="e.g., https://openrouter.ai/api/v1",
                            value="https://openrouter.ai/api/v1",
                        )

                        api_key = gr.Textbox(
                            label="API Key",
                            type="password",
                            placeholder="sk-...",
                        )

                        with gr.Row():
                            input_cost = gr.Number(
                                label="Input Cost per 1M tokens ($)",
                                value=4.0,
                                precision=2,
                            )
                            output_cost = gr.Number(
                                label="Output Cost per 1M tokens ($)",
                                value=15.0,
                                precision=2,
                            )

                        test_btn = gr.Button("🔌 Test Connection", variant="secondary")
                        connection_status = gr.Markdown(
                            "*Click 'Test Connection' to verify API access*"
                        )

                        run_mode = gr.Dropdown(
                            choices=["nano", "quick", "standard", "full"],
                            value="nano",
                            label="Run Mode",
                            info="nano: 10 questions (~30s), quick: 250 (~5min), standard: 2500 (~1hr), full: 10000 (~4hr)",
                        )

                        with gr.Row():
                            seed = gr.Number(
                                label="Seed",
                                value=42,
                                precision=0,
                                info="Use same seed for reproducibility, or randomize for fresh problems",
                            )
                            randomize_btn = gr.Button("🎲 Randomize", size="sm")

                        gr.Markdown(
                            """
                            **Seed Security:**
                            - **Public benchmark**: Use random seed, publish it with results
                            - **Contamination test**: Use secret seed that AI labs don't know
                            - **Reproducibility**: Same seed = same problems every time
                            """
                        )

                        categories_input = gr.Textbox(
                            label="Categories (comma-separated or 'all')",
                            value="all",
                        )

                        concurrency = gr.Slider(
                            minimum=1,
                            maximum=50,
                            value=10,
                            step=1,
                            label="Concurrency",
                            info="Max concurrent API requests",
                        )

                        run_btn = gr.Button("▶ Run Single Model", variant="primary", size="lg")
                        save_snapshot_btn = gr.Button(
                            "💾 Save Snapshot", variant="secondary", size="sm"
                        )

                    with gr.Column(scale=2):
                        gr.Markdown("## Results")

                        with gr.Tabs():
                            with gr.TabItem("Summary"):
                                summary_display = gr.Markdown(
                                    """
                                    ### Waiting for evaluation...
                                    
                                    Configure your model, **test the connection**, then click **Run Single Model**.
                                    
                                    ---
                                    
                                    **Score Interpretation:**
                                    - **FORGE Score**: Weighted accuracy emphasizing harder problems (α=1.5)
                                    - **Interpolation Score**: Performance on Easy/Medium (likely in training data)
                                    - **Extrapolation Score**: Performance on Hard/Expert (novel problems)
                                    - **Cliff Index**: First difficulty tier where accuracy drops >30%
                                    """
                                )

                            with gr.TabItem("Category Breakdown"):
                                category_table = gr.Dataframe(
                                    headers=["Category", "Score", "Correct", "Total", "Cliff"],
                                    datatype=["str", "number", "number", "number", "str"],
                                    interactive=False,
                                )

                            with gr.TabItem("Detailed Results"):
                                detailed_json = gr.JSON(label="Full Results")

                            with gr.TabItem("Errors"):
                                error_display = gr.Markdown("*No errors*")

            # Tab 2: Multi-Model Comparison
            with gr.TabItem("Multi-Model Comparison"):
                gr.Markdown(
                    """
                    ## Compare Multiple Models
                    
                    Add multiple models to run the same benchmark on all of them and generate 
                    a leaderboard comparison. All models will be evaluated with the same seed 
                    for fair comparison.
                    """
                )

                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Add Model")

                        multi_model_name = gr.Textbox(
                            label="Model Name",
                            placeholder="e.g., gpt-4o",
                        )

                        multi_api_base = gr.Textbox(
                            label="API Base URL",
                            value="https://openrouter.ai/api/v1",
                        )

                        multi_api_key = gr.Textbox(
                            label="API Key",
                            type="password",
                        )

                        with gr.Row():
                            multi_input_cost = gr.Number(
                                label="Input $/1M",
                                value=4.0,
                                precision=2,
                            )
                            multi_output_cost = gr.Number(
                                label="Output $/1M",
                                value=15.0,
                                precision=2,
                            )

                        add_model_btn = gr.Button("➕ Add Model", variant="secondary")

                        gr.Markdown("### Model Queue")
                        model_queue_display = gr.Dataframe(
                            headers=["Model", "API Base", "Input $/1M", "Output $/1M"],
                            datatype=["str", "str", "number", "number"],
                            interactive=False,
                        )

                        clear_models_btn = gr.Button("🗑️ Clear All Models", size="sm")

                    with gr.Column(scale=2):
                        gr.Markdown("### Evaluation Settings")

                        with gr.Row():
                            multi_run_mode = gr.Dropdown(
                                choices=["nano", "quick", "standard", "full"],
                                value="nano",
                                label="Run Mode",
                            )

                            multi_seed = gr.Number(
                                label="Seed (same for all models)",
                                value=42,
                                precision=0,
                            )

                            multi_randomize_btn = gr.Button("🎲", size="sm")

                        multi_categories = gr.Textbox(
                            label="Categories",
                            value="all",
                        )

                        multi_concurrency = gr.Slider(
                            minimum=1,
                            maximum=50,
                            value=10,
                            step=1,
                            label="Concurrency per Model",
                        )

                        run_all_btn = gr.Button(
                            "▶ Run All Models & Generate Leaderboard",
                            variant="primary",
                            size="lg",
                        )
                        save_multi_snapshot_btn = gr.Button(
                            "💾 Save Snapshot", variant="secondary", size="sm"
                        )

                gr.Markdown("---")
                gr.Markdown("## Leaderboard")

                with gr.Tabs():
                    with gr.TabItem("Leaderboard"):
                        leaderboard_display = gr.Markdown(
                            """
                            ### No results yet
                            
                            Add models and click **Run All Models** to generate the leaderboard.
                            """
                        )

                    with gr.TabItem("Comparison Table"):
                        comparison_table = gr.Dataframe(
                            headers=[
                                "Rank",
                                "Model",
                                "FORGE Score",
                                "Interpolation",
                                "Extrapolation",
                                "Cliff Index",
                                "Cost ($)",
                                "Runtime",
                            ],
                            datatype=[
                                "number",
                                "str",
                                "number",
                                "number",
                                "number",
                                "str",
                                "number",
                                "number",
                            ],
                            interactive=False,
                        )

                    with gr.TabItem("Per-Category Comparison"):
                        per_category_display = gr.Markdown(
                            "Run evaluations to see per-category breakdown."
                        )

                    with gr.TabItem("Export"):
                        export_json = gr.JSON(label="Full Comparison Data")

        # ==================== Event Handlers ====================

        def randomize_seed():
            """Generate a cryptographically secure random seed."""
            import secrets

            return secrets.randbits(64)  # 64-bit seed for good entropy

        randomize_btn.click(fn=randomize_seed, outputs=[seed])
        multi_randomize_btn.click(fn=randomize_seed, outputs=[multi_seed])

        # Test API connection
        async def test_connection(api_base, api_key, model_name):
            if not api_key:
                return "❌ **Error**: API key is required"

            model_config = ModelConfig(
                name=model_name,
                api_base=api_base,
                api_key=api_key,
            )

            try:
                async with ForgeRunner(model_config) as runner:
                    success, message = await runner.test_connection()

                    if success:
                        return f"✅ **Connection Successful**\n\nModel: `{model_name}`\nEndpoint: `{api_base}`"
                    else:
                        return f"❌ **Connection Failed**\n\n{message}"
            except Exception as e:
                return f"❌ **Error**: {str(e)}"

        test_btn.click(
            fn=lambda api_base, api_key, model: asyncio.run(
                test_connection(api_base, api_key, model)
            ),
            inputs=[api_base, api_key, model_name],
            outputs=[connection_status],
        )

        # Add model to queue
        def add_model(name, api_base, api_key, input_cost, output_cost, current_models):
            if not name or not api_key:
                gr.Warning("Model name and API key are required!")
                return current_models, []

            new_model = {
                "name": name,
                "api_base": api_base,
                "api_key": api_key,
                "input_cost": input_cost,
                "output_cost": output_cost,
            }

            updated = current_models + [new_model]

            # Format for display
            display_data = [
                [m["name"], m["api_base"], m["input_cost"], m["output_cost"]] for m in updated
            ]

            return updated, display_data

        add_model_btn.click(
            fn=add_model,
            inputs=[
                multi_model_name,
                multi_api_base,
                multi_api_key,
                multi_input_cost,
                multi_output_cost,
                models_state,
            ],
            outputs=[models_state, model_queue_display],
        )

        # Clear models
        def clear_models():
            return [], []

        clear_models_btn.click(
            fn=clear_models,
            outputs=[models_state, model_queue_display],
        )

        # Single model evaluation
        def run_single_evaluation(
            model,
            api_base,
            api_key,
            input_cost,
            output_cost,
            mode,
            seed,
            categories_str,
            concurrency_val,
        ):
            return asyncio.run(
                _evaluate_single_model(
                    model,
                    api_base,
                    api_key,
                    input_cost,
                    output_cost,
                    mode,
                    seed,
                    categories_str,
                    concurrency_val,
                )
            )

        run_btn.click(
            fn=run_single_evaluation,
            inputs=[
                model_name,
                api_base,
                api_key,
                input_cost,
                output_cost,
                run_mode,
                seed,
                categories_input,
                concurrency,
            ],
            outputs=[summary_display, category_table, detailed_json, error_display],
        )

        # Multi-model evaluation
        def run_multi_evaluation(models, mode, seed, categories_str, concurrency_val):
            if not models:
                gr.Warning("No models added! Add at least one model first.")
                return ("### No models to evaluate", [], {}, "No models configured.")

            return asyncio.run(
                _evaluate_multiple_models(models, mode, seed, categories_str, concurrency_val)
            )

        run_all_btn.click(
            fn=run_multi_evaluation,
            inputs=[
                models_state,
                multi_run_mode,
                multi_seed,
                multi_categories,
                multi_concurrency,
            ],
            outputs=[
                leaderboard_display,
                comparison_table,
                export_json,
                per_category_display,
            ],
        )

        # Save snapshot handlers
        def save_snapshot(detailed_data):
            """Save single-model snapshot to results/ directory."""
            import json as _json
            from pathlib import Path
            import time as _time

            if not detailed_data or "error" in detailed_data:
                gr.Warning("No results to save. Run an evaluation first.")
                return "No results to save."

            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)

            ts = _time.strftime("%Y-%m-%dT%H-%M-%S", _time.gmtime())
            model_slug = detailed_data.get("model", "unknown").replace("/", "_")
            filepath = results_dir / f"{ts}_{model_slug}_snapshot.json"

            with open(filepath, "w") as f:
                _json.dump(detailed_data, f, indent=2)

            # Also save as latest snapshot
            latest_path = results_dir / "latest_snapshot.json"
            with open(latest_path, "w") as f:
                _json.dump(detailed_data, f, indent=2)

            return f"Snapshot saved to {filepath}"

        def save_multi_snapshot(export_data):
            """Save multi-model snapshot to results/ directory."""
            import json as _json
            from pathlib import Path
            import time as _time

            if not export_data or "error" in export_data:
                gr.Warning("No results to save. Run an evaluation first.")
                return "No results to save."

            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)

            ts = _time.strftime("%Y-%m-%dT%H-%M-%S", _time.gmtime())
            filepath = results_dir / f"{ts}_multi_model_snapshot.json"

            with open(filepath, "w") as f:
                _json.dump(export_data, f, indent=2)

            latest_path = results_dir / "latest_snapshot.json"
            with open(latest_path, "w") as f:
                _json.dump(export_data, f, indent=2)

            return f"Snapshot saved to {filepath}"

        save_snapshot_btn.click(
            fn=save_snapshot,
            inputs=[detailed_json],
            outputs=[],
        )

        save_multi_snapshot_btn.click(
            fn=save_multi_snapshot,
            inputs=[export_json],
            outputs=[],
        )

    return app


async def _evaluate_single_model(
    model, api_base, api_key, input_cost, output_cost, mode, seed, categories_str, concurrency_val
):
    """Run evaluation for a single model."""

    if categories_str.strip().lower() == "all":
        category_list = CATEGORY_NAMES
    else:
        category_list = [c.strip() for c in categories_str.split(",")]

    configs = _get_run_configs(category_list)
    run_config = configs.get(mode, configs["quick"])

    model_config = ModelConfig(
        name=model,
        api_base=api_base,
        api_key=api_key,
        input_cost_per_1m=float(input_cost),
        output_cost_per_1m=float(output_cost),
    )

    results = []
    all_errors = []
    start_time = time.time()

    try:
        async with ForgeRunner(model_config, int(concurrency_val)) as runner:
            # Test connection first
            success, message = await runner.test_connection()
            if not success:
                error_summary = f"### ❌ Connection Failed\n\n{message}\n\nPlease check your API key and endpoint URL."
                return (error_summary, [], {"error": message}, f"**Connection Error**: {message}")

            cat_tasks = []
            for cat_name in category_list:
                if cat_name not in CATEGORIES:
                    continue
                category_cls = CATEGORIES[cat_name]
                category = category_cls(int(seed))
                cat_tasks.append(runner.run_category(category, run_config.difficulty_distribution))

            cat_results = await asyncio.gather(*cat_tasks)
            results = list(cat_results)

            for result in results:
                if result.errors:
                    all_errors.extend(result.errors)
    except Exception as e:
        error_msg = f"Error during evaluation: {str(e)}"
        return (f"### ❌ Error\n{error_msg}", [], {"error": error_msg}, f"**Error**: {error_msg}")

    elapsed = time.time() - start_time

    forge_score = ForgeRunner.compute_forge_score(results)
    interp, extra = ForgeRunner.compute_interpolation_extrapolation(results)
    cliff_indices = [r.cliff_index for r in results if r.cliff_index is not None]
    global_cliff = min(cliff_indices) if cliff_indices else None

    summary = _format_single_summary(model, forge_score, interp, extra, global_cliff, elapsed)

    table_data = []
    for r in sorted(results, key=lambda x: x.category_score, reverse=True):
        table_data.append(
            [
                r.display_name,
                round(r.category_score, 4),
                r.correct,
                r.total_questions,
                f"Tier {r.cliff_index}" if r.cliff_index else "-",
            ]
        )

    detailed = {
        "model": model,
        "forge_score": forge_score,
        "interpolation_score": interp,
        "extrapolation_score": extra,
        "cliff_index": global_cliff,
        "categories": [
            {
                "name": r.name,
                "score": r.category_score,
                "correct": r.correct,
                "total": r.total_questions,
                "cliff": r.cliff_index,
                "errors": r.errors,
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
    }

    # Format errors
    if all_errors:
        unique_errors = list(set(all_errors))[:10]
        error_md = "## ⚠️ Errors Encountered\n\n"
        error_md += "The following errors occurred during evaluation:\n\n"
        for err in unique_errors:
            error_md += f"- `{err}`\n"
        error_md += "\n**Note**: Questions with errors are marked as incorrect."
    else:
        error_md = "## ✅ No Errors\n\nAll API calls completed successfully."

    return summary, table_data, detailed, error_md


async def _evaluate_multiple_models(models, mode, seed, categories_str, concurrency_val):
    """Run evaluation for multiple models concurrently and generate leaderboard."""

    if categories_str.strip().lower() == "all":
        category_list = CATEGORY_NAMES
    else:
        category_list = [c.strip() for c in categories_str.split(",")]

    configs = _get_run_configs(category_list)
    run_config = configs.get(mode, configs["quick"])
    concurrency = int(concurrency_val)

    async def _run_single_model(model_info):
        model_name = model_info["name"]

        model_config = ModelConfig(
            name=model_name,
            api_base=model_info["api_base"],
            api_key=model_info["api_key"],
            input_cost_per_1m=model_info.get("input_cost", 4.0),
            output_cost_per_1m=model_info.get("output_cost", 15.0),
        )

        results = []
        start_time = time.time()

        try:
            async with ForgeRunner(model_config, concurrency) as runner:
                success, message = await runner.test_connection()
                if not success:
                    gr.Warning(f"Skipping {model_name}: {message}")
                    return None

                cat_tasks = []
                for cat_name in category_list:
                    if cat_name not in CATEGORIES:
                        continue
                    category_cls = CATEGORIES[cat_name]
                    category = category_cls(int(seed))
                    cat_tasks.append(
                        runner.run_category(category, run_config.difficulty_distribution)
                    )

                results = await asyncio.gather(*cat_tasks)
        except Exception as e:
            gr.Warning(f"Error evaluating {model_name}: {str(e)}")
            return None

        elapsed = time.time() - start_time

        forge_score = ForgeRunner.compute_forge_score(results)
        interp, extra = ForgeRunner.compute_interpolation_extrapolation(results)
        cliff_indices = [r.cliff_index for r in results if r.cliff_index is not None]
        global_cliff = min(cliff_indices) if cliff_indices else None

        return model_name, {
            "forge_score": forge_score,
            "interpolation_score": interp,
            "extrapolation_score": extra,
            "cliff_index": global_cliff,
            "runtime": elapsed,
            "cost": runner.compute_cost(),
            "categories": {
                r.name: {
                    "score": r.category_score,
                    "correct": r.correct,
                    "total": r.total_questions,
                    "cliff": r.cliff_index,
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
            },
        }

    model_tasks = [_run_single_model(m) for m in models]
    model_results = await asyncio.gather(*model_tasks)

    all_results = {}
    for item in model_results:
        if item is not None:
            model_name, data = item
            all_results[model_name] = data

    # Generate leaderboard
    leaderboard_md = _format_leaderboard(all_results)

    # Generate comparison table
    sorted_models = sorted(all_results.items(), key=lambda x: x[1]["forge_score"], reverse=True)

    comparison_data = []
    for rank, (model_name, data) in enumerate(sorted_models, 1):
        comparison_data.append(
            [
                rank,
                model_name,
                round(data["forge_score"], 4),
                round(data["interpolation_score"], 4),
                round(data["extrapolation_score"], 4),
                f"Tier {data['cliff_index']}" if data["cliff_index"] else "-",
                round(data.get("cost", 0), 2),
                round(data["runtime"], 1),
            ]
        )

    # Generate per-category comparison
    per_category_md = _format_per_category_comparison(all_results, category_list)

    export_data = {
        "seed": int(seed),
        "mode": mode,
        "models": all_results,
    }

    return leaderboard_md, comparison_data, export_data, per_category_md


def _get_run_configs(category_list):
    """Get run mode configurations."""
    # Nano mode uses only 5 fast categories for instant feedback
    nano_categories = [
        "arithmetic_chain",
        "mod_exp",
        "game_nim",
        "info_entropy",
        "combinatorics_stars",
    ]

    return {
        "nano": RunConfig(
            mode="nano",
            seed=42,
            categories=nano_categories,
            questions_per_category=1,  # 1 question × 5 categories = 5 total
            difficulty_distribution={3: 1},  # Single medium-hard question per category
        ),
        "quick": RunConfig(
            mode="quick",
            seed=42,
            categories=category_list,
            questions_per_category=10,
            difficulty_distribution={3: 5, 4: 5},
        ),
        "standard": RunConfig(
            mode="standard",
            seed=42,
            categories=category_list,
            questions_per_category=100,
            difficulty_distribution={1: 20, 2: 20, 3: 30, 4: 30},
        ),
        "full": RunConfig(
            mode="full",
            seed=42,
            categories=category_list,
            questions_per_category=400,
            difficulty_distribution={1: 80, 2: 80, 3: 80, 4: 80, 5: 80},
        ),
    }


def _format_single_summary(model, forge_score, interp, extra, cliff, elapsed):
    """Format summary for single model evaluation."""
    return f"""
### FORGE Results: {model}

| Metric | Value |
|--------|-------|
| **FORGE Score** | {forge_score:.4f} |
| **Interpolation Score** | {interp:.4f} |
| **Extrapolation Score** | {extra:.4f} |
| **Cliff Index** | {f"Tier {cliff}" if cliff else "No cliff detected"} |
| **Runtime** | {elapsed:.1f}s |

---

**Score Interpretation:**
- A high **Extrapolation Score** relative to **Interpolation Score** suggests genuine reasoning
- A low **Cliff Index** indicates early capability collapse
- The **Complexity Cliff** measures where the "Illusion of Thinking" breaks down
"""


def _format_leaderboard(all_results):
    """Format leaderboard markdown."""
    if not all_results:
        return "### No results yet"

    sorted_models = sorted(all_results.items(), key=lambda x: x[1]["forge_score"], reverse=True)

    md = "## FORGE Leaderboard\n\n"
    md += "| Rank | Model | FORGE Score | Interpolation | Extrapolation | Cliff Index |\n"
    md += "|------|-------|-------------|---------------|---------------|-------------|\n"

    for rank, (model, data) in enumerate(sorted_models, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
        cliff_str = f"Tier {data['cliff_index']}" if data["cliff_index"] else "-"

        md += f"| {medal} | **{model}** | {data['forge_score']:.4f} | "
        md += f"{data['interpolation_score']:.4f} | {data['extrapolation_score']:.4f} | {cliff_str} |\n"

    md += "\n---\n\n"
    md += "**Key Insights:**\n"

    if len(sorted_models) >= 2:
        best = sorted_models[0]
        worst = sorted_models[-1]
        md += f"- **Best performer**: {best[0]} (FORGE Score: {best[1]['forge_score']:.4f})\n"
        md += f"- **Largest gap**: {best[0]} outperforms {worst[0]} by "
        md += f"{best[1]['forge_score'] - worst[1]['forge_score']:.4f}\n"

    # Find model with best extrapolation
    best_extra = max(all_results.items(), key=lambda x: x[1]["extrapolation_score"])
    md += (
        f"- **Best extrapolation**: {best_extra[0]} ({best_extra[1]['extrapolation_score']:.4f})\n"
    )

    return md


def _format_per_category_comparison(all_results, category_list):
    """Format per-category comparison markdown."""
    if not all_results:
        return "No results to compare."

    md = "## Per-Category Comparison\n\n"

    for cat_name in category_list:
        display_name = cat_name.replace("_", " ").title()
        md += f"### {display_name}\n\n"
        md += "| Model | Score | Correct | Total | Cliff |\n"
        md += "|-------|-------|---------|-------|-------|\n"

        # Sort by this category's score
        cat_scores = []
        for model, data in all_results.items():
            if cat_name in data.get("categories", {}):
                cat_data = data["categories"][cat_name]
                cat_scores.append((model, cat_data))

        cat_scores.sort(key=lambda x: x[1]["score"], reverse=True)

        for model, cat_data in cat_scores:
            cliff_str = f"Tier {cat_data['cliff']}" if cat_data["cliff"] else "-"
            md += f"| {model} | {cat_data['score']:.4f} | {cat_data['correct']} | {cat_data['total']} | {cliff_str} |\n"

        md += "\n"

    return md


def launch_ui(**kwargs):
    """Launch the FORGE UI."""
    app = create_ui()
    app.launch(**kwargs)


if __name__ == "__main__":
    launch_ui()
