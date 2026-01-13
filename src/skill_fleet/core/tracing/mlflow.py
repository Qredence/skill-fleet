"""MLflow integration for skill creation experiment tracking.

Based on: https://dspy.ai/tutorials/math/#mlflow-dspy-integration

This module provides functions for setting up MLflow experiments and logging
skill creation metrics, decision trees, and checkpoint results.

Usage:
    # Start MLflow UI in one terminal
    mlflow ui

    # Run skill creation with debug mode
    uv run skill-fleet create-skill \\
      --task "Create async Python skill" \\
      --debug

The debug mode will automatically log to MLflow, capturing:
- Phase decision trees
- Checkpoint validation results
- Reasoning trace metrics
- System information

Example:
    >>> setup_mlflow_experiment("my-skill-creation")
    >>> log_phase_metrics("phase1", "extract_problem", {"accuracy": 0.95})
    >>> log_decision_tree("phase1", ["is_new_skill=True", "skill_type=technical"], "technical")
    >>> log_checkpoint_result("phase1", True, 0.9, [])
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

# Default MLflow configuration
DEFAULT_EXPERIMENT_NAME = "skill-fleet-phase1-phase2"
DEFAULT_TRACKING_URI = "mlruns"


def setup_mlflow_experiment(
    experiment_name: str = DEFAULT_EXPERIMENT_NAME,
    tracking_uri: str = DEFAULT_TRACKING_URI,
) -> None:
    """Setup MLflow experiment for skill creation tracking.

    Args:
        experiment_name: Name of the MLflow experiment
        tracking_uri: MLflow tracking URI (default: "mlruns")

    Raises:
        ImportError: If MLflow is not installed

    Examples:
        >>> setup_mlflow_experiment()
        >>> setup_mlflow_experiment("custom-experiment", "custom-tracking-uri")
    """
    try:
        import mlflow
    except ImportError as err:
        raise ImportError("MLflow is not installed. Install it with: uv add mlflow") from err

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    # Log system info
    try:
        import dspy

        mlflow.log_params(
            {
                "dspy_version": dspy.__version__,
                "workflow_version": "2.0",
            }
        )
    except Exception as e:
        logger.warning(f"Failed to log system info: {e}")

    logger.info(f"MLflow experiment '{experiment_name}' ready at {tracking_uri}")


def log_phase_metrics(
    phase: str,
    step: str,
    metrics: Mapping[str, float],
) -> None:
    """Log metrics for a phase step.

    Args:
        phase: Phase identifier (e.g., "phase1", "phase2")
        step: Step identifier (e.g., "extract_problem", "decide_novelty")
        metrics: Dictionary of metric names to values

    Examples:
        >>> log_phase_metrics("phase1", "extract_problem", {"accuracy": 0.95, "latency": 1.2})
    """
    try:
        import mlflow

        prefixed = {f"{phase}_{step}_{k}": v for k, v in metrics.items()}
        mlflow.log_metrics(prefixed)
        logger.debug(f"Logged metrics for {phase}.{step}: {prefixed}")
    except Exception as e:
        logger.warning(f"Failed to log metrics: {e}")


def log_decision_tree(
    phase: str,
    decision_path: list[str],
    final_decision: str,
) -> None:
    """Log decision tree traversal to MLflow.

    Args:
        phase: Phase identifier (e.g., "phase1", "phase2")
        decision_path: List of decision steps in order
        final_decision: Final decision reached

    Examples:
        >>> log_decision_tree(
        ...     "phase1",
        ...     ["is_new_skill=True", "skill_type=technical"],
        ...     "technical"
        ... )
    """
    try:
        import mlflow

        mlflow.log_text(
            "\n".join(decision_path),
            artifact_file=f"{phase}_decision_tree.txt",
        )
        mlflow.log_param(f"{phase}_final_decision", final_decision)
        logger.debug(f"Logged decision tree for {phase}: {final_decision}")
    except Exception as e:
        logger.warning(f"Failed to log decision tree: {e}")


def log_checkpoint_result(
    phase: str,
    checkpoint_passed: bool,
    score: float,
    errors: list[str],
) -> None:
    """Log checkpoint validation result.

    Args:
        phase: Phase identifier (e.g., "phase1", "phase2")
        checkpoint_passed: Whether checkpoint passed validation
        score: Checkpoint score (0.0-1.0)
        errors: List of validation errors (if any)

    Examples:
        >>> log_checkpoint_result("phase1", True, 0.95, [])
        >>> log_checkpoint_result("phase2", False, 0.6, ["Missing capability", "Invalid type"])
    """
    try:
        import mlflow

        mlflow.log_metrics(
            {
                f"{phase}_checkpoint_passed": float(checkpoint_passed),
                f"{phase}_checkpoint_score": score,
                f"{phase}_checkpoint_errors": len(errors),
            }
        )

        if errors:
            mlflow.log_text(
                "\n".join(errors),
                artifact_file=f"{phase}_checkpoint_errors.txt",
            )

        logger.debug(f"Logged checkpoint for {phase}: passed={checkpoint_passed}, score={score}")
    except Exception as e:
        logger.warning(f"Failed to log checkpoint result: {e}")


def log_phase_artifact(
    phase: str,
    artifact_name: str,
    content: str,
) -> None:
    """Log a text artifact for a phase.

    Args:
        phase: Phase identifier (e.g., "phase1", "phase2")
        artifact_name: Name of the artifact file
        content: Content to write to the artifact

    Examples:
        >>> log_phase_artifact("phase1", "problem_statement.txt", "Clear problem here...")
    """
    try:
        import mlflow

        artifact_file = f"{phase}_{artifact_name}"
        mlflow.log_text(content, artifact_file=artifact_file)
        logger.debug(f"Logged artifact for {phase}: {artifact_file}")
    except Exception as e:
        logger.warning(f"Failed to log artifact: {e}")


def log_parameter(
    phase: str,
    name: str,
    value: Any,
) -> None:
    """Log a parameter for a phase.

    Args:
        phase: Phase identifier (e.g., "phase1", "phase2")
        name: Parameter name
        value: Parameter value

    Examples:
        >>> log_parameter("phase1", "temperature", 0.8)
        >>> log_parameter("phase2", "max_iterations", 3)
    """
    try:
        import mlflow

        param_key = f"{phase}_{name}"
        mlflow.log_param(param_key, str(value))
        logger.debug(f"Logged parameter: {param_key}={value}")
    except Exception as e:
        logger.warning(f"Failed to log parameter: {e}")


def get_mlflow_run_id() -> str | None:
    """Get the current active MLflow run ID.

    Returns:
        Active MLflow run ID or None if no run is active

    Examples:
        >>> run_id = get_mlflow_run_id()
        >>> if run_id:
        ...     print(f"Active run: {run_id}")
    """
    try:
        import mlflow

        run = mlflow.active_run()
        return run.info.run_id if run else None
    except Exception:
        return None


def end_mlflow_run() -> None:
    """End the current active MLflow run.

    Examples:
        >>> end_mlflow_run()
    """
    try:
        import mlflow

        mlflow.end_run()
        logger.info("Ended MLflow run")
    except Exception as e:
        logger.warning(f"Failed to end MLflow run: {e}")


__all__ = [
    "setup_mlflow_experiment",
    "log_phase_metrics",
    "log_decision_tree",
    "log_checkpoint_result",
    "log_phase_artifact",
    "log_parameter",
    "get_mlflow_run_id",
    "end_mlflow_run",
    "DEFAULT_EXPERIMENT_NAME",
    "DEFAULT_TRACKING_URI",
]
