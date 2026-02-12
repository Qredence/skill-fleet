# Complete Request Flow Architecture

## Overview

This document traces a complete skill creation request from CLI command through to database persistence.

```
CLI → Client → API → Service → Workflows → DSPy Modules
                              ↓
                         Database (PostgreSQL)
                              ↓
                         Filesystem (Taxonomy)
```

## 1. CLI Command

**Entry:** `src/skill_fleet/cli/main.py`

```bash
uv run skill-fleet create "Create a Python decorators skill"
```

The CLI parses the command and creates an HTTP client to communicate with the API.

## 2. HTTP Client

**Location:** `src/skill_fleet/cli/client.py:15`

The `SkillFleetClient` sends a streaming POST request to `/api/v1/skills/stream`:

```python
async def create_skill_streaming(self, task: str, user_id: str = "default"):
    request_data = {
        "task_description": task,
        "user_id": user_id,
        "enable_hitl": True,
    }

    async with self.client.stream(
        "POST", "/api/v1/skills/stream", json=request_data
    ) as response:
        async for line in response.aiter_lines():
            event = json.loads(line[6:])
            yield event
```

## 3. API Layer

**Location:** `src/skill_fleet/api/routes/skills.py`

The FastAPI route handler:
1. Validates the request schema
2. Creates a job ID
3. Registers an event queue for streaming
4. Starts skill creation as a background task
5. Returns a StreamingResponse

## 4. Service Layer

**Location:** `src/skill_fleet/api/services/skill_service.py:53`

The `SkillService` orchestrates the three-phase workflow:

```python
class SkillService:
    def __init__(self, skills_root: Path, drafts_root: Path):
        self.taxonomy_manager = TaxonomyManager(skills_root)
        self.understanding_workflow = UnderstandingWorkflow()
        self.generation_workflow = GenerationWorkflow()
        self.validation_workflow = ValidationWorkflow()
```

### Phase Execution

```python
async def create_skill(self, request: CreateSkillRequest, ...):
    # Phase 1: Understanding
    phase1_result = await self.understanding_workflow.execute(...)

    # Phase 2: Generation
    phase2_result = await self.generation_workflow.execute(...)

    # Phase 3: Validation
    phase3_result = await self.validation_workflow.execute(...)

    # Save to draft
    result = SkillCreationResult(...)
    await self.save_skill_to_draft(job_id, result)

    return result
```

## 5. Workflow Layer

**Location:** `src/skill_fleet/core/workflows/skill_creation/`

Each phase has its own workflow orchestrator:

### UnderstandingWorkflow

- GatherRequirementsModule
- AnalyzeIntentModule
- FindTaxonomyPathModule
- AnalyzeDependenciesModule
- SynthesizePlanModule

### GenerationWorkflow

- GenerateSkillContentModule
- RefinedContentModule (quality refinement)
- IncorporateFeedbackModule (for HITL)

### ValidationWorkflow

- StructureValidator
- ContentValidator
- QualityAssessor

## 6. DSPy Module Layer

**Location:** `src/skill_fleet/core/modules/`

Modules use DSPy signatures and predictors:

```python
class SynthesizePlan(Signature):
    requirements: dict = InputField()
    intent_analysis: dict = InputField()
    taxonomy_analysis: dict = InputField()

    plan: dict = OutputField()
    confidence_score: float = OutputField()
```

## 7. Database Layer

**Location:** `src/skill_fleet/infrastructure/db/`

### Job Persistence

```python
job_state = JobState(
    job_id=job_id,
    task_description=request.task_description,
    user_id=request.user_id,
    status="running",
)
await job_manager.create_job(job_state)
```

### Skill Persistence

The `SkillRepository` handles saving skills with all relationships:
- Capabilities
- Dependencies
- Keywords/Tags
- Categories

## 8. Filesystem Layer

**Location:** `src/skill_fleet/taxony/`

### Draft Saving

```
skills/_drafts/
└── {job_id}/
    └── {skill-name}/
        ├── SKILL.md          # YAML frontmatter + content
        └── metadata.json     # Extended metadata
```

### Taxonomy Registration

After validation, skills can be promoted from draft to the main taxonomy.

## 9. Event Streaming

**Location:** `src/skill_fleet/core/workflows/streaming.py`

The `StreamingWorkflowManager` emits events during workflow execution:

```python
async def emit(self, event_type: WorkflowEventType, message: str, data: dict = None):
    event = WorkflowEvent(
        event_type=event_type,
        phase=self.current_phase,
        message=message,
        data=data or {},
    )
    await self.event_queue.put(event)
```

**Event Types:**
- `PHASE_START` / `PHASE_END`
- `PROGRESS`
- `REASONING`
- `HITL_REQUIRED`
- `COMPLETED`

## Complete Data Flow Summary

| Stage | Component | Action |
|-------|-----------|--------|
| 1 | CLI | Parse command, create HTTP client |
| 2 | Client | Send POST /api/v1/skills/stream |
| 3 | API | Authenticate, validate request, create job |
| 4 | Service | Initialize workflows, start MLflow run |
| 5 | Workflow | Execute Phase 1 (Understanding) |
| 6 | DSPy Module | LLM calls for analysis |
| 7 | DB | Persist job state, HITL interactions |
| 8 | Service | Execute Phase 2 (Generation) |
| 9 | DSPy Module | Generate SKILL.md content |
| 10 | Service | Execute Phase 3 (Validation) |
| 11 | Filesystem | Save to drafts directory |
| 12 | DB | Update job with result, draft path |
| 13 | API | Stream completion event |
| 14 | Client | Display result to user |

## Related Documentation

- `docs/explanation/dual-metadata-model.md`
- `docs/explanation/three-phase-workflow.md`
- `docs/explanation/database-relationships.md`
- `docs/explanation/taxonomy-system.md`
- `docs/explanation/validation-architecture.md`

## References

- `src/skill_fleet/cli/main.py`
- `src/skill_fleet/cli/client.py`
- `src/skill_fleet/api/routes/skills.py`
- `src/skill_fleet/api/services/skill_service.py`
- `src/skill_fleet/core/workflows/`
- `src/skill_fleet/infrastructure/db/`
- `src/skill_fleet/taxonomy/manager.py`
