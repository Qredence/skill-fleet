"""
DSPy signature for analyzing skill dependencies.

This signature identifies prerequisites, complementary skills,
and potential conflicts with existing skills.
"""

import dspy


class AnalyzeDependencies(dspy.Signature):
    """
    Identify prerequisites, complementary skills, and conflicts.

    Determine: MUST know first (prerequisites), SHOULD know (complementary),
    CANNOT use together (conflicts). Be conservative with prerequisites.
    """

    # Inputs
    task_description: str = dspy.InputField(
        desc="User's task description defining skill requirements"
    )
    intent_analysis: str = dspy.InputField(
        desc="JSON intent analysis with purpose, problem_statement, target_audience, skill_type",
        default="{}",
    )
    taxonomy_path: str = dspy.InputField(
        desc="Recommended taxonomy path (e.g., 'python/async') for finding related skills"
    )
    existing_skills: str = dspy.InputField(
        desc="JSON array of existing skills with metadata: [{skill_id, name, description, category}, ...]"
    )

    # Outputs
    prerequisite_skills: list[str] = dspy.OutputField(
        desc="0-3 hard prerequisites user MUST know first. Format: 'skill_id: brief reason'. "
        "Be conservative - only include true prerequisites, not nice-to-haves. Empty list [] if self-contained."
    )
    complementary_skills: list[str] = dspy.OutputField(
        desc="0-5 complementary skills that enhance this skill. Format: 'skill_id: brief reason'. "
        "These are optional recommendations, not requirements. Empty list [] if standalone."
    )
    conflicting_skills: list[str] = dspy.OutputField(
        desc="Skills that conflict with or supersede this skill. Format: 'skill_id: reason'. "
        "Empty list [] if no conflicts."
    )
    missing_prerequisites: list[str] = dspy.OutputField(
        desc="Prerequisites that should exist but don't yet (need to create before this skill). "
        "Format: 'skill_id: brief reason'. Empty list [] if all prerequisites exist. Max 2 items."
    )
    dependency_rationale: str = dspy.OutputField(
        desc="2-4 sentences explaining key dependencies. Why are these specific skills required/recommended?"
    )
    reasoning: dspy.Reasoning = dspy.OutputField(desc="Reasoning process for dependency analysis")
