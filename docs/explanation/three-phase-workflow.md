# Three-Phase Workflow Architecture

## Overview

Skill creation follows a **three-phase workflow** that mirrors human skill development: understanding requirements, generating content, and validating quality. Each phase is orchestrated by a dedicated workflow class and can suspend for Human-in-the-Loop (HITL) interactions.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Phase 1       │────▶│   Phase 2       │────▶│   Phase 3       │
│ Understanding   │     │ Generation      │     │ Validation      │
│                 │     │                 │     │                 │
│ • Requirements  │     │ • SKILL.md      │     │ • Compliance    │
│ • Intent        │     │ • Examples      │     │ • Quality       │
│ • Taxonomy      │     │ • Best practices│     │ • Refinement    │
│ • Dependencies  │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   [HITL: clarify]        [HITL: preview]        [HITL: review]
```

## Phase 1: Understanding

**Orchestrator:** `UnderstandingWorkflow` (`core/workflows/skill_creation/understanding.py`)

**Purpose:** Analyze user requirements, determine skill taxonomy placement, identify dependencies, and synthesize a comprehensive plan.

### Step-by-Step Execution

1. **Gather Requirements** (blocking)
   - Module: `GatherRequirementsModule`
   - Extracts: domain, topics, target_level, constraints, trigger_phrases
   - Identifies ambiguities that need clarification

2. **Validate Structure** (early validation)
   - Module: `ValidateStructureModule`
   - Catches naming/description errors before expensive operations
   - Can suspend for `structure_fix` HITL

3. **Analyze Intent, Taxonomy, Dependencies** (parallel)
   - `AnalyzeIntentModule` - purpose, target_audience, value_proposition
   - `FindTaxonomyPathModule` - recommended_path, parent_skills
   - `AnalyzeDependenciesModule` - required/recommended skills

4. **Synthesize Plan**
   - Module: `SynthesizePlanModule`
   - Creates: `SkillMetadata`, capabilities list, resource requirements

### HITL Checkpoints

| Checkpoint | Type | Triggers | Resume Action |
|------------|------|----------|---------------|
| `clarify` | `pending_user_input` | Significant ambiguities detected | Re-run Phase 1 with answers |
| `structure_fix` | `pending_user_input` | Invalid skill name or description | Fix and re-validate |
| `confirm` | `pending_hitl` | `enable_hitl_confirm=True` | Proceed to Phase 2 or revise |

### Output

```python
{
    "status": "completed",
    "requirements": {...},
    "intent": {...},
    "taxonomy": {...},
    "dependencies": {...},
    "plan": {
        "skill_metadata": SkillMetadata,
        "taxonomy_path": str,
        "capabilities": [...],
        "resource_requirements": {...}
    }
}
```

## Phase 2: Generation

**Orchestrator:** `GenerationWorkflow` (`core/workflows/skill_creation/generation.py`)

**Purpose:** Generate complete skill content (SKILL.md) based on the plan from Phase 1, with optional refinement and preview.

### Step-by-Step Execution

1. **Generate Content**
   - Module: `GenerateSkillContentModule`
   - Creates: Full SKILL.md with YAML frontmatter
   - Supports token streaming for real-time UI updates

2. **Refine Content** (optional)
   - Module: `RefinedContentModule`
   - Iterative improvement with quality reward function
   - Target quality threshold (default: 0.75)

3. **Prepare Preview** (optional)
   - Extracts highlights from generated content
   - Can suspend for user feedback

### HITL Checkpoints

| Checkpoint | Type | Triggers | Resume Action |
|------------|------|----------|---------------|
| `preview` | `pending_hitl` | `enable_hitl_preview=True` | Accept, refine, or cancel |

### Output

```python
{
    "status": "completed",
    "skill_content": str,           # Full SKILL.md content
    "sections_generated": [...],
    "code_examples_count": int,
    "estimated_reading_time": int
}
```

## Phase 3: Validation

**Orchestrator:** `ValidationWorkflow` (`core/workflows/skill_creation/validation.py`)

**Purpose:** Validate skill compliance with agentskills.io specification, assess quality, and suggest refinements.

### Validation Layers

1. **Structure Validation**
   - Check required files (SKILL.md)
   - Validate subdirectory structure
   - Check naming conventions

2. **Content Validation**
   - Required sections ("When to Use")
   - YAML frontmatter compliance
   - Code block presence

3. **Quality Assessment**
   - Word count analysis
   - Verbosity scoring
   - Trigger phrase coverage

4. **LLM-Based Validation** (optional)
   - Semantic quality evaluation
   - agentskills.io compliance check

### HITL Checkpoints

| Checkpoint | Type | Triggers | Resume Action |
|------------|------|----------|---------------|
| `validate` | `pending_hitl` | `enable_hitl_review=True` | Accept, refine, or cancel |

### Output

```python
{
    "status": "completed",
    "validation_report": ValidationReport,
    "quality_assessment": {
        "overall_score": float,
        "completeness": float,
        "compliance": float,
        "word_count": int,
        "size_assessment": str
    }
}
```

## Workflow Orchestration

### Service Layer Integration

The `SkillService` (`api/services/skill_service.py`) orchestrates all three phases:

```python
class SkillService:
    def __init__(self, skills_root: Path, drafts_root: Path):
        self.understanding_workflow = UnderstandingWorkflow()
        self.generation_workflow = GenerationWorkflow()
        self.validation_workflow = ValidationWorkflow()

    async def create_skill(self, request: CreateSkillRequest) -> SkillCreationResult:
        # Phase 1: Understanding (with potential HITL)
        phase1_result = await self.understanding_workflow.execute(...)

        # Phase 2: Generation (with potential HITL)
        phase2_result = await self.generation_workflow.execute(...)

        # Phase 3: Validation (with potential HITL)
        phase3_result = await self.validation_workflow.execute(...)

        return SkillCreationResult(...)
```

### Streaming Architecture

Each workflow supports streaming for real-time UI updates:

```python
async for event in workflow.execute_streaming(...):
    if event.event_type == WorkflowEventType.PROGRESS:
        print(f"Progress: {event.message}")
    elif event.event_type == WorkflowEventType.HITL_REQUIRED:
        # Handle HITL interaction
        pass
```

**Event Types:**
- `PHASE_START` / `PHASE_END` - Workflow phase transitions
- `PROGRESS` - Progress updates with messages
- `REASONING` - AI reasoning/thoughts
- `MODULE_START` / `MODULE_END` - Module execution
- `HITL_REQUIRED` - Suspension for human input
- `COMPLETED` / `ERROR` - Final states

## HITL (Human-in-the-Loop) System

### Suspension Points

Workflows can suspend at predefined checkpoints:

```python
await manager.suspend_for_hitl(
    hitl_type="clarify",
    data={"questions": [...]},
    context={"requirements": {...}}
)
```

### Resume Flow

1. Workflow suspends → Job state updated to `pending_hitl`
2. Client polls or receives SSE event
3. User provides response via API
4. Workflow resumes with updated context
5. May re-run phase or continue to next

### HITL Types

| Type | Phase | Purpose |
|------|-------|---------|
| `clarify` | Phase 1 | Answer clarifying questions |
| `structure_fix` | Phase 1 | Fix skill name/description |
| `confirm` | Phase 1 | Confirm plan before generation |
| `preview` | Phase 2 | Review generated content |
| `validate` | Phase 3 | Review validation results |

## MLflow Integration

Hierarchical tracking structure:

```
Parent Run (skill creation job)
├── Child Run: phase1_task_analysis
├── Child Run: phase2_content_generation
└── Child Run: phase3_quality_assurance
```

**Tracked Artifacts:**
- Complete skill content
- Validation reports
- Quality metrics
- User feedback

## Error Handling

### Phase Recovery

```python
# Phase 1 errors: Can retry with adjusted context
if phase1_result["status"] == "failed":
    return SkillCreationResult(status="failed", error=...)

# Phase 2 errors: Can regenerate from plan
if phase2_result["status"] == "failed":
    # Retry generation
    pass

# Phase 3 errors: Can refine content
if not validation_report.passed:
    # Loop back to Phase 2 with feedback
    pass
```

### HITL Cancellation

Users can cancel at any HITL checkpoint:

```python
if action == "cancel":
    return SkillCreationResult(
        job_id=job_id,
        status="cancelled",
        message="Cancelled by user"
    )
```

## Module Architecture

Each workflow uses specialized DSPy modules:

### Phase 1 Modules

| Module | Signature | Purpose |
|--------|-----------|---------|
| `GatherRequirementsModule` | `GatherRequirements` | Extract structured requirements |
| `AnalyzeIntentModule` | `AnalyzeSkillRequirements` | Understand user intent |
| `FindTaxonomyPathModule` | `SkillUnderstanding` | Determine taxonomy placement |
| `AnalyzeDependenciesModule` | `DependencyAnalysis` | Identify skill dependencies |
| `SynthesizePlanModule` | `SkillPlan` | Create complete plan |

### Phase 2 Modules

| Module | Signature | Purpose |
|--------|-----------|---------|
| `GenerateSkillContentModule` | `GenerateSkillContent` | Generate SKILL.md |
| `RefinedContentModule` | `RefinedContent` | Iterative quality improvement |
| `IncorporateFeedbackModule` | `IncorporateFeedback` | Apply user feedback |

### Phase 3 Modules

| Module | Signature | Purpose |
|--------|-----------|---------|
| `ValidateSkillModule` | `ValidateSkillStructure` | Validate compliance |
| `QualityAssessmentModule` | `QualityAssessment` | Score skill quality |

## Related Components

- `SkillService` - Orchestrates all three phases
- `StreamingWorkflowManager` - Manages streaming events
- `JobManager` - Persists workflow state
- `HITLInteraction` - Database model for HITL tracking

## References

- `src/skill_fleet/core/workflows/skill_creation/understanding.py`
- `src/skill_fleet/core/workflows/skill_creation/generation.py`
- `src/skill_fleet/core/workflows/skill_creation/validation.py`
- `src/skill_fleet/api/services/skill_service.py`
- `src/skill_fleet/core/workflows/streaming.py`
