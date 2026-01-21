"""Module monitoring wrapper for DSPy modules.

Wraps DSPy modules to provide automatic monitoring, logging, and metrics collection.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import dspy

from .execution_tracer import ExecutionTracer, TraceEntry

logger = logging.getLogger(__name__)


class ModuleMonitor(dspy.Module):
    """Monitoring wrapper for DSPy modules.

    Wraps any DSPy module to automatically track:
    - Execution timing and success rate
    - Input/output logging
    - Quality scoring
    - Error tracking
    - Token usage and cost estimation

    Example:
        # Wrap existing module
        generator = dspy.ChainOfThought("task -> output")
        monitored = ModuleMonitor(generator, name="task_generator")

        # Use normally
        result = monitored(task="Create a skill")

        # Access metrics
        metrics = monitored.get_metrics()
        print(f"Success rate: {metrics['success_rate']:.2%}")
    """

    def __init__(
        self,
        module: dspy.Module,
        name: str,
        tracer: ExecutionTracer | None = None,
        quality_metric: Callable[[Any], float] | None = None,
        log_inputs: bool = True,
        log_outputs: bool = True,
        log_level: int = logging.INFO,
    ) -> None:
        """Initialize module monitor.

        Args:
            module: DSPy module to wrap
            name: Name for this monitored module (used in metrics)
            tracer: ExecutionTracer instance (creates new if None)
            quality_metric: Optional function to score output quality
            log_inputs: Whether to log input parameters
            log_outputs: Whether to log output results
            log_level: Logging level for execution logs
        """
        super().__init__()
        self.module = module
        self.name = name
        self.tracer = tracer or ExecutionTracer()
        self.quality_metric = quality_metric
        self.log_inputs = log_inputs
        self.log_outputs = log_outputs
        self.log_level = log_level

        # Set up logger for this specific module
        self.logger = logging.getLogger(f"{__name__}.{name}")

    def forward(self, **kwargs: Any) -> dspy.Prediction:
        """Execute module with monitoring.

        Args:
            **kwargs: Input parameters for the wrapped module

        Returns:
            Module output (DSPy Prediction)

        Raises:
            Any exception from the wrapped module
        """
        # Start trace
        trace = self.tracer.start_trace(
            module_name=self.name,
            inputs=kwargs if self.log_inputs else {},
        )

        # Log execution start
        if self.log_inputs:
            self.logger.log(
                self.log_level,
                f"Executing {self.name} with inputs: {self._truncate_dict(kwargs)}",
            )
        else:
            self.logger.log(self.log_level, f"Executing {self.name}")

        try:
            # Execute wrapped module
            result = self.module(**kwargs)

            # Track outputs
            if self.log_outputs:
                trace.outputs = self._extract_outputs(result)
                self.logger.log(
                    self.log_level,
                    f"{self.name} completed: {self._truncate_dict(trace.outputs)}",
                )

            # Calculate quality score if metric provided
            if self.quality_metric:
                try:
                    trace.quality_score = self.quality_metric(result)
                    self.logger.debug(f"{self.name} quality score: {trace.quality_score:.3f}")
                except Exception as e:
                    self.logger.warning(f"Quality metric failed for {self.name}: {e}")

            # End trace successfully
            self.tracer.end_trace(trace, success=True)

            return result

        except Exception as e:
            # Log error
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.logger.error(f"{self.name} failed: {error_msg}")

            # End trace with error
            self.tracer.end_trace(trace, success=False, error=error_msg)

            # Re-raise original exception
            raise

    def get_metrics(self) -> dict[str, Any]:
        """Get aggregate metrics for this module.

        Returns:
            Dictionary of execution metrics
        """
        return self.tracer.get_metrics(module_name=self.name)

    def get_traces(self, limit: int | None = None) -> list[TraceEntry]:
        """Get execution traces for this module.

        Args:
            limit: Maximum number of recent traces to return

        Returns:
            List of trace entries
        """
        return self.tracer.get_traces(module_name=self.name, limit=limit)

    def export_traces(self, output_path: str) -> None:
        """Export traces for this module to JSON file.

        Args:
            output_path: Path to write JSON file
        """
        traces = self.get_traces()
        trace_dicts = [t.to_dict() for t in traces]

        import json
        from pathlib import Path

        Path(output_path).write_text(
            json.dumps(trace_dicts, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        self.logger.info(f"Exported {len(trace_dicts)} traces to {output_path}")

    @staticmethod
    def _extract_outputs(result: Any) -> dict[str, Any]:
        """Extract outputs from DSPy Prediction or other result types."""
        if isinstance(result, dspy.Prediction):
            # Extract all prediction fields
            return {k: str(v)[:200] for k, v in result.items()}  # Truncate for logging
        else:
            return {"result": str(result)[:200]}

    @staticmethod
    def _truncate_dict(d: dict[str, Any], max_len: int = 100) -> dict[str, Any]:
        """Truncate dictionary values for logging."""
        return {k: str(v)[:max_len] + "..." if len(str(v)) > max_len else v for k, v in d.items()}

    def __repr__(self) -> str:
        return f"ModuleMonitor(name={self.name}, module={self.module.__class__.__name__})"
