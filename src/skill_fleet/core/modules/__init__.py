"""
DSPy modules for skill creation workflows.

This package contains reusable DSPy module implementations organized by workflow phase:
- understanding/: Modules for requirements gathering and analysis
- generation/: Modules for content generation
- validation/: Modules for compliance and quality validation
- hitl/: Modules for human-in-the-loop interactions

Re-exports DSPy 3.1.2+ primitives for convenient access:
- ReAct: Tool-augmented reasoning with action/observation loops
- Refine: Iterative refinement with feedback
- ProgramOfThought: Code-based reasoning and computation
"""

from __future__ import annotations

import dspy

from skill_fleet.core.modules.base import BaseModule

# Re-export DSPy primitives for convenient access
ReAct = dspy.ReAct
Refine = dspy.Refine
ProgramOfThought = dspy.ProgramOfThought

__all__ = [
    "BaseModule",
    "ProgramOfThought",
    "ReAct",
    "Refine",
]
