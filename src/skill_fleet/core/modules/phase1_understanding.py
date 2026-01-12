"""DSPy modules for Phase 1: Understanding & Planning."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import dspy

from ...common.async_utils import run_async
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
        return {
            "domain": result.domain,
            "category": result.category,
            "target_level": result.target_level,
            "topics": result.topics,
            "constraints": result.constraints,
            "ambiguities": result.ambiguities,
            "rationale": getattr(result, "rationale", ""),
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Asynchronous forward pass."""
        return await asyncio.to_thread(self.forward, *args, **kwargs)


class IntentAnalyzerModule(dspy.Module):
    """Module for analyzing user intent."""

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(AnalyzeIntent)

    def forward(self, task_description: str, user_context: str) -> dict[str, Any]:
        """Analyze intent."""
        result = self.analyze(task_description=task_description, user_context=user_context)
        return {
            "task_intent": result.task_intent,
            "skill_type": result.skill_type,
            "scope": result.scope,
            "success_criteria": result.success_criteria,
            "rationale": getattr(result, "rationale", ""),
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Asynchronous forward pass."""
        return await asyncio.to_thread(self.forward, *args, **kwargs)


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
        return {
            "recommended_path": result.recommended_path,
            "alternative_paths": result.alternative_paths,
            "path_rationale": result.path_rationale,
            "new_directories": result.new_directories,
            "confidence": result.confidence,
            "rationale": getattr(result, "rationale", ""),
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Asynchronous forward pass."""
        return await asyncio.to_thread(self.forward, *args, **kwargs)


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
        return {
            "dependency_analysis": result.dependency_analysis,
            "prerequisite_skills": result.prerequisite_skills,
            "complementary_skills": result.complementary_skills,
            "missing_prerequisites": result.missing_prerequisites,
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Asynchronous forward pass."""
        return await asyncio.to_thread(self.forward, *args, **kwargs)


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
        return {
            "skill_metadata": result.skill_metadata,
            "content_plan": result.content_plan,
            "generation_instructions": result.generation_instructions,
            "success_criteria": result.success_criteria,
            "estimated_length": result.estimated_length,
            "rationale": getattr(result, "rationale", ""),
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Asynchronous forward pass."""
        return await asyncio.to_thread(self.forward, *args, **kwargs)


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
        taxonomy_future = self.find_taxonomy.aforward(
            task_description, taxonomy_structure, existing_skills
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
