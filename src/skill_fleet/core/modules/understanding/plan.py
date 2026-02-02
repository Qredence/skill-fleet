"""
Plan synthesis module using ReAct pattern.

Uses ReAct (Reasoning + Acting) to synthesize a complete skill plan
by iteratively refining and validating the plan components.
"""

import time

import dspy

from skill_fleet.common.llm_fallback import llm_fallback_enabled
from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.understanding.plan import SynthesizePlan


class SynthesizePlanModule(BaseModule):
    """
    Synthesize complete skill plan using ReAct pattern.

    Uses dspy.ReAct to iteratively reason about and refine the plan:
    1. Reason about requirements and intent
    2. Validate against taxonomy and dependencies
    3. Act to create plan components
    4. Reflect and refine

    Example:
        module = SynthesizePlanModule()
        result = await module.aforward(
            requirements={"domain": "technical", "topics": ["react"]},
            intent_analysis={"purpose": "...", "skill_type": "how_to"},
            taxonomy_analysis={"recommended_path": "technical/frontend/react"},
            dependency_analysis={"prerequisite_skills": [...]}
        )

    """

    def __init__(self):
        super().__init__()
        # Use ReAct for iterative reasoning and refinement
        self.synthesize = dspy.ReAct(
            SynthesizePlan, tools=[self._validate_path, self._check_constraints]
        )

    def _validate_path(self, path: str) -> str:
        """Tool: Validate taxonomy path format."""
        if "/" not in path:
            return f"Invalid path '{path}': must contain '/'"
        parts = path.split("/")
        if len(parts) != 2:
            return f"Invalid path '{path}': must be exactly 2 levels (category/skill-name)"
        return f"Valid path: category='{parts[0]}', skill='{parts[1]}'"

    def _check_constraints(self, topics: list, constraints: list) -> str:
        """Tool: Check if topics align with constraints."""
        if not topics:
            return "Warning: No topics defined"
        if len(topics) > 10:
            return f"Warning: {len(topics)} topics may be too many, consider prioritizing"
        return f"OK: {len(topics)} topics defined"

    async def aforward(  # type: ignore[override]
        self,
        requirements: dict,
        intent_analysis: dict,
        taxonomy_analysis: dict,
        dependency_analysis: dict,
        user_confirmation: str = "",
    ) -> dspy.Prediction:
        """
        Asynchronously synthesize plan using ReAct.

        Args:
            requirements: Requirements from GatherRequirementsModule
            intent_analysis: Intent from AnalyzeIntentModule
            taxonomy_analysis: Taxonomy from FindTaxonomyPathModule
            dependency_analysis: Dependencies from AnalyzeDependenciesModule
            user_confirmation: Optional HITL feedback

        Returns:
            dspy.Prediction with complete plan:
            - skill_name, skill_description, taxonomy_path
            - content_outline, generation_guidance
            - success_criteria, estimated_length, tags, rationale

        """
        start_time = time.time()

        # Use ReAct for iterative synthesis (best-effort). Some test LMs only implement
        # sync calling; fall back to heuristics if async LM calls fail.
        try:
            result = await self.synthesize.acall(
                requirements=str(requirements),
                intent_analysis=str(intent_analysis),
                taxonomy_analysis=str(taxonomy_analysis),
                dependency_analysis=str(dependency_analysis),
                user_confirmation=user_confirmation,
            )
        except Exception as e:
            if not llm_fallback_enabled():
                raise
            self.logger.warning(f"Plan synthesis failed: {e}. Using heuristic fallback.")
            result = None

        # Transform to structured output
        if result is None:
            req_topics = requirements.get("topics") if isinstance(requirements, dict) else None
            topic = req_topics[0] if isinstance(req_topics, list) and req_topics else "general"
            skill_name = (
                requirements.get("suggested_skill_name") if isinstance(requirements, dict) else None
            ) or "unnamed-skill"
            skill_description = (
                requirements.get("description") if isinstance(requirements, dict) else None
            ) or f"A skill for {topic}."
            tax_path = ""
            if isinstance(taxonomy_analysis, dict):
                tax_path = taxonomy_analysis.get("recommended_path", "") or taxonomy_analysis.get(
                    "taxonomy_path", ""
                )
            taxonomy_path = tax_path or f"general/{skill_name}"
            output = {
                "skill_name": skill_name,
                "skill_description": skill_description,
                "taxonomy_path": taxonomy_path,
                "content_outline": [
                    "Overview",
                    "When to Use",
                    "Step-by-step Instructions",
                    "Examples",
                    "Troubleshooting",
                ],
                "generation_guidance": "Write clear, actionable steps with examples.",
                "success_criteria": ["User can apply the skill successfully"],
                "estimated_length": "medium",
                "tags": [str(topic)],
                "rationale": "Fallback plan generated due to synthesis failure.",
            }
        else:
            output = {
                "skill_name": result.skill_name,
                "skill_description": result.skill_description,
                "taxonomy_path": result.taxonomy_path,
                "content_outline": result.content_outline
                if isinstance(result.content_outline, list)
                else [],
                "generation_guidance": result.generation_guidance,
                "success_criteria": result.success_criteria
                if isinstance(result.success_criteria, list)
                else [],
                "estimated_length": result.estimated_length,
                "tags": result.tags if isinstance(result.tags, list) else [],
                "rationale": result.rationale,
            }

        # Validate
        required = ["skill_name", "skill_description", "taxonomy_path", "content_outline"]
        if not self._validate_result(output, required):
            self.logger.warning("Result missing required fields, using defaults")
            output.setdefault("skill_name", "unnamed-skill")
            output.setdefault(
                "skill_description",
                "A skill for " + str(requirements.get("topics", ["general"])[0]),
            )
            output.setdefault("taxonomy_path", "general/unnamed-skill")
            output.setdefault("content_outline", ["Introduction", "Main Content", "Conclusion"])

        # Log execution
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={"requirements": str(requirements)[:100], "taxonomy": output["taxonomy_path"]},
            outputs={
                "skill_name": output["skill_name"],
                "outline_length": len(output["content_outline"]),
            },
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

    def forward(self, **kwargs) -> dspy.Prediction:
        """
        Synchronous forward - delegates to async version.

        Note: Use aforward() for better performance in async contexts.
        """
        from dspy.utils.syncify import run_async

        return run_async(self.aforward(**kwargs))
