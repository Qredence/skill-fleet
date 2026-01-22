"""
Base service class for skill-fleet services.

Provides common dependencies, DSPy context management, and error handling
for all service classes in the skill-fleet architecture.
"""

from __future__ import annotations

import logging
from abc import ABC
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

import dspy

if TYPE_CHECKING:
    from pathlib import Path

    from skill_fleet.taxonomy.manager import TaxonomyManager

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Base exception for service errors."""

    def __init__(
        self,
        message: str,
        *,
        service_name: str | None = None,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize service error.

        Args:
            message: Error message
            service_name: Name of the service that raised the error
            operation: Operation that failed
            details: Additional error details

        """
        super().__init__(message)
        self.message = message
        self.service_name = service_name
        self.operation = operation
        self.details = details or {}

    def __str__(self) -> str:
        """Format error message."""
        parts = [self.message]
        if self.service_name:
            parts.insert(0, f"[{self.service_name}]")
        if self.operation:
            parts.insert(1, f"({self.operation})")
        return " ".join(parts)


class ConfigurationError(ServiceError):
    """Error in service configuration."""

    pass


class ValidationError(ServiceError):
    """Validation failed in service operation."""

    pass


class BaseService(ABC):
    """
    Base class for all skill-fleet services.

    Provides common dependencies and utilities:
    - Taxonomy manager access
    - Task-specific LM management
    - DSPy context helpers
    - Structured logging
    - Error handling patterns
    """

    def __init__(
        self,
        taxonomy_manager: TaxonomyManager | None = None,
        task_lms: dict[str, dspy.LM] | None = None,
        skills_root: Path | None = None,
    ) -> None:
        """
        Initialize base service.

        Args:
            taxonomy_manager: Taxonomy management instance
            task_lms: Dictionary of task-specific LMs
            skills_root: Skills root directory

        """
        self._taxonomy_manager = taxonomy_manager
        self._task_lms = task_lms or {}
        self._skills_root = skills_root
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    def taxonomy(self) -> TaxonomyManager | None:
        """Get the taxonomy manager."""
        return self._taxonomy_manager

    @property
    def skills_root(self) -> Path | None:
        """Get the skills root directory."""
        return self._skills_root

    def get_task_lm(self, task: str) -> dspy.LM | None:
        """
        Get LM for a specific task.

        Args:
            task: Task name (e.g., 'skill_understand', 'skill_edit')

        Returns:
            Task-specific LM or None if not configured

        """
        return self._task_lms.get(task)

    def get_default_lm(self) -> dspy.LM:
        """
        Get the default LM from DSPy settings.

        Returns:
            Default LM configured in dspy.settings

        Raises:
            ConfigurationError: If no default LM is configured

        """
        lm = dspy.settings.lm
        if lm is None:
            raise ConfigurationError(
                "No default LM configured in dspy.settings",
                service_name=self.__class__.__name__,
                operation="get_default_lm",
            )
        return lm

    @contextmanager
    def with_lm(self, task: str | None = None) -> Iterator[dspy.LM]:
        """
        Context manager to use a task-specific or default LM.

        Args:
            task: Optional task name for task-specific LM

        Yields:
            The LM to use within this context

        Example:
            with self.with_lm("skill_edit") as lm:
                result = some_dspy_module()

        """
        if task and task in self._task_lms:
            lm = self._task_lms[task]
            self._logger.debug("Using task-specific LM for %s", task)
        else:
            lm = self.get_default_lm()
            if task:
                self._logger.debug(
                    "No task-specific LM for %s, using default", task
                )

        with dspy.context(lm=lm):
            yield lm

    @contextmanager
    def with_context(
        self,
        task: str | None = None,
        **kwargs: Any,
    ) -> Iterator[None]:
        """
        Context manager for DSPy context with optional task LM.

        Args:
            task: Optional task name for task-specific LM
            **kwargs: Additional context parameters

        Yields:
            None (context is managed by DSPy)

        Example:
            with self.with_context("skill_edit", temperature=0.7):
                result = some_dspy_module()

        """
        context_kwargs = dict(kwargs)

        if task and task in self._task_lms:
            context_kwargs["lm"] = self._task_lms[task]
            self._logger.debug("Setting task LM context for %s", task)

        with dspy.context(**context_kwargs):
            yield

    def log_operation(
        self,
        operation: str,
        *,
        level: int = logging.INFO,
        **details: Any,
    ) -> None:
        """
        Log a service operation with structured details.

        Args:
            operation: Name of the operation
            level: Logging level
            **details: Additional details to log

        """
        msg = f"{operation}"
        if details:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            msg = f"{msg}: {detail_str}"
        self._logger.log(level, msg)

    def validate_taxonomy_available(self) -> TaxonomyManager:
        """
        Ensure taxonomy manager is available.

        Returns:
            The taxonomy manager

        Raises:
            ConfigurationError: If taxonomy manager is not configured

        """
        if self._taxonomy_manager is None:
            raise ConfigurationError(
                "Taxonomy manager not configured",
                service_name=self.__class__.__name__,
                operation="validate_taxonomy_available",
            )
        return self._taxonomy_manager
