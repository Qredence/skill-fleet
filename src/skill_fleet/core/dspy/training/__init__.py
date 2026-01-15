"""Training data management for DSPy optimization.

This module provides utilities for loading and managing gold-standard
training examples used by DSPy optimizers.

Usage:
    from skill_fleet.core.dspy.training import GoldStandardLoader, load_trainset

    # Load training set
    trainset = load_trainset(min_quality=0.8)

    # Or use the loader directly
    loader = GoldStandardLoader()
    trainset = loader.load_trainset()
    testset = loader.load_testset()
"""

from __future__ import annotations

from .gold_standards import (
    GoldSkillEntry,
    GoldStandardLoader,
    load_testset,
    load_trainset,
)

__all__ = [
    "GoldSkillEntry",
    "GoldStandardLoader",
    "load_testset",
    "load_trainset",
]
