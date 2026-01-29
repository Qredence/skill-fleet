# Workflows Guide

Last updated: 2026-01-27

This guide explains the three-phase skill creation workflow used by Skills Fleet and the common orchestrators you will interact with.

## Overview

The skill creation workflow is organized in three high-level phases:

1. Phase 1 — Task Analysis: analyze the user intent and produce a plan and taxonomy recommendation.
2. Phase 2 — Content Generation: generate SKILL.md and supporting artifacts based on the plan.
3. Phase 3 — Quality Assurance: validate and refine content until it meets quality thresholds.

Each phase has an orchestrator with async and sync entrypoints and integrates with MLflow for observability.

## Cross-phase components

- HITLCheckpointManager — manages human-in-the-loop checkpoints across phases
- ConversationalOrchestrator — state-machine driven multi-turn interaction for chat flows
- SignatureTuningOrchestrator — iterative signature optimization for DSPy programs

## Quick usage (async)

```python
from skill_fleet.workflows import (
    TaskAnalysisOrchestrator,
    ContentGenerationOrchestrator,
    QualityAssuranceOrchestrator,
)

task = TaskAnalysisOrchestrator()
content = ContentGenerationOrchestrator()
qa = QualityAssuranceOrchestrator()

analysis = await task.analyze(task_description="Create a Python decorators skill")
generated = await content.generate(understanding=analysis["understanding"], plan=analysis["plan"], skill_style="comprehensive")
report = await qa.validate_and_refine(skill_content=generated["skill_content"], skill_metadata=analysis["plan"].get("skill_metadata", {}))
```

## When to use the ConversationalOrchestrator

Use the conversational flow when you need a multi-turn, interactive experience (CLI `chat` mode or streaming clients). The conversational orchestrator maps user messages to intent, asks clarifying questions, and can trigger the three-phase flow once the plan is confirmed.

## Implementation pointers

- Orchestrators live under `src/skill_fleet/workflows/` and are designed to be composable with DSPy programs in `src/skill_fleet/core/dspy/`.
- For long-running jobs use the API job endpoints (see `docs/guides/api.md`).

## See also

- Detailed orchestrator reference: `src/skill_fleet/workflows/` (code)
- DSPy modules and optimization: `docs/dspy/`
- HITL: `docs/guides/hitl.md`
