"""Unified core logic for Skill Fleet.

This module consolidates the workflow and core packages into a unified architecture.

Directory Structure:
- dspy/: DSPy components (signatures, modules, programs)
- hitl/: Human-in-the-loop handlers
- tools/: External tools and integrations
- optimization/: Optimization and evaluation logic
- tracing/: Tracing infrastructure
- models.py: Unified data models
- creator.py: Main entry point for skill creation

Import Guidelines:
- For models: from skill_fleet.core.models import ...
- For DSPy components: from skill_fleet.core.dspy import ...
- For HITL: from skill_fleet.core.hitl import ...
"""

from skill_fleet.core.models import (
    # HITL Models
    ClarifyingQuestion,
    HITLRound,
    HITLSession,
    QuestionAnswer,
    QuestionOption,
    # Example Gathering
    ExampleGatheringConfig,
    ExampleGatheringResult,
    ExampleGatheringSession,
    UserExample,
    # Understanding
    DependencyAnalysis,
    DependencyRef,
    ParentSkillInfo,
    TaskIntent,
    UnderstandingResult,
    # Skill Structure
    Capability,
    CompatibilityConstraints,
    PlanResult,
    ResourceRequirements,
    SkillMetadata,
    # Initialize
    FileSpec,
    InitializeResult,
    SkillSkeleton,
    ValidationCheckItem,
    # Edit
    BestPractice,
    CapabilityImplementation,
    EditResult,
    UsageExample,
    # Package
    PackageResult,
    PackagingManifest,
    TestCase,
    ValidationReport,
    # Iterate
    EvolutionMetadata,
    IterateResult,
    RevisionPlan,
    # Composite Results
    QuickSkillResult,
    SkillCreationResult,
    SkillRevisionResult,
    # Agent
    ChecklistState,
)

__all__ = [
    # HITL Models
    "QuestionOption",
    "ClarifyingQuestion",
    "QuestionAnswer",
    "HITLRound",
    "HITLSession",
    # Example Gathering
    "UserExample",
    "ExampleGatheringConfig",
    "ExampleGatheringSession",
    "ExampleGatheringResult",
    # Understanding
    "TaskIntent",
    "DependencyRef",
    "DependencyAnalysis",
    "ParentSkillInfo",
    "UnderstandingResult",
    # Skill Structure
    "SkillMetadata",
    "Capability",
    "ResourceRequirements",
    "CompatibilityConstraints",
    "PlanResult",
    # Initialize
    "FileSpec",
    "SkillSkeleton",
    "ValidationCheckItem",
    "InitializeResult",
    # Edit
    "UsageExample",
    "BestPractice",
    "CapabilityImplementation",
    "EditResult",
    # Package
    "ValidationReport",
    "TestCase",
    "PackagingManifest",
    "PackageResult",
    # Iterate
    "RevisionPlan",
    "EvolutionMetadata",
    "IterateResult",
    # Composite Results
    "SkillCreationResult",
    "SkillRevisionResult",
    "QuickSkillResult",
    # Agent
    "ChecklistState",
]
