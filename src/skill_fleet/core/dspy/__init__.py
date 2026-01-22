"""
DSPy components for skill-fleet.

This module contains all DSPy signatures, modules, and programs
for the skill creation workflow.

Submodules:
- signatures/: DSPy signature definitions for each phase
- modules/: DSPy module implementations
- skill_creator.py: Main 3-phase skill creator program
"""

# Re-export subpackages for auto-discovery
from skill_fleet.core.dspy import modules

# Re-export main components
from skill_fleet.core.dspy.skill_creator import SkillCreationProgram

__all__ = [
    "SkillCreationProgram",
    "modules",
]
