"""DSPy signatures for Phase 1: Understanding the Need.

These signatures implement the decision-driven workflow from skill-creation-guidelines.md
lines 191-239, using DSPy ChainOfThought for flexible reasoning within
structured decision boundaries.

From the guidelines, Phase 1 answers these interrogation questions:
1. What is the problem statement? (ExtractProblemStatement)
2. Is this a new skill or enhancement? (DecideNovelty)
3. Are there overlapping skills? (DetectOverlap)
4. What type of skill is this? (ClassifyDomain - 8 types)
5. Where does this fit in the taxonomy? (ProposeTaxonomyPath)

This phase ends with a checkpoint validation (Phase1Checkpoint) before proceeding.
"""

from __future__ import annotations

from typing import Literal

import dspy

# =============================================================================
# Phase 1 Signatures - Understanding the Need
# =============================================================================

# Valid skill types from guidelines lines 269-282
VALID_SKILL_TYPES = [
    "cognitive",  # Thinking, reasoning, decision-making skills
    "technical",  # Programming, implementation, code-focused
    "domain",  # Industry-specific knowledge
    "tool",  # External tool or service integration
    "mcp",  # Model Context Protocol server skills
    "specialization",  # Specialized expertise areas
    "task_focus",  # Focused on specific task completion
    "memory",  # Memory and recall-focused skills
]


class ExtractProblemStatement(dspy.Signature):
    """Extract a clear, specific problem statement from the task description.

    Step 1.1 of Phase 1 - Forms the foundation for all subsequent decisions.
    A clear problem statement ensures we're solving the right problem.

    Key questions:
    - What is the core problem?
    - What are the key requirements?
    - What pain points does this address?

    From guidelines line 1018: "Problem statement is clear and specific"
    """

    # Inputs
    task_description: str = dspy.InputField(desc="User's raw task description")
    context: str = dspy.InputField(
        default="", desc="Additional context about user's project or environment"
    )

    # Outputs
    problem_statement: str = dspy.OutputField(
        desc="Clear, specific problem statement (1-2 sentences)"
    )
    key_requirements: list[str] = dspy.OutputField(
        desc="List of 3-7 key requirements extracted from task"
    )
    pain_points: list[str] = dspy.OutputField(
        desc="List of pain points this skill addresses (2-5 items)"
    )


class DecideNovelty(dspy.Signature):
    """Determine if this is a new skill or enhancement to existing skill.

    Step 1.2 of Phase 1 - Critical decision that affects the entire workflow:
    - New skill: Create from scratch with full Phase 1-5 workflow
    - Enhancement: Modify existing skill with targeted updates

    From guidelines line 1019: "No existing skill covers this"
    """

    # Inputs
    problem_statement: str = dspy.InputField(
        desc="Clear problem statement from ExtractProblemStatement"
    )
    existing_skills: str = dspy.InputField(desc="JSON list of existing skill_ids for comparison")
    taxonomy_search_results: str = dspy.InputField(
        default="{}", desc="Search results from taxonomy (skill_ids and descriptions)"
    )

    # Outputs
    is_new_skill: bool = dspy.OutputField(
        desc="True if this is a new skill, False if enhancement to existing"
    )
    target_skill_id: str = dspy.OutputField(
        default="", desc="Skill to enhance (if is_new_skill=False), empty otherwise"
    )
    rationale: str = dspy.OutputField(desc="Explanation of decision with supporting evidence")


class DetectOverlap(dspy.Signature):
    """Detect overlap with existing skills.

    Step 1.3 of Phase 1 - Ensures we don't duplicate functionality.
    Even if a skill is "new", there may be overlapping capabilities that
    could be shared or composed.

    Key questions:
    - What existing skills cover similar functionality?
    - How does this skill differ from those?
    - Can capabilities be composed from existing skills?
    """

    # Inputs
    problem_statement: str = dspy.InputField(desc="Clear problem statement")
    proposed_domain: str = dspy.InputField(
        desc="Proposed skill domain (from preliminary classification)"
    )
    existing_skills_metadata: str = dspy.InputField(
        desc="JSON of existing skills' metadata for comparison"
    )

    # Outputs
    overlapping_skills: list[dict] = dspy.OutputField(
        desc="List of potentially overlapping skills with similarity scores"
    )
    overlap_analysis: str = dspy.OutputField(
        desc="Analysis of how this skill differs from overlapping ones"
    )
    confidence_no_overlap: float = dspy.OutputField(
        desc="0.0-1.0 confidence that this is novel (not a duplicate)"
    )


class ClassifyDomain(dspy.Signature):
    """Classify skill into one of 8 types using decision matrix.

    Step 1.4 of Phase 1 - Uses the decision matrix from guidelines lines 269-282:

    Decision Matrix:
    - cognitive: Focuses on thinking, reasoning, decision-making
    - technical: Programming, implementation, code-focused
    - domain: Industry-specific knowledge (medical, legal, etc.)
    - tool: External tool or service integration
    - mcp: Model Context Protocol server skills
    - specialization: Specialized expertise within a domain
    - task_focus: Focused on specific task completion
    - memory: Memory and recall-focused skills

    From guidelines line 1024: "Domain is classified using 8-type matrix"
    """

    # Inputs
    problem_statement: str = dspy.InputField(desc="Clear problem statement")
    key_characteristics: list[str] = dspy.InputField(
        desc="Extracted characteristics from problem analysis"
    )

    # Outputs
    skill_type: Literal[
        "cognitive", "technical", "domain", "tool", "mcp", "specialization", "task_focus", "memory"
    ] = dspy.OutputField(desc="One of 8 skill types from decision matrix")
    type_confidence: float = dspy.OutputField(desc="0.0-1.0 confidence in classification")
    type_rationale: str = dspy.OutputField(desc="Explanation using decision matrix criteria")


class ProposeTaxonomyPath(dspy.Signature):
    """Propose taxonomy path based on domain classification and existing structure.

    Step 1.5 of Phase 1 - Determines where this skill fits in the taxonomy.
    A well-chosen path ensures discoverability and logical organization.

    Key questions:
    - What is the appropriate domain path?
    - What are the parent skills for context?
    - How does this relate to siblings?

    From guidelines line 1023: "Taxonomy path is determined"
    """

    # Inputs
    skill_type: str = dspy.InputField(desc="Classified skill type from ClassifyDomain")
    problem_statement: str = dspy.InputField(desc="Clear problem statement")
    existing_taxonomy: str = dspy.InputField(
        desc="JSON of taxonomy structure showing available paths"
    )

    # Outputs
    proposed_path: str = dspy.OutputField(
        desc="Full taxonomy path (e.g., 'technical/programming/python/async')"
    )
    parent_skills: list[str] = dspy.OutputField(
        desc="Immediate parent skills for context and composition"
    )
    path_confidence: float = dspy.OutputField(desc="0.0-1.0 confidence in path placement")


class Phase1Checkpoint(dspy.Signature):
    """Validate Phase 1 outputs before proceeding to Phase 2.

    This checkpoint enforces the validation criteria from guidelines lines 1018-1024:
    1. Problem statement is clear and specific
    2. No existing skill covers this (or enhancement is justified)
    3. Capabilities are atomic and testable
    4. Dependencies are identified
    5. Taxonomy path is determined
    6. Domain is classified using 8-type matrix

    The checkpoint returns:
    - checkpoint_passed: True if all criteria met
    - checkpoint_score: 0.0-1.0 overall score
    - recommendations: What to do if checkpoint fails
    """

    # Inputs - All Phase 1 outputs
    problem_statement: str = dspy.InputField(desc="Problem statement from ExtractProblemStatement")
    is_new_skill: bool = dspy.InputField(desc="Novelty decision from DecideNovelty")
    skill_type: str = dspy.InputField(desc="Domain classification from ClassifyDomain")
    proposed_path: str = dspy.InputField(desc="Taxonomy path from ProposeTaxonomyPath")
    overlapping_skills: list[dict] = dspy.InputField(desc="Overlap analysis from DetectOverlap")
    key_requirements: list[str] = dspy.InputField(
        default=[], desc="Key requirements from ExtractProblemStatement"
    )

    # Outputs - Checkpoint validation
    checkpoint_passed: bool = dspy.OutputField(desc="True if all validation criteria are met")
    validation_errors: list[str] = dspy.OutputField(
        desc="List of any validation failures (empty if passed)"
    )
    checkpoint_score: float = dspy.OutputField(
        desc="0.0-1.0 overall checkpoint score (>=0.8 to proceed)"
    )
    recommendations: list[str] = dspy.OutputField(desc="Recommendations to proceed or fix issues")


__all__ = [
    "VALID_SKILL_TYPES",
    "ExtractProblemStatement",
    "DecideNovelty",
    "DetectOverlap",
    "ClassifyDomain",
    "ProposeTaxonomyPath",
    "Phase1Checkpoint",
]
