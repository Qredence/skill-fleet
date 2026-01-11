"""Capture and store LM reasoning traces throughout skill creation.

This module provides the ReasoningTracer class for capturing, displaying,
and storing LM reasoning traces during the skill creation workflow.

Tracer Modes:
- CLI: Display reasoning in real-time with --verbose flag
- MLflow: Log to MLflow with --debug flag for experiment tracking
- Training: Save to file only for training dataset runs
- None: Disable tracing

Example usage:
    # Create tracer for CLI display
    tracer = ReasoningTracer(mode="cli")

    # Start a run
    tracer.start_run("Create async Python skill", is_training=False)

    # Capture reasoning from DSPy module result
    result = my_module(input="test")
    tracer.trace(
        phase="phase1",
        step="extract_problem",
        result=result,
        inputs={"input": "test"}
    )

    # End run
    tracer.end_run(save_traces=False)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

import dspy

logger = logging.getLogger(__name__)


@dataclass
class ReasoningTrace:
    """Single reasoning trace from a DSPy module call.

    Attributes:
        phase: Phase identifier (e.g., "phase1", "phase2")
        step: Step identifier (e.g., "extract_problem", "decide_novelty")
        timestamp: ISO format timestamp of when the trace was captured
        reasoning: Full LM reasoning output
        inputs: Input values provided to the module
        outputs: Output values returned by the module
        trace_id: Unique identifier for this trace (ISO format timestamp)
    """

    phase: str
    step: str
    timestamp: str
    reasoning: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    trace_id: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert trace to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the trace
        """
        return {
            "trace_id": self.trace_id,
            "phase": self.phase,
            "step": self.step,
            "timestamp": self.timestamp,
            "reasoning": self.reasoning,
            "inputs": self.inputs,
            "outputs": self.outputs,
        }


class ReasoningTracer:
    """Capture reasoning traces during skill creation.

    This tracer supports multiple modes for different use cases:
    - CLI mode: Display reasoning in real-time with --verbose flag
    - MLflow mode: Log to MLflow with --debug flag for experiment tracking
    - Training mode: Save to file for MIPROv2 optimization
    - Combined modes: e.g., "cli+mlflow+training" for all three at once

    Args:
        mode: Tracing mode ("cli", "mlflow", "training", combined like "cli+mlflow", "none")
        output_dir: Directory for trace output files

    Attributes:
        mode: Current tracing mode (can be combined with "+")
        output_dir: Directory for output files
        traces: List of captured traces
        _mlflow_run_id: Active MLflow run ID (if mlflow is enabled in mode)
        _cli_enabled: Whether CLI display is enabled
        _mlflow_enabled: Whether MLflow logging is enabled
        _save_traces: Whether to save traces to file

    Examples:
        CLI mode only:
        >>> tracer = ReasoningTracer(mode="cli")
        >>> tracer.start_run("Create async Python skill")
        >>> # ... run modules ...
        >>> tracer.trace("phase1", "extract_problem", result, inputs)
        >>> tracer.end_run()

        Combined mode (CLI + MLflow + save traces):
        >>> tracer = ReasoningTracer(mode="cli+mlflow+training", output_dir=Path("traces"))
        >>> tracer.start_run("Create async Python skill")
        >>> # ... run modules ...
        >>> tracer.end_run(save_traces=True)
    """

    # Valid tracing modes
    VALID_MODES = ("cli", "mlflow", "training", "none")

    def __init__(
        self,
        mode: str = "cli",
        output_dir: Path | None = None,
    ) -> None:
        """Initialize ReasoningTracer.

        Args:
            mode: Tracing mode ("cli", "mlflow", "training", combined like "cli+mlflow", "none")
            output_dir: Directory for trace output files (default: "traces")

        Raises:
            ValueError: If mode contains invalid components
        """
        # Parse combined mode
        mode_parts = mode.split("+") if "+" in mode else [mode]

        # Validate all mode parts
        for part in mode_parts:
            if part not in self.VALID_MODES:
                raise ValueError(
                    f"Invalid mode '{part}'. Must be one of: {', '.join(self.VALID_MODES)}"
                )

        self.mode = mode
        self.output_dir = output_dir or Path("traces")
        self.traces: list[ReasoningTrace] = []
        self._mlflow_run_id: str | None = None

        # Parse enabled features from mode
        self._cli_enabled = "cli" in mode_parts
        self._mlflow_enabled = "mlflow" in mode_parts
        self._save_traces = "training" in mode_parts

    def start_run(self, task_description: str, is_training: bool = False) -> None:
        """Start a new tracing run.

        Args:
            task_description: Description of the skill being created
            is_training: Whether this is a training run (affects MLflow logging)

        Examples:
            >>> tracer = ReasoningTracer(mode="mlflow")
            >>> tracer.start_run("Create async Python skill", is_training=False)

            >>> # Combined mode
            >>> tracer = ReasoningTracer(mode="cli+mlflow+training")
            >>> tracer.start_run("Create async Python skill", is_training=True)
        """
        self.traces = []

        if self._mlflow_enabled or (is_training and self._save_traces):
            try:
                import mlflow

                mlflow.start_run()
                mlflow.log_params({"task_description": task_description})
                self._mlflow_run_id = mlflow.active_run().info.run_id
                logger.info(f"Started MLflow run: {self._mlflow_run_id}")
            except ImportError:
                logger.warning("MLflow not installed, skipping MLflow logging")
            except Exception as e:
                logger.warning(f"Failed to start MLflow run: {e}")

    def trace(
        self,
        phase: str,
        step: str,
        result: dspy.Prediction,
        inputs: dict[str, Any],
    ) -> ReasoningTrace:
        """Capture reasoning from a DSPy module result.

        This method:
        1. Extracts reasoning from the DSPy Prediction result
        2. Creates a ReasoningTrace object
        3. Displays in CLI if mode is "cli"
        4. Logs to MLflow if run is active

        Args:
            phase: Phase identifier (e.g., "phase1", "phase2")
            step: Step identifier (e.g., "extract_problem", "decide_novelty")
            result: DSPy Prediction object from module execution
            inputs: Input values provided to the module

        Returns:
            ReasoningTrace object with captured data

        Examples:
            >>> result = my_module(input="test")
            >>> trace = tracer.trace(
            ...     phase="phase1",
            ...     step="extract_problem",
            ...     result=result,
            ...     inputs={"input": "test"}
            ... )
        """
        # Extract reasoning from DSPy Prediction
        reasoning = ""
        if hasattr(result, "reasoning"):
            reasoning = result.reasoning
        elif hasattr(result, "rationale"):
            reasoning = result.rationale

        # Convert outputs to dict (handle Pydantic models)
        outputs = {}
        for key, value in dict(result).items():
            if hasattr(value, "model_dump"):
                outputs[key] = value.model_dump()
            else:
                outputs[key] = value

        trace = ReasoningTrace(
            phase=phase,
            step=step,
            timestamp=datetime.now().isoformat(),
            reasoning=reasoning,
            inputs=inputs,
            outputs=outputs,
        )
        self.traces.append(trace)

        # Display in CLI mode
        if self._cli_enabled:
            self._display_trace(trace)

        # Log to MLflow if active
        if self._mlflow_run_id:
            self._log_to_mlflow(trace)

        return trace

    def _display_trace(self, trace: ReasoningTrace) -> None:
        """Display reasoning in CLI with formatted output.

        Args:
            trace: ReasoningTrace to display
        """
        print(f"\n{'=' * 70}")
        print(f"[{trace.phase.upper()}] {trace.step}")
        print(f"{'=' * 70}")
        print(f"\n📝 Reasoning:\n{trace.reasoning}")
        print("\n✓ Output:")
        for key, value in trace.outputs.items():
            if key != "reasoning":
                # Truncate long values for display
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "..."
                print(f"  • {key}: {value_str}")

    def _log_to_mlflow(self, trace: ReasoningTrace) -> None:
        """Log reasoning trace to MLflow.

        Args:
            trace: ReasoningTrace to log
        """
        try:
            import mlflow

            # Log as artifact
            trace_file = self.output_dir / f"{trace.step}_{trace.trace_id}.json"
            trace_file.parent.mkdir(parents=True, exist_ok=True)
            trace_file.write_text(json.dumps(trace.to_dict(), indent=2))

            mlflow.log_artifact(str(trace_file))

            # Log as metrics
            mlflow.log_metrics(
                {
                    f"{trace.step}_success": 1.0,
                    f"{trace.step}_reasoning_length": len(trace.reasoning),
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log trace to MLflow: {e}")

    def end_run(self, save_traces: bool = False) -> None:
        """End tracing run.

        Args:
            save_traces: If True, save traces to file (training mode)

        Examples:
            >>> tracer.end_run(save_traces=False)

            For training data collection:
            >>> tracer.end_run(save_traces=True)
        """
        if self._mlflow_run_id:
            try:
                import mlflow

                mlflow.end_run()
                logger.info(f"Ended MLflow run: {self._mlflow_run_id}")
            except Exception as e:
                logger.warning(f"Failed to end MLflow run: {e}")
            finally:
                self._mlflow_run_id = None

        # Save traces to file if training mode enabled
        if save_traces and self._save_traces:
            self._save_training_traces()

    def _save_training_traces(self) -> None:
        """Save all traces to training data file.

        Creates a JSONL file with one trace per line for easy processing.
        """
        output_file = self.output_dir / "training_traces.jsonl"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "a") as f:
            for trace in self.traces:
                f.write(json.dumps(trace.to_dict()) + "\n")

        logger.info(f"Saved {len(self.traces)} traces to {output_file}")

    def get_traces_by_phase(self, phase: str) -> list[ReasoningTrace]:
        """Get all traces for a specific phase.

        Args:
            phase: Phase identifier (e.g., "phase1", "phase2")

        Returns:
            List of ReasoningTrace objects for the phase
        """
        return [t for t in self.traces if t.phase == phase]

    def get_traces_by_step(self, step: str) -> list[ReasoningTrace]:
        """Get all traces for a specific step.

        Args:
            step: Step identifier (e.g., "extract_problem", "decide_novelty")

        Returns:
            List of ReasoningTrace objects for the step
        """
        return [t for t in self.traces if t.step == step]

    def to_dict_list(self) -> list[dict[str, Any]]:
        """Convert all traces to a list of dictionaries.

        Returns:
            List of trace dictionaries
        """
        return [trace.to_dict() for trace in self.traces]


__all__ = [
    "ReasoningTrace",
    "ReasoningTracer",
]
