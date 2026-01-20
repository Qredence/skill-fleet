"""Optimizer Auto-Selection Engine.

Intelligently recommends the best DSPy optimizer based on task characteristics,
budget constraints, and historical performance data.

Decision Rules (from optimization plan):
- trainset < 100 AND budget < $5 → GEPA (fast, reflection-based)
- trainset < 500 AND budget < $20 → MIPROv2 auto="light"
- trainset >= 500 AND budget >= $20 → MIPROv2 auto="medium"
- budget > $100 → MIPROv2 auto="heavy" or BootstrapFinetune
- Fallback: BootstrapFewShot (always works)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)


class OptimizerType(str, Enum):
    """Available optimizer types."""

    BOOTSTRAP_FEWSHOT = "bootstrap_fewshot"
    MIPROV2 = "miprov2"
    GEPA = "gepa"
    REFLECTION_METRICS = "reflection_metrics"
    BOOTSTRAP_FINETUNE = "bootstrap_finetune"


@dataclass
class OptimizerContext:
    """Context for optimizer selection decision.

    Attributes:
        trainset_size: Number of training examples available
        budget_dollars: Maximum budget in USD
        quality_target: Target quality score (0.0-1.0)
        complexity_score: Task complexity (0.0-1.0, higher = more complex)
        domain: Skill domain/category
        time_constraint_minutes: Maximum time allowed (optional)
        previous_optimizer: Last optimizer used (for iteration)
        historical_quality: Quality from previous optimization runs
    """

    trainset_size: int
    budget_dollars: float = 10.0
    quality_target: float = 0.85
    complexity_score: float = 0.5
    domain: str = "general"
    time_constraint_minutes: int | None = None
    previous_optimizer: str | None = None
    historical_quality: float | None = None


@dataclass
class OptimizerConfig:
    """Configuration for a specific optimizer."""

    auto: Literal["light", "medium", "heavy"] = "medium"
    max_bootstrapped_demos: int = 4
    max_labeled_demos: int = 4
    num_threads: int = 8
    num_candidates: int = 10  # For GEPA
    num_iters: int = 3  # For GEPA


@dataclass
class OptimizerRecommendation:
    """Result of optimizer selection.

    Attributes:
        recommended: The recommended optimizer type
        config: Suggested configuration for the optimizer
        estimated_cost: Estimated cost in USD
        estimated_time_minutes: Estimated time to complete
        confidence: Confidence in recommendation (0.0-1.0)
        reasoning: Human-readable explanation
        alternatives: Other viable options with trade-offs
    """

    recommended: OptimizerType
    config: OptimizerConfig
    estimated_cost: float
    estimated_time_minutes: int
    confidence: float
    reasoning: str
    alternatives: list[dict[str, Any]] = field(default_factory=list)


class OptimizerSelector:
    """Intelligent optimizer selection based on task characteristics.

    Decision Rules:
    - trainset < 100 AND budget < $5 → GEPA (fast, reflection-based)
    - trainset < 500 AND budget < $20 → MIPROv2 auto="light"
    - trainset >= 500 AND budget >= $20 → MIPROv2 auto="medium"
    - budget > $100 → MIPROv2 auto="heavy" or BootstrapFinetune
    - Fallback: BootstrapFewShot (always works)

    Additional considerations:
    - Time constraints
    - Previous optimizer performance
    - Domain-specific patterns
    """

    # Cost estimates per optimizer (USD per 100 examples)
    COST_ESTIMATES: dict[OptimizerType, float] = {
        OptimizerType.BOOTSTRAP_FEWSHOT: 0.10,
        OptimizerType.REFLECTION_METRICS: 0.05,
        OptimizerType.GEPA: 0.50,
        OptimizerType.MIPROV2: 2.50,  # light
        OptimizerType.BOOTSTRAP_FINETUNE: 20.00,
    }

    # Time estimates per optimizer (minutes per 100 examples)
    TIME_ESTIMATES: dict[OptimizerType, int] = {
        OptimizerType.BOOTSTRAP_FEWSHOT: 1,
        OptimizerType.REFLECTION_METRICS: 1,
        OptimizerType.GEPA: 5,
        OptimizerType.MIPROV2: 15,  # medium
        OptimizerType.BOOTSTRAP_FINETUNE: 60,
    }

    # MIPROv2 auto setting cost multipliers
    MIPRO_MULTIPLIERS: dict[str, float] = {
        "light": 0.5,
        "medium": 1.0,
        "heavy": 2.5,
    }

    def __init__(self, metrics_path: str | None = None):
        """Initialize selector.

        Args:
            metrics_path: Path to historical metrics JSONL file
        """
        self.metrics_path = metrics_path
        self._historical_data: list[dict[str, Any]] = []
        if metrics_path:
            self._load_historical_data()

    def _load_historical_data(self) -> None:
        """Load historical optimization metrics."""
        path = Path(self.metrics_path) if self.metrics_path else None
        if path and path.exists():
            try:
                with open(path) as f:
                    for line in f:
                        if line.strip():
                            self._historical_data.append(json.loads(line))
                logger.info(f"Loaded {len(self._historical_data)} historical records")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load historical data: {e}")

    def recommend(self, context: OptimizerContext) -> OptimizerRecommendation:
        """Recommend best optimizer for the given context.

        Args:
            context: Task and budget context

        Returns:
            OptimizerRecommendation with suggested optimizer and config
        """
        # Apply decision tree
        optimizer, config, reasoning = self._apply_decision_rules(context)

        # Calculate estimates
        cost = self._estimate_cost(optimizer, config, context.trainset_size)
        time_mins = self._estimate_time(optimizer, config, context.trainset_size)

        # Calculate confidence based on historical data match
        confidence = self._calculate_confidence(context, optimizer)

        # Generate alternatives
        alternatives = self._generate_alternatives(context, optimizer)

        return OptimizerRecommendation(
            recommended=optimizer,
            config=config,
            estimated_cost=cost,
            estimated_time_minutes=time_mins,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=alternatives,
        )

    def _apply_decision_rules(
        self, context: OptimizerContext
    ) -> tuple[OptimizerType, OptimizerConfig, str]:
        """Apply decision tree to select optimizer.

        Returns:
            Tuple of (optimizer_type, config, reasoning)
        """
        trainset = context.trainset_size
        budget = context.budget_dollars
        quality_target = context.quality_target
        time_limit = context.time_constraint_minutes

        # Rule 1: Very tight time constraint → Reflection Metrics
        if time_limit and time_limit < 2:
            return (
                OptimizerType.REFLECTION_METRICS,
                OptimizerConfig(),
                f"Time constraint ({time_limit}min) requires fastest optimizer. "
                "Reflection Metrics completes in <1 second.",
            )

        # Rule 2: Very low budget → GEPA or Reflection Metrics
        if budget < 1.0:
            return (
                OptimizerType.REFLECTION_METRICS,
                OptimizerConfig(),
                f"Budget (${budget:.2f}) is very low. "
                "Reflection Metrics costs ~$0.01-0.05 per run.",
            )

        # Rule 3: Low budget + small trainset → GEPA
        if trainset < 100 and budget < 5.0:
            return (
                OptimizerType.GEPA,
                OptimizerConfig(num_candidates=5, num_iters=2),
                f"Small trainset ({trainset}) + low budget (${budget:.2f}). "
                "GEPA is fast and cost-effective for this scenario.",
            )

        # Rule 4: Medium budget + medium trainset → MIPROv2 light
        if trainset < 500 and budget < 20.0:
            return (
                OptimizerType.MIPROV2,
                OptimizerConfig(auto="light", max_bootstrapped_demos=2),
                f"Medium trainset ({trainset}) + moderate budget (${budget:.2f}). "
                "MIPROv2 'light' provides good quality/cost balance.",
            )

        # Rule 5: Large trainset + good budget → MIPROv2 medium
        if trainset >= 500 and budget >= 20.0 and budget < 100.0:
            return (
                OptimizerType.MIPROV2,
                OptimizerConfig(auto="medium", max_bootstrapped_demos=4),
                f"Large trainset ({trainset}) + good budget (${budget:.2f}). "
                "MIPROv2 'medium' maximizes quality within budget.",
            )

        # Rule 6: High budget → MIPROv2 heavy or BootstrapFinetune
        if budget >= 100.0:
            if quality_target >= 0.95:
                return (
                    OptimizerType.BOOTSTRAP_FINETUNE,
                    OptimizerConfig(),
                    f"High budget (${budget:.2f}) + high quality target ({quality_target}). "
                    "BootstrapFinetune provides maximum quality through weight tuning.",
                )
            return (
                OptimizerType.MIPROV2,
                OptimizerConfig(auto="heavy", max_bootstrapped_demos=6, max_labeled_demos=6),
                f"High budget (${budget:.2f}) allows thorough optimization. "
                "MIPROv2 'heavy' maximizes prompt quality.",
            )

        # Fallback: BootstrapFewShot (always works, cheap)
        return (
            OptimizerType.BOOTSTRAP_FEWSHOT,
            OptimizerConfig(max_bootstrapped_demos=3),
            "Default fallback: BootstrapFewShot is reliable and cheap. "
            "Good baseline for any scenario.",
        )

    def _estimate_cost(
        self,
        optimizer: OptimizerType,
        config: OptimizerConfig,
        trainset_size: int,
    ) -> float:
        """Estimate optimization cost in USD."""
        base_cost = self.COST_ESTIMATES.get(optimizer, 1.0)

        # Scale by trainset size (per 100 examples)
        scale = trainset_size / 100.0

        # Apply MIPROv2 auto multiplier if applicable
        if optimizer == OptimizerType.MIPROV2:
            multiplier = self.MIPRO_MULTIPLIERS.get(config.auto, 1.0)
            base_cost *= multiplier

        return round(base_cost * scale, 2)

    def _estimate_time(
        self,
        optimizer: OptimizerType,
        config: OptimizerConfig,
        trainset_size: int,
    ) -> int:
        """Estimate optimization time in minutes."""
        base_time = self.TIME_ESTIMATES.get(optimizer, 10)

        # Scale by trainset size (per 100 examples)
        scale = trainset_size / 100.0

        # Apply MIPROv2 auto multiplier if applicable
        if optimizer == OptimizerType.MIPROV2:
            multiplier = self.MIPRO_MULTIPLIERS.get(config.auto, 1.0)
            base_time = int(base_time * multiplier)

        return max(1, int(base_time * scale))

    def _calculate_confidence(self, context: OptimizerContext, optimizer: OptimizerType) -> float:
        """Calculate confidence in recommendation (0.0-1.0)."""
        base_confidence = 0.75

        # Boost if we have historical data
        if self._historical_data:
            matching = [
                r
                for r in self._historical_data
                if r.get("domain") == context.domain and r.get("optimizer") == optimizer.value
            ]
            if matching:
                # Average success rate from matching records
                successes = sum(1 for r in matching if r.get("quality", 0) >= 0.8)
                base_confidence = min(0.95, base_confidence + 0.1 * (successes / len(matching)))

        # Reduce confidence for edge cases
        if context.trainset_size < 20:
            base_confidence *= 0.8  # Very small trainset = less confident

        return round(base_confidence, 2)

    def _generate_alternatives(
        self, context: OptimizerContext, primary: OptimizerType
    ) -> list[dict[str, Any]]:
        """Generate alternative optimizer recommendations."""
        alternatives: list[dict[str, Any]] = []

        # Always include fast option
        if primary != OptimizerType.REFLECTION_METRICS:
            cost = self._estimate_cost(
                OptimizerType.REFLECTION_METRICS,
                OptimizerConfig(),
                context.trainset_size,
            )
            alternatives.append(
                {
                    "optimizer": OptimizerType.REFLECTION_METRICS.value,
                    "cost": f"${cost:.2f}",
                    "time": "< 1 min",
                    "quality_risk": 0.15,
                    "note": "Fastest option, may sacrifice some quality",
                }
            )

        # Include upgrade option if budget allows
        if context.budget_dollars >= 20 and primary == OptimizerType.GEPA:
            alternatives.append(
                {
                    "optimizer": OptimizerType.MIPROV2.value,
                    "cost": f"${self._estimate_cost(OptimizerType.MIPROV2, OptimizerConfig(auto='light'), context.trainset_size):.2f}",
                    "time": f"{self._estimate_time(OptimizerType.MIPROV2, OptimizerConfig(auto='light'), context.trainset_size)} min",
                    "quality_risk": -0.10,  # Negative = quality improvement
                    "note": "Higher quality, moderate cost increase",
                }
            )

        # Include safe fallback
        if primary != OptimizerType.BOOTSTRAP_FEWSHOT:
            cost = self._estimate_cost(
                OptimizerType.BOOTSTRAP_FEWSHOT,
                OptimizerConfig(),
                context.trainset_size,
            )
            alternatives.append(
                {
                    "optimizer": OptimizerType.BOOTSTRAP_FEWSHOT.value,
                    "cost": f"${cost:.2f}",
                    "time": f"{self._estimate_time(OptimizerType.BOOTSTRAP_FEWSHOT, OptimizerConfig(), context.trainset_size)} min",
                    "quality_risk": 0.10,
                    "note": "Safe fallback, always works",
                }
            )

        return alternatives[:3]  # Max 3 alternatives

    def record_result(
        self,
        context: OptimizerContext,
        optimizer: OptimizerType,
        actual_cost: float,
        actual_time_minutes: int,
        quality_score: float,
    ) -> None:
        """Record optimization result for future learning.

        Args:
            context: Original context used for selection
            optimizer: Optimizer that was used
            actual_cost: Actual cost incurred
            actual_time_minutes: Actual time taken
            quality_score: Resulting quality score
        """
        if not self.metrics_path:
            return

        record = {
            "timestamp": datetime.now().isoformat(),
            "trainset_size": context.trainset_size,
            "budget": context.budget_dollars,
            "quality_target": context.quality_target,
            "domain": context.domain,
            "optimizer": optimizer.value,
            "actual_cost": actual_cost,
            "actual_time": actual_time_minutes,
            "quality": quality_score,
        }

        path = Path(self.metrics_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "a") as f:
            f.write(json.dumps(record) + "\n")

        self._historical_data.append(record)
        logger.info(f"Recorded optimization result: {optimizer.value} → quality={quality_score}")
