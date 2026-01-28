"""
DSPy components for skill-fleet.

This module contains all DSPy signatures, modules, and programs
for the skill creation workflow.

Submodules:
- signatures/: DSPy signature definitions for each phase
- modules/: DSPy module implementations
- skill_creator.py: Main 3-phase skill creator program
- lm_config.py: DSPy LM configuration
- fleet_config.py: Fleet config loader and LM factory
"""

# Re-export subpackages for auto-discovery
from skill_fleet.core.dspy import modules
from skill_fleet.core.dspy.fleet_config import (
    FleetConfigError,
    build_lm_for_task,
    load_fleet_config,
)

# Re-export LM configuration (moved from llm/ module)
from skill_fleet.core.dspy.lm_config import configure_dspy, get_task_lm

# Re-export main components
from skill_fleet.core.dspy.skill_creator import SkillCreationProgram

__all__ = [
    "SkillCreationProgram",
    "modules",
    # LM configuration
    "configure_dspy",
    "get_task_lm",
    "FleetConfigError",
    "build_lm_for_task",
    "load_fleet_config",
]
