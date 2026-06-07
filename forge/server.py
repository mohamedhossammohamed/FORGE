"""
FORGE Backend Server

Serves the researcher tool frontend and provides API endpoints
for running evaluations with real-time progress via SSE.
"""

import asyncio
import json
import time
import secrets
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from .core.runner import ForgeRunner, ModelConfig, RunConfig
from .categories import CATEGORIES, CATEGORY_NAMES

app = FastAPI(title="FORGE API")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
STATIC_DIR = Path(__file__).parent.parent


class RunRequest(BaseModel):
    model: str
    api_base: str
    api_key: str
    seed: int = 42
    mode: str = "nano"
    input_cost: float = 0.0
    output_cost: float = 0.0
    categories: Optional[str] = None


def get_mode_config(mode: str, categories_str: str = None):
    """Get run configuration for a mode."""
    if categories_str and categories_str != "all":
        category_list = [c.strip() for c in categories_str.split(",")]
    else:
        category_list = CATEGORY_NAMES

    configs = {
        "nano": RunConfig(
            mode="nano", seed=42, categories=["arithmetic_chain", "mod_exp", "game_nim", "info_entropy", "combinatorics_stars"],
            questions_per_category=1, difficulty_distribution={3: 1},
        ),
        "quick": RunConfig(
            mode="quick", seed=42, categories=category_list,
            questions_per_category=10, difficulty_distribution={3: 5, 4: 5},
        ),
        "standard": RunConfig(
            mode="standard", seed=42, categories=category_list,
            questions_per_category=100, difficulty_distribution={1: 20, 2: 20, 3: 30, 4: 30},
        ),
        "full": RunConfig(
            mode="full", seed=42, categories=category_list,
            questions_per_category=400, difficulty_distribution={1: 80, 2: 80, 3: 80, 4: 80, 5: 80},
        ),
    }
    return configs.get(mode, configs["nano"])


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the leaderboard."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/researcher.html", response_class=HTMLResponse)
async def serve_researcher():
    """Serve the researcher tool."""
    return FileResponse(STATIC_DIR / "researcher.html")


@app.post("/api/run")
async def run_evaluation(req: RunRequest):
    """Run a FORGE evaluation with SSE progress updates."""

    model_config = ModelConfig(
        name=req.model,
        api_base=req.api_base,
        api_key=req.api_key,
        input_cost_per_1m=req.input_cost,
        output_cost_per_1m=req.output_cost,
    )

    run_config = get_mode_config(req.mode, req.categories)

    async def event_stream():
        # Test connection first
        try:
            async with ForgeRunner(model_config, concurrency=10) as runner:
                success, msg = await runner.test_connection()
                if not success:
                    yield f"data: {json.dumps({'type': 'error', 'message': msg})}\n\n"
                    return

                category_list = run_config.categories
                results = []
                total_questions = 0
                completed = 0

                for cat_name in category_list:
                    if cat_name not in CATEGORIES:
                        continue
                    cat_cls = CATEGORIES[cat_name]
                    category = cat_cls(req.seed)
                    cat_questions = sum(run_config.difficulty_distribution.values())
                    total_questions += cat_questions

                yield f"data: {json.dumps({'type': 'start', 'total': total_questions})}\n\n"

                start_time = time.time()

                for cat_name in category_list:
                    if cat_name not in CATEGORIES:
                        continue

                    cat_cls = CATEGORIES[cat_name]
                    category = cat_cls(req.seed)

                    # Run one problem at a time for streaming
                    for diff, count in run_config.difficulty_distribution.items():
                        for iteration in range(count):
                            problem = category.generate(diff, iteration)
                            result = await runner.run_single(problem, category)
                            completed += 1

                            yield f"data: {json.dumps({'type': 'progress', 'category': cat_name, 'difficulty': diff, 'correct': result['correct'], 'elapsed': result['elapsed'], 'completed': completed, 'total': total_questions})}\n\n"

                    # Compute category-level result
                    cat_result = await runner.run_category(category, run_config.difficulty_distribution)
                    results.append(cat_result)

                elapsed = time.time() - start_time

                # Compute final scores
                forge_score = ForgeRunner.compute_forge_score(results)
                interp, extra = ForgeRunner.compute_interpolation_extrapolation(results)
                cliff_indices = [r.cliff_index for r in results if r.cliff_index is not None]
                global_cliff = min(cliff_indices) if cliff_indices else None

                cost = runner.compute_cost()

                # Build category breakdown with tier data
                categories_data = []
                for r in results:
                    tiers = {}
                    for d, stats in r.accuracy_by_difficulty.items():
                        tiers[str(d)] = {"correct": stats["correct"], "total": stats["total"]}
                    categories_data.append({
                        "name": r.name,
                        "display_name": r.display_name,
                        "score": r.category_score,
                        "correct": r.correct,
                        "total": r.total_questions,
                        "cliff": r.cliff_index,
                        "tiers": tiers,
                    })

                final = {
                    "type": "result",
                    "forge_score": forge_score,
                    "interpolation_score": interp,
                    "extrapolation_score": extra,
                    "cliff_index": global_cliff,
                    "cost": cost,
                    "elapsed": elapsed,
                    "total_questions": completed,
                    "categories": categories_data,
                }

                yield f"data: {json.dumps(final)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/test")
async def test_connection(req: RunRequest):
    """Test API connection."""
    model_config = ModelConfig(
        name=req.model,
        api_base=req.api_base,
        api_key=req.api_key,
    )

    try:
        async with ForgeRunner(model_config) as runner:
            success, msg = await runner.test_connection()
            return {"success": success, "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)}


def main():
    """Run the server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")


if __name__ == "__main__":
    main()
