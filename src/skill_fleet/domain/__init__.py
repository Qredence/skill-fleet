"""
Domain layer for skill-fleet.

This package contains the core business domain logic, separated from
API and infrastructure concerns.

Architecture:
- models: Domain entities and value objects
- repositories: Data access abstractions
- services: Domain business logic
- specifications: Business rules and validations
"""

from __future__ import annotations

# Models
from .models import (
    DomainEvent,
    Job,
    JobCompletedEvent,
    JobStatus,
    Skill,
    SkillCreatedEvent,
    SkillMetadata,
    SkillType,
    SkillWeight,
    LoadPriority,
    TaxonomyPath,
)

# Repositories
from .repositories import (
    JobRepository,
    SkillRepository,
    TaxonomyRepository,
)

# Services
from .services import (
    JobDomainService,
    SkillDomainService,
    TaxonomyDomainService,
)

# Specifications
from .specifications import (
    Specification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
    SkillSpecification,
    SkillHasValidName,
    SkillHasValidType,
    SkillHasValidTaxonomyPath,
    SkillIsComplete,
    SkillIsReadyForPublication,
    JobSpecification,
    JobHasValidDescription,
    JobIsPending,
    JobIsRunning,
    JobIsTerminal,
    JobCanBeStarted,
    JobCanBeRetried,
    JobRequiresHITL,
    JobIsStale,
)

__all__ = [
    # Models
    "DomainEvent",
    "Job",
    "JobCompletedEvent",
    "JobStatus",
    "Skill",
    "SkillCreatedEvent",
    "SkillMetadata",
    "SkillType",
    "SkillWeight",
    "LoadPriority",
    "TaxonomyPath",
    # Repositories
    "JobRepository",
    "SkillRepository",
    "TaxonomyRepository",
    # Services
    "JobDomainService",
    "SkillDomainService",
    "TaxonomyDomainService",
    # Specifications
    "Specification",
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
    "SkillSpecification",
    "SkillHasValidName",
    "SkillHasValidType",
    "SkillHasValidTaxonomyPath",
    "SkillIsComplete",
    "SkillIsReadyForPublication",
    "JobSpecification",
    "JobHasValidDescription",
    "JobIsPending",
    "JobIsRunning",
    "JobIsTerminal",
    "JobCanBeStarted",
    "JobCanBeRetried",
    "JobRequiresHITL",
    "JobIsStale",
]
