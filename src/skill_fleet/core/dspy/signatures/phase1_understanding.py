"""DSPy signatures for Phase 1: Understanding & Planning.

Phase 1 performs parallel analysis of user intent, taxonomy placement,
and dependencies, then synthesizes a coherent plan.

Workflow:
1. GatherRequirements (initial understanding)
2. Parallel: AnalyzeIntent + FindTaxonomyPath + AnalyzeDependencies
3. SynthesizePlan (combine results)

All signatures use Pydantic models for type safety.
"""

from __future__ import annotations

import dspy

from ...models import (
    DependencyAnalysis,
    DependencyRef,
    SkillMetadata,
    TaskIntent,
)

# =============================================================================
# Step 1.1: Gather Requirements (Pre-Analysis)
# =============================================================================


class GatherRequirements(dspy.Signature):
    """Initial requirements gathering from task description.

    Extract basic requirements before detailed analysis:
    - What domain/category?
    - What level (beginner/intermediate/advanced)?
    - What specific topics to cover?
    - Any constraints or preferences?
    """

    # Inputs
    task_description: str = dspy.InputField(
        desc="User's task description (may include clarifications)"
    )

    # Outputs
    domain: str = dspy.OutputField(
        desc="Primary domain: 'technical', 'cognitive', 'domain_knowledge', etc."
    )
    category: str = dspy.OutputField(
        desc="Category within domain: 'programming', 'devops', 'data_science', etc."
    )
    target_level: str = dspy.OutputField(
        desc="Target level: 'beginner', 'intermediate', 'advanced', 'expert'"
    )
    topics: list[str] = dspy.OutputField(desc="List of specific topics to cover (3-7 items)")
    constraints: list[str] = dspy.OutputField(
        desc="Any constraints or preferences (e.g., 'focus on Python 3.12+', 'no deprecated patterns')"
    )
    ambiguities: list[str] = dspy.OutputField(
        desc="Detected ambiguities that need clarification via HITL"
    )


# =============================================================================
# Step 1.2: Analyze Intent (Parallel Branch 1)
# =============================================================================


class AnalyzeIntent(dspy.Signature):
    """Deeply analyze user intent to understand what skill is needed.

    This is one of three parallel analyses in Phase 1. Focus on:
    - WHY is this skill needed?
    - WHAT problem does it solve?
    - WHO is the target user?
    - WHAT value does it provide?

    Use chain-of-thought reasoning for thorough analysis.
    """

    # Inputs
    task_description: str = dspy.InputField(desc="User's task description with any clarifications")
    user_context: str = dspy.InputField(
        desc="JSON user context (user_id, existing skills, preferences)"
    )

    # Outputs
    task_intent: TaskIntent = dspy.OutputField(
        desc="Structured intent with: purpose, problem_statement, target_audience, value_proposition"
    )
    skill_type: str = dspy.OutputField(
        desc="Type of skill: 'how_to', 'reference', 'concept', 'workflow', 'checklist'"
    )
    scope: str = dspy.OutputField(desc="Scope description: what's included and excluded")
    success_criteria: list[str] = dspy.OutputField(
        desc="How will we know this skill is successful? (3-5 criteria)"
    )


# =============================================================================
# Step 1.3: Find Taxonomy Path (Parallel Branch 2)
# =============================================================================


class FindTaxonomyPath(dspy.Signature):
    """Determine optimal taxonomy placement for this skill.

    This is one of three parallel analyses in Phase 1. Analyze the
    taxonomy structure and find the best location for this skill.

    Rules:
    - Prefer deeper paths (more specific is better)
    - Consider existing skills in similar categories
    - Follow taxonomy naming conventions
    - Avoid creating new top-level categories
    """

    # Inputs
    task_description: str = dspy.InputField(desc="User's task description")
    taxonomy_structure: str = dspy.InputField(desc="JSON representation of full taxonomy structure")
    existing_skills: list[str] = dspy.InputField(desc="List of existing skill paths for reference")

    # Outputs
    recommended_path: str = dspy.OutputField(
        desc="Recommended taxonomy path (e.g., 'technical_skills/programming/python/async')"
    )
    alternative_paths: list[str] = dspy.OutputField(
        desc="2-3 alternative paths if primary has issues"
    )
    path_rationale: str = dspy.OutputField(
        desc="Why this path is optimal (mention similar skills, category fit, etc.)"
    )
    new_directories: list[str] = dspy.OutputField(
        desc="Any new directories that need to be created (empty if using existing path)"
    )
    confidence: float = dspy.OutputField(
        desc="Confidence in path selection 0-1. <0.7 means may need user confirmation"
    )


# =============================================================================
# Step 1.4: Analyze Dependencies (Parallel Branch 3)
# =============================================================================


class AnalyzeDependencies(dspy.Signature):
    """Analyze skill dependencies and prerequisites.

    This is one of three parallel analyses in Phase 1. Determine:
    - What skills must user know first? (prerequisites)
    - What skills complement this one? (related skills)
    - What skills might conflict? (conflicts)
    """

    # Inputs
    task_description: str = dspy.InputField(desc="User's task description")
    task_intent: str = dspy.InputField(desc="Analyzed task intent (from AnalyzeIntent)")
    taxonomy_path: str = dspy.InputField(desc="Recommended taxonomy path (from FindTaxonomyPath)")
    existing_skills: str = dspy.InputField(desc="JSON list of existing skills with metadata")

    # Outputs
    dependency_analysis: DependencyAnalysis = dspy.OutputField(
        desc="Complete dependency analysis with: required, recommended, conflicts"
    )
    prerequisite_skills: list[DependencyRef] = dspy.OutputField(
        desc="Skills user must know first (hard prerequisites)"
    )
    complementary_skills: list[DependencyRef] = dspy.OutputField(
        desc="Skills that complement this one (soft recommendations)"
    )
    missing_prerequisites: list[str] = dspy.OutputField(
        desc="Prerequisites that don't exist yet (need to create first)"
    )


# =============================================================================
# Step 1.5: Synthesize Plan (Combines All Analyses)
# =============================================================================


class SynthesizePlan(dspy.Signature):
    """Synthesize all Phase 1 analyses into a coherent skill creation plan.

    Combine results from:
    - Intent analysis
    - Taxonomy path selection
    - Dependency analysis

    Create a unified plan that guides Phase 2 (generation).

    This signature uses dspy.Refine for iterative improvement.
    """

    # Inputs
    intent_analysis: str = dspy.InputField(desc="JSON TaskIntent from AnalyzeIntent")
    taxonomy_analysis: str = dspy.InputField(
        desc="JSON taxonomy path and rationale from FindTaxonomyPath"
    )
    dependency_analysis: str = dspy.InputField(
        desc="JSON DependencyAnalysis from AnalyzeDependencies"
    )
    user_confirmation: str = dspy.InputField(
        desc="User's confirmation or feedback from HITL checkpoint (may be empty on first pass)"
    )

    # Outputs
    skill_metadata: SkillMetadata = dspy.OutputField(
        desc="Complete skill metadata: name, description, taxonomy_path, tags, etc."
    )
    content_plan: str = dspy.OutputField(
        desc="Outline of skill content: sections, topics, example count, etc."
    )
    generation_instructions: str = dspy.OutputField(
        desc="Specific instructions for Phase 2 generation (style, tone, depth, etc.)"
    )
    success_criteria: list[str] = dspy.OutputField(
        desc="How to evaluate if generated content is successful"
    )
    estimated_length: str = dspy.OutputField(
        desc="Estimated skill length: 'short' (<500 lines), 'medium' (500-1500), 'long' (>1500)"
    )
