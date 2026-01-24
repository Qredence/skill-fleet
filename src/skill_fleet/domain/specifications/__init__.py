"""
Domain specifications for skill-fleet.

Specifications encapsulate business rules and validation logic.
They follow the Specification pattern from Domain-Driven Design.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import Job, JobStatus, Skill, SkillMetadata, TaxonomyPath


class Specification(ABC):
    """
    Base class for specifications.

    A specification is a predicate that determines if an object
    satisfies some business rule.
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: Any) -> bool:
        """Check if the candidate satisfies this specification."""
        pass

    def and_spec(self, other: "Specification") -> "AndSpecification":
        """Combine with another specification using AND logic."""
        return AndSpecification(self, other)

    def or_spec(self, other: "Specification") -> "OrSpecification":
        """Combine with another specification using OR logic."""
        return OrSpecification(self, other)

    def not_spec(self) -> "NotSpecification":
        """Negate this specification."""
        return NotSpecification(self)


class AndSpecification(Specification):
    """AND combination of two specifications."""

    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(candidate)


class OrSpecification(Specification):
    """OR combination of two specifications."""

    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(candidate)


class NotSpecification(Specification):
    """NOT of a specification."""

    def __init__(self, spec: Specification):
        self.spec = spec

    def is_satisfied_by(self, candidate: Any) -> bool:
        return not self.spec.is_satisfied_by(candidate)


# ============================================================================
# Skill Specifications
# ============================================================================


class SkillSpecification(Specification):
    """Base specification for skills."""

    def is_satisfied_by(self, candidate: Any) -> bool:
        if not isinstance(candidate, (Skill, SkillMetadata)):
            return False
        return self._is_satisfied_by(candidate)

    def _is_satisfied_by(self, candidate: Skill | SkillMetadata) -> bool:
        """Subclasses implement the actual rule."""
        return True


class SkillHasValidName(SkillSpecification):
    """Specification for valid skill names."""

    def _is_satisfied_by(self, candidate: Skill | SkillMetadata) -> bool:
        import re

        name = candidate.name if isinstance(candidate, Skill) else candidate.name

        if not name:
            return False
        if len(name) < 1 or len(name) > 64:
            return False
        if not re.match(r"^[a-z0-9-]+$", name):
            return False
        if name.startswith("-") or name.endswith("-"):
            return False
        if "--" in name:
            return False

        return True


class SkillHasValidType(SkillSpecification):
    """Specification for valid skill types."""

    VALID_TYPES = {"guide", "tool_integration", "workflow", "reference", "memory_block"}

    def _is_satisfied_by(self, candidate: Skill | SkillMetadata) -> bool:
        if isinstance(candidate, Skill):
            skill_type = candidate.metadata.type.value
        else:
            skill_type = candidate.type.value if isinstance(candidate.type, type) else candidate.type

        return skill_type in self.VALID_TYPES


class SkillHasValidTaxonomyPath(SkillSpecification):
    """Specification for valid taxonomy paths."""

    def _is_satisfied_by(self, candidate: Skill | SkillMetadata) -> bool:
        try:
            if isinstance(candidate, Skill):
                TaxonomyPath(candidate.metadata.taxonomy_path or candidate.metadata.skill_id)
            else:
                TaxonomyPath(candidate.taxonomy_path or candidate.skill_id)
            return True
        except ValueError:
            return False


class SkillIsComplete(SkillSpecification):
    """Specification for complete skills (has required fields)."""

    def _is_satisfied_by(self, candidate: Skill | SkillMetadata) -> bool:
        if isinstance(candidate, Skill):
            metadata = candidate.metadata
        else:
            metadata = candidate

        return bool(
            metadata.skill_id
            and metadata.name
            and metadata.description
            and metadata.version
        )


class SkillIsReadyForPublication(SkillSpecification):
    """
    Specification for skills ready to be published.

    A skill is ready when it:
    - Is complete
    - Has valid name
    - Has valid type
    - Has valid taxonomy path
    - Has content (if checking Skill entity)
    """

    def __init__(self, require_content: bool = True):
        self.require_content = require_content

    def _is_satisfied_by(self, candidate: Skill | SkillMetadata) -> bool:
        return SkillHasValidName().is_satisfied_by(candidate) and \
               SkillHasValidType().is_satisfied_by(candidate) and \
               SkillHasValidTaxonomyPath().is_satisfied_by(candidate) and \
               SkillIsComplete().is_satisfied_by(candidate) and \
               (not self.require_content or not isinstance(candidate, Skill) or bool(candidate.content))


# ============================================================================
# Job Specifications
# ============================================================================


class JobSpecification(Specification):
    """Base specification for jobs."""

    def is_satisfied_by(self, candidate: Any) -> bool:
        return isinstance(candidate, Job) and self._is_satisfied_by(candidate)

    def _is_satisfied_by(self, job: Job) -> bool:
        """Subclasses implement the actual rule."""
        return True


class JobHasValidDescription(JobSpecification):
    """Specification for valid job task descriptions."""

    def _is_satisfied_by(self, job: Job) -> bool:
        desc = job.task_description
        return bool(desc and len(desc) >= 10 and len(desc) <= 10000)


class JobIsPending(JobSpecification):
    """Specification for jobs in pending status."""

    def _is_satisfied_by(self, job: Job) -> bool:
        return job.status == JobStatus.PENDING


class JobIsRunning(JobSpecification):
    """Specification for jobs in running status."""

    def _is_satisfied_by(self, job: Job) -> bool:
        return job.status == JobStatus.RUNNING


class JobIsTerminal(JobSpecification):
    """Specification for jobs in terminal state (completed or failed)."""

    def _is_satisfied_by(self, job: Job) -> bool:
        return job.status in (JobStatus.COMPLETED, JobStatus.FAILED)


class JobCanBeStarted(JobSpecification):
    """Specification for jobs that can be started."""

    def _is_satisfied_by(self, job: Job) -> bool:
        return JobIsPending().is_satisfied_by(job) and \
               JobHasValidDescription().is_satisfied_by(job)


class JobCanBeRetried(JobSpecification):
    """Specification for jobs that can be retried."""

    def _is_satisfied_by(self, job: Job) -> bool:
        return job.status == JobStatus.FAILED and bool(job.error)


class JobRequiresHITL(JobSpecification):
    """Specification for jobs waiting for human input."""

    def _is_satisfied_by(self, job: Job) -> bool:
        return job.status == JobStatus.PENDING_HITL


class JobIsStale(JobSpecification):
    """
    Specification for stale jobs.

    A job is stale if it's been running for too long without updates.
    """

    def __init__(self, max_age_seconds: int = 3600):
        self.max_age_seconds = max_age_seconds

    def _is_satisfied_by(self, job: Job) -> bool:
        from datetime import datetime, UTC

        if not JobIsRunning().is_satisfied_by(job):
            return False

        age = (datetime.now(UTC) - job.updated_at).total_seconds()
        return age > self.max_age_seconds


__all__ = [
    # Base
    "Specification",
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
    # Skill specifications
    "SkillSpecification",
    "SkillHasValidName",
    "SkillHasValidType",
    "SkillHasValidTaxonomyPath",
    "SkillIsComplete",
    "SkillIsReadyForPublication",
    # Job specifications
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
