"""
DSPy signatures for Phase 1: Understanding & Planning.

Phase 1 performs parallel analysis of user intent, taxonomy placement,
and dependencies, then synthesizes a coherent plan.

Workflow:
1. GatherRequirements (initial understanding)
2. Parallel: AnalyzeIntent + FindTaxonomyPath + AnalyzeDependencies
3. SynthesizePlan (combine results)

All signatures use Pydantic models for type safety.
"""

from __future__ import annotations

from typing import Literal

import dspy

from ...models import (
    DependencyAnalysis,
    DependencyRef,
    SkillMetadata,
    TaskIntent,
)

# =============================================================================
# Type Definitions for Constrained Outputs
# =============================================================================

Domain = Literal["technical", "cognitive", "domain_knowledge", "tool", "meta"]
TargetLevel = Literal["beginner", "intermediate", "advanced", "expert"]
SkillType = Literal["how_to", "reference", "concept", "workflow", "checklist", "troubleshooting"]
SkillLength = Literal["short", "medium", "long"]

# =============================================================================
# Step 1.1: Gather Requirements (Pre-Analysis)
# =============================================================================


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


# =============================================================================
# Step 1.2: Analyze Intent (Parallel Branch 1)
# =============================================================================


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
    user_context: str = dspy.InputField(
        desc="JSON user context: user_id, existing_skills (list of IDs), preferences (dict)"
    )

    # Outputs
    task_intent: TaskIntent = dspy.OutputField(
        desc="Structured intent object with fields: purpose (1-2 sentences), "
        "problem_statement (specific problem solved), target_audience (who needs this), "
        "value_proposition (unique value this skill provides)"
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


# =============================================================================
# Step 1.3: Find Taxonomy Path (Parallel Branch 2)
# =============================================================================


class FindTaxonomyPath(dspy.Signature):
    """
    Find optimal taxonomy path using existing structure and similar skills.

    Rules: prefer specific over general, use existing categories, follow kebab-case naming.
    Avoid creating new top-level categories unless absolutely necessary.
    """

    # Inputs
    task_description: str = dspy.InputField(desc="User's task description with skill requirements")
    taxonomy_structure: str = dspy.InputField(
        desc="JSON taxonomy tree showing all existing categories and their structure"
    )
    existing_skills: list[str] = dspy.InputField(
        desc="List of existing skill paths (e.g., ['python/async', 'web/react']). "
        "Use for finding similar skills and appropriate placement."
    )

    # Outputs
    recommended_path: str = dspy.OutputField(
        desc="Taxonomy path in format 'category/skill-name' (2-level v0.2 structure). "
        "Use kebab-case for skill-name. Example: 'python/async-patterns' not 'Python/Async Patterns'. "
        "Path MUST match existing categories unless creating new is justified."
    )
    alternative_paths: list[str] = dspy.OutputField(
        desc="2-3 alternative valid paths if primary recommendation has issues. "
        "Order by preference. Format same as recommended_path. Empty list [] if primary is clearly optimal."
    )
    path_rationale: str = dspy.OutputField(
        desc="1-3 sentence explanation. Mention: (1) why this category fits, (2) similar existing skills, "
        "(3) how it relates to parent category. Be specific, reference actual skill names."
    )
    new_directories: list[str] = dspy.OutputField(
        desc="New directories to create (e.g., ['python'] if category doesn't exist). "
        "Empty list [] if using existing paths. Justify new categories in rationale."
    )
    confidence: float = dspy.OutputField(
        desc="Confidence 0.0-1.0 in path selection. >0.8 = high confidence (proceed), "
        "0.6-0.8 = moderate (acceptable), <0.6 = low (request user confirmation before proceeding)"
    )


# =============================================================================
# Step 1.4: Analyze Dependencies (Parallel Branch 3)
# =============================================================================


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
    task_intent: str = dspy.InputField(
        desc="JSON TaskIntent from AnalyzeIntent with purpose and problem statement"
    )
    taxonomy_path: str = dspy.InputField(
        desc="Recommended taxonomy path (e.g., 'python/async') for finding related skills"
    )
    existing_skills: str = dspy.InputField(
        desc="JSON array of existing skills with metadata: [{skill_id, name, description, category}, ...]"
    )

    # Outputs
    dependency_analysis: DependencyAnalysis = dspy.OutputField(
        desc="Structured analysis object with: required (hard prerequisites), "
        "recommended (soft suggestions), conflicts (incompatible skills), rationale"
    )
    prerequisite_skills: list[DependencyRef] = dspy.OutputField(
        desc="0-3 hard prerequisites user MUST know first. Each includes: skill_id, reason (why required). "
        "Be conservative - only include true prerequisites, not nice-to-haves. Empty list [] if self-contained."
    )
    complementary_skills: list[DependencyRef] = dspy.OutputField(
        desc="0-5 complementary skills that enhance this skill. Each includes: skill_id, reason (how it helps). "
        "These are optional recommendations, not requirements. Empty list [] if standalone."
    )
    missing_prerequisites: list[str] = dspy.OutputField(
        desc="Prerequisites that should exist but don't yet (need to create before this skill). "
        "Format: 'skill_id: brief reason'. Empty list [] if all prerequisites exist. Max 2 items."
    )


# =============================================================================
# Step 1.5: Synthesize Plan (Combines All Analyses)
# =============================================================================


class SynthesizePlan(dspy.Signature):
    """
    Combine all Phase 1 analyses into a coherent, executable skill plan (v0.2).

    Create unified plan incorporating intent, taxonomy placement, dependencies,
    and any HITL feedback. This plan drives Phase 2 generation quality.

    IMPORTANT: v0.2 Changes (Jan 2026)
    - Description must emphasize WHEN to use (triggering conditions, symptoms)
      NOT what the skill teaches. This enables CSO (Claude Search Optimization).
    - Minimal frontmatter in generated SKILL.md: name + description ONLY
      (no metadata block; metadata goes in separate metadata.json)
    - Include Real-World Impact section in content plan (measurable outcomes)
    """

    # Inputs
    intent_analysis: str = dspy.InputField(
        desc="JSON TaskIntent with purpose, problem_statement, target_audience, value_proposition"
    )
    taxonomy_analysis: str = dspy.InputField(
        desc="JSON with: recommended_path, path_rationale, confidence, new_directories"
    )
    dependency_analysis: str = dspy.InputField(
        desc="JSON DependencyAnalysis with: prerequisite_skills, complementary_skills, conflicts"
    )
    user_confirmation: str = dspy.InputField(
        desc="User feedback from HITL confirmation checkpoint. "
        "Empty string '' on first pass, contains adjustments/preferences if user provided feedback."
    )

    # Outputs
    skill_metadata: SkillMetadata = dspy.OutputField(
        desc="Complete metadata object: name (kebab-case), description (CSO-optimized: 'Use when...' + symptoms/triggers, "
        "NOT workflow summary), taxonomy_path, tags (3-7 keywords), version (1.0.0), type (matches skill_type). "
        "Description is CRITICAL for agent discovery—focus on WHEN to use, not WHAT it teaches. "
        "Ensure name matches taxonomy path leaf for agentskills.io compliance."
    )
    content_plan: str = dspy.OutputField(
        desc="Structured content outline (bullet format): main sections with subsections, "
        "code example count per section, pattern count target (5+ recommended), "
        "subdirectory files to create (for navigation_hub style). Min 5 bullet points, max 15."
    )
    generation_instructions: str = dspy.OutputField(
        desc="Specific generation guidance (3-7 sentences): writing style (formal/conversational), "
        "tone (imperative/descriptive), depth (comprehensive/focused), quality requirements "
        "(must have ❌/✅ contrasts, core principle, strong guidance). Reference target_level."
    )
    success_criteria: list[str] = dspy.OutputField(
        desc="3-5 measurable success criteria for generated content. Format: 'Quality score >0.80', "
        "'Contains 5+ patterns with contrasts', 'All examples are executable'. "
        "These criteria will be checked during validation."
    )
    estimated_length: SkillLength = dspy.OutputField(
        desc="Estimated SKILL.md length: short (<500 lines, minimal style), "
        "medium (500-1500 lines, typical), long (>1500 lines, comprehensive with many patterns)"
    )
