"""
DSPy programs (complex workflow orchestrators).

This package contains high-level DSPy programs that orchestrate
multiple modules and signatures into complete workflows:

- conversational.py: Multi-turn conversation orchestrator
- task_analysis.py: Task analysis and planning program
- content_generation.py: Skill content creation program
- quality_assurance.py: QA pipeline program
- hitl.py: HITL checkpoint orchestrator
- signature_optimization.py: Signature tuning program

These programs evolved from core/dspy/programs.py and skill_creator.py.
"""

from __future__ import annotations

# Re-export from existing location during migration
from skill_fleet.core.dspy.skill_creator import SkillCreationProgram

__all__ = ["SkillCreationProgram"]
