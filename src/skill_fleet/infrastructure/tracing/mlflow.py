r"""
MLflow integration for skill creation experiment tracking.

Based on: https://dspy.ai/tutorials/math/#mlflow-dspy-integration

This module provides functions for setting up MLflow experiments and logging
skill creation metrics, decision trees, and checkpoint results.

## Enhanced Features (v2.0)

- **Hierarchical run structure**: Parent run for skill creation, child runs for phases
- **Tag organization**: Tags for user_id, job_id, skill_type for easy filtering
- **LM usage tracking**: Automatic extraction of token usage from DSPy predictions
- **Complete artifacts**: Full skill content, validation reports, quality assessments
- **Quality metrics**: Validation scores, issues found, refinements made

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
- Token usage from DSPy LMs
- Complete skill artifacts

Example:
    >>> # Start parent run for skill creation
    >>> start_parent_run("my-skill-creation", user_id="user123", job_id="job456")
    >>> # Start child run for phase 1
    >>> with start_child_run("phase1_task_analysis"):
    ...     log_phase_metrics("phase1", "extract_problem", {"accuracy": 0.95})
    ...     log_lm_usage(prediction)  # Auto-extracts token usage
    >>> # Log quality metrics
    >>> log_quality_metrics({"score": 0.95, "issues_count": 2})
    >>> # Log complete skill artifacts
    >>> log_skill_artifacts(content="...", metadata={"name": "my-skill"})
    >>> end_parent_run()

"""

from __future__ import annotations

import logging
from datetime import UTC
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
    """
    Set up MLflow experiment for skill creation tracking.

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

        mlflow.log_params(  # type: ignore[attr-defined]
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
    """
    Log metrics for a phase step.

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
        mlflow.log_metrics(prefixed)  # type: ignore[attr-defined]
        logger.debug(f"Logged metrics for {phase}.{step}: {prefixed}")
    except Exception as e:
        logger.warning(f"Failed to log metrics: {e}")


def log_decision_tree(
    phase: str,
    decision_path: list[str],
    final_decision: str,
) -> None:
    """
    Log decision tree traversal to MLflow.

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

        mlflow.log_text(  # type: ignore[attr-defined]
            "\n".join(decision_path),
            artifact_file=f"{phase}_decision_tree.txt",
        )
        mlflow.log_param(f"{phase}_final_decision", final_decision)  # type: ignore[attr-defined]
        logger.debug(f"Logged decision tree for {phase}: {final_decision}")
    except Exception as e:
        logger.warning(f"Failed to log decision tree: {e}")


def log_checkpoint_result(
    phase: str,
    checkpoint_passed: bool,
    score: float,
    errors: list[str],
) -> None:
    """
    Log checkpoint validation result.

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

        mlflow.log_metrics(  # type: ignore[attr-defined]
            {
                f"{phase}_checkpoint_passed": float(checkpoint_passed),
                f"{phase}_checkpoint_score": score,
                f"{phase}_checkpoint_errors": len(errors),
            }
        )

        if errors:
            mlflow.log_text(  # type: ignore[attr-defined]
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
    """
    Log a text artifact for a phase.

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
        mlflow.log_text(content, artifact_file=artifact_file)  # type: ignore[attr-defined]
        logger.debug(f"Logged artifact for {phase}: {artifact_file}")
    except Exception as e:
        logger.warning(f"Failed to log artifact: {e}")


def log_parameter(
    phase_or_name: str,
    name_or_value: str | Any = None,
    value: Any = None,
) -> None:
    """
    Log a parameter.

    This function supports two calling conventions:
    1. Two-argument form: log_parameter(name, value) - uses implicit phase
    2. Three-argument form: log_parameter(phase, name, value) - explicit phase

    Args:
        phase_or_name: Phase identifier (3-arg form) or parameter name (2-arg form)
        name_or_value: Parameter name (3-arg form) or parameter value (2-arg form)
        value: Parameter value (3-arg form only, omitted in 2-arg form)

    Examples:
        >>> # Two-argument form (convenience for workflow-level logging)
        >>> log_parameter("skill_style", "comprehensive")
        >>> # Three-argument form (explicit phase for granular tracking)
        >>> log_parameter("phase1", "temperature", 0.8)

    """
    try:
        import mlflow

        # Detect which form is being used based on argument types
        if value is None:
            # Two-argument form: log_parameter(name, value)
            # Use empty phase for workflow-level parameters
            param_name = str(phase_or_name)
            param_value = str(name_or_value)
            mlflow.log_param(param_name, param_value)  # type: ignore[attr-defined]
            logger.debug(f"Logged parameter: {param_name}={param_value}")
        else:
            # Three-argument form: log_parameter(phase, name, value)
            phase = str(phase_or_name)
            name = str(name_or_value)
            param_key = f"{phase}_{name}"
            mlflow.log_param(param_key, str(value))  # type: ignore[attr-defined]
            logger.debug(f"Logged parameter: {param_key}={value}")
    except Exception as e:
        logger.warning(f"Failed to log parameter: {e}")


def get_mlflow_run_id() -> str | None:
    """
    Get the current active MLflow run ID.

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
    """
    End the current active MLflow run.

    Examples:
        >>> end_mlflow_run()

    """
    try:
        import mlflow

        mlflow.end_run()  # type: ignore[attr-defined]
        logger.info("Ended MLflow run")
    except Exception as e:
        logger.warning(f"Failed to end MLflow run: {e}")


# =============================================================================
# Enhanced MLflow Functions (v2.0) - Hierarchical runs, tagging, artifacts
# =============================================================================


def start_parent_run(
    run_name: str,
    user_id: str | None = None,
    job_id: str | None = None,
    skill_type: str | None = None,
    description: str | None = None,
    experiment_name: str = "skill-creation",
) -> str | None:
    """
    Start a parent MLflow run for a skill creation workflow.

    Parent runs provide a hierarchical structure where each phase can be
    logged as a child run. This makes it easy to see the complete skill
    creation workflow in MLflow UI.

    Args:
        run_name: Name for the run (e.g., task description or skill name)
        user_id: Optional user ID for tagging
        job_id: Optional job ID for tagging
        skill_type: Optional skill type for tagging (guide, tool_integration, etc.)
        description: Optional description for the run
        experiment_name: MLflow experiment name (default: "skill-creation")

    Returns:
        Parent run ID, or None if MLflow is not available

    Examples:
        >>> run_id = start_parent_run(
        ...     "python-decorators-skill",
        ...     user_id="user123",
        ...     job_id="job456",
        ...     skill_type="guide"
        ... )

    """
    try:
        from datetime import datetime

        import mlflow

        mlflow.set_tracking_uri(DEFAULT_TRACKING_URI)
        mlflow.set_experiment(experiment_name)

        start_run = getattr(mlflow, "start_run", None)
        if start_run is None:
            logger.warning("mlflow.start_run is not available; skipping MLflow parent run")
            return None

        # Start the parent run
        run = start_run(
            run_name=run_name[:100],  # MLflow limits run name to 100 chars
            description=description,
        )

        # Log tags for easy filtering
        tags: dict[str, str] = {
            "workflow_version": "2.0",
            "run_type": "parent",
        }

        if user_id:
            tags["user_id"] = user_id
        if job_id:
            tags["job_id"] = job_id
        if skill_type:
            tags["skill_type"] = skill_type

        # Add date tag for time-based filtering
        tags["date"] = datetime.now(UTC).strftime("%Y-%m-%d")

        mlflow.set_tags(tags)  # type: ignore[attr-defined]

        logger.info(f"Started parent MLflow run: {run.info.run_id}")
        return run.info.run_id

    except Exception as e:
        logger.warning(f"Failed to start parent run: {e}")
        return None


def start_child_run(run_name: str) -> Any:
    """
    Start a child MLflow run nested under the current parent run.

    Child runs are used for individual phases of the skill creation workflow.
    They inherit the parent run's tags and provide a hierarchical view
    in the MLflow UI.

    Args:
        run_name: Name for the child run (e.g., "phase1_task_analysis")

    Returns:
        Context manager for the child run (use with 'with' statement)

    Examples:
        >>> with start_child_run("phase1_task_analysis"):
        ...     log_phase_metrics("phase1", "understanding", {...})
        ...     log_lm_usage(prediction)

    """
    try:
        import mlflow

        start_run = getattr(mlflow, "start_run", None)
        if start_run is None:
            from contextlib import nullcontext

            logger.warning("mlflow.start_run is not available; skipping MLflow child run")
            return nullcontext()

        return start_run(run_name=run_name, nested=True)
    except Exception as e:
        logger.warning(f"Failed to start child run: {e}")
        # Return a no-op context manager
        from contextlib import nullcontext

        return nullcontext()


def end_parent_run() -> None:
    """
    End the current parent MLflow run.

    This should be called after all child runs are completed.

    Examples:
        >>> end_parent_run()

    """
    end_mlflow_run()


def log_tags(tags: dict[str, str]) -> None:
    """
    Log tags to the current MLflow run.

    Tags are useful for filtering and organizing runs in the MLflow UI.
    Unlike parameters, tags don't need to be unique across runs.

    Args:
        tags: Dictionary of tag names to values

    Examples:
        >>> log_tags({
        ...     "framework": "django",
        ...     "level": "advanced",
        ...     "validated": "true"
        ... })

    """
    try:
        import mlflow

        mlflow.set_tags(tags)  # type: ignore[attr-defined]
        logger.debug(f"Logged {len(tags)} tags")
    except Exception as e:
        logger.warning(f"Failed to log tags: {e}")


def log_lm_usage(prediction: Any, prefix: str = "lm") -> None:
    """
    Extract and log LM usage metrics from a DSPy prediction.

    DSPy 3.1.2+ with `track_usage=True` provides token usage information
    via the `get_lm_usage()` method on predictions.

    Args:
        prediction: DSPy prediction object with get_lm_usage() method
        prefix: Prefix for metric names (default: "lm")

    Examples:
        >>> # From within an orchestrator
        >>> result = await module.aforward(...)
        >>> log_lm_usage(result, prefix="phase1_lm")
        # Logs: phase1_lm_tokens_in, phase1_lm_tokens_out, phase1_lm_total_tokens

    """
    try:
        if not hasattr(prediction, "get_lm_usage"):
            logger.debug("Prediction does not have get_lm_usage method")
            return

        usage = prediction.get_lm_usage()
        if not usage:
            logger.debug("No LM usage data available")
            return

        # Extract token counts from usage data
        metrics: dict[str, float] = {}

        # Handle different usage formats
        if isinstance(usage, dict):
            for lm_name, lm_usage in usage.items():
                if isinstance(lm_usage, dict):
                    tokens_in = lm_usage.get("tokens_in", 0)
                    tokens_out = lm_usage.get("tokens_out", 0)
                    total_tokens = lm_usage.get("total_tokens", tokens_in + tokens_out)

                    base_key = f"{prefix}_{lm_name}" if lm_name else prefix
                    metrics[f"{base_key}_tokens_in"] = float(tokens_in)
                    metrics[f"{base_key}_tokens_out"] = float(tokens_out)
                    metrics[f"{base_key}_total_tokens"] = float(total_tokens)
                else:
                    # Simple numeric usage
                    metrics[f"{prefix}_{lm_name}"] = float(lm_usage)

        log_phase_metrics("", prefix, metrics)
        logger.debug(f"Logged LM usage: {metrics}")

    except Exception as e:
        logger.warning(f"Failed to log LM usage: {e}")


def log_quality_metrics(quality_data: dict[str, Any], prefix: str = "quality") -> None:
    """
    Log quality assessment metrics to MLflow.

    Logs validation scores, issue counts, and other quality indicators
    that can be tracked over time in the MLflow UI.

    Args:
        quality_data: Dictionary with quality assessment data
        prefix: Prefix for metric names (default: "quality")

    Examples:
        >>> log_quality_metrics({
        ...     "score": 0.95,
        ...     "issues_count": 2,
        ...     "warnings_count": 1,
        ...     "refinements_made": 3
        ... })
        # Logs: quality_score, quality_issues_count, quality_warnings_count, quality_refinements_made

    """
    try:
        import mlflow

        metrics: dict[str, float] = {}

        # Extract common quality metrics
        for key, value in quality_data.items():
            if isinstance(value, int | float | bool):
                metrics[f"{prefix}_{key}"] = float(value)

        mlflow.log_metrics(metrics)  # type: ignore[attr-defined]
        logger.debug(f"Logged quality metrics: {metrics}")

    except Exception as e:
        logger.warning(f"Failed to log quality metrics: {e}")


def log_skill_artifacts(
    content: str | None = None,
    metadata: dict[str, Any] | None = None,
    validation_report: dict[str, Any] | None = None,
    quality_assessment: dict[str, Any] | None = None,
) -> None:
    r"""
    Log complete skill artifacts to MLflow.

    This function logs the full skill content and metadata as artifacts
    in the current MLflow run. Artifacts are stored as files that can
    be viewed in the MLflow UI.

    Args:
        content: The generated skill content (e.g., SKILL.md content)
        metadata: Skill metadata dictionary
        validation_report: Validation report dictionary
        quality_assessment: Quality assessment dictionary

    Examples:
        >>> log_skill_artifacts(
        ...     content="# Python Decorators\\n...",
        ...     metadata={"name": "python-decorators", "type": "guide"},
        ...     validation_report={"passed": True, "score": 0.95}
        ... )

    """
    try:
        import json

        import mlflow

        # Log skill content if provided
        if content:
            mlflow.log_text(content, artifact_file="skill_content.md")  # type: ignore[attr-defined]

        # Log metadata as JSON artifact
        if metadata:
            metadata_json = json.dumps(metadata, indent=2, default=str)
            mlflow.log_text(metadata_json, artifact_file="skill_metadata.json")  # type: ignore[attr-defined]

        # Log validation report if provided
        if validation_report:
            report_json = json.dumps(validation_report, indent=2, default=str)
            mlflow.log_text(report_json, artifact_file="validation_report.json")  # type: ignore[attr-defined]

        # Log quality assessment if provided
        if quality_assessment:
            assessment_json = json.dumps(quality_assessment, indent=2, default=str)
            mlflow.log_text(assessment_json, artifact_file="quality_assessment.json")  # type: ignore[attr-defined]

        logger.debug("Logged skill artifacts")

    except Exception as e:
        logger.warning(f"Failed to log skill artifacts: {e}")


def log_validation_results(
    validation_report: dict[str, Any],
    prefix: str = "validation",
) -> None:
    """
    Log validation results as metrics and artifacts.

    Extracts key validation metrics from the report and logs them both
    as metrics (for charting) and as a JSON artifact (for details).

    Args:
        validation_report: Validation report dictionary
        prefix: Prefix for metric names (default: "validation")

    Examples:
        >>> log_validation_results({
        ...     "passed": True,
        ...     "score": 0.95,
        ...     "issues": [{"severity": "error", "message": "..."}]
        ... })
        # Logs: validation_passed=1.0, validation_score=0.95, validation_issues_count=1

    """
    try:
        import json

        import mlflow

        metrics: dict[str, float] = {}

        # Extract common validation metrics
        passed = validation_report.get("passed")
        if passed is not None:
            metrics[f"{prefix}_passed"] = float(passed)

        score = validation_report.get("score")
        if score is not None:
            metrics[f"{prefix}_score"] = float(score)

        issues = validation_report.get("issues", [])
        if isinstance(issues, list):
            metrics[f"{prefix}_issues_count"] = float(len(issues))
            metrics[f"{prefix}_errors_count"] = float(
                sum(1 for i in issues if i.get("severity") == "error")
            )
            metrics[f"{prefix}_warnings_count"] = float(
                sum(1 for i in issues if i.get("severity") == "warning")
            )

        mlflow.log_metrics(metrics)  # type: ignore[attr-defined]

        # Log full report as artifact
        report_json = json.dumps(validation_report, indent=2, default=str)
        mlflow.log_text(report_json, artifact_file=f"{prefix}_report.json")  # type: ignore[attr-defined]

        logger.debug(f"Logged validation results: {metrics}")

    except Exception as e:
        logger.warning(f"Failed to log validation results: {e}")


__all__ = [
    # Original functions
    "setup_mlflow_experiment",
    "log_phase_metrics",
    "log_decision_tree",
    "log_checkpoint_result",
    "log_phase_artifact",
    "log_parameter",
    "get_mlflow_run_id",
    "end_mlflow_run",
    # Enhanced v2.0 functions
    "start_parent_run",
    "start_child_run",
    "end_parent_run",
    "log_tags",
    "log_lm_usage",
    "log_quality_metrics",
    "log_skill_artifacts",
    "log_validation_results",
    # Constants
    "DEFAULT_EXPERIMENT_NAME",
    "DEFAULT_TRACKING_URI",
]
