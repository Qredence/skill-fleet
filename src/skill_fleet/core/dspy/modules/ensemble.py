"""Ensemble methods for DSPy modules.

Combines multiple module executions or optimized programs for improved quality.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import dspy

logger = logging.getLogger(__name__)


class EnsembleModule(dspy.Module):
    """Ensemble multiple DSPy modules with voting/selection strategy.
    
    Executes multiple modules in parallel and selects best result using
    a voting or scoring function.
    
    Example:
        # Create multiple generators
        gen1 = dspy.ChainOfThought("task -> output")
        gen2 = dspy.ChainOfThought("task -> output") 
        gen3 = dspy.ChainOfThought("task -> output")
        
        # Ensemble with quality-based selection
        ensemble = EnsembleModule(
            modules=[gen1, gen2, gen3],
            selector=lambda results: max(results, key=lambda r: score(r))
        )
        
        result = ensemble(task="Generate skill")  # Returns best of 3
    """
    
    def __init__(
        self,
        modules: list[dspy.Module],
        selector: Callable[[list[dspy.Prediction]], dspy.Prediction] | None = None,
        parallel: bool = True,
    ) -> None:
        """Initialize ensemble.
        
        Args:
            modules: List of DSPy modules to ensemble (2-5 recommended)
            selector: Function to select best result from list (default: first)
            parallel: Whether to execute modules in parallel (faster)
        """
        super().__init__()
        self.modules = modules
        self.selector = selector or (lambda results: results[0])
        self.parallel = parallel
        
        if len(modules) < 2:
            logger.warning("Ensemble with <2 modules has no benefit")
    
    def forward(self, **kwargs: Any) -> dspy.Prediction:
        """Execute all modules and select best result.
        
        Args:
            **kwargs: Input parameters passed to each module
        
        Returns:
            Selected best prediction from ensemble
        """
        if self.parallel:
            # Execute all modules
            results = []
            for i, module in enumerate(self.modules):
                try:
                    result = module(**kwargs)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Module {i} in ensemble failed: {e}")
            
            if not results:
                raise RuntimeError("All modules in ensemble failed")
        else:
            # Sequential execution (useful for debugging)
            results = []
            for module in self.modules:
                result = module(**kwargs)
                results.append(result)
        
        # Select best result
        try:
            best = self.selector(results)
            logger.debug(f"Ensemble selected result from {len(results)} candidates")
            return best
        except Exception as e:
            logger.error(f"Ensemble selector failed: {e}, returning first result")
            return results[0]


class BestOfN(dspy.Module):
    """Generate N candidates and select best using quality metric.
    
    Specialized ensemble for generating multiple outputs and selecting
    highest-quality result. Common pattern in DSPy for critical generations.
    
    Example:
        generator = dspy.ChainOfThought("task -> skill_content")
        best_of_3 = BestOfN(
            module=generator,
            n=3,
            quality_fn=lambda x: score_skill_quality(x.skill_content)
        )
        
        result = best_of_3(task="Create async skill")  # Best of 3 attempts
    """
    
    def __init__(
        self,
        module: dspy.Module,
        n: int = 3,
        quality_fn: Callable[[dspy.Prediction], float] | None = None,
    ) -> None:
        """Initialize BestOfN.
        
        Args:
            module: DSPy module to execute N times
            n: Number of candidates to generate (2-5 recommended)
            quality_fn: Function to score prediction quality (higher is better)
        """
        super().__init__()
        self.module = module
        self.n = n
        self.quality_fn = quality_fn or (lambda _: 0.5)
        
        if n < 2:
            raise ValueError("BestOfN requires n >= 2")
    
    def forward(self, **kwargs: Any) -> dspy.Prediction:
        """Generate N candidates and return highest quality.
        
        Args:
            **kwargs: Input parameters for module
        
        Returns:
            Highest quality prediction
        """
        candidates = []
        scores = []
        
        logger.info(f"Generating {self.n} candidates...")
        
        for i in range(self.n):
            try:
                candidate = self.module(**kwargs)
                score = self.quality_fn(candidate)
                
                candidates.append(candidate)
                scores.append(score)
                
                logger.debug(f"Candidate {i+1}: quality={score:.3f}")
            
            except Exception as e:
                logger.warning(f"Candidate {i+1} generation failed: {e}")
        
        if not candidates:
            raise RuntimeError(f"All {self.n} candidate generations failed")
        
        # Select best candidate
        best_idx = scores.index(max(scores))
        best_score = scores[best_idx]
        
        logger.info(
            f"Selected candidate {best_idx+1}/{len(candidates)} "
            f"(quality={best_score:.3f})"
        )
        
        return candidates[best_idx]


class MajorityVote(dspy.Module):
    """Ensemble with majority voting for classification tasks.
    
    Executes multiple modules and returns most common prediction.
    Useful for classification, sentiment analysis, or binary decisions.
    
    Example:
        classifiers = [model1, model2, model3]
        voter = MajorityVote(
            modules=classifiers,
            vote_field="category"  // Field to vote on
        )
        
        result = voter(text="Sample text")  // Returns most common category
    """
    
    def __init__(
        self,
        modules: list[dspy.Module],
        vote_field: str,
        min_agreement: float = 0.5,
    ) -> None:
        """Initialize majority vote ensemble.
        
        Args:
            modules: List of modules to ensemble
            vote_field: Name of field to vote on
            min_agreement: Minimum agreement fraction (0-1) to accept result
        """
        super().__init__()
        self.modules = modules
        self.vote_field = vote_field
        self.min_agreement = min_agreement
    
    def forward(self, **kwargs: Any) -> dspy.Prediction:
        """Execute all modules and return majority vote.
        
        Args:
            **kwargs: Input parameters
        
        Returns:
            Prediction with majority vote and confidence
        """
        from collections import Counter
        
        results = []
        votes = []
        
        for module in self.modules:
            try:
                result = module(**kwargs)
                results.append(result)
                
                if hasattr(result, self.vote_field):
                    vote = getattr(result, self.vote_field)
                    votes.append(vote)
            except Exception as e:
                logger.warning(f"Module in voting ensemble failed: {e}")
        
        if not votes:
            raise RuntimeError("No modules produced votable results")
        
        # Count votes
        vote_counts = Counter(votes)
        winner, winner_count = vote_counts.most_common(1)[0]
        
        agreement = winner_count / len(votes)
        
        logger.info(
            f"Majority vote: {winner} ({winner_count}/{len(votes)} votes, "
            f"agreement={agreement:.2%})"
        )
        
        # Check minimum agreement threshold
        if agreement < self.min_agreement:
            logger.warning(
                f"Low agreement ({agreement:.2%} < {self.min_agreement:.2%}), "
                "result may be unreliable"
            )
        
        # Return first result with winning vote
        for result in results:
            if hasattr(result, self.vote_field) and getattr(result, self.vote_field) == winner:
                # Add ensemble metadata
                result._ensemble_agreement = agreement
                result._ensemble_votes = winner_count
                result._ensemble_total = len(votes)
                return result
        
        # Fallback: return first result
        return results[0]
