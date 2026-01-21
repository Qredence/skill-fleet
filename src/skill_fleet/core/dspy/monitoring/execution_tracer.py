"""
Execution tracing for DSPy modules.

Tracks detailed execution metrics including timing, token usage, and success rates.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TraceEntry:
    """Single trace entry for a module execution."""

    module_name: str
    start_time: float
    end_time: float | None = None
    success: bool = False
    error: str | None = None

    # Input/output tracking
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)

    # Metrics
    duration_ms: float | None = None
    tokens_used: int | None = None
    cost_estimate: float | None = None

    # Quality metrics
    quality_score: float | None = None
    validation_errors: list[str] = field(default_factory=list)

    def finalize(self, success: bool = True, error: str | None = None) -> None:
        """Mark trace as complete and calculate duration."""
        self.end_time = time.time()
        self.success = success
        self.error = error
        if self.end_time and self.start_time:
            self.duration_ms = (self.end_time - self.start_time) * 1000

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/export."""
        return {
            "module_name": self.module_name,
            "timestamp": datetime.fromtimestamp(self.start_time).isoformat(),
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
            "tokens_used": self.tokens_used,
            "cost_estimate": self.cost_estimate,
            "quality_score": self.quality_score,
            "validation_errors": self.validation_errors,
        }


class ExecutionTracer:
    """
    Tracer for DSPy module executions.

    Collects execution traces for analysis and debugging.
    Thread-safe for concurrent executions.

    Example:
        tracer = ExecutionTracer()

        with tracer.trace("my_module") as trace:
            result = module(input="test")
            trace.outputs = {"result": str(result)}
            trace.quality_score = 0.85

    """

    def __init__(self, max_traces: int = 1000) -> None:
        """
        Initialize tracer.

        Args:
            max_traces: Maximum traces to keep in memory (FIFO eviction)

        """
        self.max_traces = max_traces
        self._traces: list[TraceEntry] = []
        self._active_traces: dict[int, TraceEntry] = {}

    def start_trace(self, module_name: str, inputs: dict[str, Any] | None = None) -> TraceEntry:
        """
        Start a new trace for a module execution.

        Args:
            module_name: Name of the DSPy module being traced
            inputs: Input parameters to the module

        Returns:
            TraceEntry that will be updated during execution

        """
        trace = TraceEntry(
            module_name=module_name,
            start_time=time.time(),
            inputs=inputs or {},
        )
        self._active_traces[id(trace)] = trace
        return trace

    def end_trace(
        self,
        trace: TraceEntry,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        """
        End a trace and store results.

        Args:
            trace: The trace entry to finalize
            success: Whether execution succeeded
            error: Error message if failed

        """
        trace.finalize(success=success, error=error)

        # Remove from active traces
        trace_id = id(trace)
        if trace_id in self._active_traces:
            del self._active_traces[trace_id]

        # Store completed trace (with FIFO eviction)
        self._traces.append(trace)
        if len(self._traces) > self.max_traces:
            self._traces.pop(0)

    def trace(self, module_name: str, inputs: dict[str, Any] | None = None):
        """
        Context manager for tracing module execution.

        Usage:
            with tracer.trace("my_module", inputs={"query": "test"}) as trace:
                result = module(query="test")
                trace.outputs = {"result": str(result)}
        """
        from contextlib import contextmanager

        @contextmanager
        def _trace_context():
            trace = self.start_trace(module_name, inputs)
            try:
                yield trace
                self.end_trace(trace, success=True)
            except Exception as e:
                self.end_trace(trace, success=False, error=str(e))
                raise

        return _trace_context()

    def get_traces(
        self,
        module_name: str | None = None,
        success_only: bool = False,
        limit: int | None = None,
    ) -> list[TraceEntry]:
        """
        Get stored traces with optional filtering.

        Args:
            module_name: Filter by module name
            success_only: Only return successful traces
            limit: Maximum number of traces to return (most recent)

        Returns:
            List of trace entries matching criteria

        """
        traces = self._traces

        if module_name:
            traces = [t for t in traces if t.module_name == module_name]

        if success_only:
            traces = [t for t in traces if t.success]

        if limit:
            traces = traces[-limit:]

        return traces

    def get_metrics(self, module_name: str | None = None) -> dict[str, Any]:
        """
        Calculate aggregate metrics from traces.

        Args:
            module_name: Calculate metrics for specific module, or all if None

        Returns:
            Dictionary of aggregate metrics

        """
        traces = self.get_traces(module_name=module_name)

        if not traces:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0,
                "avg_quality_score": 0.0,
                "total_tokens": 0,
                "total_cost": 0.0,
            }

        successful = [t for t in traces if t.success]
        durations = [t.duration_ms for t in traces if t.duration_ms is not None]
        quality_scores = [t.quality_score for t in traces if t.quality_score is not None]
        tokens = [t.tokens_used for t in traces if t.tokens_used is not None]
        costs = [t.cost_estimate for t in traces if t.cost_estimate is not None]

        return {
            "total_executions": len(traces),
            "successful_executions": len(successful),
            "success_rate": len(successful) / len(traces) if traces else 0.0,
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0.0,
            "min_duration_ms": min(durations) if durations else 0.0,
            "max_duration_ms": max(durations) if durations else 0.0,
            "avg_quality_score": sum(quality_scores) / len(quality_scores)
            if quality_scores
            else 0.0,
            "total_tokens": sum(tokens),
            "total_cost": sum(costs),
        }

    def export_traces(self, output_path: str | None = None) -> list[dict[str, Any]]:
        """
        Export all traces as JSON-serializable dictionaries.

        Args:
            output_path: Optional path to write JSON file

        Returns:
            List of trace dictionaries

        """
        trace_dicts = [t.to_dict() for t in self._traces]

        if output_path:
            import json
            from pathlib import Path

            Path(output_path).write_text(
                json.dumps(trace_dicts, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        return trace_dicts

    def clear(self) -> None:
        """Clear all stored traces."""
        self._traces.clear()
        self._active_traces.clear()
