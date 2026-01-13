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
    # Edit
    BestPractice,
    # Skill Structure
    Capability,
    CapabilityImplementation,
    # Agent
    ChecklistState,
    # HITL Models
    ClarifyingQuestion,
    CompatibilityConstraints,
    # Understanding
    DependencyAnalysis,
    DependencyRef,
    EditResult,
    # Iterate
    EvolutionMetadata,
    # Example Gathering
    ExampleGatheringConfig,
    ExampleGatheringResult,
    ExampleGatheringSession,
    # Initialize
    FileSpec,
    HITLRound,
    HITLSession,
    InitializeResult,
    IterateResult,
    # Package
    PackageResult,
    PackagingManifest,
    ParentSkillInfo,
    PlanResult,
    QuestionAnswer,
    QuestionOption,
    # Composite Results
    QuickSkillResult,
    ResourceRequirements,
    RevisionPlan,
    SkillCreationResult,
    SkillMetadata,
    SkillRevisionResult,
    SkillSkeleton,
    TaskIntent,
    TestCase,
    UnderstandingResult,
    UsageExample,
    UserExample,
    ValidationCheckItem,
    ValidationReport,
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
