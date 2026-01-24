"""
Repository interfaces for data access.

These interfaces define the contracts for data access,
allowing the domain to be independent of infrastructure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..models import Job, JobStatus, Skill, SkillMetadata, TaxonomyPath


class SkillRepository(ABC):
    """
    Repository interface for Skill entities.

    This defines the contract for skill data access without
    coupling to any specific storage mechanism (filesystem, database, etc.).
    """

    @abstractmethod
    def find_by_id(self, skill_id: str) -> Skill | None:
        """Find a skill by its ID."""
        pass

    @abstractmethod
    def find_by_taxonomy_path(self, path: str | TaxonomyPath) -> Skill | None:
        """Find a skill by its taxonomy path."""
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> list[Skill]:
        """Find all skills with a given name."""
        pass

    @abstractmethod
    def find_by_type(self, skill_type: str) -> list[Skill]:
        """Find all skills of a given type."""
        pass

    @abstractmethod
    def find_always_loaded(self) -> list[Skill]:
        """Find all skills that should be loaded at startup."""
        pass

    @abstractmethod
    def save(self, skill: Skill) -> bool:
        """
        Save a skill.

        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def delete(self, skill_id: str) -> bool:
        """
        Delete a skill by ID.

        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def exists(self, skill_id: str) -> bool:
        """Check if a skill exists."""
        pass

    @abstractmethod
    def list_all(self, root: Path | None = None) -> list[Skill]:
        """List all skills in the taxonomy."""
        pass


class JobRepository(ABC):
    """
    Repository interface for Job entities.

    This defines the contract for job data access without
    coupling to any specific storage mechanism.
    """

    @abstractmethod
    def find_by_id(self, job_id: str) -> Job | None:
        """Find a job by its ID."""
        pass

    @abstractmethod
    def save(self, job: Job) -> bool:
        """
        Save a job.

        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def delete(self, job_id: str) -> bool:
        """
        Delete a job by ID.

        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def find_by_status(self, status: JobStatus) -> list[Job]:
        """Find all jobs with a given status."""
        pass

    @abstractmethod
    def find_pending_jobs(self) -> list[Job]:
        """Find all pending jobs that should be resumed."""
        pass

    @abstractmethod
    def find_running_jobs(self) -> list[Job]:
        """Find all currently running jobs."""
        pass

    @abstractmethod
    def find_jobs_by_user(self, user_id: str) -> list[Job]:
        """Find all jobs for a given user."""
        pass

    @abstractmethod
    def list_all(self) -> list[Job]:
        """List all jobs."""
        pass


class TaxonomyRepository(ABC):
    """
    Repository interface for Taxonomy data.

    This defines the contract for taxonomy data access without
    coupling to any specific storage mechanism.
    """

    @abstractmethod
    def get_structure(self) -> dict[str, Any]:
        """Get the full taxonomy structure."""
        pass

    @abstractmethod
    def get_branch(self, path: str) -> dict[str, Any] | None:
        """Get a specific branch of the taxonomy."""
        pass

    @abstractmethod
    def resolve_path(self, identifier: str) -> str | None:
        """
        Resolve a skill identifier to a canonical taxonomy path.

        Handles aliases, partial matches, and legacy paths.
        """
        pass

    @abstractmethod
    def get_dependencies(self, skill_id: str) -> list[str]:
        """Get dependencies for a skill."""
        pass

    @abstractmethod
    def get_dependents(self, skill_id: str) -> list[str]:
        """Get skills that depend on this skill."""
        pass

    @abstractmethod
    def validate_dependencies(self, skill_id: str, dependencies: list[str]) -> tuple[bool, str | None]:
        """
        Validate dependencies for a skill.

        Returns (is_valid, error_message).
        Checks for:
        - Circular dependencies
        - Missing dependencies
        - Invalid dependency paths
        """
        pass

    @abstractmethod
    def find_relevant_branches(self, task_description: str) -> dict[str, Any]:
        """
        Find taxonomy branches relevant to a task description.

        This is used for context-aware path selection.
        """
        pass


__all__ = [
    "SkillRepository",
    "JobRepository",
    "TaxonomyRepository",
]
