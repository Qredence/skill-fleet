"""DEPRECATED: Backward compatibility shim for workflow.modules.

All modules have been moved to skill_fleet.core.dspy.modules.
This file re-exports for backward compatibility.
"""

from __future__ import annotations

# Re-export all modules from the new location
from skill_fleet.core.dspy.modules import (
    EditModule,
    EditModuleQA,
    GatherExamplesModule,
    InitializeModule,
    IterateModule,
    PackageModule,
    PackageModuleQA,
    PlanModule,
    PlanModuleQA,
    UnderstandModule,
    UnderstandModuleQA,
)

__all__ = [
    "EditModule",
    "EditModuleQA",
    "GatherExamplesModule",
    "InitializeModule",
    "IterateModule",
    "PackageModule",
    "PackageModuleQA",
    "PlanModule",
    "PlanModuleQA",
    "UnderstandModule",
    "UnderstandModuleQA",
]
