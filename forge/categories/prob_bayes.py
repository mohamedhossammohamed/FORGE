"""
Category 20: Probability - Bayesian Updating

Generates multi-stage conditional probability scenarios.
Difficulty scales from undergraduate (1 update) to frontier (4 sequential updates).
"""

from fractions import Fraction

from ..core.generator import ForgeCategory, Problem


class ProbBayesCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "prob_bayes"
    
    @property
    def display_name(self) -> str:
        return "Probability: Bayesian Updating"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"n_stages": 1, "use_counterintuitive": False},
            2: {"n_stages": 1, "use_counterintuitive": True},
            3: {"n_stages": 2, "use_counterintuitive": True},
            4: {"n_stages": 3, "use_counterintuitive": True},
            5: {"n_stages": 4, "use_counterintuitive": True},
        }
        return params.get(difficulty, params[3])
    
    def _generate_rates(self, rng, counterintuitive=False):
        """Generate test rates that may be counterintuitive."""
        if counterintuitive:
            # Low prevalence, high false positive
            prevalence = Fraction(int(rng.integers(1, 10)), 100)
            sensitivity = Fraction(int(rng.integers(80, 99)), 100)
            specificity = Fraction(int(rng.integers(70, 95)), 100)
        else:
            prevalence = Fraction(int(rng.integers(10, 50)), 100)
            sensitivity = Fraction(int(rng.integers(80, 99)), 100)
            specificity = Fraction(int(rng.integers(80, 99)), 100)
        
        return prevalence, sensitivity, specificity
    
    def _bayes_update(self, prior: Fraction, sensitivity: Fraction, 
                     specificity: Fraction) -> Fraction:
        """Single Bayesian update: P(Disease | Positive Test)."""
        # P(D|+) = P(+|D) * P(D) / P(+)
        # P(+) = P(+|D)*P(D) + P(+|~D)*P(~D)
        false_positive_rate = 1 - specificity
        
        numerator = sensitivity * prior
        denominator = sensitivity * prior + false_positive_rate * (1 - prior)
        
        return numerator / denominator
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        n_stages = params["n_stages"]
        counterintuitive = params["use_counterintuitive"]
        
        stages = []
        prior = Fraction(int(rng.integers(10, 50)), 100)
        
        for i in range(n_stages):
            prevalence, sensitivity, specificity = self._generate_rates(
                rng, counterintuitive
            )
            stages.append({
                "prevalence": prevalence,
                "sensitivity": sensitivity,
                "specificity": specificity,
            })
        
        # Build question
        scenario = "A disease screening program has the following characteristics:\n\n"
        
        for i, stage in enumerate(stages):
            scenario += (
                f"Stage {i+1}:\n"
                f"  - Prevalence: {float(stage['prevalence']*100):.1f}%\n"
                f"  - Sensitivity (true positive rate): {float(stage['sensitivity']*100):.1f}%\n"
                f"  - Specificity (true negative rate): {float(stage['specificity']*100):.1f}%\n\n"
            )
        
        # Compute final posterior
        current_prior = stages[0]["prevalence"]
        for stage in stages:
            current_prior = self._bayes_update(
                current_prior,
                stage["sensitivity"],
                stage["specificity"]
            )
        
        # Format answer as fraction
        answer = str(current_prior)
        
        scenario += (
            f"A person tests positive through all {n_stages} stage(s).\n\n"
            f"What is the probability that they actually have the disease?\n"
            f"Provide your answer as an exact fraction (e.g., 123/4567)."
        )
        
        question = scenario
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={
                "n_stages": n_stages,
                "stages": stages,
                "posterior": str(current_prior),
            },
        )
    
    def grade(self, prediction: str, answer: str) -> bool:
        """Grade using exact fraction comparison."""
        try:
            pred = prediction.strip()
            if '/' in pred:
                pred_frac = Fraction(pred)
            else:
                pred_frac = Fraction(pred).limit_denominator(10**12)
            
            ans_frac = Fraction(answer)
            
            return pred_frac == ans_frac
        except (ValueError, TypeError):
            return False
