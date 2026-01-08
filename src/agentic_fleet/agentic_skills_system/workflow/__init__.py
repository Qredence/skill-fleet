"""DSPy workflow for dynamic skill creation.

This package provides:
- TaxonomySkillCreator: Main orchestrator for skill creation
- Pydantic models for structured outputs (models.py)
- Reward functions for quality assurance (rewards.py)
- Evaluation metrics and data loading (evaluation.py)
- MIPROv2/GEPA optimization (optimize.py)
"""

from __future__ import annotations

from .skill_creator import TaxonomySkillCreator

# Core workflow components
__all__ = [
    "TaxonomySkillCreator",
]


# Lazy imports for optional components
def __getattr__(name: str):
    """Lazy import for optimization and evaluation modules."""
    if name == "optimize_with_miprov2":
        from .optimize import optimize_with_miprov2

        return optimize_with_miprov2
    elif name == "optimize_with_gepa":
        from .optimize import optimize_with_gepa

        return optimize_with_gepa
    elif name == "load_optimized_program":
        from .optimize import load_optimized_program

        return load_optimized_program
    elif name == "skill_creation_metric":
        from .evaluation import skill_creation_metric

        return skill_creation_metric
    elif name == "load_trainset":
        from .evaluation import load_trainset

        return load_trainset
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
