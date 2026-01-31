"""
Phase 3: Validation Workflow.

Validates generated skill content for compliance and quality.
Can refine content if quality is insufficient.
"""

import logging
from typing import Any

from skill_fleet.core.modules.validation.compliance import (
    AssessQualityModule,
    RefineSkillModule,
    ValidateComplianceModule,
)
from skill_fleet.core.modules.validation.structure import ValidateStructureModule
from skill_fleet.core.modules.validation.test_cases import GenerateTestCasesModule

logger = logging.getLogger(__name__)


class ValidationWorkflow:
    """
    Phase 3: Validation & Quality Assurance Workflow.

    Validates skill content:
    1. Check agentskills.io compliance
    2. Assess overall quality
    3. Refine if below threshold
    4. Return validation report

    Example:
        workflow = ValidationWorkflow()
        result = await workflow.execute(
            skill_content="# Skill\n...",
            plan={"success_criteria": [...]},
            taxonomy_path="technical/python"
        )

    """

    def __init__(self):
        self.compliance = ValidateComplianceModule()
        self.quality = AssessQualityModule()
        self.refinement = RefineSkillModule()
        self.structure_validator = ValidateStructureModule()
        self.test_generator = GenerateTestCasesModule()

    async def execute(
        self,
        skill_content: str,
        plan: dict,
        taxonomy_path: str,
        enable_hitl_review: bool = False,
        quality_threshold: float = 0.75,
    ) -> dict[str, Any]:
        """
        Execute validation workflow.

        Args:
            skill_content: Generated SKILL.md content
            plan: Original plan with success criteria
            taxonomy_path: Expected taxonomy path
            enable_hitl_review: Whether to show for human review
            quality_threshold: Minimum quality score

        Returns:
            Validation results

        """
        logger.info("Starting validation workflow")

        # Step 0: Validate structure (NEW)
        logger.debug("Step 0: Validating skill structure")
        skill_name = plan.get("skill_name", "")
        description = plan.get("skill_description", "")
        structure_result = self.structure_validator(
            skill_name=skill_name,
            description=description,
            skill_content=skill_content,
        )

        # Step 1: Generate test cases (NEW)
        logger.debug("Step 1: Generating test cases")
        trigger_phrases = plan.get("trigger_phrases", [])
        negative_triggers = plan.get("negative_triggers", [])
        skill_category = plan.get("skill_category", "other")

        test_cases = self.test_generator(
            skill_description=description,
            trigger_phrases=trigger_phrases,
            negative_triggers=negative_triggers,
            skill_category=skill_category,
        )

        # Calculate trigger coverage
        trigger_coverage = self._assess_trigger_coverage(
            test_cases.get("positive_tests", []), trigger_phrases
        )

        # Step 2: Validate compliance
        logger.debug("Step 2: Checking compliance")
        compliance_result = await self.compliance.aforward(
            skill_content=skill_content, taxonomy_path=taxonomy_path
        )

        # Step 3: Assess quality
        logger.debug("Step 3: Assessing quality")
        quality_result = await self.quality.aforward(
            skill_content=skill_content,
            plan=plan,
            success_criteria=plan.get("success_criteria", []),
        )

        # Check if HITL review requested
        if enable_hitl_review:
            return self._create_review_checkpoint(
                skill_content=skill_content,
                compliance=compliance_result,
                quality=quality_result,
                structure=structure_result,
                test_cases=test_cases,
            )

        # Step 3: Refine if needed
        final_content = skill_content
        refinements_made = []

        if quality_result["overall_score"] < quality_threshold:
            logger.info(
                f"Quality {quality_result['overall_score']:.2f} below threshold {quality_threshold}"
            )

            if quality_result.get("weaknesses"):
                refine_result = await self.refinement.aforward(
                    current_content=skill_content,
                    weaknesses=quality_result["weaknesses"],
                    target_score=quality_threshold,
                )

                final_content = refine_result.get("refined_content", skill_content)
                refinements_made = refine_result.get("improvements_made", [])

        # Determine final status
        passed = (
            compliance_result.get("passed", False)
            and quality_result.get("overall_score", 0.0) >= quality_threshold
        )

        logger.info(f"Validation completed: passed={passed}")

        # Build validation report matching ValidationReport model
        errors = (
            compliance_result.get("issues", [])
            if not compliance_result.get("passed", False)
            else []
        )
        # Include structure errors in validation errors
        if not structure_result.get("overall_valid", False):
            errors.extend(structure_result.get("name_errors", []))
            errors.extend(structure_result.get("description_errors", []))
            errors.extend(structure_result.get("security_issues", []))

        warnings = quality_result.get("weaknesses", [])[:5]  # Top 5 weaknesses as warnings
        # Include structure warnings
        warnings.extend(structure_result.get("description_warnings", [])[:3])

        # Generate validation summary
        validation_summary = self._generate_validation_summary(
            structure_result, compliance_result, quality_result, test_cases
        )

        return {
            "status": "completed" if passed else "needs_improvement",
            "passed": passed,
            "skill_content": final_content,
            "validation_report": {
                "passed": passed,
                "status": "passed" if passed else "failed",
                "score": quality_result.get("overall_score", 0.0),
                "errors": errors,
                "warnings": warnings,
                "checks_performed": [
                    "structure_validation",
                    "agentskills.io_compliance",
                    "quality_assessment",
                    "test_case_generation",
                    "content_refinement",
                ],
                "checks": [],
                "feedback": quality_result.get("feedback", ""),
                # NEW: Structure validation fields
                "structure_valid": structure_result.get("overall_valid", False),
                "name_errors": structure_result.get("name_errors", []),
                "description_errors": structure_result.get("description_errors", []),
                "security_issues": structure_result.get("security_issues", []),
                # NEW: Test case fields
                "test_cases": test_cases,
                "trigger_coverage": trigger_coverage,
                # NEW: Quality fields
                "word_count": quality_result.get("word_count", 0),
                "size_assessment": quality_result.get("size_assessment", "unknown"),
                "verbosity_score": quality_result.get("verbosity_score", 0.0),
                "refinements_made": refinements_made,
                # Summary
                "validation_summary": validation_summary,
            },
        }

    def _create_review_checkpoint(
        self,
        skill_content: str,
        compliance: dict,
        quality: dict,
        structure: dict | None = None,
        test_cases: dict | None = None,
    ) -> dict[str, Any]:
        """
        Create HITL review checkpoint.

        Args:
            skill_content: Content to review
            compliance: Compliance results
            quality: Quality results
            structure: Optional structure validation results
            test_cases: Optional generated test cases

        Returns:
            Review checkpoint

        """
        logger.info("Creating review checkpoint")

        # Include structure and test case data in checkpoint
        hitl_data = {
            "skill_content_preview": skill_content[:2000] + "..."
            if len(skill_content) > 2000
            else skill_content,
            "compliance_score": compliance.get("compliance_score", 0.0),
            "quality_score": quality.get("overall_score", 0.0),
            "strengths": quality.get("strengths", [])[:3],
            "weaknesses": quality.get("weaknesses", [])[:3],
            "issues": compliance.get("issues", []),
        }

        # Add structure validation data if provided
        if structure:
            hitl_data["structure_valid"] = structure.get("overall_valid", False)
            hitl_data["structure_issues"] = structure.get("name_errors", []) + structure.get(
                "description_errors", []
            )

        # Add test case data if provided
        if test_cases:
            hitl_data["test_case_count"] = test_cases.get("total_tests", 0)
            hitl_data["test_cases_preview"] = test_cases.get("positive_tests", [])[:3]

        return {
            "status": "pending_hitl",
            "hitl_type": "review",
            "hitl_data": hitl_data,
            "context": {
                "full_content": skill_content,
                "compliance": compliance,
                "quality": quality,
                "structure": structure,
                "test_cases": test_cases,
            },
        }

    def _assess_trigger_coverage(
        self, positive_tests: list[str], trigger_phrases: list[str]
    ) -> float:
        """
        Assess how well test cases cover trigger phrases.

        Args:
            positive_tests: Generated positive test cases
            trigger_phrases: Expected trigger phrases

        Returns:
            Coverage score (0.0 - 1.0)

        """
        if not trigger_phrases:
            return 0.0

        # Simple heuristic: count how many trigger phrases appear in test cases
        covered = 0
        for phrase in trigger_phrases:
            phrase_lower = phrase.lower()
            for test in positive_tests:
                if phrase_lower in test.lower():
                    covered += 1
                    break

        return covered / len(trigger_phrases)

    def _generate_validation_summary(
        self,
        structure: dict,
        compliance: dict,
        quality: dict,
        test_cases: dict,
    ) -> str:
        """
        Generate human-readable validation summary.

        Args:
            structure: Structure validation results
            compliance: Compliance validation results
            quality: Quality assessment results
            test_cases: Generated test cases

        Returns:
            Human-readable summary string

        """
        parts = []

        # Structure summary
        if structure.get("overall_valid"):
            parts.append("✓ Structure validation passed")
        else:
            parts.append("✗ Structure validation failed")
            errors = structure.get("name_errors", []) + structure.get("description_errors", [])
            if errors:
                parts.append(f"  Issues: {', '.join(errors[:2])}")

        # Compliance summary
        if compliance.get("passed"):
            parts.append("✓ Compliance check passed")
        else:
            parts.append("✗ Compliance check failed")

        # Quality summary
        score = quality.get("overall_score", 0.0)
        parts.append(f"✓ Quality score: {score:.2f}")

        # Test cases summary
        total_tests = test_cases.get("total_tests", 0)
        parts.append(f"✓ Generated {total_tests} test cases")

        return "\n".join(parts)
