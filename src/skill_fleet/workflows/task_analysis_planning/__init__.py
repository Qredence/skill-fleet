"""
Task Analysis & Planning Workflow Orchestrator.

This module coordinates Phase 1 of the skill creation workflow:
- Understanding user intent
- Finding taxonomy path
- Analyzing dependencies
- Synthesizing a coherent plan

The orchestrator uses DSPy modules from the signatures task_analysis_planning
and coordinates HITL checkpoints when clarification is needed.
"""

from .orchestrator import TaskAnalysisOrchestrator

__all__ = ["TaskAnalysisOrchestrator"]
