"""
Taxonomy path finder module.

Uses FindTaxonomyPath signature to determine optimal
placement in the skill taxonomy.
"""

import time

import dspy

from skill_fleet.common.llm_fallback import llm_fallback_enabled
from skill_fleet.common.utils import safe_float
from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.understanding.taxonomy import FindTaxonomyPath


class FindTaxonomyPathModule(BaseModule):
    """
    Find optimal taxonomy path for a skill.

    Uses FindTaxonomyPath signature to determine:
    - Recommended taxonomy path
    - Alternative paths
    - Path rationale
    - New directories needed
    - Confidence score

    Example:
        module = FindTaxonomyPathModule()
        result = module.forward(
            task_description="Build a React component library",
            requirements={"domain": "technical", "category": "frontend"},
            taxonomy_structure={"technical": {"frontend": ["react", "vue"]}},
            existing_skills=["technical/frontend/react-basics"]
        )
        # Returns: {
        #   "recommended_path": "technical/frontend/react-components",
        #   "alternative_paths": ["web/react-components"],
        #   "path_rationale": "React-specific skill...",
        #   "new_directories": [],
        #   "confidence": 0.85
        # }

    """

    def __init__(self):
        super().__init__()
        self.find_path = dspy.ChainOfThought(FindTaxonomyPath)

    async def aforward(  # type: ignore[override]
        self,
        task_description: str,
        requirements: dict | None = None,
        taxonomy_structure: dict | None = None,
        existing_skills: list[str] | None = None,
    ) -> dspy.Prediction:
        """Async taxonomy analysis using DSPy `acall`."""
        start_time = time.time()

        clean_task = self._sanitize_input(task_description)
        clean_requirements = self._sanitize_input(str(requirements or {}))
        clean_structure = self._sanitize_input(str(taxonomy_structure or {}))
        clean_existing = existing_skills if existing_skills else []

        try:
            result = await self.find_path.acall(
                task_description=clean_task,
                requirements=clean_requirements,
                taxonomy_structure=clean_structure,
                existing_skills=clean_existing,
            )
        except Exception as e:
            if not llm_fallback_enabled():
                raise
            self.logger.warning(f"Taxonomy analysis failed: {e}. Using fallback path.")
            result = None

        output = (
            {
                "recommended_path": result.recommended_path,
                "alternative_paths": result.alternative_paths
                if isinstance(result.alternative_paths, list)
                else [],
                "path_rationale": result.path_rationale,
                "new_directories": result.new_directories
                if isinstance(result.new_directories, list)
                else [],
                "confidence": float(result.confidence) if hasattr(result, "confidence") else 0.5,
            }
            if result is not None
            else {
                "recommended_path": "general/uncategorized",
                "alternative_paths": [],
                "path_rationale": "Fallback taxonomy path due to analysis failure.",
                "new_directories": [],
                "confidence": 0.0,
                "fallback": True,
            }
        )
        if result is not None and hasattr(result, "reasoning"):
            output.setdefault("reasoning", str(result.reasoning))

        required = ["recommended_path", "path_rationale", "confidence"]
        if not self._validate_result(output, required):
            self.logger.warning("Result missing required fields, using defaults")
            output.setdefault("recommended_path", "general/uncategorized")
            output.setdefault("path_rationale", "Default path due to analysis failure")
            output.setdefault("confidence", 0.0)

        confidence_value = safe_float(output.get("confidence", 0.0), default=0.0)
        output["confidence"] = max(0.0, min(1.0, confidence_value))

        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={
                "task_description": clean_task[:100],
                "taxonomy": clean_structure[:100],
            },
            outputs={
                "path": output["recommended_path"],
                "confidence": output["confidence"],
            },
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

    def forward(  # type: ignore[override]
        self,
        task_description: str,
        requirements: dict | None = None,
        taxonomy_structure: dict | None = None,
        existing_skills: list[str] | None = None,
    ) -> dspy.Prediction:
        """
        Find taxonomy path for skill.

        Args:
            task_description: User's task description
            requirements: Requirements from GatherRequirementsModule
            taxonomy_structure: Current taxonomy structure
            existing_skills: List of existing skill paths

        Returns:
            dspy.Prediction with taxonomy analysis:
            - recommended_path: Suggested taxonomy path
            - alternative_paths: Alternative valid paths
            - path_rationale: Explanation for path choice
            - new_directories: New directories to create
            - confidence: Confidence score (0.0-1.0)

        """
        start_time = time.time()

        # Sanitize inputs
        clean_task = self._sanitize_input(task_description)
        clean_requirements = self._sanitize_input(str(requirements or {}))
        clean_structure = self._sanitize_input(str(taxonomy_structure or {}))
        clean_existing = existing_skills if existing_skills else []

        # Execute signature
        try:
            result = self.find_path(
                task_description=clean_task,
                requirements=clean_requirements,
                taxonomy_structure=clean_structure,
                existing_skills=clean_existing,
            )
        except Exception as e:
            if not llm_fallback_enabled():
                raise
            self.logger.warning(f"Taxonomy analysis failed: {e}. Using fallback path.")
            result = None

        # Transform to structured output
        if result is None:
            output = {
                "recommended_path": "general/uncategorized",
                "alternative_paths": [],
                "path_rationale": "Fallback taxonomy path due to analysis failure.",
                "new_directories": [],
                "confidence": 0.0,
            }
        else:
            output = {
                "recommended_path": result.recommended_path,
                "alternative_paths": result.alternative_paths
                if isinstance(result.alternative_paths, list)
                else [],
                "path_rationale": result.path_rationale,
                "new_directories": result.new_directories
                if isinstance(result.new_directories, list)
                else [],
                "confidence": float(result.confidence) if hasattr(result, "confidence") else 0.5,
            }
            if hasattr(result, "reasoning"):
                output.setdefault("reasoning", str(result.reasoning))

        # Validate
        required = ["recommended_path", "path_rationale", "confidence"]
        if not self._validate_result(output, required):
            self.logger.warning("Result missing required fields, using defaults")
            output.setdefault("recommended_path", "general/uncategorized")
            output.setdefault("path_rationale", "Default path due to analysis failure")
            output.setdefault("confidence", 0.0)

        # Ensure confidence is in valid range
        output["confidence"] = max(0.0, min(1.0, output["confidence"]))

        # Log execution
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={
                "task_description": clean_task[:100],
                "taxonomy": clean_structure[:100],
            },
            outputs={
                "path": output["recommended_path"],
                "confidence": output["confidence"],
            },
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)
