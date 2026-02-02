"""Optimization utilities for DSPy programs."""

from .cache import WorkflowOptimizer
from .evaluation import (
    content_quality_metric,
    evaluate_program,
    load_trainset,
    metadata_metric,
    print_evaluation_report,
    skill_creation_metric,
    split_dataset,
    taxonomy_path_metric,
)
from .optimizer import (
    APPROVED_MODELS,
    DEFAULT_MODEL,
    REFLECTION_MODEL,
    get_lm,
)

__all__ = [
    # Cache/Workflow
    "WorkflowOptimizer",
    # Evaluation
    "load_trainset",
    "split_dataset",
    "taxonomy_path_metric",
    "metadata_metric",
    "content_quality_metric",
    "skill_creation_metric",
    "evaluate_program",
    "print_evaluation_report",
    # Optimizer (minimal - LegacySkillCreationProgram removed)
    "APPROVED_MODELS",
    "DEFAULT_MODEL",
    "REFLECTION_MODEL",
    "get_lm",
]
