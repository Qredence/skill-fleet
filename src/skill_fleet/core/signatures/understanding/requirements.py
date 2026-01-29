"""
DSPy signature for gathering requirements from task descriptions.

This signature extracts structured requirements including domain, topics,
constraints, and ambiguities that may require HITL clarification.
"""

from typing import Literal

import dspy

# Type definitions for constrained outputs
Domain = Literal["technical", "cognitive", "domain_knowledge", "tool", "meta"]
TargetLevel = Literal["beginner", "intermediate", "advanced", "expert"]


class GatherRequirements(dspy.Signature):
    """
    Extract structured requirements from user task description.

    Identify domain, skill level, topics, and ambiguities for HITL clarification.
    Be specific about what's unclear vs. what can be inferred.
    """

    # Inputs
    task_description: str = dspy.InputField(
        desc="User's task description, may include clarifications from previous rounds"
    )
    user_context: str = dspy.InputField(
        desc="JSON user context: user_id, existing_skills (list of IDs), preferences (dict)",
        default="{}",
    )

    # Outputs
    domain: Domain = dspy.OutputField(
        desc="Primary domain based on skill content: technical (code/tools), cognitive (thinking patterns), "
        "domain_knowledge (specific field), tool (specific software), or meta (about skills themselves)"
    )
    category: str = dspy.OutputField(
        desc="Specific category within domain (e.g., 'python', 'devops', 'web', 'testing'). "
        "Use kebab-case, match existing taxonomy categories when possible. Single word preferred."
    )
    target_level: TargetLevel = dspy.OutputField(
        desc="Target expertise level: beginner (assumes no prior knowledge), intermediate (assumes basics), "
        "advanced (assumes strong foundation), expert (edge cases and optimizations)"
    )
    topics: list[str] = dspy.OutputField(
        desc="3-7 specific topics to cover. Be concrete (not 'basics' but 'async/await syntax'). "
        "Order by importance. Each topic should map to a skill section or pattern."
    )
    constraints: list[str] = dspy.OutputField(
        desc="Technical constraints and preferences (e.g., 'Python 3.12+', 'production patterns only', "
        "'no deprecated features'). Empty list [] if none detected. Max 5 constraints."
    )
    ambiguities: list[str] = dspy.OutputField(
        desc="Unclear aspects requiring HITL clarification (e.g., 'Unclear if user wants sync or async examples'). "
        "Be specific about what's ambiguous. Empty list [] if task is clear. Max 3 ambiguities."
    )
