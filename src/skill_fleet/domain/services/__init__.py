"""
Domain services for skill-fleet.

Domain services contain business logic that doesn't naturally fit
within entities or value objects. They orchestrate domain behavior
across multiple entities.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..models import (
    Job,
    JobStatus,
    Skill,
    SkillMetadata,
    SkillType,
    TaxonomyPath,
)
from ..repositories import SkillRepository, TaxonomyRepository
from ...common.security import sanitize_taxonomy_path

logger = logging.getLogger(__name__)


class SkillDomainService:
    """
    Domain service for Skill-related business logic.

    This service handles complex business operations that involve
    multiple skills or cross-cutting concerns.
    """

    def __init__(
        self,
        skill_repository: SkillRepository,
        taxonomy_repository: TaxonomyRepository,
    ):
        self.skill_repository = skill_repository
        self.taxonomy_repository = taxonomy_repository

    def validate_skill_metadata(self, metadata: SkillMetadata) -> tuple[bool, list[str]]:
        """
        Validate skill metadata according to business rules.

        Returns (is_valid, list_of_errors).
        """
        errors = []

        # Required fields
        if not metadata.skill_id:
            errors.append("skill_id is required")
        if not metadata.name:
            errors.append("name is required")
        if not metadata.description:
            errors.append("description is required")

        # Name validation (per agentskills.io spec)
        name_errors = self._validate_skill_name(metadata.name)
        errors.extend(name_errors)

        # Taxonomy path validation
        if metadata.taxonomy_path:
            try:
                TaxonomyPath(metadata.taxonomy_path)
            except ValueError as e:
                errors.append(str(e))

        # Dependency validation
        if metadata.dependencies:
            for dep in metadata.dependencies:
                if not self.skill_repository.exists(dep):
                    errors.append(f"Dependency not found: {dep}")

        # Circular dependency check
        if metadata.skill_id and metadata.dependencies:
            has_circular = self.taxonomy_repository.validate_dependencies(
                metadata.skill_id,
                metadata.dependencies,
            )
            if not has_circular[0]:
                errors.append(f"Invalid dependencies: {has_circular[1]}")

        return (len(errors) == 0, errors)

    def _validate_skill_name(self, name: str) -> list[str]:
        """Validate skill name per agentskills.io spec."""
        errors = []

        if not name:
            errors.append("Name cannot be empty")
            return errors

        if len(name) < 1 or len(name) > 64:
            errors.append("Name must be 1-64 characters")

        if not re.match(r"^[a-z0-9-]+$", name):
            errors.append("Name must contain only lowercase letters, numbers, and hyphens")

        if name.startswith("-") or name.endswith("-"):
            errors.append("Name must not start or end with hyphen")

        if "--" in name:
            errors.append("Name must not contain consecutive hyphens")

        return errors

    def generate_skill_id(self, name: str, taxonomy_path: str) -> str:
        """
        Generate a skill ID from name and taxonomy path.

        The skill_id is the full taxonomy path including the skill name.
        """
        # Normalize the name
        normalized_name = name.lower().replace("_", "-")
        normalized_name = re.sub(r"[^a-z0-9-]", "", normalized_name)
        normalized_name = re.sub(r"-+", "-").strip("-")

        # Combine with taxonomy path
        if taxonomy_path and not taxonomy_path.endswith(normalized_name):
            return f"{taxonomy_path}/{normalized_name}"
        return normalized_name

    def extract_artifacts_from_content(self, skill_content: str) -> dict[str, dict[str, str]]:
        """
        Extract code artifacts from skill content.

        Returns a dict with 'assets' and 'examples' keys,
        each mapping filenames to content.

        This is domain logic because it represents business rules
        about how skill content should be parsed.
        """
        assets = self._extract_named_file_code_blocks(skill_content)
        examples = self._extract_usage_example_code_blocks(skill_content)

        return {
            "assets": assets,
            "examples": examples,
        }

    def _extract_named_file_code_blocks(self, skill_md: str) -> dict[str, str]:
        """
        Extract code blocks labeled with a backticked filename heading.

        Example:
            ### `pytest.ini`
            ```ini
            ...
            ```
        """
        assets: dict[str, str] = {}
        lines = skill_md.splitlines()

        heading_backtick_re = re.compile(r"^\s{0,3}#{2,6}\s+`(?P<name>[^`]+)`\s*$")
        fence_start_re = re.compile(r"^\s*```(?P<lang>[a-zA-Z0-9_+-]*)\s*$")

        i = 0
        while i < len(lines):
            m = heading_backtick_re.match(lines[i])
            if not m:
                i += 1
                continue

            raw_name = m.group("name")
            filename = self._safe_single_filename(raw_name)
            if not filename:
                i += 1
                continue

            # Scan forward for the code block
            j = i + 1
            fence_line = None
            while j < len(lines):
                if lines[j].lstrip().startswith("#"):
                    break
                if fence_start_re.match(lines[j]):
                    fence_line = j
                    break
                j += 1
            if fence_line is None:
                i += 1
                continue

            # Extract code block body
            j = fence_line + 1
            body: list[str] = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                body.append(lines[j])
                j += 1

            if j < len(lines) and lines[j].strip().startswith("```"):
                assets[filename] = "\n".join(body).rstrip() + "\n"
                i = j + 1
                continue

            i += 1

        return assets

    def _extract_usage_example_code_blocks(self, skill_md: str) -> dict[str, str]:
        """
        Extract fenced code blocks under the '## Usage Examples' section.
        """
        lines = skill_md.splitlines()

        # Find Usage Examples section
        start = None
        for idx, line in enumerate(lines):
            if line.strip() == "## Usage Examples":
                start = idx + 1
                break
        if start is None:
            return {}

        # Find end of section
        end = len(lines)
        for idx in range(start, len(lines)):
            if lines[idx].startswith("#") and lines[idx].lstrip().startswith("## "):
                end = idx
                break

        section = lines[start:end]

        # Language to extension mapping
        ext_for_lang = {
            "python": "py",
            "py": "py",
            "bash": "sh",
            "sh": "sh",
            "zsh": "sh",
            "shell": "sh",
            "ini": "ini",
            "toml": "toml",
            "yaml": "yml",
            "yml": "yml",
            "json": "json",
        }

        # Extract code blocks
        fence_start_re = re.compile(r"^\s*```(?P<lang>[a-zA-Z0-9_+-]*)\s*$")
        examples: dict[str, str] = {}

        i = 0
        example_idx = 0
        while i < len(section):
            fence = fence_start_re.match(section[i])
            if not fence:
                i += 1
                continue

            lang = (fence.group("lang") or "").lower()
            i += 1
            body: list[str] = []
            while i < len(section) and not section[i].strip().startswith("```"):
                body.append(section[i])
                i += 1

            if i < len(section) and section[i].strip().startswith("```"):
                example_idx += 1
                ext = ext_for_lang.get(lang, "txt")
                filename = f"example_{example_idx}.{ext}"
                examples[filename] = "\n".join(body).rstrip() + "\n"
                i += 1
                continue

            i += 1

        return examples

    def _safe_single_filename(self, candidate: str) -> str | None:
        """
        Return a safe single-path filename or None.

        LLM output is untrusted; keep this strict to prevent path traversal.
        """
        name = candidate.strip()
        if not name:
            return None
        if "/" in name or "\\" in name:
            return None
        if name.startswith("."):
            return None
        if not all(c.isalnum() or c in "._-" for c in name):
            return None
        return name


class JobDomainService:
    """
    Domain service for Job-related business logic.

    This service handles job lifecycle, transitions, and validation.
    """

    def __init__(self, job_repository: JobRepository):
        self.job_repository = job_repository

    def create_job(self, task_description: str, user_id: str) -> Job:
        """Create a new job with proper initialization."""
        import uuid

        job_id = str(uuid.uuid4())[:12]
        return Job(
            job_id=job_id,
            task_description=task_description,
            user_id=user_id,
            status=JobStatus.PENDING,
        )

    def can_transition_to(self, job: Job, new_status: JobStatus) -> tuple[bool, str | None]:
        """
        Check if a job can transition to a new status.

        Returns (can_transition, error_message).
        """
        valid_transitions = {
            JobStatus.PENDING: [JobStatus.RUNNING, JobStatus.FAILED],
            JobStatus.RUNNING: [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.PENDING_HITL],
            JobStatus.PENDING_HITL: [JobStatus.RUNNING, JobStatus.FAILED],
            JobStatus.COMPLETED: [],  # Terminal
            JobStatus.FAILED: [],  # Terminal (unless retry is implemented)
        }

        allowed = valid_transitions.get(job.status, [])
        if new_status not in allowed:
            return (
                False,
                f"Cannot transition from {job.status} to {new_status}. "
                f"Allowed: {allowed or 'none'}"
            )

        return (True, None)

    def validate_job_description(self, description: str) -> tuple[bool, str | None]:
        """
        Validate a job's task description.

        Returns (is_valid, error_message).
        """
        if not description or not description.strip():
            return (False, "Task description cannot be empty")

        if len(description) < 10:
            return (False, "Task description must be at least 10 characters")

        if len(description) > 10000:
            return (False, "Task description is too long (max 10000 characters)")

        return (True, None)

    def get_jobs_resumeable(self) -> list[Job]:
        """Get jobs that should be resumed after a restart."""
        return self.job_repository.find_pending_jobs()

    def cleanup_old_jobs(self, older_than_days: int = 7) -> int:
        """
        Clean up old completed/failed jobs.

        Returns the number of jobs deleted.
        """
        cutoff = datetime.now(UTC).replace(tzinfo=None) - __import__(
            "datetime"
        ).timedelta(days=older_than_days)

        all_jobs = self.job_repository.list_all()
        old_jobs = [
            job
            for job in all_jobs
            if job.is_terminal() and job.updated_at.replace(tzinfo=None) < cutoff
        ]

        count = 0
        for job in old_jobs:
            if self.job_repository.delete(job.job_id):
                count += 1

        return count


class TaxonomyDomainService:
    """
    Domain service for Taxonomy-related business logic.

    This service handles taxonomy structure, path resolution,
    and dependency management.
    """

    def __init__(
        self,
        taxonomy_repository: TaxonomyRepository,
        skill_repository: SkillRepository,
    ):
        self.taxonomy_repository = taxonomy_repository
        self.skill_repository = skill_repository

    def resolve_skill_location(
        self, identifier: str, user_id: str | None = None
    ) -> TaxonomyPath | None:
        """
        Resolve a skill identifier to a canonical taxonomy path.

        Handles:
        - Direct taxonomy paths
        - Skill IDs
        - Aliases
        - Partial matches

        Returns None if not found.
        """
        # Try direct resolution first
        resolved = self.taxonomy_repository.resolve_path(identifier)
        if resolved:
            return TaxonomyPath(resolved)

        # Try as skill ID
        skill = self.skill_repository.find_by_id(identifier)
        if skill:
            return skill.taxonomy_path

        # Try as name (get first match)
        skills = self.skill_repository.find_by_name(identifier)
        if skills:
            return skills[0].taxonomy_path

        return None

    def suggest_taxonomy_path(
        self, task_description: str, user_skills: list[str] | None = None
    ) -> TaxonomyPath | None:
        """
        Suggest an appropriate taxonomy path for a new skill.

        Uses the existing taxonomy structure and user's skills
        to make an intelligent suggestion.
        """
        # Get relevant branches based on task description
        branches = self.taxonomy_repository.find_relevant_branches(task_description)

        if not branches:
            # Default to root level
            return TaxonomyPath("user_skills")

        # Find the most relevant branch
        # This is a simple heuristic - could be improved with ML
        best_branch = max(branches.items(), key=lambda x: len(x[1]))[0] if branches else "user_skills"

        return TaxonomyPath(best_branch)

    def validate_taxonomy_structure(self, structure: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate a taxonomy structure.

        Returns (is_valid, list_of_errors).
        """
        errors = []

        # Basic structure validation
        if not isinstance(structure, dict):
            errors.append("Taxonomy structure must be a dictionary")
            return (False, errors)

        # Recursively validate paths
        for path, value in structure.items():
            path_errors = self._validate_taxonomy_path(path, value)
            errors.extend(path_errors)

        return (len(errors) == 0, errors)

    def _validate_taxonomy_path(self, path: str, value: Any) -> list[str]:
        """Validate a single taxonomy path."""
        errors = []

        # Path format validation
        try:
            TaxonomyPath(path)
        except ValueError as e:
            errors.append(f"Invalid path '{path}': {e}")

        # Value validation
        if isinstance(value, dict):
            # Recursively validate children
            for child_path, child_value in value.items():
                full_path = f"{path}/{child_path}"
                errors.extend(self._validate_taxonomy_path(full_path, child_value))

        return errors


__all__ = [
    "SkillDomainService",
    "JobDomainService",
    "TaxonomyDomainService",
]
