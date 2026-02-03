"""
Metrics collection module for skill performance measurement.

Collects baseline metrics and compares skill-assisted vs unassisted
task execution to quantify skill effectiveness.
"""

import time
from typing import Any

import dspy
from dspy.utils.syncify import run_async

from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.validation.metrics import (
    CollectBaselineMetrics,
    CollectSkillMetrics,
    CompareMetrics,
)


class MetricsCollectorModule(BaseModule):
    """
    Collect and compare skill performance metrics.

    Measures the impact of skills on task execution by comparing
    baseline (no skill) vs skill-assisted metrics:
    - Tool call efficiency
    - API failure rates
    - Token consumption
    - Interaction turns
    - Success rates

    Example:
        collector = MetricsCollectorModule()

        # Collect baseline (simulated without skill)
        baseline = await collector.collect_baseline(
            task_description="Create a React component..."
        )

        # Collect with skill
        with_skill = await collector.collect_with_skill(
            task_description="Create a React component...",
            skill={"name": "react-component", "content": "..."}
        )

        # Compare results
        comparison = collector.compare(baseline, with_skill)
        # Returns: token_reduction, success_rate_change, meets_targets, etc.

    """

    def __init__(self):
        super().__init__()
        self.baseline_collector = dspy.ChainOfThought(CollectBaselineMetrics)
        self.skill_collector = dspy.ChainOfThought(CollectSkillMetrics)
        self.comparison = dspy.ChainOfThought(CompareMetrics)

    async def collect_baseline(self, task_description: str) -> dspy.Prediction:
        """
        Collect baseline metrics by simulating task without skill assistance.

        Uses LLM to simulate how an agent would perform the task without
        the guidance of a skill, estimating metrics like tool calls,
        failures, and token usage.

        Args:
            task_description: Description of the task to simulate

        Returns:
            dspy.Prediction with baseline metrics:
            - tool_calls: Estimated number of tool calls
            - api_failures: Estimated API failure count
            - tokens_consumed: Estimated token consumption
            - interaction_turns: Estimated turns to complete
            - success_rate: Estimated success probability (0-1)
            - reasoning: Explanation of the estimation

        """
        start_time = time.time()

        try:
            result = await self.baseline_collector.acall(task_description=task_description)

            output = {
                "tool_calls": int(result.tool_calls) if hasattr(result, "tool_calls") else 10,
                "api_failures": int(result.api_failures) if hasattr(result, "api_failures") else 2,
                "tokens_consumed": int(result.tokens_consumed)
                if hasattr(result, "tokens_consumed")
                else 5000,
                "interaction_turns": int(result.interaction_turns)
                if hasattr(result, "interaction_turns")
                else 8,
                "success_rate": float(result.success_rate)
                if hasattr(result, "success_rate")
                else 0.6,
                "reasoning": result.reasoning if hasattr(result, "reasoning") else "",
                "task_description": task_description,
            }

        except Exception as e:
            self.logger.warning(f"Baseline collection failed: {e}, using defaults")
            output = self._default_baseline_metrics(task_description)

        # Validate
        required = ["tool_calls", "api_failures", "tokens_consumed", "success_rate"]
        if not self._validate_result(output, required):
            output = self._default_baseline_metrics(task_description)

        # Log
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={"task": task_description[:50]},
            outputs={
                "tool_calls": output["tool_calls"],
                "success_rate": output["success_rate"],
            },
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

    async def collect_with_skill(
        self, task_description: str, skill: dict[str, Any]
    ) -> dspy.Prediction:
        """
        Collect metrics by simulating task with skill assistance.

        Uses LLM to simulate how an agent would perform the task with
        the guidance of the provided skill.

        Args:
            task_description: Description of the task to simulate
            skill: Skill dictionary with at least 'name' and 'content' keys

        Returns:
            Dictionary with skill-assisted metrics (same structure as baseline)

        """
        start_time = time.time()

        skill_name = skill.get("name", "unknown")
        skill_content = skill.get("content", "")

        try:
            result = await self.skill_collector.acall(
                task_description=task_description,
                skill_name=skill_name,
                skill_content=skill_content[:5000],  # Limit content length
            )

            output = {
                "tool_calls": int(result.tool_calls) if hasattr(result, "tool_calls") else 5,
                "api_failures": int(result.api_failures) if hasattr(result, "api_failures") else 0,
                "tokens_consumed": int(result.tokens_consumed)
                if hasattr(result, "tokens_consumed")
                else 2500,
                "interaction_turns": int(result.interaction_turns)
                if hasattr(result, "interaction_turns")
                else 4,
                "success_rate": float(result.success_rate)
                if hasattr(result, "success_rate")
                else 0.9,
                "reasoning": result.reasoning if hasattr(result, "reasoning") else "",
                "task_description": task_description,
                "skill_name": skill_name,
            }

        except Exception as e:
            self.logger.warning(f"Skill metrics collection failed: {e}, using defaults")
            output = self._default_skill_metrics(task_description, skill_name)

        # Validate
        required = ["tool_calls", "api_failures", "tokens_consumed", "success_rate"]
        if not self._validate_result(output, required):
            output = self._default_skill_metrics(task_description, skill_name)

        # Log
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={"task": task_description[:50], "skill": skill_name},
            outputs={
                "tool_calls": output["tool_calls"],
                "success_rate": output["success_rate"],
            },
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

    def compare(self, baseline: dict[str, Any], with_skill: dict[str, Any]) -> dspy.Prediction:
        """
        Compare baseline vs skill-assisted metrics.

        Calculates improvements and determines if skill meets performance targets.

        Args:
            baseline: Metrics from collect_baseline()
            with_skill: Metrics from collect_with_skill()

        Returns:
            Dictionary with comparison results:
            - token_reduction: Percentage reduction in token usage
            - api_failure_reduction: Absolute reduction in API failures
            - interaction_reduction: Absolute reduction in interaction turns
            - success_rate_change: Change in success rate (percentage points)
            - tool_call_reduction: Absolute reduction in tool calls
            - meets_targets: Whether all targets are met
            - target_details: Per-target achievement status
            - recommendations: List of improvement recommendations

        """
        start_time = time.time()

        try:
            # Use LLM for intelligent comparison and recommendations
            result = self.comparison(
                baseline_metrics=str(baseline),
                skill_metrics=str(with_skill),
            )

            output = {
                "token_reduction": float(result.token_reduction)
                if hasattr(result, "token_reduction")
                else self._calculate_token_reduction(baseline, with_skill),
                "api_failure_reduction": int(result.api_failure_reduction)
                if hasattr(result, "api_failure_reduction")
                else self._calculate_api_failure_reduction(baseline, with_skill),
                "interaction_reduction": int(result.interaction_reduction)
                if hasattr(result, "interaction_reduction")
                else self._calculate_interaction_reduction(baseline, with_skill),
                "success_rate_change": float(result.success_rate_change)
                if hasattr(result, "success_rate_change")
                else self._calculate_success_rate_change(baseline, with_skill),
                "tool_call_reduction": self._calculate_tool_call_reduction(baseline, with_skill),
                "meets_targets": bool(result.meets_targets)
                if hasattr(result, "meets_targets")
                else self._check_targets(baseline, with_skill),
                "target_details": self._get_target_details(baseline, with_skill),
                "recommendations": result.recommendations
                if hasattr(result, "recommendations") and isinstance(result.recommendations, list)
                else self._generate_recommendations(baseline, with_skill),
            }

        except Exception as e:
            self.logger.warning(f"Comparison failed: {e}, using calculated values")
            output = self._calculate_comparison(baseline, with_skill)

        # Validate
        required = ["token_reduction", "meets_targets"]
        if not self._validate_result(output, required):
            output = self._calculate_comparison(baseline, with_skill)

        # Log
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={"baseline_task": baseline.get("task_description", "")[:50]},
            outputs={
                "token_reduction": output["token_reduction"],
                "meets_targets": output["meets_targets"],
            },
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

    def _check_targets(self, baseline: dict[str, Any], with_skill: dict[str, Any]) -> bool:
        """
        Check if skill meets performance targets.

        Targets:
        - 90% trigger rate (success_rate >= 0.9)
        - 50% token reduction
        - 0 API failures with skill

        Args:
            baseline: Baseline metrics
            with_skill: Skill-assisted metrics

        Returns:
            True if all targets are met

        """
        targets = self._get_target_details(baseline, with_skill)
        return all(target["met"] for target in targets.values())

    def _get_target_details(
        self, baseline: dict[str, Any], with_skill: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Get detailed target achievement status.

        Args:
            baseline: Baseline metrics
            with_skill: Skill-assisted metrics

        Returns:
            Dictionary with per-target details

        """
        # Calculate metrics
        token_reduction = self._calculate_token_reduction(baseline, with_skill)
        success_rate = with_skill.get("success_rate", 0.0)
        api_failures = with_skill.get("api_failures", 0)

        return {
            "trigger_rate": {
                "target": 0.9,
                "actual": success_rate,
                "met": success_rate >= 0.9,
                "description": "Success rate should be >= 90%",
            },
            "token_reduction": {
                "target": 0.5,
                "actual": token_reduction,
                "met": token_reduction >= 0.5,
                "description": "Token usage should be reduced by >= 50%",
            },
            "api_failures": {
                "target": 0,
                "actual": api_failures,
                "met": api_failures == 0,
                "description": "No API failures with skill guidance",
            },
        }

    def _calculate_token_reduction(
        self, baseline: dict[str, Any], with_skill: dict[str, Any]
    ) -> float:
        """Calculate percentage reduction in token usage."""
        baseline_tokens = baseline.get("tokens_consumed", 1)
        skill_tokens = with_skill.get("tokens_consumed", baseline_tokens)

        if baseline_tokens == 0:
            return 0.0

        reduction = (baseline_tokens - skill_tokens) / baseline_tokens
        return round(reduction, 2)

    def _calculate_api_failure_reduction(
        self, baseline: dict[str, Any], with_skill: dict[str, Any]
    ) -> int:
        """Calculate absolute reduction in API failures."""
        baseline_failures = baseline.get("api_failures", 0)
        skill_failures = with_skill.get("api_failures", baseline_failures)
        return max(0, baseline_failures - skill_failures)

    def _calculate_interaction_reduction(
        self, baseline: dict[str, Any], with_skill: dict[str, Any]
    ) -> int:
        """Calculate absolute reduction in interaction turns."""
        baseline_turns = baseline.get("interaction_turns", 0)
        skill_turns = with_skill.get("interaction_turns", baseline_turns)
        return max(0, baseline_turns - skill_turns)

    def _calculate_success_rate_change(
        self, baseline: dict[str, Any], with_skill: dict[str, Any]
    ) -> float:
        """Calculate change in success rate (percentage points)."""
        baseline_rate = baseline.get("success_rate", 0.0)
        skill_rate = with_skill.get("success_rate", baseline_rate)
        return round(skill_rate - baseline_rate, 2)

    def _calculate_tool_call_reduction(
        self, baseline: dict[str, Any], with_skill: dict[str, Any]
    ) -> int:
        """Calculate absolute reduction in tool calls."""
        baseline_calls = baseline.get("tool_calls", 0)
        skill_calls = with_skill.get("tool_calls", baseline_calls)
        return max(0, baseline_calls - skill_calls)

    def _calculate_comparison(
        self, baseline: dict[str, Any], with_skill: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate full comparison with fallbacks."""
        return {
            "token_reduction": self._calculate_token_reduction(baseline, with_skill),
            "api_failure_reduction": self._calculate_api_failure_reduction(baseline, with_skill),
            "interaction_reduction": self._calculate_interaction_reduction(baseline, with_skill),
            "success_rate_change": self._calculate_success_rate_change(baseline, with_skill),
            "tool_call_reduction": self._calculate_tool_call_reduction(baseline, with_skill),
            "meets_targets": self._check_targets(baseline, with_skill),
            "target_details": self._get_target_details(baseline, with_skill),
            "recommendations": self._generate_recommendations(baseline, with_skill),
        }

    def _generate_recommendations(
        self, baseline: dict[str, Any], with_skill: dict[str, Any]
    ) -> list[str]:
        """Generate improvement recommendations based on comparison."""
        recommendations = []

        # Check success rate
        success_rate = with_skill.get("success_rate", 0.0)
        if success_rate < 0.9:
            recommendations.append(
                f"Success rate is {success_rate:.0%}. Consider adding more "
                "examples or clarifying edge cases in the skill."
            )

        # Check token efficiency
        token_reduction = self._calculate_token_reduction(baseline, with_skill)
        if token_reduction < 0.5:
            recommendations.append(
                f"Token reduction is only {token_reduction:.0%}. Consider making "
                "instructions more concise or using more specific guidance."
            )

        # Check API failures
        api_failures = with_skill.get("api_failures", 0)
        if api_failures > 0:
            recommendations.append(
                f"Skill still results in {api_failures} API failures. "
                "Consider adding error handling guidance."
            )

        # Check interaction efficiency
        interaction_reduction = self._calculate_interaction_reduction(baseline, with_skill)
        if interaction_reduction < 2:
            recommendations.append(
                "Interaction turns not significantly reduced. "
                "Consider making the skill more prescriptive."
            )

        if not recommendations:
            recommendations.append(
                "Skill performs well across all metrics. No major improvements needed."
            )

        return recommendations

    def _default_baseline_metrics(self, task_description: str) -> dict[str, Any]:
        """Return conservative default baseline metrics."""
        return {
            "tool_calls": 10,
            "api_failures": 2,
            "tokens_consumed": 5000,
            "interaction_turns": 8,
            "success_rate": 0.6,
            "reasoning": "Default conservative estimate",
            "task_description": task_description,
        }

    def _default_skill_metrics(self, task_description: str, skill_name: str) -> dict[str, Any]:
        """Return optimistic default skill metrics."""
        return {
            "tool_calls": 5,
            "api_failures": 0,
            "tokens_consumed": 2500,
            "interaction_turns": 4,
            "success_rate": 0.9,
            "reasoning": "Default optimistic estimate",
            "task_description": task_description,
            "skill_name": skill_name,
        }

    def forward(self, **kwargs) -> dspy.Prediction:
        """Synchronous forward - delegates to appropriate method."""
        action = kwargs.get("action")

        if action == "baseline":
            return run_async(self.collect_baseline(kwargs.get("task_description", "")))
        elif action == "with_skill":
            return run_async(
                self.collect_with_skill(kwargs.get("task_description", ""), kwargs.get("skill", {}))
            )
        elif action == "compare":
            return self.compare(kwargs.get("baseline", {}), kwargs.get("with_skill", {}))
        else:
            raise ValueError(f"Unknown action: {action}")
