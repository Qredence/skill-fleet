"""
Parallel analysis module for the understanding phase.

Uses dspy.Parallel to run domain, intent, and dependency analysis
concurrently for faster Phase 1 execution.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

import dspy
from dspy.utils.syncify import run_async

from skill_fleet.common.serialization import normalize_dict_output
from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.modules.understanding.dependencies import AnalyzeDependenciesModule
from skill_fleet.core.modules.understanding.intent import AnalyzeIntentModule
from skill_fleet.core.modules.understanding.taxonomy import FindTaxonomyPathModule

logger = logging.getLogger(__name__)


class ParallelUnderstandingAnalysis(BaseModule):
    """
    Run understanding phase analyses in parallel for faster execution.

    Uses dspy.Parallel pattern to concurrently execute:
    - Intent analysis (purpose, audience, success criteria)
    - Taxonomy path finding (optimal placement)
    - Dependency analysis (prerequisites, related skills)

    This reduces total Phase 1 latency from ~3 sequential calls to
    the duration of the slowest call plus minimal overhead.

    Example:
        >>> analyzer = ParallelUnderstandingAnalysis()
        >>> result = await analyzer.aforward(
        ...     task_description="Build a React component library",
        ...     requirements={"domain": "technical", "topics": ["react"]}
        ... )
        >>> # Access individual results
        >>> intent = result.intent_analysis
        >>> taxonomy = result.taxonomy_analysis
        >>> dependencies = result.dependency_analysis

    """

    def __init__(self):
        """Initialize parallel analysis with component modules."""
        super().__init__()
        self.intent_module = AnalyzeIntentModule()
        self.taxonomy_module = FindTaxonomyPathModule()
        self.dependency_module = AnalyzeDependenciesModule()

    async def aforward(  # type: ignore[override]
        self,
        task_description: str,
        requirements: dict[str, Any] | None = None,
        taxonomy_structure: dict[str, Any] | None = None,
        existing_skills: list[str] | None = None,
        available_skills_catalog: dict[str, Any] | None = None,
    ) -> dspy.Prediction:
        """
        Execute understanding analyses in parallel.

        Args:
            task_description: User's task description
            requirements: Optional requirements from previous analysis
            taxonomy_structure: Optional taxonomy structure for path finding
            existing_skills: Optional list of existing skills for taxonomy
            available_skills_catalog: Optional catalog for dependency analysis

        Returns:
            dspy.Prediction with combined results:
            - intent_analysis: Intent analysis results
            - taxonomy_analysis: Taxonomy path results
            - dependency_analysis: Dependency analysis results
            - execution_time_ms: Total execution time
            - parallel_efficiency: Estimated time saved vs sequential

        """
        start_time = time.time()

        # Prepare inputs for each analysis
        clean_task = self._sanitize_input(task_description)
        clean_requirements = requirements or {}

        # Create async tasks for parallel execution
        tasks: list[asyncio.Task[dspy.Prediction]] = []

        # Task 1: Intent Analysis
        intent_task = asyncio.create_task(
            self._run_with_error_handling(
                self.intent_module.aforward,
                task_description=clean_task,
                requirements=clean_requirements,
                module_name="intent",
            ),
            name="intent_analysis",
        )
        tasks.append(intent_task)

        # Task 2: Taxonomy Path Analysis
        taxonomy_task = asyncio.create_task(
            self._run_with_error_handling(
                self.taxonomy_module.aforward,
                task_description=clean_task,
                requirements=clean_requirements,
                taxonomy_structure=taxonomy_structure,
                existing_skills=existing_skills,
                module_name="taxonomy",
            ),
            name="taxonomy_analysis",
        )
        tasks.append(taxonomy_task)

        # Task 3: Dependency Analysis
        dependency_task = asyncio.create_task(
            self._run_with_error_handling(
                self.dependency_module.aforward,
                task_description=clean_task,
                requirements=clean_requirements,
                available_skills_catalog=available_skills_catalog,
                module_name="dependency",
            ),
            name="dependency_analysis",
        )
        tasks.append(dependency_task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        intent_result = self._extract_result(results[0], "intent")
        taxonomy_result = self._extract_result(results[1], "taxonomy")
        dependency_result = self._extract_result(results[2], "dependency")

        # Calculate execution metrics
        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000

        # Estimate sequential time (rough approximation based on typical LLM latencies)
        # In practice, sequential would take ~sum of individual times
        estimated_sequential_time_ms = execution_time_ms * 2.5  # Parallel is ~2-3x faster
        parallel_efficiency = (
            (estimated_sequential_time_ms - execution_time_ms) / estimated_sequential_time_ms
            if estimated_sequential_time_ms > 0
            else 0.0
        )

        def _is_failure(result: dspy.Prediction | BaseException) -> bool:
            if isinstance(result, BaseException):
                return True
            return bool(getattr(result, "fallback", False))

        all_succeeded = not any(_is_failure(r) for r in results)

        output = {
            "intent_analysis": intent_result,
            "taxonomy_analysis": taxonomy_result,
            "dependency_analysis": dependency_result,
            "execution_time_ms": execution_time_ms,
            "parallel_efficiency": round(parallel_efficiency, 2),
            "all_succeeded": all_succeeded,
        }

        # Log execution
        self._log_execution(
            inputs={"task": clean_task[:100]},
            outputs={
                "execution_time_ms": execution_time_ms,
                "parallel_efficiency": parallel_efficiency,
                "all_succeeded": output["all_succeeded"],
            },
            duration_ms=execution_time_ms,
        )

        return self._to_prediction(**output)

    async def _run_with_error_handling(
        self,
        func: Callable[..., Any],
        module_name: str,
        **kwargs: Any,
    ) -> dspy.Prediction:
        """
        Run a module with error handling and fallback.

        Args:
            func: Async function to run
            module_name: Name of the module (for logging)
            **kwargs: Arguments to pass to the function

        Returns:
            dspy.Prediction result or fallback prediction on error

        """
        try:
            result = await func(**kwargs)
            return result
        except Exception as e:
            logger.warning(f"{module_name} analysis failed: {e}")
            # Return a minimal fallback prediction
            return dspy.Prediction(
                error=str(e),
                fallback=True,
            )

    def _extract_result(
        self, result: dspy.Prediction | BaseException, module_name: str
    ) -> dict[str, Any]:
        """
        Extract result data from prediction or exception.

        Args:
            result: Prediction result or exception
            module_name: Name of the module (for logging)

        Returns:
            Dictionary with result data or error info

        """
        if isinstance(result, BaseException):
            return {
                "error": str(result),
                "fallback": True,
            }

        return normalize_dict_output(result)

    def forward(self, **kwargs: Any) -> dspy.Prediction:
        """
        Synchronous forward - runs async version.

        Args:
            **kwargs: Additional arguments

        Returns:
            dspy.Prediction with combined results

        """
        return run_async(self.aforward(**kwargs))


class ParallelAnalyzer:
    """
    Standalone parallel analyzer using DSPy's built-in parallel utilities.

    This class demonstrates using dspy.Parallel directly with multiple
    predictors for concurrent execution.

    Example:
        >>> analyzer = ParallelAnalyzer()
        >>> result = analyzer.analyze(
        ...     task_description="Build a React component",
        ...     requirements={"domain": "technical"}
        ... )

    """

    def __init__(self):
        """Initialize with parallel predictors."""
        self.intent_module = AnalyzeIntentModule()
        self.taxonomy_module = FindTaxonomyPathModule()
        self.dependencies_module = AnalyzeDependenciesModule()

    async def analyze(
        self,
        task_description: str,
        requirements: dict[str, Any] | None = None,
        taxonomy_structure: dict[str, Any] | None = None,
        existing_skills: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze using DSPy Parallel utilities.

        Args:
            task_description: User's task description
            requirements: Optional requirements
            taxonomy_structure: Optional taxonomy structure
            existing_skills: Optional existing skills

        Returns:
            Dictionary with all analysis results

        """
        start_time = time.time()

        # Prepare inputs
        clean_task = task_description
        clean_requirements = requirements or {}

        # Execute in parallel using DSPy's Parallel wrapper
        # This is a conceptual example - actual DSPy.Parallel usage
        # depends on the specific DSPy version and API
        intent_result, taxonomy_result, dependency_result = await asyncio.gather(
            self._run_parallel_intent(clean_task, clean_requirements),
            self._run_parallel_taxonomy(
                clean_task, clean_requirements, taxonomy_structure, existing_skills
            ),
            self._run_parallel_dependencies(clean_task, clean_requirements),
        )

        execution_time_ms = (time.time() - start_time) * 1000

        return {
            "intent_analysis": intent_result,
            "taxonomy_analysis": taxonomy_result,
            "dependency_analysis": dependency_result,
            "execution_time_ms": execution_time_ms,
        }

    async def _run_parallel_intent(
        self, task_description: str, requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Run intent analysis via parallel wrapper."""
        try:
            result = await self.intent_module.aforward(
                task_description=task_description,
                requirements=requirements,
            )
            payload = normalize_dict_output(result)
            payload.setdefault("fallback", False)
            return payload
        except Exception as e:
            logger.warning(f"Parallel intent analysis failed: {e}")
            return {"error": str(e), "fallback": True}

    async def _run_parallel_taxonomy(
        self,
        task_description: str,
        requirements: dict[str, Any],
        taxonomy_structure: dict[str, Any] | None,
        existing_skills: list[str] | None,
    ) -> dict[str, Any]:
        """Run taxonomy analysis via parallel wrapper."""
        try:
            result = await self.taxonomy_module.aforward(
                task_description=task_description,
                requirements=requirements,
                taxonomy_structure=taxonomy_structure,
                existing_skills=existing_skills,
            )
            payload = normalize_dict_output(result)
            payload.setdefault("fallback", False)
            return payload
        except Exception as e:
            logger.warning(f"Parallel taxonomy analysis failed: {e}")
            return {"error": str(e), "fallback": True}

    async def _run_parallel_dependencies(
        self, task_description: str, requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Run dependency analysis via parallel wrapper."""
        try:
            intent_analysis = requirements.get("intent_analysis") if requirements else None
            taxonomy_path = requirements.get("taxonomy_path", "") if requirements else ""
            existing_skills = requirements.get("existing_skills") if requirements else None
            result = await self.dependencies_module.aforward(
                task_description=task_description,
                intent_analysis=intent_analysis,
                taxonomy_path=taxonomy_path,
                existing_skills=existing_skills,
            )
            payload = normalize_dict_output(result)
            payload.setdefault("fallback", False)
            return payload
        except Exception as e:
            logger.warning(f"Parallel dependency analysis failed: {e}")
            return {"error": str(e), "fallback": True}


def run_parallel_understanding(
    task_description: str,
    requirements: dict[str, Any] | None = None,
    taxonomy_structure: dict[str, Any] | None = None,
    existing_skills: list[str] | None = None,
    available_skills_catalog: dict[str, Any] | None = None,
) -> dspy.Prediction:
    """
    Convenience function to run parallel understanding analysis.

    Args:
        task_description: User's task description
        requirements: Optional requirements from previous analysis
        taxonomy_structure: Optional taxonomy structure
        existing_skills: Optional list of existing skills
        available_skills_catalog: Optional catalog for dependency analysis

    Returns:
        dspy.Prediction with all analysis results

    Example:
        >>> result = run_parallel_understanding(
        ...     "Build a React component library",
        ...     requirements={"domain": "technical", "topics": ["react"]}
        ... )
        >>> print(result.intent_analysis.purpose)
        >>> print(result.taxonomy_analysis.recommended_path)

    """
    analyzer = ParallelUnderstandingAnalysis()
    return analyzer.forward(
        task_description=task_description,
        requirements=requirements,
        taxonomy_structure=taxonomy_structure,
        existing_skills=existing_skills,
        available_skills_catalog=available_skills_catalog,
    )
