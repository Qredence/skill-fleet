"""
Signatures for metrics collection and comparison.

Used by MetricsCollectorModule to estimate baseline performance
and compare skill-assisted vs unassisted execution.
"""

import dspy


class CollectBaselineMetrics(dspy.Signature):
    """
    Simulate task execution WITHOUT skill assistance and estimate metrics.

    Imagine an AI agent trying to complete the described task without any
    specific skill guidance. Estimate the following metrics:

    - tool_calls: Number of tool/API calls needed
    - api_failures: Number of failed API calls (due to incorrect usage)
    - tokens_consumed: Total tokens used in the interaction
    - interaction_turns: Number of back-and-forth turns
    - success_rate: Probability of successful completion (0-1)

    Be realistic but slightly conservative in estimates. Consider that
    without guidance, the agent may need to explore and may make mistakes.

    Examples:
        Task: "Create a simple React component"
        Baseline: ~8 tool calls, 1-2 API failures, ~4000 tokens, 6 turns, 70% success

        Task: "Set up a complex database migration"
        Baseline: ~15 tool calls, 3-4 API failures, ~8000 tokens, 12 turns, 50% success

    """

    task_description: str = dspy.InputField(desc="Description of the task to simulate")

    tool_calls: int = dspy.OutputField(desc="Estimated number of tool/API calls")
    api_failures: int = dspy.OutputField(
        desc="Estimated number of API failures due to incorrect usage"
    )
    tokens_consumed: int = dspy.OutputField(desc="Estimated total token consumption")
    interaction_turns: int = dspy.OutputField(
        desc="Estimated number of interaction turns to complete"
    )
    success_rate: float = dspy.OutputField(
        desc="Estimated probability of successful completion (0.0-1.0)"
    )
    reasoning: str = dspy.OutputField(desc="Brief explanation of the estimation")


class CollectSkillMetrics(dspy.Signature):
    """
    Simulate task execution WITH skill assistance and estimate metrics.

    Imagine an AI agent using the provided skill to complete the task.
    The skill provides guidance, examples, and best practices. Estimate
    how much the skill improves efficiency:

    - tool_calls: Fewer calls due to guidance
    - api_failures: Reduced failures due to correct examples
    - tokens_consumed: Less exploration = fewer tokens
    - interaction_turns: More direct path = fewer turns
    - success_rate: Higher success due to proven approach

    Examples:
        With a good React component skill:
        - Tool calls: 50% reduction (8 → 4)
        - API failures: Near zero (2 → 0)
        - Tokens: 40% reduction (4000 → 2400)
        - Success rate: +25% (70% → 95%)

    """

    task_description: str = dspy.InputField(desc="Description of the task")
    skill_name: str = dspy.InputField(desc="Name of the skill")
    skill_content: str = dspy.InputField(desc="Content/guidance provided by the skill")

    tool_calls: int = dspy.OutputField(desc="Estimated tool calls WITH skill guidance")
    api_failures: int = dspy.OutputField(desc="Estimated API failures WITH skill guidance")
    tokens_consumed: int = dspy.OutputField(desc="Estimated tokens consumed WITH skill guidance")
    interaction_turns: int = dspy.OutputField(desc="Estimated turns WITH skill guidance")
    success_rate: float = dspy.OutputField(
        desc="Estimated success rate WITH skill guidance (0.0-1.0)"
    )
    reasoning: str = dspy.OutputField(desc="Explanation of how the skill improves performance")


class CompareMetrics(dspy.Signature):
    """
    Compare baseline vs skill-assisted metrics and provide recommendations.

    Analyze the difference between unassisted and skill-assisted task execution.
    Calculate improvements and determine if the skill meets performance targets:

    Targets:
    - 90% trigger rate (success_rate >= 0.9)
    - 50% token reduction
    - 0 API failures with skill

    Provide specific recommendations for improvement if targets aren't met.

    """

    baseline_metrics: str = dspy.InputField(desc="String representation of baseline metrics dict")
    skill_metrics: str = dspy.InputField(
        desc="String representation of skill-assisted metrics dict"
    )

    token_reduction: float = dspy.OutputField(desc="Percentage reduction in token usage (0.0-1.0)")
    api_failure_reduction: int = dspy.OutputField(desc="Absolute reduction in API failures")
    interaction_reduction: int = dspy.OutputField(desc="Absolute reduction in interaction turns")
    success_rate_change: float = dspy.OutputField(desc="Change in success rate (skill - baseline)")
    meets_targets: bool = dspy.OutputField(desc="Whether all performance targets are met")
    recommendations: list[str] = dspy.OutputField(
        desc="Specific recommendations for skill improvement"
    )
