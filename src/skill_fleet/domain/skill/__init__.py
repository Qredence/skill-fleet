"""
Skill domain logic.

This package contains the core business logic for skills:
- creator.py: Skill creation orchestration
- models.py: Domain models (SkillMetadata, Capability, etc.)
- repository/: Skill storage and retrieval
"""

from __future__ import annotations

# Re-export from existing locations during migration
from skill_fleet.core.models import (
    BestPractice,
    Capability,
    CapabilityImplementation,
    CompatibilityConstraints,
    EditResult,
    FileSpec,
    InitializeResult,
    PackageResult,
    PackagingManifest,
    PlanResult,
    ResourceRequirements,
    SkillCreationResult,
    SkillMetadata,
    SkillRevisionResult,
    SkillSkeleton,
    TestCase,
    UsageExample,
    ValidationCheckItem,
    ValidationReport,
)

__all__ = [
    "BestPractice",
    "Capability",
    "CapabilityImplementation",
    "CompatibilityConstraints",
    "EditResult",
    "FileSpec",
    "InitializeResult",
    "PackageResult",
    "PackagingManifest",
    "PlanResult",
    "ResourceRequirements",
    "SkillCreationResult",
    "SkillMetadata",
    "SkillRevisionResult",
    "SkillSkeleton",
    "TestCase",
    "UsageExample",
    "ValidationCheckItem",
    "ValidationReport",
]
