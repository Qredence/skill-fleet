"""Pydantic models for the reworked skill-fleet architecture.

These models provide type-safe interfaces for all workflow steps,
HITL interactions, and configuration. Follows agentskills.io specification.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

# =============================================================================
# HITL (Human-in-the-Loop) Models
# =============================================================================


class QuestionOption(BaseModel):
    """A single option for a multi-choice clarifying question."""

    id: str = Field(description="Option identifier (e.g., 'a', 'b', 'c')")
    label: str = Field(description="Short label for the option")
    description: str = Field(
        default="", description="Detailed description of what this option means"
    )


class ClarifyingQuestion(BaseModel):
    """A clarifying question to ask the user during skill creation."""

    id: str = Field(description="Unique question identifier")
    question: str = Field(description="The question text to display to the user")
    context: str = Field(default="", description="Why this question is being asked")
    options: list[QuestionOption] = Field(
        default_factory=list,
        description="Multi-choice options (if empty, expects free-form answer)",
    )
    allows_multiple: bool = Field(
        default=False, description="Whether multiple options can be selected"
    )
    required: bool = Field(default=True, description="Whether an answer is required")


class QuestionAnswer(BaseModel):
    """User's answer to a clarifying question."""

    question_id: str = Field(description="ID of the question being answered")
    selected_options: list[str] = Field(
        default_factory=list, description="IDs of selected options (for multi-choice)"
    )
    free_text: str = Field(default="", description="Free-form text answer")


# =============================================================================
# Phase 1: Understanding Models
# =============================================================================


class TaskIntent(BaseModel):
    """Structured analysis of user intent."""

    purpose: str = Field(description="Primary purpose of the skill")
    problem_statement: str = Field(description="What problem does it solve?")
    target_audience: str = Field(description="Who is the target user?")
    value_proposition: str = Field(description="What value does it provide?")


class DependencyRef(BaseModel):
    """Reference to a dependency with justification."""

    skill_id: str = Field(description="Path-style skill identifier")
    justification: str = Field(description="Why this dependency is needed")
    required: bool = Field(default=True, description="Whether strictly required")


class DependencyAnalysis(BaseModel):
    """Complete analysis of required skill dependencies."""

    required: list[DependencyRef] = Field(
        default_factory=list, description="Skills user must know first (hard prerequisites)"
    )
    recommended: list[DependencyRef] = Field(
        default_factory=list, description="Skills that complement this one (soft recommendations)"
    )
    conflicts: list[str] = Field(
        default_factory=list, description="Skills that might conflict with this one"
    )


class SkillMetadata(BaseModel):
    """Metadata for a skill following agentskills.io spec."""

    skill_id: str = Field(
        description="Path-style identifier (e.g., 'technical_skills/programming/python')"
    )
    name: str = Field(
        max_length=64,
        pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
        description="Kebab-case name per agentskills.io spec",
    )
    description: str = Field(max_length=1024, description="What the skill does and when to use it")
    version: str = Field(
        default="1.0.0",
        pattern=r"^\d+\.\d+\.\d+$",
        description="Semantic version",
    )
    type: str = Field(description="Skill category (e.g., 'technical', 'cognitive')")
    tags: list[str] = Field(default_factory=list, description="Search keywords for discovery")
    taxonomy_path: str = Field(description="Full path in taxonomy")
    dependencies: list[str] = Field(default_factory=list, description="Required skill_ids")


# =============================================================================
# Phase 2: Generation Models
# =============================================================================


class Capability(BaseModel):
    """A discrete, testable capability within a skill."""

    name: str = Field(description="Capability name (snake_case)")
    description: str = Field(description="What this capability provides")
    test_criteria: str = Field(default="", description="How to verify this capability works")


class UsageExample(BaseModel):
    """A runnable usage example."""

    title: str = Field(description="Example title")
    description: str = Field(description="What this example demonstrates")
    code: str = Field(description="Example code")
    expected_output: str = Field(default="", description="Expected result")
    language: str = Field(default="python", description="Programming language")


class BestPractice(BaseModel):
    """A best practice recommendation."""

    title: str = Field(description="Best practice title")
    description: str = Field(description="What to do and why")
    example: str = Field(default="", description="Example demonstrating the practice")


class TestCase(BaseModel):
    """An integration test case."""

    name: str = Field(description="Test name")
    description: str = Field(description="What this test verifies")
    input_data: str = Field(default="", description="Test input")
    expected_result: str = Field(default="", description="Expected outcome")


# =============================================================================
# Phase 3: Validation Models
# =============================================================================


class ValidationCheckItem(BaseModel):
    """A single validation check result."""

    id: str = Field(description="Unique check identifier")
    check: str = Field(description="Description of what was validated")
    passed: bool = Field(description="Whether the check passed")
    message: str = Field(default="", description="Validation message or error")
    severity: Literal["critical", "warning", "info"] = Field(default="info")


class ValidationReport(BaseModel):
    """Complete validation report for a skill."""

    passed: bool = Field(description="Whether all critical checks passed")
    score: float = Field(ge=0.0, le=1.0, description="Overall quality score")
    checks: list[ValidationCheckItem] = Field(default_factory=list)
    feedback: str = Field(default="", description="Consolidated feedback for refinement")


# =============================================================================
# Orchestration Models
# =============================================================================


class SkillCreationResult(BaseModel):
    """Complete result from the skill creation workflow."""

    status: str = Field(description="Status: 'completed', 'failed', 'cancelled', 'pending_review'")
    skill_content: str | None = Field(default=None, description="Generated SKILL.md content")
    metadata: SkillMetadata | None = Field(default=None, description="Skill metadata")
    validation_report: ValidationReport | None = Field(default=None)
    error: str | None = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
