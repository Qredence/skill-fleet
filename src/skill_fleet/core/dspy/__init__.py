"""DSPy components for skill-fleet.

This module contains all DSPy signatures, modules, and programs
for the skill creation workflow.

Submodules:
- signatures/: DSPy signature definitions for each phase
- modules/: DSPy module implementations
- programs.py: Workflow programs (legacy)
- skill_creator.py: Main 3-phase skill creator program
- conversational.py: Conversational DSPy modules
"""

# Re-export main components
from skill_fleet.core.dspy.skill_creator import SkillCreationProgram
from skill_fleet.core.dspy.programs import (
    SkillCreationProgram as LegacySkillCreationProgram,
)

__all__ = [
    "SkillCreationProgram",
    "LegacySkillCreationProgram",
]
