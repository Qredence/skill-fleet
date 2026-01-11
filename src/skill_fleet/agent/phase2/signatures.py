"""DSPy signatures for Phase 2: Scope & Boundaries.

These signatures implement the decision-driven workflow from skill-creation-guidelines.md
lines 240-353, using DSPy ChainOfThought for flexible reasoning within
structured decision boundaries.

From the guidelines, Phase 2 answers these key questions:
1. Confirm the skill type (from Phase 1 classification)
2. Determine weight based on capability count (lightweight/medium/heavyweight)
3. Decide load priority using decision tree (always/task_specific/on_demand/dormant)
4. Design 3-7 atomic capabilities
5. Validate dependencies against 5 composition rules
6. Generate complete skill metadata

This phase ends with a checkpoint validation (Phase2Checkpoint) before proceeding.

Decision Matrices from Guidelines:
- Weight Guidelines (lines 286-295): 1-3=lightweight, 4-7=medium, 8+=heavyweight
- Load Priority Tree (lines 297-316): Core→always, Common→task_specific, Rare→on_demand
- Dependency Rules (lines 318-344): No cycles, prefer abstractions, specify versions,
  minimize depth (2-3 levels), document why
"""

from __future__ import annotations

from typing import Literal

import dspy

# Import models from existing models.py for type-safe outputs
from .models import (
    Capability,
    CompatibilityConstraints,
    DependencyRef,
    ResourceRequirements,
    SkillMetadata,
)

# Valid skill weights (from guidelines lines 286-295)
VALID_WEIGHTS = ["lightweight", "medium", "heavyweight"]

# Valid load priorities (from guidelines lines 297-316)
VALID_PRIORITIES = ["always", "task_specific", "on_demand", "dormant"]

# Valid skill types (from Phase 1)
VALID_SKILL_TYPES = [
    "cognitive",
    "technical",
    "domain",
    "tool",
    "mcp",
    "specialization",
    "task_focus",
    "memory",
]


class ConfirmSkillType(dspy.Signature):
    """Confirm skill type from Phase 1 classification.

    Step 2.1 of Phase 2 - Re-validates the Phase 1 classification with
    additional context from the scope planning phase.

    Key questions:
    - Is the Phase 1 classification still accurate?
    - Are there edge cases that suggest a different type?
    - What is the confidence in this classification?
    """

    # Inputs
    phase1_type: str = dspy.InputField(desc="Skill type from Phase 1 classification")
    phase1_rationale: str = dspy.InputField(desc="Rationale from Phase 1 classification")
    problem_statement: str = dspy.InputField(desc="Problem statement from Phase 1")

    # Outputs
    confirmed_type: Literal[
        "cognitive", "technical", "domain", "tool", "mcp", "specialization", "task_focus", "memory"
    ] = dspy.OutputField(desc="Confirmed skill type (may differ from Phase 1)")
    confirmation_confidence: float = dspy.OutputField(
        desc="0.0-1.0 confidence in this classification"
    )


class DetermineWeight(dspy.Signature):
    """Determine skill weight based on capability count and complexity.

    Step 2.2 of Phase 2 - Uses the weight matrix from guidelines lines 286-295:

    Weight Guidelines:
    - Lightweight: 1-3 capabilities, < 500 lines docs, 1-2 examples
    - Medium: 4-7 capabilities, 500-2000 lines docs, 3-5 examples
    - Heavyweight: 8+ capabilities, > 2000 lines docs, 6+ examples

    From guidelines line 1072: "Weight assigned based on capability count"
    """

    # Inputs
    proposed_capabilities: list[str] = dspy.InputField(desc="List of proposed capability names")
    estimated_documentation_lines: int = dspy.InputField(desc="Estimated lines of documentation")
    planned_examples_count: int = dspy.InputField(desc="Number of planned usage examples")

    # Outputs
    weight: Literal["lightweight", "medium", "heavyweight"] = dspy.OutputField(
        desc="One of: lightweight, medium, heavyweight"
    )
    weight_justification: str = dspy.OutputField(desc="Explanation using guidelines matrix")


class DecideLoadPriority(dspy.Signature):
    """Determine load priority using decision tree.

    Step 2.3 of Phase 2 - Uses the decision tree from guidelines lines 297-316:

    Decision Tree:
    ```
    Is this a core/foundational skill?
    ├─ Yes → load_priority: "always"
    └─ No
       ├─ Is this commonly used across tasks?
       │  ├─ Yes → load_priority: "task_specific"
       │  └─ No
       │     ├─ Is this rarely needed or experimental?
       │     │  ├─ Yes → load_priority: "on_demand" or "dormant"
    ```

    From guidelines line 1073: "Load priority chosen using decision tree"
    """

    # Inputs
    problem_statement: str = dspy.InputField(desc="Problem statement")
    skill_type: str = dspy.InputField(desc="Skill type")
    is_core_foundation: bool = dspy.InputField(desc="Is this a foundational skill?")
    is_commonly_used: bool = dspy.InputField(desc="Is this commonly used across tasks?")
    is_experimental: bool = dspy.InputField(desc="Is this experimental or unstable?")

    # Outputs
    load_priority: Literal["always", "task_specific", "on_demand", "dormant"] = dspy.OutputField(
        desc="One of: always, task_specific, on_demand, dormant"
    )
    priority_justification: str = dspy.OutputField(
        desc="Decision trace through tree with reasoning"
    )


class DesignCapabilities(dspy.Signature):
    """Design 3-7 atomic capabilities.

    Step 2.4 of Phase 2 - Designs atomic, testable capabilities following
    guidelines lines 354-414.

    Key principles:
    - Each capability must be atomic and testable
    - Each must have single responsibility
    - Clear input/output contracts
    - Cross-referencable for composition

    From guidelines line 1068: "All capabilities have content outlines"
    """

    # Inputs
    problem_statement: str = dspy.InputField(desc="Problem statement")
    phase1_requirements: list[str] = dspy.InputField(desc="Key requirements from Phase 1")
    target_count: int = dspy.InputField(desc="Target number of capabilities (3-7)")

    # Outputs
    capabilities: list[Capability] = dspy.OutputField(
        desc="List of atomic capabilities (3-7 items)"
    )
    capability_count: int = dspy.OutputField(desc="Actual number of capabilities designed")
    atomicity_analysis: str = dspy.OutputField(desc="Analysis of each capability's atomicity")


class ValidateDependencies(dspy.Signature):
    """Validate dependencies against 5 composition rules.

    Step 2.5 of Phase 2 - Validates against composition rules from
    guidelines lines 318-344:

    5 Composition Rules:
    1. No cycles - Dependency graph must be acyclic
    2. Prefer abstractions - Depend on interfaces, not implementations
    3. Specify versions - Pin dependency versions for reproducibility
    4. Minimize depth - Keep dependency depth to 2-3 levels max
    5. Document why - Explain why each dependency is needed
    """

    # Inputs
    proposed_dependencies: list[DependencyRef] = dspy.InputField(
        desc="Proposed dependency references"
    )
    existing_taxonomy: str = dspy.InputField(desc="JSON of taxonomy for cycle detection")

    # Outputs
    dependencies_valid: bool = dspy.OutputField(desc="True if all 5 rules pass")
    validation_details: list[dict] = dspy.OutputField(desc="Result for each of the 5 rules")
    suggested_revisions: list[str] = dspy.OutputField(desc="Suggestions to fix violations (if any)")


class GenerateSkillMetadata(dspy.Signature):
    """Generate complete skill metadata following agentskills.io spec.

    Step 2.6 of Phase 2 - Creates the complete skill metadata that includes
    all decisions from Phase 1 and Phase 2.

    From guidelines lines 1066-1067:
    - metadata.json is complete and valid
    - Directory structure is planned
    """

    # Inputs - All Phase 1 and Phase 2 outputs
    phase1_outputs: str = dspy.InputField(
        desc="JSON of Phase 1 outputs (problem_statement, skill_type, proposed_path)"
    )
    confirmed_type: str = dspy.InputField(desc="Confirmed skill type")
    weight: str = dspy.InputField(desc="Weight from DetermineWeight")
    load_priority: str = dspy.InputField(desc="Load priority from DecideLoadPriority")
    capabilities: list[Capability] = dspy.InputField(desc="Capabilities from DesignCapabilities")
    dependencies: list[DependencyRef] = dspy.InputField(
        desc="Validated dependencies from ValidateDependencies"
    )

    # Outputs - Complete skill metadata
    skill_metadata: SkillMetadata = dspy.OutputField(
        desc="Complete skill metadata following agentskills.io spec"
    )
    resource_requirements: ResourceRequirements = dspy.OutputField(desc="External resources needed")
    compatibility_constraints: CompatibilityConstraints = dspy.OutputField(
        desc="Platform requirements and conflicts"
    )


class Phase2Checkpoint(dspy.Signature):
    """Validate Phase 2 outputs before proceeding to Phase 3.

    This checkpoint enforces the validation criteria from guidelines lines 1066-1073:
    1. metadata.json is complete and valid
    2. Directory structure is planned
    3. All capabilities have content outlines
    4. Examples are planned for each capability
    5. Tests are planned
    6. Type determined using decision matrix
    7. Weight assigned based on capability count
    8. Load priority chosen using decision tree

    The checkpoint returns:
    - checkpoint_passed: True if all criteria met
    - checkpoint_score: 0.0-1.0 overall score
    - readiness_for_phase3: True if ready for content generation
    """

    # Inputs - All Phase 2 outputs
    skill_metadata: str = dspy.InputField(desc="JSON of skill metadata from GenerateSkillMetadata")
    capabilities: list[Capability] = dspy.InputField(desc="List of capabilities")
    dependencies: list[DependencyRef] = dspy.InputField(desc="List of validated dependencies")
    confirmed_type: str = dspy.InputField(desc="Confirmed skill type")
    weight: str = dspy.InputField(desc="Weight assignment")
    load_priority: str = dspy.InputField(desc="Load priority decision")

    # Outputs - Checkpoint validation
    checkpoint_passed: bool = dspy.OutputField(desc="True if all validation criteria are met")
    validation_errors: list[str] = dspy.OutputField(
        desc="List of any validation failures (empty if passed)"
    )
    checkpoint_score: float = dspy.OutputField(
        desc="0.0-1.0 overall checkpoint score (>=0.8 to proceed)"
    )
    readiness_for_phase3: bool = dspy.OutputField(
        desc="True if ready to proceed to content generation"
    )


__all__ = [
    "VALID_WEIGHTS",
    "VALID_PRIORITIES",
    "VALID_SKILL_TYPES",
    "ConfirmSkillType",
    "DetermineWeight",
    "DecideLoadPriority",
    "DesignCapabilities",
    "ValidateDependencies",
    "GenerateSkillMetadata",
    "Phase2Checkpoint",
]
