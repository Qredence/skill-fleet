"""DSPy modules for skill creation workflow steps.

Each module encapsulates one step of the workflow with its own
logic, validation, and error handling.

This module provides two types of modules:
1. Standard modules (ChainOfThought) - faster, single-shot generation
2. Quality-assured modules (with Refine/BestOfN) - higher quality, multiple attempts

Approved LLM Models:
- gemini-3-flash-preview: Primary model for all steps
- gemini-3-pro-preview: For GEPA reflection
- deepseek-v3.2: Cost-effective alternative
- Nemotron-3-Nano-30B-A3B: Lightweight operations
"""

from __future__ import annotations

import json
import logging
from typing import Any

import dspy

from .models import Capability, ExampleGatheringConfig
from .signatures import (
    EditSkillContent,
    GatherExamplesForSkill,
    InitializeSkillSkeleton,
    IterateSkillWithFeedback,
    PackageSkillForApproval,
    PlanSkillStructure,
    UnderstandTaskForSkill,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Safe JSON Parsing Utilities
# =============================================================================


def safe_json_loads(
    value: str | Any,
    default: dict | list | None = None,
    field_name: str = "unknown",
) -> dict | list:
    """Safely parse JSON string with fallback to default.

    Handles:
    - Already parsed objects (returns as-is)
    - Valid JSON strings (parses and returns)
    - Invalid JSON (returns default with warning)

    Args:
        value: String to parse or already-parsed object
        default: Default value if parsing fails (dict or list)
        field_name: Field name for logging

    Returns:
        Parsed JSON or default value (never None)
    """
    if default is None:
        default = {}

    # Already parsed (dict, list, or Pydantic model)
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        # Handle list of Pydantic models
        return [item.model_dump() if hasattr(item, "model_dump") else item for item in value]
    if hasattr(value, "model_dump"):  # Pydantic model
        return value.model_dump()

    # Empty or None
    if not value:
        return default

    # Try to parse JSON string
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.warning(
                f"Failed to parse JSON for field '{field_name}': {e}. "
                f"Value preview: {value[:100]}..."
            )
            return default

    # Unknown type
    logger.warning(f"Unexpected type for field '{field_name}': {type(value)}")
    return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float.

    Args:
        value: Value to convert
        default: Default if conversion fails

    Returns:
        Float value
    """
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


# =============================================================================
# Standard Modules
# =============================================================================


class GatherExamplesModule(dspy.Module):
    """Module for Step 0: Gathering concrete examples before skill creation.

    This module iteratively asks clarifying questions and collects usage
    examples from the user until we have enough context to proceed with
    skill creation. This ensures skills are grounded in real use cases.
    """

    def __init__(self):
        super().__init__()
        self.gather = dspy.ChainOfThought(GatherExamplesForSkill)

    def forward(
        self,
        task_description: str,
        user_responses: list[dict] | None = None,
        collected_examples: list[dict] | None = None,
        config: ExampleGatheringConfig | None = None,
    ) -> dict:
        """Gather examples and ask clarifying questions.

        Args:
            task_description: Original task description from user
            user_responses: Previous answers to clarifying questions
            collected_examples: Examples collected so far
            config: Configuration for gathering process

        Returns:
            Dict with clarifying_questions, new_examples, terminology_updates,
            refined_task, readiness_score, and readiness_reasoning
        """
        if user_responses is None:
            user_responses = []
        if collected_examples is None:
            collected_examples = []
        if config is None:
            config = ExampleGatheringConfig()

        result = self.gather(
            task_description=task_description,
            user_responses=json.dumps(user_responses, indent=2),
            collected_examples=json.dumps(collected_examples, indent=2),
            config=config.model_dump_json(indent=2),
        )

        # Parse new examples from result
        new_examples = []
        if hasattr(result, "new_examples") and result.new_examples:
            for ex in result.new_examples:
                if isinstance(ex, dict):
                    new_examples.append(ex)
                elif hasattr(ex, "model_dump"):
                    new_examples.append(ex.model_dump())
                else:
                    new_examples.append({"input_description": str(ex), "expected_output": ""})

        # Parse clarifying questions
        questions = []
        if hasattr(result, "clarifying_questions") and result.clarifying_questions:
            for q in result.clarifying_questions:
                if isinstance(q, dict):
                    questions.append(q)
                elif hasattr(q, "model_dump"):
                    questions.append(q.model_dump())
                else:
                    questions.append({"id": "q1", "question": str(q)})

        # Parse terminology updates
        term_updates = {}
        if hasattr(result, "terminology_updates") and result.terminology_updates:
            if isinstance(result.terminology_updates, dict):
                term_updates = result.terminology_updates
            else:
                term_updates = safe_json_loads(
                    result.terminology_updates, default={}, field_name="terminology_updates"
                )

        return {
            "clarifying_questions": questions,
            "new_examples": new_examples,
            "terminology_updates": term_updates,
            "refined_task": getattr(result, "refined_task", task_description),
            "readiness_score": safe_float(getattr(result, "readiness_score", 0.0), default=0.0),
            "readiness_reasoning": getattr(result, "readiness_reasoning", ""),
        }

    async def aforward(
        self,
        task_description: str,
        user_responses: list[dict] | None = None,
        collected_examples: list[dict] | None = None,
        config: ExampleGatheringConfig | None = None,
    ) -> dict:
        """Gather examples asynchronously."""
        if user_responses is None:
            user_responses = []
        if collected_examples is None:
            collected_examples = []
        if config is None:
            config = ExampleGatheringConfig()

        result = await self.gather.acall(
            task_description=task_description,
            user_responses=json.dumps(user_responses, indent=2),
            collected_examples=json.dumps(collected_examples, indent=2),
            config=config.model_dump_json(indent=2),
        )

        # Parse new examples from result
        new_examples = []
        if hasattr(result, "new_examples") and result.new_examples:
            for ex in result.new_examples:
                if isinstance(ex, dict):
                    new_examples.append(ex)
                elif hasattr(ex, "model_dump"):
                    new_examples.append(ex.model_dump())
                else:
                    new_examples.append({"input_description": str(ex), "expected_output": ""})

        # Parse clarifying questions
        questions = []
        if hasattr(result, "clarifying_questions") and result.clarifying_questions:
            for q in result.clarifying_questions:
                if isinstance(q, dict):
                    questions.append(q)
                elif hasattr(q, "model_dump"):
                    questions.append(q.model_dump())
                else:
                    questions.append({"id": "q1", "question": str(q)})

        # Parse terminology updates
        term_updates = {}
        if hasattr(result, "terminology_updates") and result.terminology_updates:
            if isinstance(result.terminology_updates, dict):
                term_updates = result.terminology_updates
            else:
                term_updates = safe_json_loads(
                    result.terminology_updates, default={}, field_name="terminology_updates"
                )

        return {
            "clarifying_questions": questions,
            "new_examples": new_examples,
            "terminology_updates": term_updates,
            "refined_task": getattr(result, "refined_task", task_description),
            "readiness_score": safe_float(getattr(result, "readiness_score", 0.0), default=0.0),
            "readiness_reasoning": getattr(result, "readiness_reasoning", ""),
        }


class UnderstandModule(dspy.Module):
    """Module for Step 1: Understanding task and mapping to taxonomy."""

    def __init__(self):
        super().__init__()
        self.understand = dspy.ChainOfThought(UnderstandTaskForSkill)

    def forward(
        self,
        task_description: str,
        existing_skills: list[str],
        taxonomy_structure: dict,
    ) -> dict:
        """Analyze task and determine taxonomy placement.

        Returns:
            Dict with task_intent, taxonomy_path, parent_skills,
            dependency_analysis, and confidence_score
        """
        result = self.understand(
            task_description=task_description,
            existing_skills=json.dumps(existing_skills, indent=2),
            taxonomy_structure=json.dumps(taxonomy_structure, indent=2),
        )

        return {
            "task_intent": result.task_intent,
            "taxonomy_path": result.taxonomy_path.strip(),
            "parent_skills": safe_json_loads(
                result.parent_skills, default=[], field_name="parent_skills"
            ),
            "dependency_analysis": safe_json_loads(
                result.dependency_analysis, default={}, field_name="dependency_analysis"
            ),
            "confidence_score": safe_float(result.confidence_score, default=0.5),
        }

    async def aforward(
        self,
        task_description: str,
        existing_skills: list[str],
        taxonomy_structure: dict,
    ) -> dict:
        """Analyze task asynchronously."""
        result = await self.understand.acall(
            task_description=task_description,
            existing_skills=json.dumps(existing_skills, indent=2),
            taxonomy_structure=json.dumps(taxonomy_structure, indent=2),
        )

        return {
            "task_intent": result.task_intent,
            "taxonomy_path": result.taxonomy_path.strip(),
            "parent_skills": safe_json_loads(
                result.parent_skills, default=[], field_name="parent_skills"
            ),
            "dependency_analysis": safe_json_loads(
                result.dependency_analysis, default={}, field_name="dependency_analysis"
            ),
            "confidence_score": safe_float(result.confidence_score, default=0.5),
        }


class PlanModule(dspy.Module):
    """Module for Step 2: Planning skill structure."""

    def __init__(self):
        super().__init__()
        self.plan = dspy.ChainOfThought(PlanSkillStructure)

    def forward(
        self,
        task_intent: str,
        taxonomy_path: str,
        parent_skills: list[dict],
        dependency_analysis: dict | str,
    ) -> dict:
        """Design skill structure with dependencies.

        Returns:
            Dict with skill_metadata, dependencies, capabilities,
            resource_requirements, compatibility_constraints,
            and composition_strategy
        """
        # Serialize dependency_analysis if it's a dict (from UnderstandModule)
        dependency_analysis_str = (
            json.dumps(dependency_analysis, indent=2)
            if isinstance(dependency_analysis, dict)
            else dependency_analysis
        )

        result = self.plan(
            task_intent=task_intent,
            taxonomy_path=taxonomy_path,
            parent_skills=json.dumps(parent_skills, indent=2),
            dependency_analysis=dependency_analysis_str,
        )

        return {
            "skill_metadata": safe_json_loads(
                result.skill_metadata, default={}, field_name="skill_metadata"
            ),
            "dependencies": safe_json_loads(
                result.dependencies, default=[], field_name="dependencies"
            ),
            "capabilities": safe_json_loads(
                result.capabilities, default=[], field_name="capabilities"
            ),
            "resource_requirements": safe_json_loads(
                result.resource_requirements, default={}, field_name="resource_requirements"
            ),
            "compatibility_constraints": safe_json_loads(
                result.compatibility_constraints,
                default={},
                field_name="compatibility_constraints",
            ),
            "composition_strategy": result.composition_strategy,
        }

    async def aforward(
        self,
        task_intent: str,
        taxonomy_path: str,
        parent_skills: list[dict],
        dependency_analysis: dict | str,
    ) -> dict:
        """Design skill structure asynchronously."""
        # Serialize dependency_analysis if it's a dict (from UnderstandModule)
        dependency_analysis_str = (
            json.dumps(dependency_analysis, indent=2)
            if isinstance(dependency_analysis, dict)
            else dependency_analysis
        )

        result = await self.plan.acall(
            task_intent=task_intent,
            taxonomy_path=taxonomy_path,
            parent_skills=json.dumps(parent_skills, indent=2),
            dependency_analysis=dependency_analysis_str,
        )

        return {
            "skill_metadata": safe_json_loads(
                result.skill_metadata, default={}, field_name="skill_metadata"
            ),
            "dependencies": safe_json_loads(
                result.dependencies, default=[], field_name="dependencies"
            ),
            "capabilities": safe_json_loads(
                result.capabilities, default=[], field_name="capabilities"
            ),
            "resource_requirements": safe_json_loads(
                result.resource_requirements, default={}, field_name="resource_requirements"
            ),
            "compatibility_constraints": safe_json_loads(
                result.compatibility_constraints,
                default={},
                field_name="compatibility_constraints",
            ),
            "composition_strategy": result.composition_strategy,
        }


class InitializeModule(dspy.Module):
    """Module for Step 3: Initializing skill skeleton."""

    def __init__(self):
        super().__init__()
        self.initialize = dspy.ChainOfThought(InitializeSkillSkeleton)

    def forward(
        self,
        skill_metadata: dict,
        capabilities: list[Capability] | list[dict],
        taxonomy_path: str,
    ) -> dict:
        """Create a skill file structure.

        Returns:
            Dict with skill_skeleton and validation_checklist
        """
        # Note: capabilities can be either Pydantic Capability objects (from PlanModule)
        # or plain dicts (from tests). We need to serialize them to JSON for the LLM.
        # Use .model_dump() for Pydantic objects to convert to dict, then json.dumps()
        # to create the JSON string expected by the LLM.
        result = self.initialize(
            skill_metadata=json.dumps(skill_metadata, indent=2),
            capabilities=json.dumps(
                [c.model_dump() if hasattr(c, "model_dump") else c for c in capabilities], indent=2
            ),
            taxonomy_path=taxonomy_path,
        )

        return {
            "skill_skeleton": safe_json_loads(
                result.skill_skeleton, default={}, field_name="skill_skeleton"
            ),
            "validation_checklist": safe_json_loads(
                result.validation_checklist, default=[], field_name="validation_checklist"
            ),
        }

    async def aforward(
        self,
        skill_metadata: dict,
        capabilities: list[Capability] | list[dict],
        taxonomy_path: str,
    ) -> dict:
        """Create a skill file structure asynchronously."""
        result = await self.initialize.acall(
            skill_metadata=json.dumps(skill_metadata, indent=2),
            capabilities=json.dumps(
                [c.model_dump() if hasattr(c, "model_dump") else c for c in capabilities], indent=2
            ),
            taxonomy_path=taxonomy_path,
        )

        return {
            "skill_skeleton": safe_json_loads(
                result.skill_skeleton, default={}, field_name="skill_skeleton"
            ),
            "validation_checklist": safe_json_loads(
                result.validation_checklist, default=[], field_name="validation_checklist"
            ),
        }


class EditModule(dspy.Module):
    """Module for Step 4: Editing skill content."""

    def __init__(self):
        super().__init__()
        self.edit = dspy.ChainOfThought(EditSkillContent)

    def forward(
        self,
        skill_skeleton: dict,
        parent_skills: str,
        composition_strategy: str,
        revision_feedback: str | None = None,
    ) -> dict:
        """Generate comprehensive skill content.

        Args:
            skill_skeleton: Directory structure
            parent_skills: Context from related skills
            composition_strategy: How skill composes with others
            revision_feedback: Optional feedback for regeneration

        Returns:
            Dict with skill_content, capability_implementations,
            usage_examples, best_practices, and integration_guide
        """
        # TODO: Incorporate revision_feedback into prompt
        result = self.edit(
            skill_skeleton=json.dumps(skill_skeleton, indent=2),
            parent_skills=parent_skills,
            composition_strategy=composition_strategy,
        )

        return {
            "skill_content": result.skill_content,
            "capability_implementations": safe_json_loads(
                result.capability_implementations,
                default={},
                field_name="capability_implementations",
            ),
            "usage_examples": safe_json_loads(
                result.usage_examples, default=[], field_name="usage_examples"
            ),
            "best_practices": safe_json_loads(
                result.best_practices, default=[], field_name="best_practices"
            ),
            "integration_guide": result.integration_guide,
        }

    async def aforward(
        self,
        skill_skeleton: dict,
        parent_skills: str,
        composition_strategy: str,
        revision_feedback: str | None = None,
    ) -> dict:
        """Generate comprehensive skill content asynchronously."""
        result = await self.edit.acall(
            skill_skeleton=json.dumps(skill_skeleton, indent=2),
            parent_skills=parent_skills,
            composition_strategy=composition_strategy,
        )

        return {
            "skill_content": result.skill_content,
            "capability_implementations": safe_json_loads(
                result.capability_implementations,
                default={},
                field_name="capability_implementations",
            ),
            "usage_examples": safe_json_loads(
                result.usage_examples, default=[], field_name="usage_examples"
            ),
            "best_practices": safe_json_loads(
                result.best_practices, default=[], field_name="best_practices"
            ),
            "integration_guide": result.integration_guide,
        }


class PackageModule(dspy.Module):
    """Module for Step 5: Packaging and validation."""

    def __init__(self):
        super().__init__()
        self.package = dspy.ChainOfThought(PackageSkillForApproval)

    def forward(
        self,
        skill_content: str,
        skill_metadata: dict,
        taxonomy_path: str,
        capability_implementations: str,
    ) -> dict:
        """Validate and package skill for approval.

        Returns:
            Dict with validation_report, integration_tests,
            packaging_manifest, and quality_score
        """
        result = self.package(
            skill_content=skill_content,
            skill_metadata=json.dumps(skill_metadata, indent=2),
            taxonomy_path=taxonomy_path,
            capability_implementations=capability_implementations,
        )

        default_report = {"passed": False, "status": "unknown", "errors": []}
        report = safe_json_loads(
            result.validation_report, default=default_report, field_name="validation_report"
        )

        return {
            "validation_report": report,
            "integration_tests": safe_json_loads(
                result.integration_tests, default=[], field_name="integration_tests"
            ),
            "packaging_manifest": safe_json_loads(
                result.packaging_manifest, default={}, field_name="packaging_manifest"
            ),
            "quality_score": safe_float(result.quality_score, default=0.0),
        }

    async def aforward(
        self,
        skill_content: str,
        skill_metadata: dict,
        taxonomy_path: str,
        capability_implementations: str,
    ) -> dict:
        """Validate and package skill for approval asynchronously."""
        result = await self.package.acall(
            skill_content=skill_content,
            skill_metadata=json.dumps(skill_metadata, indent=2),
            taxonomy_path=taxonomy_path,
            capability_implementations=capability_implementations,
        )

        default_report = {"passed": False, "status": "unknown", "errors": []}
        report = safe_json_loads(
            result.validation_report, default=default_report, field_name="validation_report"
        )

        return {
            "validation_report": report,
            "integration_tests": safe_json_loads(
                result.integration_tests, default=[], field_name="integration_tests"
            ),
            "packaging_manifest": safe_json_loads(
                result.packaging_manifest, default={}, field_name="packaging_manifest"
            ),
            "quality_score": safe_float(result.quality_score, default=0.0),
        }


class IterateModule(dspy.Module):
    """Module for Step 6: Iteration with human feedback."""

    def __init__(self):
        super().__init__()
        self.iterate = dspy.ChainOfThought(IterateSkillWithFeedback)

    def forward(
        self,
        packaged_skill: str,
        validation_report: dict,
        human_feedback: str,
        usage_analytics: dict | None = None,
    ) -> dict:
        """Process human feedback and determine next steps.

        Returns:
            Dict with approval_status, revision_plan,
            evolution_metadata, and next_steps
        """
        result = self.iterate(
            packaged_skill=packaged_skill,
            validation_report=json.dumps(validation_report, indent=2),
            human_feedback=human_feedback,
            usage_analytics=json.dumps(usage_analytics or {}),
        )

        return {
            "approval_status": result.approval_status.strip().lower(),
            "revision_plan": safe_json_loads(
                result.revision_plan, default={}, field_name="revision_plan"
            ),
            "evolution_metadata": safe_json_loads(
                result.evolution_metadata, default={}, field_name="evolution_metadata"
            ),
            "next_steps": result.next_steps,
        }

    async def aforward(
        self,
        packaged_skill: str,
        validation_report: dict,
        human_feedback: str,
        usage_analytics: dict | None = None,
    ) -> dict:
        """Process human feedback and determine next steps asynchronously."""
        result = await self.iterate.acall(
            packaged_skill=packaged_skill,
            validation_report=json.dumps(validation_report, indent=2),
            human_feedback=human_feedback,
            usage_analytics=json.dumps(usage_analytics or {}),
        )

        return {
            "approval_status": result.approval_status.strip().lower(),
            "revision_plan": safe_json_loads(
                result.revision_plan, default={}, field_name="revision_plan"
            ),
            "evolution_metadata": safe_json_loads(
                result.evolution_metadata, default={}, field_name="evolution_metadata"
            ),
            "next_steps": result.next_steps,
        }


# =============================================================================
# Quality-Assured Modules (with Refine/BestOfN)
# =============================================================================
# These modules wrap the base modules with quality assurance:
# - Refine: Automatic feedback loop to improve outputs
# - BestOfN: Generate multiple candidates and select the best


class UnderstandModuleQA(dspy.Module):
    """Quality-assured UnderstandModule with Refine wrapper.

    Uses dspy.Refine to automatically retry and improve taxonomy
    path selection based on the taxonomy_path_reward function.
    """

    def __init__(self, n_refinements: int = 3, threshold: float = 0.8):
        """Initialize with refinement parameters.

        Args:
            n_refinements: Maximum attempts before accepting best result
            threshold: Score threshold to accept result early (0.0-1.0)
        """
        super().__init__()
        from .rewards import taxonomy_path_reward

        # Wrap ChainOfThought with Refine for automatic feedback
        self.understand = dspy.Refine(
            module=dspy.ChainOfThought(UnderstandTaskForSkill),
            N=n_refinements,
            reward_fn=taxonomy_path_reward,
            threshold=threshold,
        )
        self._n_refinements = n_refinements
        self._threshold = threshold

    def forward(
        self,
        task_description: str,
        existing_skills: list[str],
        taxonomy_structure: dict,
    ) -> dict:
        """Analyze task with quality assurance.

        Returns:
            Dict with task_intent, taxonomy_path, parent_skills,
            dependency_analysis, and confidence_score
        """
        result = self.understand(
            task_description=task_description,
            existing_skills=json.dumps(existing_skills, indent=2),
            taxonomy_structure=json.dumps(taxonomy_structure, indent=2),
        )

        return {
            "task_intent": result.task_intent,
            "taxonomy_path": result.taxonomy_path.strip(),
            "parent_skills": safe_json_loads(
                result.parent_skills, default=[], field_name="parent_skills"
            ),
            "dependency_analysis": safe_json_loads(
                result.dependency_analysis, default={}, field_name="dependency_analysis"
            ),
            "confidence_score": safe_float(result.confidence_score, default=0.5),
        }

    async def aforward(
        self,
        task_description: str,
        existing_skills: list[str],
        taxonomy_structure: dict,
    ) -> dict:
        """Analyze task with quality assurance asynchronously."""
        result = await self.understand.acall(
            task_description=task_description,
            existing_skills=json.dumps(existing_skills, indent=2),
            taxonomy_structure=json.dumps(taxonomy_structure, indent=2),
        )

        return {
            "task_intent": result.task_intent,
            "taxonomy_path": result.taxonomy_path.strip(),
            "parent_skills": safe_json_loads(
                result.parent_skills, default=[], field_name="parent_skills"
            ),
            "dependency_analysis": safe_json_loads(
                result.dependency_analysis, default={}, field_name="dependency_analysis"
            ),
            "confidence_score": safe_float(result.confidence_score, default=0.5),
        }


class PlanModuleQA(dspy.Module):
    """Quality-assured PlanModule with Refine wrapper.

    Uses dspy.Refine to ensure metadata completeness and validity.
    """

    def __init__(self, n_refinements: int = 3, threshold: float = 0.8):
        super().__init__()
        from .rewards import combined_plan_reward

        self.plan = dspy.Refine(
            module=dspy.ChainOfThought(PlanSkillStructure),
            N=n_refinements,
            reward_fn=combined_plan_reward,
            threshold=threshold,
        )

    def forward(
        self,
        task_intent: str,
        taxonomy_path: str,
        parent_skills: list[dict],
        dependency_analysis: dict | str,
    ) -> dict:
        """Design skill structure with quality assurance."""
        # Serialize dependency_analysis if it's a dict (from UnderstandModule)
        dependency_analysis_str = (
            json.dumps(dependency_analysis, indent=2)
            if isinstance(dependency_analysis, dict)
            else dependency_analysis
        )

        result = self.plan(
            task_intent=task_intent,
            taxonomy_path=taxonomy_path,
            parent_skills=json.dumps(parent_skills, indent=2),
            dependency_analysis=dependency_analysis_str,
        )

        return {
            "skill_metadata": safe_json_loads(
                result.skill_metadata, default={}, field_name="skill_metadata"
            ),
            "dependencies": safe_json_loads(
                result.dependencies, default=[], field_name="dependencies"
            ),
            "capabilities": safe_json_loads(
                result.capabilities, default=[], field_name="capabilities"
            ),
            "resource_requirements": safe_json_loads(
                result.resource_requirements, default={}, field_name="resource_requirements"
            ),
            "compatibility_constraints": safe_json_loads(
                result.compatibility_constraints,
                default={},
                field_name="compatibility_constraints",
            ),
            "composition_strategy": result.composition_strategy,
        }

    async def aforward(
        self,
        task_intent: str,
        taxonomy_path: str,
        parent_skills: list[dict],
        dependency_analysis: dict | str,
    ) -> dict:
        """Design skill structure with quality assurance asynchronously."""
        # Serialize dependency_analysis if it's a dict (from UnderstandModule)
        dependency_analysis_str = (
            json.dumps(dependency_analysis, indent=2)
            if isinstance(dependency_analysis, dict)
            else dependency_analysis
        )

        result = await self.plan.acall(
            task_intent=task_intent,
            taxonomy_path=taxonomy_path,
            parent_skills=json.dumps(parent_skills, indent=2),
            dependency_analysis=dependency_analysis_str,
        )

        return {
            "skill_metadata": safe_json_loads(
                result.skill_metadata, default={}, field_name="skill_metadata"
            ),
            "dependencies": safe_json_loads(
                result.dependencies, default=[], field_name="dependencies"
            ),
            "capabilities": safe_json_loads(
                result.capabilities, default=[], field_name="capabilities"
            ),
            "resource_requirements": safe_json_loads(
                result.resource_requirements, default={}, field_name="resource_requirements"
            ),
            "compatibility_constraints": safe_json_loads(
                result.compatibility_constraints,
                default={},
                field_name="compatibility_constraints",
            ),
            "composition_strategy": result.composition_strategy,
        }


class EditModuleQA(dspy.Module):
    """Quality-assured EditModule with BestOfN wrapper.

    Uses dspy.BestOfN to generate multiple content candidates
    and select the best based on content quality scoring.
    """

    def __init__(self, n_candidates: int = 3, threshold: float = 0.85):
        """Initialize with BestOfN parameters.

        Args:
            n_candidates: Number of content candidates to generate
            threshold: Score threshold to accept result early (0.0-1.0)
        """
        super().__init__()
        from .rewards import combined_edit_reward

        # Use BestOfN for content generation - pick best of N attempts
        self.edit = dspy.BestOfN(
            module=dspy.ChainOfThought(EditSkillContent),
            N=n_candidates,
            reward_fn=combined_edit_reward,
            threshold=threshold,
        )
        self._n_candidates = n_candidates
        self._threshold = threshold

    def forward(
        self,
        skill_skeleton: dict,
        parent_skills: str,
        composition_strategy: str,
        revision_feedback: str | None = None,
    ) -> dict:
        """Generate skill content with quality assurance.

        Args:
            skill_skeleton: Directory structure
            parent_skills: Context from related skills
            composition_strategy: How skill composes with others
            revision_feedback: Optional feedback for regeneration

        Returns:
            Dict with skill_content, capability_implementations,
            usage_examples, best_practices, and integration_guide
        """
        # TODO: Incorporate revision_feedback into prompt
        result = self.edit(
            skill_skeleton=json.dumps(skill_skeleton, indent=2),
            parent_skills=parent_skills,
            composition_strategy=composition_strategy,
        )

        return {
            "skill_content": result.skill_content,
            "capability_implementations": safe_json_loads(
                result.capability_implementations,
                default={},
                field_name="capability_implementations",
            ),
            "usage_examples": safe_json_loads(
                result.usage_examples, default=[], field_name="usage_examples"
            ),
            "best_practices": safe_json_loads(
                result.best_practices, default=[], field_name="best_practices"
            ),
            "integration_guide": result.integration_guide,
        }

    async def aforward(
        self,
        skill_skeleton: dict,
        parent_skills: str,
        composition_strategy: str,
        revision_feedback: str | None = None,
    ) -> dict:
        """Generate skill content with quality assurance asynchronously."""
        result = await self.edit.acall(
            skill_skeleton=json.dumps(skill_skeleton, indent=2),
            parent_skills=parent_skills,
            composition_strategy=composition_strategy,
        )

        return {
            "skill_content": result.skill_content,
            "capability_implementations": safe_json_loads(
                result.capability_implementations,
                default={},
                field_name="capability_implementations",
            ),
            "usage_examples": safe_json_loads(
                result.usage_examples, default=[], field_name="usage_examples"
            ),
            "best_practices": safe_json_loads(
                result.best_practices, default=[], field_name="best_practices"
            ),
            "integration_guide": result.integration_guide,
        }


class PackageModuleQA(dspy.Module):
    """Quality-assured PackageModule with Refine wrapper.

    Uses dspy.Refine to ensure validation report completeness.
    """

    def __init__(self, n_refinements: int = 2, threshold: float = 0.9):
        super().__init__()
        from .rewards import combined_package_reward

        self.package = dspy.Refine(
            module=dspy.ChainOfThought(PackageSkillForApproval),
            N=n_refinements,
            reward_fn=combined_package_reward,
            threshold=threshold,
        )

    def forward(
        self,
        skill_content: str,
        skill_metadata: dict,
        taxonomy_path: str,
        capability_implementations: str,
    ) -> dict:
        """Validate and package skill with quality assurance."""
        result = self.package(
            skill_content=skill_content,
            skill_metadata=json.dumps(skill_metadata, indent=2),
            taxonomy_path=taxonomy_path,
            capability_implementations=capability_implementations,
        )

        default_report = {"passed": False, "status": "unknown", "errors": []}
        report = safe_json_loads(
            result.validation_report,
            default=default_report,
            field_name="validation_report",
        )

        return {
            "validation_report": report,
            "integration_tests": safe_json_loads(
                result.integration_tests, default=[], field_name="integration_tests"
            ),
            "packaging_manifest": safe_json_loads(
                result.packaging_manifest, default={}, field_name="packaging_manifest"
            ),
            "quality_score": safe_float(result.quality_score, default=0.0),
        }

    async def aforward(
        self,
        skill_content: str,
        skill_metadata: dict,
        taxonomy_path: str,
        capability_implementations: str,
    ) -> dict:
        """Validate and package skill with quality assurance asynchronously."""
        result = await self.package.acall(
            skill_content=skill_content,
            skill_metadata=json.dumps(skill_metadata, indent=2),
            taxonomy_path=taxonomy_path,
            capability_implementations=capability_implementations,
        )

        default_report = {"passed": False, "status": "unknown", "errors": []}
        report = safe_json_loads(
            result.validation_report,
            default=default_report,
            field_name="validation_report",
        )

        return {
            "validation_report": report,
            "integration_tests": safe_json_loads(
                result.integration_tests, default=[], field_name="integration_tests"
            ),
            "packaging_manifest": safe_json_loads(
                result.packaging_manifest, default={}, field_name="packaging_manifest"
            ),
            "quality_score": safe_float(result.quality_score, default=0.0),
        }


# =============================================================================
# Module Factory
# =============================================================================


def create_modules(
    quality_assured: bool = False,
    understand_refinements: int = 3,
    plan_refinements: int = 3,
    edit_candidates: int = 3,
    package_refinements: int = 2,
) -> dict[str, dspy.Module]:
    """Create a set of workflow modules.

    Args:
        quality_assured: If True, use Refine/BestOfN wrappers
        understand_refinements: Max refinements for UnderstandModule
        plan_refinements: Max refinements for PlanModule
        edit_candidates: Number of candidates for EditModule
        package_refinements: Max refinements for PackageModule

    Returns:
        Dict mapping step names to modules
    """
    if quality_assured:
        return {
            "understand": UnderstandModuleQA(n_refinements=understand_refinements),
            "plan": PlanModuleQA(n_refinements=plan_refinements),
            "initialize": InitializeModule(),  # No QA needed for skeleton
            "edit": EditModuleQA(n_candidates=edit_candidates),
            "package": PackageModuleQA(n_refinements=package_refinements),
            "iterate": IterateModule(),  # No QA needed for feedback processing
        }
    else:
        return {
            "understand": UnderstandModule(),
            "plan": PlanModule(),
            "initialize": InitializeModule(),
            "edit": EditModule(),
            "package": PackageModule(),
            "iterate": IterateModule(),
        }
