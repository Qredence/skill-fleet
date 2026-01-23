"""
DSPy components for Skills Fleet.

This package contains all DSPy-specific building blocks organized by function:

Directory Structure:
- signatures/: DSPy signature definitions (flat, task-based naming)
- modules/: DSPy module implementations that compose signatures
- programs/: DSPy programs (complex workflow orchestrators)
- optimizer/: DSPy optimizer for signature tuning
- evaluations/: DSPy evaluation metrics and pipelines
- tools/: DSPy tools for external integrations
- metrics/: Quality metrics for skill evaluation
- utils/: DSPy-specific utilities

Import Guidelines:
    # Signatures
    from skill_fleet.dspy.signatures import task_analysis, content_generation

    # Programs (orchestrators)
    from skill_fleet.dspy.programs import SkillCreationProgram

    # Modules
    from skill_fleet.dspy.modules import UnderstandingOrchestrator

Migration Note:
    During the migration period, imports from skill_fleet.core.dspy
    will continue to work but emit deprecation warnings.
"""

from __future__ import annotations

# Re-export main components for convenience
# These will be populated as migration progresses

__all__: list[str] = []
