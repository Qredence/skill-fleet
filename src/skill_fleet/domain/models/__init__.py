"""
Domain models for skill-fleet.

These are the core business entities, independent of any
infrastructure concerns (databases, APIs, file systems).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ...common.security import sanitize_taxonomy_path


class SkillType(str, Enum):
    """Type of skill per agentskills.io specification."""

    GUIDE = "guide"
    TOOL_INTEGRATION = "tool_integration"
    WORKFLOW = "workflow"
    REFERENCE = "reference"
    MEMORY_BLOCK = "memory_block"


class SkillWeight(str, Enum):
    """Relative weight/contribution of a skill."""

    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


class LoadPriority(str, Enum):
    """When to load the skill."""

    ALWAYS_LOADED = "always_loaded"
    ON_DEMAND = "on_demand"
    LAZY = "lazy"


class JobStatus(str, Enum):
    """Status of a skill creation job."""

    PENDING = "pending"
    RUNNING = "running"
    PENDING_HITL = "pending_hitl"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class TaxonomyPath:
    """
    Value object representing a taxonomy path.

    Provides validation and safe string representation.
    """

    path: str

    def __post_init__(self) -> None:
        # Validate path format
        if not self.path:
            raise ValueError("Taxonomy path cannot be empty")

        # Sanitize to prevent traversal attacks
        safe = sanitize_taxonomy_path(self.path)
        if not safe:
            raise ValueError(f"Invalid taxonomy path: {self.path}")

        # Update with safe value (frozen dataclass workaround)
        object.__setattr__(self, "path", safe)

    def __str__(self) -> str:
        return self.path

    def parent(self) -> TaxonomyPath | None:
        """Get the parent taxonomy path, or None if at root."""
        parts = self.path.split("/")
        if len(parts) <= 1:
            return None
        return TaxonomyPath("/".join(parts[:-1]))

    def child(self, segment: str) -> TaxonomyPath:
        """Create a child taxonomy path."""
        return TaxonomyPath(f"{self.path}/{segment}")

    def depth(self) -> int:
        """Return the depth of this path in the taxonomy tree."""
        return len(self.path.split("/"))


@dataclass
class SkillMetadata:
    """
    Metadata for a skill.

    This is a domain model that represents the business entity
    independent of storage format.
    """

    skill_id: str
    name: str
    description: str
    version: str = "1.0.0"
    type: SkillType = SkillType.GUIDE
    weight: SkillWeight = SkillWeight.MEDIUM
    load_priority: LoadPriority = LoadPriority.ON_DEMAND
    dependencies: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    category: str = ""
    keywords: list[str] = field(default_factory=list)
    scope: str = ""
    see_also: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    taxonomy_path: str = ""
    always_loaded: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        from pydantic import BaseModel

        # Use Pydantic for proper serialization
        class SkillMetadataModel(BaseModel):
            skill_id: str
            name: str
            description: str
            version: str = "1.0.0"
            type: str = "guide"
            weight: str = "medium"
            load_priority: str = "on_demand"
            dependencies: list[str] = []
            capabilities: list[str] = []
            category: str = ""
            keywords: list[str] = []
            scope: str = ""
            see_also: list[str] = []
            tags: list[str] = []
            taxonomy_path: str = ""
            always_loaded: bool = False

        return SkillMetadataModel(
            skill_id=self.skill_id,
            name=self.name,
            description=self.description,
            version=self.version,
            type=self.type.value,
            weight=self.weight.value,
            load_priority=self.load_priority.value,
            dependencies=self.dependencies,
            capabilities=self.capabilities,
            category=self.category,
            keywords=self.keywords,
            scope=self.scope,
            see_also=self.see_also,
            tags=self.tags,
            taxonomy_path=self.taxonomy_path,
            always_loaded=self.always_loaded,
        ).model_dump()


@dataclass
class Skill:
    """
    A skill in the taxonomy.

    This is the core domain entity for skills.
    """

    metadata: SkillMetadata
    content: str
    extra_files: dict[str, str] = field(default_factory=dict)
    path: Path | None = None  # File system location (infrastructure concern)

    @property
    def skill_id(self) -> str:
        return self.metadata.skill_id

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def taxonomy_path(self) -> TaxonomyPath:
        return TaxonomyPath(self.metadata.taxonomy_path or self.metadata.skill_id)

    def has_capability(self, capability: str) -> bool:
        """Check if skill has a specific capability."""
        return capability in self.metadata.capabilities

    def has_dependency(self, skill_id: str) -> bool:
        """Check if skill depends on another skill."""
        return skill_id in self.metadata.dependencies

    def is_always_loaded(self) -> bool:
        """Check if skill should be loaded at startup."""
        return self.metadata.always_loaded or self.metadata.load_priority == LoadPriority.ALWAYS_LOADED


@dataclass
class Job:
    """
    A skill creation job.

    This is the core domain entity for background jobs.
    """

    job_id: str
    task_description: str
    user_id: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    current_phase: str = field(default="")
    progress_message: str = field(default="")
    error: str | None = None
    result: Any = None
    draft_path: str | None = None
    intended_taxonomy_path: str | None = None
    validation_passed: bool | None = None
    validation_status: str | None = None
    validation_score: float | None = None
    hitl_type: str | None = None
    hitl_data: dict[str, Any] | None = None

    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status == JobStatus.RUNNING

    def is_terminal(self) -> bool:
        """Check if job is in a terminal state."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED)

    def is_pending_hitl(self) -> bool:
        """Check if job is waiting for human input."""
        return self.status == JobStatus.PENDING_HITL

    def can_be_retried(self) -> bool:
        """Check if failed job can be retried."""
        return self.status == JobStatus.FAILED

    def update_progress(self, phase: str, message: str) -> None:
        """Update job progress information."""
        self.current_phase = phase
        self.progress_message = message
        self.updated_at = datetime.now(UTC)

    def mark_failed(self, error: str) -> None:
        """Mark job as failed with an error message."""
        self.status = JobStatus.FAILED
        self.error = error
        self.updated_at = datetime.now(UTC)

    def mark_completed(self, result: Any) -> None:
        """Mark job as completed with a result."""
        self.status = JobStatus.COMPLETED
        self.result = result
        self.updated_at = datetime.now(UTC)


# Domain events for event-driven architecture (future use)
@dataclass(frozen=True)
class DomainEvent:
    """Base class for domain events."""

    event_id: str
    occurred_at: datetime


@dataclass(frozen=True)
class SkillCreatedEvent(DomainEvent):
    """Event raised when a skill is created."""

    skill_id: str
    taxonomy_path: str
    user_id: str


@dataclass(frozen=True)
class JobCompletedEvent(DomainEvent):
    """Event raised when a job completes."""

    job_id: str
    status: JobStatus
    result: Any


__all__ = [
    # Enums
    "SkillType",
    "SkillWeight",
    "LoadPriority",
    "JobStatus",
    # Value objects
    "TaxonomyPath",
    # Entities
    "SkillMetadata",
    "Skill",
    "Job",
    # Events
    "DomainEvent",
    "SkillCreatedEvent",
    "JobCompletedEvent",
]
