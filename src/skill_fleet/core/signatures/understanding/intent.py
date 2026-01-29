"""
DSPy signature for analyzing user intent.

This signature analyzes user intent to determine skill purpose,
value proposition, target audience, and success criteria.
"""

from typing import Literal

import dspy

# Type definitions
SkillType = Literal["how_to", "reference", "concept", "workflow", "checklist", "troubleshooting"]


class AnalyzeIntent(dspy.Signature):
    """
    Analyze user intent to determine skill purpose and value.

    Focus on WHY needed, WHAT problem solved, WHO target user, WHAT value provided.
    Be thorough but concise. This analysis guides all downstream generation.
    """

    # Inputs
    task_description: str = dspy.InputField(
        desc="User's task description with any HITL clarifications incorporated"
    )
    requirements: str = dspy.InputField(
        desc="JSON requirements from GatherRequirements: domain, category, target_level, topics, constraints",
        default="{}",
    )

    # Outputs
    purpose: str = dspy.OutputField(
        desc="1-2 sentence statement of WHY this skill exists. What problem does it solve?"
    )
    problem_statement: str = dspy.OutputField(
        desc="Specific problem this skill addresses. Be concrete about pain points."
    )
    target_audience: str = dspy.OutputField(
        desc="Who needs this skill? Describe the user persona (role, experience level, context)."
    )
    value_proposition: str = dspy.OutputField(
        desc="Unique value this skill provides. What makes it different from alternatives?"
    )
    skill_type: SkillType = dspy.OutputField(
        desc="Type determining structure: how_to (procedural steps), reference (lookup/cheatsheet), "
        "concept (deep understanding), workflow (multi-step process), checklist (verification), "
        "troubleshooting (problem diagnosis)"
    )
    scope: str = dspy.OutputField(
        desc="Scope definition (2-4 sentences): what IS included, what is NOT included. "
        "Be specific to set clear boundaries. Helps prevent scope creep."
    )
    success_criteria: list[str] = dspy.OutputField(
        desc="3-5 measurable success criteria. Format: 'User can do X', 'Skill achieves Y'. "
        "Be specific and testable. Use action verbs (implement, debug, configure, etc.)."
    )
