"""
FORGE Backend Server

Serves the researcher tool frontend and provides API endpoints
for running evaluations with real-time progress via SSE.
"""

import asyncio
import json
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

import uvicorn
uvicorn.config.WORKER_TIMEOUT = 0  # No worker timeout

from .core.runner import ForgeRunner, ModelConfig, RunConfig
from .categories import CATEGORIES, CATEGORY_NAMES

app = FastAPI(title="FORGE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    if categories_str and categories_str != "all":
        category_list = [c.strip() for c in categories_str.split(",")]
    else:
        category_list = CATEGORY_NAMES

    configs = {
        "nano": RunConfig(
            mode="nano", seed=42,
            categories=["arithmetic_chain", "mod_exp", "game_nim", "info_entropy", "combinatorics_stars"],
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
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/researcher.html", response_class=HTMLResponse)
async def serve_researcher():
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
        try:
            async with ForgeRunner(model_config, concurrency=10) as runner:
                success, msg = await runner.test_connection()
                if not success:
                    yield f"data: {json.dumps({'type': 'error', 'message': msg})}\n\n"
                    return

                category_list = [c for c in run_config.categories if c in CATEGORIES]

                # Count total questions
                total_questions = 0
                for cat_name in category_list:
                    total_questions += sum(run_config.difficulty_distribution.values())

                yield f"data: {json.dumps({'type': 'start', 'total': total_questions})}\n\n"

                start_time = time.time()
                completed = 0

                # Results accumulator per category
                cat_results = {}
                for cat_name in category_list:
                    cat_results[cat_name] = {"correct": 0, "total": 0, "by_diff": {}}

                for cat_name in category_list:
                    cat_cls = CATEGORIES[cat_name]
                    category = cat_cls(req.seed)

                    for diff, count in run_config.difficulty_distribution.items():
                        if diff not in cat_results[cat_name]["by_diff"]:
                            cat_results[cat_name]["by_diff"][diff] = {"correct": 0, "total": 0}

                        for iteration in range(count):
                            problem = category.generate(diff, iteration)
                            result = await runner.run_single(problem, category)
                            completed += 1

                            # Accumulate results
                            cat_results[cat_name]["total"] += 1
                            cat_results[cat_name]["by_diff"][diff]["total"] += 1
                            if result["correct"]:
                                cat_results[cat_name]["correct"] += 1
                                cat_results[cat_name]["by_diff"][diff]["correct"] += 1

                            progress_data = {
                                "type": "progress",
                                "category": cat_name,
                                "difficulty": diff,
                                "correct": result["correct"],
                                "elapsed": result["elapsed"],
                                "completed": completed,
                                "total": total_questions,
                                "is_error": result.get("is_error", False),
                                "error_message": result.get("error_message"),
                                "expected": str(result.get("expected", "")),
                                "extracted": str(result.get("extracted", "")),
                                "response_preview": str(result.get("response", ""))[:500],
                            }
                            yield f"data: {json.dumps(progress_data)}\n\n"

                elapsed = time.time() - start_time

                # Build category results
                from .core.runner import CategoryResult
                category_results = []
                for cat_name in category_list:
                    cat_cls = CATEGORIES[cat_name]
                    cat_instance = cat_cls(req.seed)
                    cr = cat_results[cat_name]
                    score = ForgeRunner.compute_category_score(cr["by_diff"])
                    cliff = ForgeRunner.compute_cliff_index(cr["by_diff"])
                    category_results.append(CategoryResult(
                        name=cat_name,
                        display_name=cat_instance.display_name,
                        total_questions=cr["total"],
                        correct=cr["correct"],
                        accuracy_by_difficulty=cr["by_diff"],
                        category_score=score,
                        cliff_index=cliff,
                    ))

                forge_score = ForgeRunner.compute_forge_score(category_results)
                interp, extra = ForgeRunner.compute_interpolation_extrapolation(category_results)
                cliff_indices = [r.cliff_index for r in category_results if r.cliff_index is not None]
                global_cliff = min(cliff_indices) if cliff_indices else None
                cost = runner.compute_cost()

                categories_data = []
                for r in category_results:
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
    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info", timeout_keep_alive=0)


if __name__ == "__main__":
    main()
