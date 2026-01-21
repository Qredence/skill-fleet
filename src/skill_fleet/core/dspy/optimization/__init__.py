"""
DSPy optimization modules.

This package provides:
- OptimizerSelector: Intelligent auto-selection of DSPy optimizers
"""

from __future__ import annotations

from .selector import (
    OptimizerConfig,
    OptimizerContext,
    OptimizerRecommendation,
    OptimizerSelector,
    OptimizerType,
)

__all__ = [
    "OptimizerConfig",
    "OptimizerContext",
    "OptimizerRecommendation",
    "OptimizerSelector",
    "OptimizerType",
]
