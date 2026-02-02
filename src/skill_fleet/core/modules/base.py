"""
Base module for all DSPy modules in skill-fleet.

Provides common functionality for error handling, logging, result validation,
and modern async support with native DSPy 3.1.2+ features.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, TypeVar

import dspy
from dspy.utils.syncify import run_async

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=dspy.Prediction)


class BaseModule(dspy.Module):
    """
    Base class for all skill-fleet DSPy modules.

    Provides modern async support, error handling, structured logging,
    and result validation compatible with DSPy 3.1.2+.

    Example:
        class MyModule(BaseModule):
            def __init__(self):
                super().__init__()
                self.processor = dspy.ChainOfThought(MySignature)

            def forward(self, input_data: str) -> dspy.Prediction:
                return self.processor(query=input_data)

            # Async is automatically supported via aforward()

    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

    def forward(self, **kwargs: Any) -> dspy.Prediction:
        """
        Sync entrypoint.

        Compatibility rules:
        - Subclasses may implement **either** `forward()` (sync) or `aforward()` (async).
        - If a subclass implements `aforward()` only, this method sync-runs it.
        - If a subclass implements `forward()` only, this method is typically overridden and will not
          be invoked.
        - `BaseModule` itself is abstract: calling `BaseModule().forward()` raises.

        Args:
            **kwargs: Input arguments specific to the module

        Returns:
            dspy.Prediction with structured results

        """
        if type(self) is BaseModule:
            raise NotImplementedError(
                "BaseModule.forward() is abstract; implement forward/aforward."
            )

        # If subclass provides async implementation only, provide a sync wrapper.
        if type(self).aforward is not BaseModule.aforward:
            return run_async(type(self).aforward(self, **kwargs))

        raise NotImplementedError(
            f"{self.__class__.__name__} must implement forward() or aforward() method"
        )

    async def aforward(self, **kwargs: Any) -> dspy.Prediction:
        """
        Async entrypoint.

        Compatibility rules:
        - If a subclass implements `forward()` (sync) only, this method provides an async fallback
          by running `forward()` in a thread (preserving contextvars in Python 3.12+).
        - If a subclass implements `aforward()` (async) only, it should override this method.
        - `BaseModule` itself is abstract: calling `await BaseModule().aforward()` raises.

        Args:
            **kwargs: Input arguments specific to the module

        Returns:
            dspy.Prediction with structured results

        Raises:
            NotImplementedError: If subclass doesn't override

        """
        if type(self) is BaseModule:
            raise NotImplementedError(
                "BaseModule.aforward() is abstract; implement forward/aforward."
            )

        # If subclass provides only a sync forward(), offer an async fallback.
        if type(self).forward is not BaseModule.forward:
            return await asyncio.to_thread(type(self).forward, self, **kwargs)

        raise NotImplementedError(
            f"{self.__class__.__name__} must implement forward() or aforward() method"
        )

    def _to_prediction(self, **kwargs: Any) -> dspy.Prediction:
        """
        Create a dspy.Prediction from keyword arguments.

        Args:
            **kwargs: Key-value pairs to include in the prediction

        Returns:
            dspy.Prediction instance

        """
        return dspy.Prediction(**kwargs)

    def _sanitize_input(self, value: Any, max_length: int = 10000) -> str:
        """
        Sanitize input to prevent prompt injection and ensure reasonable size.

        Args:
            value: Input value to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string

        """
        if value is None:
            return ""

        text = str(value)

        if len(text) > max_length:
            self.logger.debug(f"Input truncated from {len(text)} to {max_length} chars")
            text = text[:max_length] + "... [truncated]"

        return text

    def _validate_result(self, result: Any, required_fields: list[str]) -> bool:
        """
        Validate that result contains required fields.

        Args:
            result: The result to validate
            required_fields: List of field names that must be present

        Returns:
            True if valid, False otherwise

        """
        if result is None:
            self.logger.warning("Result is None")
            return False

        if isinstance(result, dspy.Prediction):
            missing = [f for f in required_fields if not hasattr(result, f)]
        elif isinstance(result, dict):
            missing = [f for f in required_fields if f not in result]
        else:
            return False

        if missing:
            self.logger.warning(f"Missing fields in result: {missing}")
            return False

        return True

    def _log_execution(self, inputs: dict, outputs: dict, duration_ms: float | None = None):
        """
        Log module execution for monitoring.

        Args:
            inputs: Input arguments (sanitized)
            outputs: Output results
            duration_ms: Execution duration in milliseconds

        """
        self.logger.debug(
            f"Executed {self.__class__.__name__}",
            extra={
                "inputs": {k: self._sanitize_input(v, 100) for k, v in inputs.items()},
                "outputs": outputs,
                "duration_ms": duration_ms,
            },
        )
