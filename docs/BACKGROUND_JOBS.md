# Background Job Processing for Skill Creation

`★ Insight ─────────────────────────────────────`
**DSPy + Background Jobs Architecture:**
- Skills are created by AI agents via DSPy optimization programs
- These programs run asynchronously as background jobs
- The `jobs` table tracks the entire lifecycle from request to completion
- Human-in-the-Loop (HITL) interactions allow user feedback during execution
`─────────────────────────────────────────────────`

## Overview

The skills-fleet system uses background jobs to handle long-running skill creation workflows. When a user requests a new skill, a job is created that:

1. **Refines the task description** (DSPy enhancement)
2. **Gathers deep understanding** (asks clarifying questions)
3. **Runs TDD workflow** (RED → GREEN → REFACTOR)
4. **Validates the result** (quality checks)
5. **Promotes to production** (moves draft → active)

## Database Schema

### Core Tables

```sql
-- Jobs table: Tracks all background jobs
CREATE TABLE jobs (
    job_id UUID PRIMARY KEY,
    status job_status_enum,          -- pending, running, pending_hitl, completed, failed
    job_type VARCHAR(64),             -- skill_creation, optimization, etc.
    user_id VARCHAR(128),
    task_description TEXT,            -- Original user request
    task_description_refined TEXT,    -- AI-enhanced description
    current_phase VARCHAR(64),        -- Current workflow phase
    progress_message TEXT,
    progress_percent INTEGER,
    result JSONB,                     -- Final result
    error TEXT,
    draft_path TEXT,                  -- Where draft skill is stored
    final_path TEXT,                  -- Where published skill lives
    promoted BOOLEAN DEFAULT FALSE,
    validation_passed BOOLEAN,
    validation_score FLOAT,
    created_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- HITL interactions: Human-in-the-Loop feedback
CREATE TABLE hitl_interactions (
    interaction_id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES jobs(job_id),
    interaction_type hitl_type_enum,  -- clarify, confirm, preview, validate, tdd_*
    prompt_data JSONB,                -- Question presented to user
    response_data JSONB,              -- User's response
    status VARCHAR(32),               -- pending, responded, timeout
    created_at TIMESTAMPTZ
);

-- Deep Understanding State
CREATE TABLE deep_understanding_state (
    state_id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES jobs(job_id),
    questions_asked JSONB,
    answers JSONB,
    research_performed JSONB,
    understanding_summary TEXT,
    user_problem TEXT,
    user_goals TEXT[],
    readiness_score FLOAT,
    complete BOOLEAN
);

-- TDD Workflow State
CREATE TABLE tdd_workflow_state (
    state_id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES jobs(job_id),
    phase VARCHAR(32),                -- red, green, refactor
    baseline_tests_run BOOLEAN,
    compliance_tests_run BOOLEAN,
    rationalizations_identified TEXT[],
    checklist_state JSONB
);
```

## Job Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                     JOB LIFECYCLE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. PENDING                                                     │
│     ├── Job queued, waiting for worker                          │
│     └── user_id, task_description stored                        │
│                                                                  │
│  2. RUNNING                                                     │
│     ├── Worker picks up job                                     │
│     ├── Phase 1: Task Refinement (DSPy)                         │
│     ├── Phase 2: Deep Understanding (HITL)                      │
│     │    └── May transition to PENDING_HITL                     │
│     ├── Phase 3: TDD Workflow                                   │
│     │    ├── RED: Write failing tests                           │
│     │    ├── GREEN: Make tests pass                             │
│     │    └── REFACTOR: Improve code                             │
│     └── Phase 4: Validation                                    │
│                                                                  │
│  3. PENDING_HITL (Human-in-the-Loop)                           │
│     ├── Worker waiting for user input                           │
│     ├── User prompted via API/WebSocket                         │
│     └── On response → RUNNING                                  │
│                                                                  │
│  4. COMPLETED                                                   │
│     ├── All phases finished                                     │
│     ├── result JSONB populated                                  │
│     ├── draft_path set                                          │
│     └── Promoted to skills table (if validated)                │
│                                                                  │
│  5. FAILED                                                      │
│     ├── error TEXT populated                                    │
│     └── error_stack for debugging                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation

### Job Creation

```python
from skill_fleet.db.repositories import JobRepository
from skill_fleet.db.models import job_status_enum
import uuid

def create_skill_job(user_id: str, task_description: str) -> str:
    """Create a new skill creation job."""
    repo = JobRepository(db)

    job = repo.create({
        "user_id": user_id,
        "task_description": task_description,
        "job_type": "skill_creation",
        "status": job_status_enum.pending,
        "intended_taxonomy_path": "development",  # or auto-detected
    })

    # Queue for background processing
    queue_job_for_processing(job.job_id)

    return job.job_id
```

### Job Worker (Background Process)

```python
import time
from sqlalchemy.orm import Session

class SkillJobWorker:
    """Background worker that processes skill creation jobs."""

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)

    def poll_for_jobs(self):
        """Continuously poll for pending jobs."""
        while True:
            with Session(self.engine) as session:
                repo = JobRepository(session)

                # Get next pending job
                job = repo.get_next_pending_job()

                if job:
                    print(f"Processing job: {job.job_id}")
                    self.process_job(job, session)

            time.sleep(1)  # Polling interval

    def process_job(self, job, session):
        """Process a single job through all phases."""
        try:
            # Update status to running
            job = repo.update_status(job.job_id, job_status_enum.running)

            # Phase 1: Task Refinement
            self.phase_refine_task(job, session)

            # Phase 2: Deep Understanding (HITL)
            self.phase_deep_understanding(job, session)

            # Phase 3: TDD Workflow
            self.phase_tdd_workflow(job, session)

            # Phase 4: Validation
            self.phase_validate(job, session)

            # Complete job
            repo.update_status(job.job_id, job_status_enum.completed)

        except Exception as e:
            repo.update_status(
                job.job_id,
                job_status_enum.failed,
                error=str(e)
            )
```

### HITL (Human-in-the-Loop) Flow

```python
def phase_deep_understanding(self, job, session):
    """Gather deep understanding through user interaction."""
    from skill_fleet.db.models import hitl_type_enum

    # Check if we already have understanding
    state = get_deep_understanding_state(job.job_id, session)
    if state and state.complete:
        return  # Skip if already done

    # Ask clarifying questions
    hitl = create_hitl_interaction(
        job_id=job.job_id,
        interaction_type=hitl_type_enum.deep_understanding,
        prompt_data={
            "questions": [
                "What problem are you trying to solve?",
                "What are your success criteria?",
                "Are there any constraints or preferences?"
            ]
        }
    )

    # Update job status to wait for user
    repo.update_status(job.job_id, job_status_enum.pending_hitl)

    # Worker will be notified when user responds
    # Then continue with job...
```

### Polling Endpoint for Frontend

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Poll endpoint for job status."""
    with get_db() as db:
        repo = JobRepository(db)
        job = repo.get(job_id)

        if not job:
            raise HTTPException(404, "Job not found")

        return {
            "job_id": str(job.job_id),
            "status": job.status.value,
            "current_phase": job.current_phase,
            "progress_percent": job.progress_percent,
            "progress_message": job.progress_message,
            "result": job.result,
            "error": job.error,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }

@router.get("/jobs/pending")
async def get_pending_hitl_jobs(user_id: str):
    """Get jobs waiting for human input."""
    with get_db() as db:
        repo = JobRepository(db)
        jobs = repo.get_pending_hitl_jobs(user_id)

        return [{
            "job_id": str(j.job_id),
            "task_description": j.task_description,
            "current_phase": j.current_phase,
        } for j in jobs]
```

## Frontend Integration

### WebSocket for Real-time Updates

```python
from fastapi import WebSocket

@router.websocket("/ws/jobs/{job_id}")
async def job_updates(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job updates."""
    await websocket.accept()

    try:
        while True:
            with get_db() as db:
                repo = JobRepository(db)
                job = repo.get(job_id)

                await websocket.send_json({
                    "status": job.status.value,
                    "phase": job.current_phase,
                    "progress": job.progress_percent,
                    "message": job.progress_message,
                })

                if job.status in [job_status_enum.completed, job_status_enum.failed]:
                    break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
```

## Deployment

### Option 1: Celery (Recommended for Production)

```python
# tasks.py
from celery import Celery

celery_app = Celery('skills_fleet', broker='redis://localhost:6379/0')

@celery_app.task
def process_skill_job(job_id: str):
    """Process a skill creation job."""
    with get_db() as db:
        repo = JobRepository(db)
        job = repo.get(job_id)
        worker = SkillJobWorker(DATABASE_URL)
        worker.process_job(job, db)
```

### Option 2: FastAPI BackgroundTasks (Simple)

```python
from fastapi import BackgroundTasks

@router.post("/skills/create")
async def create_skill(
    task_description: str,
    background_tasks: BackgroundTasks
):
    """Create a new skill via background job."""
    job_id = create_skill_job(user_id="default", task_description=task_description)
    background_tasks.add_task(process_skill_job, job_id)
    return {"job_id": job_id}
```

### Option 3: Dedicated Worker Process

```python
# worker.py (run as separate process)
if __name__ == "__main__":
    worker = SkillJobWorker(DATABASE_URL)
    print("Starting job worker...")
    worker.poll_for_jobs()
```

## Monitoring

```sql
-- View job statistics
SELECT
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_duration_seconds
FROM jobs
GROUP BY status
ORDER BY count DESC;

-- Find stuck jobs (running > 1 hour)
SELECT job_id, current_phase, created_at
FROM jobs
WHERE status = 'running'
AND created_at < NOW() - INTERVAL '1 hour';
```
