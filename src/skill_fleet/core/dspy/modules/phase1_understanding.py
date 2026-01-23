"""DSPy modules for Phase 1: Understanding & Planning."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import dspy

from ....common.async_utils import run_async
from ....common.dspy_compat import coerce_reasoning_text
from ....common.utils import safe_float, safe_json_loads
from ..signatures.phase1_understanding import (
    AnalyzeDependencies,
    AnalyzeIntent,
    FindTaxonomyPath,
    GatherRequirements,
    SynthesizePlan,
)

logger = logging.getLogger(__name__)


class RequirementsGathererModule(dspy.Module):
    """Module for gathering requirements from a task description."""

    def __init__(self):
        super().__init__()
        self.gather = dspy.ChainOfThought(GatherRequirements)

    def forward(self, task_description: str) -> dict[str, Any]:
        """Gather requirements."""
        result = self.gather(task_description=task_description)
        topics = safe_json_loads(getattr(result, "topics", []), default=[], field_name="topics")
        constraints = safe_json_loads(
            getattr(result, "constraints", []), default=[], field_name="constraints"
        )
        ambiguities = safe_json_loads(
            getattr(result, "ambiguities", []), default=[], field_name="ambiguities"
        )
        return {
            "domain": result.domain,
            "category": result.category,
            "target_level": result.target_level,
            "topics": topics if isinstance(topics, list) else [],
            "constraints": constraints if isinstance(constraints, list) else [],
            "ambiguities": ambiguities if isinstance(ambiguities, list) else [],
            "rationale": coerce_reasoning_text(
                getattr(result, "reasoning", getattr(result, "rationale", ""))
            ),
        }

    async def aforward(self, task_description: str) -> dict[str, Any]:
        """Asynchronous forward pass (preferred)."""
        result = await self.gather.acall(task_description=task_description)
        topics = safe_json_loads(getattr(result, "topics", []), default=[], field_name="topics")
        constraints = safe_json_loads(
            getattr(result, "constraints", []), default=[], field_name="constraints"
        )
        ambiguities = safe_json_loads(
            getattr(result, "ambiguities", []), default=[], field_name="ambiguities"
        )
        return {
            "domain": result.domain,
            "category": result.category,
            "target_level": result.target_level,
            "topics": topics if isinstance(topics, list) else [],
            "constraints": constraints if isinstance(constraints, list) else [],
            "ambiguities": ambiguities if isinstance(ambiguities, list) else [],
            "rationale": coerce_reasoning_text(
                getattr(result, "reasoning", getattr(result, "rationale", ""))
            ),
        }


class IntentAnalyzerModule(dspy.Module):
    """Module for analyzing user intent."""

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(AnalyzeIntent)

    def forward(self, task_description: str, user_context: str) -> dict[str, Any]:
        """Analyze intent."""
        result = self.analyze(task_description=task_description, user_context=user_context)
        success_criteria = safe_json_loads(
            getattr(result, "success_criteria", []),
            default=[],
            field_name="success_criteria",
        )
        return {
            "task_intent": result.task_intent,
            "skill_type": result.skill_type,
            "scope": result.scope,
            "success_criteria": success_criteria if isinstance(success_criteria, list) else [],
            "rationale": coerce_reasoning_text(
                getattr(result, "reasoning", getattr(result, "rationale", ""))
            ),
        }

    async def aforward(self, task_description: str, user_context: str) -> dict[str, Any]:
        """Asynchronous forward pass (preferred)."""
        result = await self.analyze.acall(
            task_description=task_description, user_context=user_context
        )
        success_criteria = safe_json_loads(
            getattr(result, "success_criteria", []),
            default=[],
            field_name="success_criteria",
        )
        return {
            "task_intent": result.task_intent,
            "skill_type": result.skill_type,
            "scope": result.scope,
            "success_criteria": success_criteria if isinstance(success_criteria, list) else [],
            "rationale": coerce_reasoning_text(
                getattr(result, "reasoning", getattr(result, "rationale", ""))
            ),
        }


class TaxonomyPathFinderModule(dspy.Module):
    """Module for finding the best taxonomy path for a skill."""

    def __init__(self):
        super().__init__()
        self.find_path = dspy.ChainOfThought(FindTaxonomyPath)

    def forward(
        self, task_description: str, taxonomy_structure: str, existing_skills: list[str]
    ) -> dict[str, Any]:
        """Find taxonomy path."""
        result = self.find_path(
            task_description=task_description,
            taxonomy_structure=taxonomy_structure,
            existing_skills=existing_skills,
        )
        alternative_paths = safe_json_loads(
            getattr(result, "alternative_paths", []),
            default=[],
            field_name="alternative_paths",
        )
        new_directories = safe_json_loads(
            getattr(result, "new_directories", []),
            default=[],
            field_name="new_directories",
        )
        confidence = safe_float(getattr(result, "confidence", 0.0), default=0.0)
        return {
            "recommended_path": result.recommended_path,
            "alternative_paths": alternative_paths if isinstance(alternative_paths, list) else [],
            "path_rationale": result.path_rationale,
            "new_directories": new_directories if isinstance(new_directories, list) else [],
            "confidence": confidence,
            "rationale": coerce_reasoning_text(
                getattr(result, "reasoning", getattr(result, "rationale", ""))
            ),
        }

    async def aforward(
        self, task_description: str, taxonomy_structure: str, existing_skills: list[str]
    ) -> dict[str, Any]:
        """Asynchronous forward pass (preferred)."""
        result = await self.find_path.acall(
            task_description=task_description,
            taxonomy_structure=taxonomy_structure,
            existing_skills=existing_skills,
        )
        alternative_paths = safe_json_loads(
            getattr(result, "alternative_paths", []),
            default=[],
            field_name="alternative_paths",
        )
        new_directories = safe_json_loads(
            getattr(result, "new_directories", []),
            default=[],
            field_name="new_directories",
        )
        confidence = safe_float(getattr(result, "confidence", 0.0), default=0.0)
        return {
            "recommended_path": result.recommended_path,
            "alternative_paths": alternative_paths if isinstance(alternative_paths, list) else [],
            "path_rationale": result.path_rationale,
            "new_directories": new_directories if isinstance(new_directories, list) else [],
            "confidence": confidence,
            "rationale": coerce_reasoning_text(
                getattr(result, "reasoning", getattr(result, "rationale", ""))
            ),
        }


class DependencyAnalyzerModule(dspy.Module):
    """Module for analyzing skill dependencies."""

    def __init__(self):
        super().__init__()
        self.analyze = dspy.Predict(AnalyzeDependencies)

    def forward(
        self, task_description: str, task_intent: str, taxonomy_path: str, existing_skills: str
    ) -> dict[str, Any]:
        """Analyze dependencies."""
        result = self.analyze(
            task_description=task_description,
            task_intent=task_intent,
            taxonomy_path=taxonomy_path,
            existing_skills=existing_skills,
        )
        prerequisite_skills = safe_json_loads(
            getattr(result, "prerequisite_skills", []),
            default=[],
            field_name="prerequisite_skills",
        )
        complementary_skills = safe_json_loads(
            getattr(result, "complementary_skills", []),
            default=[],
            field_name="complementary_skills",
        )
        missing_prerequisites = safe_json_loads(
            getattr(result, "missing_prerequisites", []),
            default=[],
            field_name="missing_prerequisites",
        )
        return {
            "dependency_analysis": (
                result.dependency_analysis.model_dump()
                if hasattr(result.dependency_analysis, "model_dump")
                else result.dependency_analysis
            ),
            "prerequisite_skills": prerequisite_skills
            if isinstance(prerequisite_skills, list)
            else [],
            "complementary_skills": complementary_skills
            if isinstance(complementary_skills, list)
            else [],
            "missing_prerequisites": missing_prerequisites
            if isinstance(missing_prerequisites, list)
            else [],
        }

    async def aforward(
        self, task_description: str, task_intent: str, taxonomy_path: str, existing_skills: str
    ) -> dict[str, Any]:
        """Asynchronous forward pass (preferred)."""
        result = await self.analyze.acall(
            task_description=task_description,
            task_intent=task_intent,
            taxonomy_path=taxonomy_path,
            existing_skills=existing_skills,
        )
        prerequisite_skills = safe_json_loads(
            getattr(result, "prerequisite_skills", []),
            default=[],
            field_name="prerequisite_skills",
        )
        complementary_skills = safe_json_loads(
            getattr(result, "complementary_skills", []),
            default=[],
            field_name="complementary_skills",
        )
        missing_prerequisites = safe_json_loads(
            getattr(result, "missing_prerequisites", []),
            default=[],
            field_name="missing_prerequisites",
        )
        return {
            "dependency_analysis": (
                result.dependency_analysis.model_dump()
                if hasattr(result.dependency_analysis, "model_dump")
                else result.dependency_analysis
            ),
            "prerequisite_skills": prerequisite_skills
            if isinstance(prerequisite_skills, list)
            else [],
            "complementary_skills": complementary_skills
            if isinstance(complementary_skills, list)
            else [],
            "missing_prerequisites": missing_prerequisites
            if isinstance(missing_prerequisites, list)
            else [],
        }


class PlanSynthesizerModule(dspy.Module):
    """Module for synthesizing all analyses into a plan."""

    def __init__(self):
        super().__init__()
        # Changed from Refine to ChainOfThought to avoid complex reward logic for now
        self.synthesize = dspy.ChainOfThought(SynthesizePlan)

    def forward(
        self,
        intent_analysis: str,
        taxonomy_analysis: str,
        dependency_analysis: str,
        user_confirmation: str = "",
    ) -> dict[str, Any]:
        """Synthesize plan."""
        result = self.synthesize(
            intent_analysis=intent_analysis,
            taxonomy_analysis=taxonomy_analysis,
            dependency_analysis=dependency_analysis,
            user_confirmation=user_confirmation,
        )
        success_criteria = safe_json_loads(
            getattr(result, "success_criteria", []),
            default=[],
            field_name="success_criteria",
        )
        return {
            "skill_metadata": result.skill_metadata,
            "content_plan": result.content_plan,
            "generation_instructions": result.generation_instructions,
            "success_criteria": success_criteria if isinstance(success_criteria, list) else [],
            "estimated_length": result.estimated_length,
            "rationale": coerce_reasoning_text(
                getattr(result, "reasoning", getattr(result, "rationale", ""))
            ),
        }

    async def aforward(
        self,
        intent_analysis: str,
        taxonomy_analysis: str,
        dependency_analysis: str,
        user_confirmation: str = "",
    ) -> dict[str, Any]:
        """Asynchronous forward pass (preferred)."""
        result = await self.synthesize.acall(
            intent_analysis=intent_analysis,
            taxonomy_analysis=taxonomy_analysis,
            dependency_analysis=dependency_analysis,
            user_confirmation=user_confirmation,
        )
        success_criteria = safe_json_loads(
            getattr(result, "success_criteria", []),
            default=[],
            field_name="success_criteria",
        )
        return {
            "skill_metadata": result.skill_metadata,
            "content_plan": result.content_plan,
            "generation_instructions": result.generation_instructions,
            "success_criteria": success_criteria if isinstance(success_criteria, list) else [],
            "estimated_length": result.estimated_length,
            "rationale": coerce_reasoning_text(
                getattr(result, "reasoning", getattr(result, "rationale", ""))
            ),
        }


class Phase1UnderstandingModule(dspy.Module):
    """Composite module for Phase 1: Understanding."""

    def __init__(self):
        super().__init__()
        self.gather_requirements = RequirementsGathererModule()
        self.analyze_intent = IntentAnalyzerModule()
        self.find_taxonomy = TaxonomyPathFinderModule()
        self.analyze_dependencies = DependencyAnalyzerModule()
        self.synthesize = PlanSynthesizerModule()

    async def aforward(
        self,
        task_description: str,
        user_context: str,
        taxonomy_structure: str,
        existing_skills: str,
        user_confirmation: str = "",
    ) -> dict[str, Any]:
        """Execute Phase 1 orchestrator asynchronously."""
        requirements = await self.gather_requirements.aforward(task_description)
        intent_future = self.analyze_intent.aforward(task_description, user_context)

        # `FindTaxonomyPath` signature expects a list[str] for existing_skills.
        # The public program contract uses JSON strings; normalize here.
        existing_skill_paths = safe_json_loads(
            existing_skills,
            default=[],
            field_name="existing_skills",
        )
        if not isinstance(existing_skill_paths, list):
            existing_skill_paths = []
        existing_skill_paths = [str(s) for s in existing_skill_paths]

        taxonomy_future = self.find_taxonomy.aforward(
            task_description,
            taxonomy_structure,
            existing_skill_paths,
        )
        intent_result, taxonomy_result = await asyncio.gather(intent_future, taxonomy_future)
        deps_result = await self.analyze_dependencies.aforward(
            task_description,
            str(intent_result["task_intent"]),
            taxonomy_result["recommended_path"],
            existing_skills,
        )
        plan = await self.synthesize.aforward(
            intent_analysis=str(intent_result),
            taxonomy_analysis=str(taxonomy_result),
            dependency_analysis=str(deps_result),
            user_confirmation=user_confirmation,
        )

        # agentskills.io: frontmatter `name` must match the skill directory name.
        # Ensure the taxonomy path leaf matches the planned kebab-case name so newly
        # generated skills are spec-compliant by construction.
        try:
            skill_metadata = plan.get("skill_metadata")
            skill_name = getattr(skill_metadata, "name", "") if skill_metadata is not None else ""
            recommended_path = str(taxonomy_result.get("recommended_path", "")).strip().strip("/")
            if skill_name and recommended_path:
                leaf = recommended_path.split("/")[-1]
                if leaf != skill_name:
                    parent = "/".join(recommended_path.split("/")[:-1])
                    aligned_path = f"{parent}/{skill_name}" if parent else skill_name
                    taxonomy_result["recommended_path"] = aligned_path
                    # Keep metadata aligned with the chosen on-disk path.
                    if hasattr(skill_metadata, "skill_id"):
                        skill_metadata.skill_id = aligned_path
                    if hasattr(skill_metadata, "taxonomy_path"):
                        skill_metadata.taxonomy_path = aligned_path
        except Exception:
            # Best-effort: do not fail Phase 1 if alignment fails.
            # This is a non-critical operation for taxonomy path normalization.
            pass

        return {
            "requirements": requirements,
            "intent": intent_result,
            "taxonomy": taxonomy_result,
            "dependencies": deps_result,
            "plan": plan,
        }

    def forward(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for aforward."""
        return run_async(lambda: self.aforward(*args, **kwargs))
