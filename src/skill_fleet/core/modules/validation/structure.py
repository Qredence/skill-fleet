"""
Structural validation for skill requirements.

This module combines rule-based validation (regex patterns) with LLM-based validation
to comprehensively check skill structure against Anthropic's published requirements.
"""

from __future__ import annotations

import re
from typing import Any

import dspy

from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.validation.structure import ValidateSkillStructure


class ValidateStructureModule(BaseModule):
    """
    Validate skill structure before content generation.

    Combines fast rule-based validation (regex patterns) with comprehensive
    LLM-based validation to prevent common errors early in the workflow.

    Enforces:
    - Kebab-case naming (lowercase, hyphens, no spaces/capitals/underscores)
    - Description requirements (trigger phrases, length limits)
    - Security restrictions (no XML tags, reserved names)
    - Size recommendations (< 5,000 words)

    Example:
        module = ValidateStructureModule()
        result = module(
            skill_name="my-cool-skill",
            description="Creates React components. Use when user asks to 'build a component' or 'create React UI'.",
            skill_content="# My Cool Skill\n\n## Instructions..."
        )
        # result["overall_valid"] == True

        result = module(
            skill_name="My Cool Skill",
            description="Helps with projects"
        )
        # result["overall_valid"] == False
        # result["name_errors"] == ["Name 'My Cool Skill' contains capital letters",
        #                          "Name 'My Cool Skill' contains spaces"]
        # result["description_errors"] == ["Description missing trigger conditions"]

    """

    # Reserved terms that cannot appear in skill names (security/policy)
    RESERVED_NAMES: frozenset[str] = frozenset(
        {"claude", "anthropic", "claude-code", "anthropic-ai"}
    )

    # Patterns for rule-based validation
    KEBAB_CASE_PATTERN: re.Pattern[str] = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
    XML_TAG_PATTERN: re.Pattern[str] = re.compile(r"<[^>]+>")

    # Trigger condition indicators to check for
    TRIGGER_INDICATORS: list[str] = [
        "use when",
        "for when",
        "trigger",
        "activate",
        "if user",
        "when user",
        "for user",
        "mention",
        "ask",
        "say",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.validator = dspy.ChainOfThought(ValidateSkillStructure)

    def _is_valid_kebab_case(self, name: str) -> bool:
        """Return True if name matches kebab-case requirements."""
        return bool(name) and bool(self.KEBAB_CASE_PATTERN.match(name))

    def _is_reserved_name(self, name: str) -> bool:
        """Return True if the name contains a reserved term."""
        name_lower = (name or "").lower()
        return any(reserved in name_lower for reserved in self.RESERVED_NAMES)

    def forward(
        self,
        skill_name: str,
        description: str,
        skill_content: str = "",
    ) -> dspy.Prediction:  # type:ignore[override]
        """
        Validate skill structure against requirements.

        Performs both fast rule-based checks and comprehensive LLM-based
        validation, merging results for actionable feedback.

        Args:
            skill_name: Proposed skill name
            description: Skill description
            skill_content: Full SKILL.md content (optional, for size checks)

        Returns:
            Validation report with:
            - name_valid/name_errors: Naming convention compliance
            - description_valid/description_errors: Description requirements
            - description_warnings: Improvement suggestions
            - has_trigger_conditions: Whether trigger phrases are present
            - estimated_word_count: Size estimate
            - size_recommendation: Size guidance
            - security_issues: Security concerns
            - overall_valid: Can proceed with generation

        """
        start_time = self._get_time()

        # Rule-based validation (fast, deterministic)
        name_errors = self._check_name(skill_name)
        desc_errors = self._check_description(description)
        security_issues = self._check_security(description, skill_name)
        word_count = self._estimate_word_count(skill_content)

        # LLM-based validation (comprehensive, nuanced)
        try:
            result = self.validator(
                skill_name=self._sanitize_input(skill_name, max_length=100),
                description=self._sanitize_input(description, max_length=2000),
                skill_content=self._sanitize_input(skill_content, max_length=5000),
            )
        except Exception as e:
            self.logger.warning(f"LLM validation failed: {e}, using rule-based only")
            # Fallback to rule-based validation only
            fallback = self._create_fallback_result(
                skill_name,
                description,
                skill_content,
                name_errors,
                desc_errors,
                security_issues,
                word_count,
            )
            return self._to_prediction(**fallback)

        # Merge rule-based and LLM results
        merged_name_errors = name_errors + (result.name_errors or [])
        merged_desc_errors = desc_errors + (result.description_errors or [])
        merged_security = security_issues + (result.security_issues or [])

        # Determine overall validity
        overall_valid = (
            len(merged_name_errors) == 0
            and len(merged_desc_errors) == 0
            and len(merged_security) == 0
            and result.overall_valid
        )

        output = {
            "name_valid": len(name_errors) == 0 and result.name_valid,
            "name_errors": merged_name_errors,
            "description_valid": len(desc_errors) == 0 and result.description_valid,
            "description_errors": merged_desc_errors,
            "description_warnings": result.description_warnings or [],
            "has_trigger_conditions": result.has_trigger_conditions,
            "estimated_word_count": word_count or result.estimated_word_count,
            "size_recommendation": result.size_recommendation
            or self._size_recommendation(word_count),
            "security_issues": merged_security,
            "overall_valid": overall_valid,
        }

        # Log execution
        duration_ms = (self._get_time() - start_time) * 1000
        self._log_execution(
            inputs={"skill_name": skill_name, "description": description[:100]},
            outputs={"overall_valid": overall_valid, "name_errors": len(merged_name_errors)},
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

    def _check_name(self, name: str) -> list[str]:
        """
        Validate skill name follows kebab-case conventions.

        Rules:
        - Must match: ^[a-z][a-z0-9]*(-[a-z0-9]+)*$
        - No spaces, capitals, or underscores
        - Cannot contain reserved terms

        Args:
            name: Proposed skill name

        Returns:
            List of validation errors (empty if valid)

        """
        errors: list[str] = []

        if not name:
            errors.append("Skill name is required")
            return errors

        if not self.KEBAB_CASE_PATTERN.match(name):
            # Provide specific error messages for common mistakes
            if any(c.isupper() for c in name):
                errors.append(
                    f"Name '{name}' contains capital letters - use kebab-case "
                    f"(e.g., '{self._to_kebab_case(name)}')"
                )
            if " " in name:
                errors.append(
                    f"Name '{name}' contains spaces - use kebab-case "
                    f"(e.g., '{name.replace(' ', '-').lower()}')"
                )
            if "_" in name:
                errors.append(
                    f"Name '{name}' uses underscores - use hyphens "
                    f"(e.g., '{name.replace('_', '-')}')"
                )
            if not errors:
                errors.append(
                    f"Name '{name}' is not valid kebab-case. "
                    f"Use lowercase letters, numbers, and hyphens only."
                )

        # Check for reserved terms
        name_lower = name.lower()
        for reserved in self.RESERVED_NAMES:
            if reserved in name_lower:
                errors.append(
                    f"Name '{name}' contains reserved term '{reserved}' - "
                    f"these terms are reserved for official Anthropic skills"
                )

        return errors

    def _check_description(self, description: str) -> list[str]:
        """
        Validate description meets requirements.

        Rules:
        - Maximum 1024 characters
        - Must include trigger condition indicators

        Args:
            description: Skill description

        Returns:
            List of validation errors (empty if valid)

        """
        errors: list[str] = []

        if len(description) > 1024:
            errors.append(
                f"Description exceeds 1024 characters ({len(description)} chars). "
                f"Current length: {len(description)}. Please make it more concise."
            )

        # Check for trigger condition indicators
        desc_lower = description.lower()
        has_trigger = any(ind in desc_lower for ind in self.TRIGGER_INDICATORS)

        if not has_trigger:
            errors.append(
                "Description missing trigger conditions - add 'Use when...' clause. "
                "Example: 'Use when user asks to create React components'"
            )

        return errors

    def _check_security(self, description: str, name: str) -> list[str]:
        """
        Check for security issues in skill metadata.

        Checks:
        - XML angle brackets in description (prompt injection risk)
        - Reserved terms in name (already checked in _check_name)

        Args:
            description: Skill description
            name: Skill name

        Returns:
            List of security issues (empty if none found)

        """
        issues: list[str] = []

        if self.XML_TAG_PATTERN.search(description):
            issues.append(
                "Description contains XML angle brackets (< >) - "
                "remove for security. These can be interpreted as HTML/XML tags."
            )

        return issues

    def _estimate_word_count(self, content: str) -> int:
        """Estimate word count from content."""
        if not content:
            return 0
        return len(content.split())

    def _size_recommendation(self, word_count: int) -> str:
        """Determine size recommendation based on word count."""
        if word_count < 3000:
            return "optimal"
        elif word_count < 5000:
            return "acceptable"
        else:
            return "consider_splitting"

    def _to_kebab_case(self, name: str) -> str:
        """Convert a name to kebab-case (best effort)."""
        # Replace spaces and underscores with hyphens
        result = name.replace(" ", "-").replace("_", "-")
        # Convert to lowercase
        result = result.lower()
        # Remove any non-alphanumeric characters except hyphens
        result = "".join(c for c in result if c.isalnum() or c == "-")
        # Remove consecutive hyphens
        while "--" in result:
            result = result.replace("--", "-")
        # Remove leading/trailing hyphens
        result = result.strip("-")
        return result

    def _create_fallback_result(
        self,
        skill_name: str,
        description: str,
        skill_content: str,
        name_errors: list[str],
        desc_errors: list[str],
        security_issues: list[str],
        word_count: int,
    ) -> dict[str, Any]:
        """Create validation result when LLM validation fails."""
        has_trigger = any(ind in description.lower() for ind in self.TRIGGER_INDICATORS)

        return {
            "name_valid": len(name_errors) == 0,
            "name_errors": name_errors,
            "description_valid": len(desc_errors) == 0,
            "description_errors": desc_errors,
            "description_warnings": [],
            "has_trigger_conditions": has_trigger,
            "estimated_word_count": word_count,
            "size_recommendation": self._size_recommendation(word_count),
            "security_issues": security_issues,
            "overall_valid": len(name_errors) == 0
            and len(desc_errors) == 0
            and len(security_issues) == 0,
        }

    def _get_time(self) -> float:
        """Get current time for duration tracking."""
        import time

        return time.time()
