"""
API execution engine for FORGE evaluations.

Handles model queries via OpenAI-compatible endpoints with async execution,
timeout handling, token counting, and cost estimation.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from .generator import ForgeCategory, Problem


@dataclass
class ModelConfig:
    """Configuration for the model API endpoint."""
    
    name: str
    api_base: str
    api_key: str
    input_cost_per_1m: float = 4.0
    output_cost_per_1m: float = 15.0
    timeout: int = 180  # Increased for thinking models
    max_tokens: int = 16384  # Increased for thinking models that use reasoning tokens
    temperature: float = 0.0


@dataclass
class RunConfig:
    """Configuration for a single evaluation run."""
    
    mode: str  # "full", "standard", "quick"
    seed: int
    categories: list[str]  # Category names or ["all"]
    questions_per_category: int
    difficulty_distribution: dict[int, int]  # {difficulty: count}
    timeout: int = 120


@dataclass
class CategoryResult:
    """Results for a single category evaluation."""
    
    name: str
    display_name: str
    total_questions: int
    correct: int
    accuracy_by_difficulty: dict[int, dict]  # {diff: {"correct": int, "total": int}}
    category_score: float
    cliff_index: Optional[int] = None
    errors: list[str] = field(default_factory=list)


@dataclass
class RunResult:
    """Complete results for a FORGE evaluation run."""
    
    run_config: RunConfig
    model_config: ModelConfig
    category_results: list[CategoryResult]
    total_questions: int
    total_correct: int
    forge_score: float
    interpolation_score: float  # Easy/Medium accuracy
    extrapolation_score: float  # Hard/Expert accuracy
    cliff_index: Optional[int]
    total_tokens: int
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    elapsed_time: float


class ForgeRunner:
    """
    Async execution engine for running FORGE evaluations.
    
    Handles:
    - OpenAI-compatible API queries
    - Parallel execution with configurable concurrency
    - Token counting and cost estimation
    - Progress tracking
    """
    
    def __init__(
        self,
        model_config: ModelConfig,
        concurrency: int = 10,
    ):
        self.model_config = model_config
        self.concurrency = concurrency
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.client: Optional[httpx.AsyncClient] = None
        self.errors: list[str] = []
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=self.model_config.api_base,
            headers={
                "Authorization": f"Bearer {self.model_config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(self.model_config.timeout),
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def test_connection(self) -> tuple[bool, str]:
        """
        Test API connection and authentication.
        
        Returns:
            Tuple of (success, message)
        """
        if not self.client:
            return False, "Client not initialized"
        
        try:
            # Try to list models or make a simple request
            response = await self.client.get("/models", timeout=10.0)
            
            if response.status_code == 200:
                return True, "Connection successful"
            elif response.status_code == 401:
                return False, "Authentication failed - invalid API key"
            elif response.status_code == 403:
                return False, "Access forbidden - check API key permissions"
            elif response.status_code == 404:
                # Some APIs don't have /models endpoint, try a minimal completion
                return await self._test_completion()
            else:
                return False, f"Unexpected status code: {response.status_code}"
        
        except httpx.ConnectError:
            return False, f"Cannot connect to {self.model_config.api_base}"
        except httpx.TimeoutException:
            return False, "Connection timeout"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    async def _test_completion(self) -> tuple[bool, str]:
        """Test with a minimal completion request."""
        try:
            payload = {
                "model": self.model_config.name,
                "messages": [{"role": "user", "content": "Say 'OK'"}],
                "max_tokens": 10,
            }
            
            response = await self.client.post("/chat/completions", json=payload)
            
            content_type = response.headers.get("content-type", "")
            
            if response.status_code == 200:
                # Verify it's actually JSON
                if "application/json" not in content_type:
                    return False, f"Expected JSON response but got {content_type}\nResponse: {response.text[:200]}"
                
                try:
                    data = response.json()
                    if "choices" in data:
                        return True, f"Connection successful (completion test passed)\nModel: {self.model_config.name}"
                    else:
                        return False, f"Unexpected response format: {list(data.keys())}"
                except Exception as e:
                    return False, f"Failed to parse JSON: {e}\nResponse: {response.text[:200]}"
            
            elif response.status_code == 401:
                if "application/json" in content_type:
                    try:
                        error_data = response.json()
                        return False, f"Authentication failed: {error_data.get('error', {}).get('message', 'Invalid API key')}"
                    except:
                        pass
                return False, "Authentication failed - invalid API key"
            
            elif response.status_code == 404:
                return False, f"Model '{self.model_config.name}' not found at {self.model_config.api_base}"
            
            else:
                error_msg = f"API returned status {response.status_code}"
                if "application/json" in content_type:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("error", {}).get("message", "")
                        if error_detail:
                            error_msg += f": {error_detail}"
                    except:
                        error_msg += f": {response.text[:200]}"
                else:
                    error_msg += f"\nContent-Type: {content_type}"
                    error_msg += f"\nResponse: {response.text[:200]}"
                return False, error_msg
        
        except httpx.ConnectError:
            return False, f"Cannot connect to {self.model_config.api_base}\nCheck if the URL is correct and the server is running."
        except httpx.TimeoutException:
            return False, "Connection timeout - server took too long to respond"
        except Exception as e:
            return False, f"Completion test failed: {type(e).__name__}: {str(e)}"
    
    async def query_model(self, prompt: str) -> tuple[str, int, int]:
        """
        Query the model with a single prompt.
        
        Args:
            prompt: The problem prompt to send
            
        Returns:
            Tuple of (response_text, input_tokens, output_tokens)
        """
        if not self.client:
            raise RuntimeError("Runner not initialized. Use async context manager.")
        
        payload = {
            "model": self.model_config.name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a precise mathematical reasoning engine. "
                        "Solve the given problem step by step. "
                        "Provide your final answer after 'ANSWER:'. "
                        "The answer should be a single value (number, expression, or short phrase) "
                        "that can be computationally verified."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": self.model_config.max_tokens,
            "temperature": self.model_config.temperature,
        }
        
        try:
            response = await self.client.post("/chat/completions", json=payload)
            
            # Check if response is JSON
            content_type = response.headers.get("content-type", "")
            
            if response.status_code != 200:
                error_msg = f"API error {response.status_code}"
                
                if "application/json" in content_type:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("error", {}).get("message", "")
                        if error_detail:
                            error_msg += f": {error_detail}"
                    except:
                        error_msg += f": {response.text[:200]}"
                else:
                    # Non-JSON response (HTML, etc.)
                    error_msg += f": Received {content_type or 'unknown content type'}"
                    error_msg += f"\nResponse preview: {response.text[:200]}"
                
                self.errors.append(error_msg)
                return f"[ERROR: {error_msg}]", 0, 0
            
            # Try to parse JSON response
            try:
                data = response.json()
            except Exception as json_err:
                error_msg = f"Failed to parse response as JSON: {json_err}"
                error_msg += f"\nContent-Type: {content_type}"
                error_msg += f"\nResponse: {response.text[:300]}"
                self.errors.append(error_msg)
                return f"[ERROR: {error_msg}]", 0, 0
            
            # Extract content from response
            try:
                message = data["choices"][0]["message"]
                content = message.get("content")
                
                # Handle thinking/reasoning models (e.g., Qwen, DeepSeek)
                # These models put the answer in 'content' and thinking in 'reasoning'
                # If content is None but reasoning exists, check if we need more tokens
                if content is None:
                    reasoning = message.get("reasoning", "")
                    if reasoning:
                        # Model is still thinking - content will be populated when done
                        # This usually means max_tokens was too low
                        content = f"[Model reasoning incomplete - increase max_tokens]\nReasoning preview: {reasoning[:200]}"
                    else:
                        content = "[Empty response from model]"
                
                usage = data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                
                # Track reasoning tokens if available
                completion_details = usage.get("completion_tokens_details", {})
                reasoning_tokens = completion_details.get("reasoning_tokens", 0)
                if reasoning_tokens > 0:
                    # Add reasoning tokens to output count for cost calculation
                    output_tokens += reasoning_tokens
                
                return content, input_tokens, output_tokens
            except (KeyError, IndexError) as e:
                error_msg = f"Unexpected response format: {e}"
                error_msg += f"\nResponse keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}"
                error_msg += f"\nResponse: {str(data)[:300]}"
                self.errors.append(error_msg)
                return f"[ERROR: {error_msg}]", 0, 0
        
        except httpx.TimeoutException:
            self.errors.append("Request timeout - model took too long to respond")
            return "[TIMEOUT]", 0, 0
        except httpx.ConnectError:
            error_msg = f"Cannot connect to {self.model_config.api_base}"
            self.errors.append(error_msg)
            return f"[ERROR: {error_msg}]", 0, 0
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.errors.append(error_msg)
            return f"[ERROR: {error_msg}]", 0, 0
    
    def extract_answer(self, response: str) -> str:
        """
        Extract the final answer from a model's response.
        
        Looks for 'ANSWER:' marker, falls back to last line if not found.
        
        Args:
            response: Full model response text
            
        Returns:
            Extracted answer string
        """
        if not response or response.startswith("["):
            return response
        
        # Look for ANSWER: marker
        lines = response.split('\n')
        for line in reversed(lines):
            if 'ANSWER:' in line:
                answer = line.split('ANSWER:', 1)[1].strip()
                if answer:
                    return answer
        
        # Fall back to last non-empty line
        for line in reversed(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                return stripped
        
        return response.strip()
    
    async def run_single(
        self,
        problem: Problem,
        category: ForgeCategory,
    ) -> dict:
        """
        Run a single problem through the model and grade it.
        
        Args:
            problem: The generated Problem instance
            category: The category instance for grading
            
        Returns:
            Dict with problem result details
        """
        start_time = time.time()
        response, input_tokens, output_tokens = await self.query_model(problem.question)
        elapsed = time.time() - start_time
        
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        extracted = self.extract_answer(response)
        
        # Only grade if we got a real response
        is_error = response.startswith("[ERROR") or response.startswith("[TIMEOUT")
        correct = False if is_error else category.grade(extracted, problem.answer)
        
        return {
            "question": problem.question,
            "expected": problem.answer,
            "response": response,
            "extracted": extracted,
            "correct": correct,
            "difficulty": problem.difficulty,
            "iteration": problem.iteration,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "elapsed": elapsed,
            "is_error": is_error,
            "error_message": response if is_error else None,
        }
    
    async def run_category(
        self,
        category: ForgeCategory,
        difficulty_distribution: dict[int, int],
    ) -> CategoryResult:
        """
        Run all problems for a category across difficulty levels.
        
        Args:
            category: The category instance to run
            difficulty_distribution: {difficulty: count} mapping
            
        Returns:
            CategoryResult with aggregated statistics
        """
        problems = []
        for difficulty, count in difficulty_distribution.items():
            for iteration in range(count):
                problem = category.generate(difficulty, iteration)
                problems.append(problem)
        
        # Execute with concurrency limit
        semaphore = asyncio.Semaphore(self.concurrency)
        
        async def run_with_semaphore(problem):
            async with semaphore:
                return await self.run_single(problem, category)
        
        results = await asyncio.gather(
            *[run_with_semaphore(p) for p in problems]
        )
        
        # Aggregate results
        accuracy_by_difficulty = {}
        category_errors = []
        
        for result in results:
            diff = result["difficulty"]
            if diff not in accuracy_by_difficulty:
                accuracy_by_difficulty[diff] = {"correct": 0, "total": 0}
            accuracy_by_difficulty[diff]["total"] += 1
            if result["correct"]:
                accuracy_by_difficulty[diff]["correct"] += 1
            
            if result.get("is_error") and result.get("error_message"):
                category_errors.append(result["error_message"])
        
        total = len(results)
        correct = sum(1 for r in results if r["correct"])
        
        # Compute weighted category score
        category_score = self.compute_category_score(accuracy_by_difficulty)
        cliff_index = self.compute_cliff_index(accuracy_by_difficulty)
        
        # Deduplicate errors
        unique_errors = list(set(category_errors))[:5]  # Keep top 5 unique errors
        
        return CategoryResult(
            name=category.name,
            display_name=category.display_name,
            total_questions=total,
            correct=correct,
            accuracy_by_difficulty=accuracy_by_difficulty,
            category_score=category_score,
            cliff_index=cliff_index,
            errors=unique_errors,
        )
    
    @staticmethod
    def compute_category_score(
        accuracy_by_difficulty: dict[int, dict],
        alpha: float = 1.5,
    ) -> float:
        """
        Compute weighted category score with extrapolation bias.
        
        Formula: C_c = sum(alpha^d * S_{c,d}) / sum(alpha^d)
        where S_{c,d} is accuracy at difficulty d.
        
        Args:
            accuracy_by_difficulty: {difficulty: {"correct": int, "total": int}}
            alpha: Extrapolation weight parameter (default 1.5)
            
        Returns:
            Weighted category score between 0.0 and 1.0
        """
        if not accuracy_by_difficulty:
            return 0.0
        
        numerator = 0.0
        denominator = 0.0
        
        for difficulty, stats in accuracy_by_difficulty.items():
            if stats["total"] > 0:
                accuracy = stats["correct"] / stats["total"]
                weight = alpha ** difficulty
                numerator += weight * accuracy
                denominator += weight
        
        return numerator / denominator if denominator > 0 else 0.0
    
    @staticmethod
    def compute_cliff_index(
        accuracy_by_difficulty: dict[int, dict],
        threshold: float = 0.3,
    ) -> Optional[int]:
        """
        Find the difficulty level where accuracy drops by more than threshold.
        
        The "Complexity Cliff Index" identifies where a model's internal
        world-model collapses, as described in the Illusion of Thinking.
        
        Args:
            accuracy_by_difficulty: {difficulty: {"correct": int, "total": int}}
            threshold: Accuracy drop threshold (default 0.3 for 30%)
            
        Returns:
            Difficulty level where cliff occurs, or None if no cliff detected
        """
        if not accuracy_by_difficulty:
            return None
        
        sorted_diffs = sorted(accuracy_by_difficulty.keys())
        prev_accuracy = None
        
        for diff in sorted_diffs:
            stats = accuracy_by_difficulty[diff]
            if stats["total"] > 0:
                accuracy = stats["correct"] / stats["total"]
                if prev_accuracy is not None:
                    if prev_accuracy - accuracy > threshold:
                        return diff
                prev_accuracy = accuracy
        
        return None
    
    def compute_cost(self) -> float:
        """
        Compute estimated API cost based on token counts.
        
        Returns:
            Estimated cost in dollars
        """
        input_cost = (self.total_input_tokens / 1_000_000) * self.model_config.input_cost_per_1m
        output_cost = (self.total_output_tokens / 1_000_000) * self.model_config.output_cost_per_1m
        return input_cost + output_cost
    
    @staticmethod
    def compute_forge_score(category_results: list[CategoryResult]) -> float:
        """
        Compute the final FORGE score as unweighted average of category scores.
        
        Args:
            category_results: List of CategoryResult instances
            
        Returns:
            Final FORGE score between 0.0 and 1.0
        """
        if not category_results:
            return 0.0
        
        scores = [cr.category_score for cr in category_results]
        return sum(scores) / len(scores)
    
    @staticmethod
    def compute_interpolation_extrapolation(
        category_results: list[CategoryResult],
    ) -> tuple[float, float]:
        """
        Compute separate scores for interpolation (Easy/Medium) and 
        extrapolation (Hard/Expert) zones.
        
        Returns:
            Tuple of (interpolation_score, extrapolation_score)
        """
        interpolation_correct = 0
        interpolation_total = 0
        extrapolation_correct = 0
        extrapolation_total = 0
        
        for result in category_results:
            for diff, stats in result.accuracy_by_difficulty.items():
                if diff <= 2:  # Easy/Medium
                    interpolation_correct += stats["correct"]
                    interpolation_total += stats["total"]
                else:  # Hard/Expert
                    extrapolation_correct += stats["correct"]
                    extrapolation_total += stats["total"]
        
        interp = interpolation_correct / interpolation_total if interpolation_total > 0 else 0.0
        extra = extrapolation_correct / extrapolation_total if extrapolation_total > 0 else 0.0
        
        return interp, extra
