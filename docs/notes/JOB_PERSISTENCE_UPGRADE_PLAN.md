# Job Persistence Architecture Upgrade

## Status
**Phase**: Design Complete  
**Date**: Jan 20, 2026  
**Priority**: CRITICAL (Production Readiness)  

---

## Problem Statement

### Current Architecture (In-Memory Only)
```python
# api/jobs.py
JOBS: dict[str, JobState] = {}  # Lost on server restart!
SESSION_DIR = Path(".skill_fleet_sessions")  # Manual, fragile JSON persistence
```

**Risks**:
1. ✗ Server restart = all job state lost
2. ✗ Multi-instance deployment = no state sharing
3. ✗ HITL events (`asyncio.Event`) not serializable
4. ✗ Race conditions when save/reload timing is off
5. ✗ No transactional guarantees
6. ✗ Cannot query job history across restarts

### Why Option B (DB-Backed)?
- ✅ Fault-tolerant (survives restarts)
- ✅ Multi-instance ready (shared Postgres)
- ✅ Transactional integrity
- ✅ Query capabilities (analytics, auditing)
- ✅ Leverage existing schema (Job + HITLInteraction tables exist!)
- ✅ Repository pattern already in place

---

## Architecture Design

### Dual-Layer Strategy (Hybrid)

```
┌─────────────────────────────────────┐
│   API Request Handler               │
│   (api/routes/jobs.py)              │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   JobManager (NEW)                  │
│   - Facade over both layers         │
│   - Route to memory or DB            │
│   - Handle HITL event lifecycle     │
└────────────┬────────────────────────┘
             │
        ┌────┴─────┐
        │           │
        ▼           ▼
    ┌────────┐  ┌──────────┐
    │ Memory │  │  Database│
    │ Store  │  │ Repository
    │ (hot)  │  │ (source)
    └────────┘  └──────────┘
        │           │
        └─────┬─────┘
              ▼
        ┌──────────────┐
        │ Job Lifecycle│
        │ (Created,    │
        │  In-Flight,  │
        │  Completed)  │
        └──────────────┘
```

### Layer 1: Memory Store (Hot Cache)
- **Scope**: Current jobs in-flight (created < 1 hour ago)
- **Why**: Avoid DB round-trip for every HITL interaction
- **Implementation**: `JobMemoryStore` (existing `JOBS` dict, refactored)
- **TTL**: 1 hour, auto-eviction to DB

### Layer 2: Database Store (Source of Truth)
- **Scope**: All job metadata + history
- **Why**: Persistence, multi-instance, auditability
- **Implementation**: `JobRepository` (use `JobRepository` already in repos.py)
- **Tables**:
  - `Job` - Main job record (exists!)
  - `HITLInteraction` - HITL prompts/responses (exists!)
  - `DeepUnderstandingState` - Phase 1 tracking (exists!)
  - `TDDWorkflowState` - Phase 3 tracking (exists!)

---

## Implementation Plan

### Phase 1: New JobManager Facade (30 mins)

**File**: `src/skill_fleet/api/job_manager.py` (NEW)

```python
from datetime import datetime, UTC, timedelta
from typing import Optional, Any
from uuid import UUID
import logging

from ..db.database import get_db
from ..db.repositories import JobRepository
from .schemas import JobState

logger = logging.getLogger(__name__)

class JobMemoryStore:
    """Hot cache for in-flight jobs (created < 1 hour ago)."""
    
    def __init__(self, ttl_minutes: int = 60):
        self.ttl_minutes = ttl_minutes
        self.store: dict[str, tuple[JobState, datetime]] = {}
    
    def set(self, job_id: str, job: JobState) -> None:
        """Store job in memory with timestamp."""
        self.store[job_id] = (job, datetime.now(UTC))
    
    def get(self, job_id: str) -> Optional[JobState]:
        """Get job from memory if not expired."""
        if job_id not in self.store:
            return None
        
        job, created_at = self.store[job_id]
        age = datetime.now(UTC) - created_at
        
        if age > timedelta(minutes=self.ttl_minutes):
            # Expired: remove from memory
            del self.store[job_id]
            return None
        
        return job
    
    def delete(self, job_id: str) -> bool:
        """Remove job from memory."""
        if job_id in self.store:
            del self.store[job_id]
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """Remove expired entries. Call periodically."""
        expired_ids = [
            job_id for job_id, (_, created_at) in self.store.items()
            if datetime.now(UTC) - created_at > timedelta(minutes=self.ttl_minutes)
        ]
        for job_id in expired_ids:
            del self.store[job_id]
        return len(expired_ids)


class JobManager:
    """Manage job lifecycle across memory and database layers."""
    
    def __init__(self, memory_store: Optional[JobMemoryStore] = None):
        self.memory = memory_store or JobMemoryStore(ttl_minutes=60)
        self.db_repo: Optional[JobRepository] = None
    
    def set_db_repo(self, db_repo: JobRepository) -> None:
        """Set database repository (called at API startup)."""
        self.db_repo = db_repo
    
    def get_job(self, job_id: str) -> Optional[JobState]:
        """Retrieve job from memory (fast), fall back to DB (durable)."""
        # Try memory first (hot cache)
        job = self.memory.get(job_id)
        if job:
            logger.debug(f"Job {job_id} found in memory cache")
            return job
        
        # Fall back to database
        if self.db_repo:
            db_job = self.db_repo.get_by_id(job_id)
            if db_job:
                # Reconstruct JobState from DB model
                job_state = self._db_to_memory(db_job)
                # Warm the memory cache for future access
                self.memory.set(job_id, job_state)
                logger.info(f"Job {job_id} loaded from database")
                return job_state
        
        logger.warning(f"Job {job_id} not found in memory or database")
        return None
    
    def create_job(self, job_state: JobState) -> None:
        """Create a new job (memory + DB)."""
        # Store in memory immediately
        self.memory.set(job_state.job_id, job_state)
        
        # Persist to DB asynchronously
        if self.db_repo:
            self._save_to_db(job_state)
            logger.info(f"Job {job_state.job_id} created (memory + DB)")
    
    def update_job(self, job_id: str, updates: dict[str, Any]) -> Optional[JobState]:
        """Update job in both layers."""
        # Update memory (fast path for in-flight updates)
        job = self.memory.get(job_id)
        if not job:
            job = self.get_job(job_id)  # Try DB fallback
        
        if not job:
            logger.error(f"Cannot update: job {job_id} not found")
            return None
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(job, key):
                setattr(job, key, value)
        
        # Update both layers
        self.memory.set(job_id, job)
        if self.db_repo:
            self._save_to_db(job)
        
        logger.debug(f"Job {job_id} updated")
        return job
    
    def save_job(self, job: JobState) -> bool:
        """Explicit save to DB (for completed/important jobs)."""
        self.memory.set(job.job_id, job)
        
        if self.db_repo:
            try:
                self._save_to_db(job)
                logger.info(f"Job {job.job_id} saved to database")
                return True
            except Exception as e:
                logger.error(f"Failed to save job {job.job_id}: {e}")
                return False
        
        return True
    
    def _save_to_db(self, job: JobState) -> None:
        """Internal: Save JobState to database."""
        if not self.db_repo:
            return
        
        # Serialize nested objects
        deep_understanding = None
        tdd_workflow = None
        hitl_interactions = []
        
        if job.deep_understanding:
            deep_understanding = job.deep_understanding.model_dump()
        
        if job.tdd_workflow:
            tdd_workflow = job.tdd_workflow.model_dump()
        
        # Note: HITL interactions should be stored separately
        # See Phase 2 for implementation
        
        job_data = {
            'job_id': UUID(job.job_id),
            'status': job.status,
            'result': job.result,
            'error': job.error,
            'progress_percent': job.progress_percent,
            'updated_at': job.updated_at,
            'deep_understanding': deep_understanding,
            'tdd_workflow': tdd_workflow,
        }
        
        # Upsert to database
        existing = self.db_repo.get_by_id(job.job_id)
        if existing:
            self.db_repo.update(db_obj=existing, obj_in=job_data)
        else:
            self.db_repo.create(obj_in=job_data)
    
    def _db_to_memory(self, db_job: Any) -> JobState:
        """Internal: Reconstruct JobState from database model."""
        # Implementation in Phase 2
        # For now: schema compatibility layer
        job_state = JobState(job_id=str(db_job.job_id))
        job_state.status = db_job.status
        job_state.result = db_job.result
        job_state.error = db_job.error
        job_state.progress_percent = db_job.progress_percent or 0
        job_state.updated_at = db_job.updated_at or datetime.now(UTC)
        return job_state
    
    def cleanup_expired(self) -> int:
        """Clean up expired memory entries (call from background task)."""
        return self.memory.cleanup_expired()


# Global instance
_job_manager: Optional[JobManager] = None

def get_job_manager() -> JobManager:
    """Get the global job manager."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager

def initialize_job_manager(db_repo: JobRepository) -> JobManager:
    """Initialize job manager with database repo (call at API startup)."""
    global _job_manager
    _job_manager = JobManager()
    _job_manager.set_db_repo(db_repo)
    logger.info("JobManager initialized with database persistence")
    return _job_manager
```

### Phase 2: Update API Routes (45 mins)

**File**: `src/skill_fleet/api/routes/jobs.py` (MODIFY)

```python
# OLD
def create_job() -> str:
    job_id = str(uuid.uuid4())
    JOBS[job_id] = JobState(job_id=job_id)
    return job_id

# NEW
def create_job() -> str:
    from .job_manager import get_job_manager
    
    job_id = str(uuid.uuid4())
    job_state = JobState(job_id=job_id)
    
    manager = get_job_manager()
    manager.create_job(job_state)  # Saves to memory + DB
    return job_id


# OLD
def get_job(job_id: str) -> JobState | None:
    job = JOBS.get(job_id)
    if job:
        return job
    return load_job_session(job_id)  # Fragile JSON loading

# NEW
def get_job(job_id: str) -> JobState | None:
    from .job_manager import get_job_manager
    
    manager = get_job_manager()
    return manager.get_job(job_id)  # Memory + DB fallback


# OLD
def notify_hitl_response(job_id: str, response: dict[str, Any]) -> None:
    job = JOBS.get(job_id)
    if job is None:
        return
    job.hitl_response = response
    job.hitl_event.set()

# NEW
def notify_hitl_response(job_id: str, response: dict[str, Any]) -> None:
    from .job_manager import get_job_manager
    
    manager = get_job_manager()
    job = manager.get_job(job_id)
    
    if job is None:
        logger.error(f"Cannot notify: job {job_id} not found")
        return
    
    job.hitl_response = response
    if job.hitl_event is None:
        job.hitl_event = asyncio.Event()
    
    job.hitl_event.set()
    manager.update_job(job_id, {"hitl_response": response})  # Persist
```

### Phase 3: Background Cleanup Task (15 mins)

**File**: `src/skill_fleet/api/lifespan.py` (NEW)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan events (startup/shutdown)."""
    
    # STARTUP
    from .job_manager import initialize_job_manager
    from ..db.database import get_db_context
    from ..db.repositories import JobRepository
    
    with get_db_context() as db:
        job_repo = JobRepository(db)
        initialize_job_manager(job_repo)
    
    # Start cleanup background task
    cleanup_task = asyncio.create_task(cleanup_expired_jobs())
    logger.info("JobManager and cleanup task started")
    
    yield  # App runs here
    
    # SHUTDOWN
    cleanup_task.cancel()
    logger.info("Cleanup task stopped")


async def cleanup_expired_jobs():
    """Periodically clean up expired in-memory jobs."""
    from .job_manager import get_job_manager
    
    while True:
        try:
            await asyncio.sleep(300)  # Every 5 minutes
            
            manager = get_job_manager()
            cleaned = manager.cleanup_expired()
            
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired jobs from memory")
        
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
```

### Phase 4: Update API App (10 mins)

**File**: `src/skill_fleet/api/app.py` (MODIFY)

```python
# OLD
from fastapi import FastAPI

app = FastAPI()

# NEW
from contextlib import asynccontextmanager
from .lifespan import lifespan

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    async with lifespan(app) as _:
        yield

app = FastAPI(lifespan=app_lifespan)
```

---

## Schema Integration

### Existing Tables (Already in Place!)

**`Job` table** (db/models.py:839-913)
```sql
CREATE TABLE jobs (
    job_id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    job_type VARCHAR(64),
    status VARCHAR(32) NOT NULL,  -- pending, running, pending_hitl, completed, failed
    result JSONB,
    error TEXT,
    progress_percent INTEGER,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    promoted BOOLEAN DEFAULT false,
    ...
);
```

**`HITLInteraction` table** (db/models.py:916-957)
```sql
CREATE TABLE hitl_interactions (
    interaction_id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES jobs(job_id) ON DELETE CASCADE,
    interaction_type VARCHAR(32),  -- clarify, confirm, preview, validate, ...
    round_number INTEGER,
    prompt_data JSONB,  -- Serialized ClarifyingQuestion
    response_data JSONB,  -- Serialized QuestionAnswer
    responded_at TIMESTAMPTZ,
    status VARCHAR(32),  -- pending, answered
    created_at TIMESTAMPTZ,
    timeout_at TIMESTAMPTZ,
    metadata JSONB,
    ...
);
```

**`DeepUnderstandingState` table** (db/models.py:960-991)
```sql
CREATE TABLE deep_understanding_state (
    state_id SERIAL PRIMARY KEY,
    job_id UUID UNIQUE REFERENCES jobs(job_id) ON DELETE CASCADE,
    questions_asked JSONB[],
    answers JSONB[],
    research_performed JSONB[],
    understanding_summary TEXT,
    user_problem TEXT,
    readiness_score FLOAT,
    complete BOOLEAN,
    ...
);
```

### No Migration Needed! ✅
The schema already supports everything we need. We're just:
- Populating existing tables consistently
- Using repositories instead of in-memory dicts
- Adding cleanup/lifecycle management

---

## Migration Strategy

### Step 1: Deploy JobManager (Non-Breaking)
- Add JobManager code
- Keep both memory + DB working in parallel
- Write to both layers
- Read from memory first, DB as fallback
- **No breaking changes**: existing code still works

### Step 2: Monitor & Validate
- Run in production with dual-layer writes
- Verify DB persistence works
- Check for race conditions
- Confirm HITL event handling

### Step 3: Cleanup Phase-Out (Future)
- Remove direct JOBS dict usage
- Remove JSON session files (.skill_fleet_sessions)
- Retire SESSION_DIR code
- Move entirely to DB-backed approach

---

## Testing Strategy

### Unit Tests (30 mins)
```python
# tests/api/test_job_manager.py

def test_job_memory_store():
    """Test memory store creation, retrieval, TTL."""
    store = JobMemoryStore(ttl_minutes=1)
    job = JobState(job_id="test-1")
    
    store.set("test-1", job)
    assert store.get("test-1") == job
    
    # Wait for expiry
    time.sleep(61)
    assert store.get("test-1") is None  # Expired


def test_job_manager_memory_first():
    """Test that manager returns memory before DB."""
    manager = JobManager()
    job = JobState(job_id="test-2")
    
    manager.memory.set("test-2", job)
    assert manager.get_job("test-2") == job  # From memory


def test_job_manager_db_fallback():
    """Test that manager falls back to DB when memory miss."""
    manager = JobManager()
    # Simulate job in DB only
    # Create mock DB repo
    # Verify manager reconstructs JobState correctly


def test_hitl_response_persistence():
    """Test that HITL responses are persisted to DB."""
    manager = JobManager()
    job = JobState(job_id="test-3")
    manager.create_job(job)
    
    # Simulate HITL response
    response = {"answer": "yes", "confidence": 0.9}
    manager.update_job("test-3", {"hitl_response": response})
    
    # Verify saved to DB
    assert manager.db_repo.get_by_id("test-3").result["hitl_response"] == response
```

### Integration Tests (30 mins)
```python
# tests/api/test_job_persistence_e2e.py

@pytest.mark.integration
async def test_job_survives_server_restart():
    """Test that job state survives in-memory server restart."""
    async with AsyncClient(app=app) as client:
        # Create job
        response = await client.post("/api/v1/jobs")
        job_id = response.json()["job_id"]
        
        # Update job
        await client.patch(f"/api/v1/jobs/{job_id}", json={
            "progress_percent": 50
        })
        
        # "Restart" server (clear memory, reload from DB)
        manager = get_job_manager()
        manager.memory.store.clear()
        
        # Verify job restored from DB
        job = manager.get_job(job_id)
        assert job.progress_percent == 50  # From DB


@pytest.mark.integration
async def test_multi_instance_job_access():
    """Test that multiple instances can access same job."""
    manager1 = JobManager()
    manager2 = JobManager()
    
    # Both share same DB repo
    db_repo = JobRepository(db)
    manager1.set_db_repo(db_repo)
    manager2.set_db_repo(db_repo)
    
    # Create job in manager1
    job = JobState(job_id="shared-1")
    manager1.create_job(job)
    
    # Access from manager2
    job2 = manager2.get_job("shared-1")
    assert job2 is not None
    assert job2.job_id == "shared-1"
```

---

## Rollout Plan

### Week 1: Deploy JobManager
- [ ] Create JobManager (Phase 1)
- [ ] Update API routes (Phase 2)
- [ ] Add lifespan management (Phase 3)
- [ ] Deploy to staging
- [ ] Run unit tests

### Week 2: Validate in Production
- [ ] Monitor job persistence
- [ ] Check HITL response handling
- [ ] Verify cleanup task
- [ ] A/B test with 10% of users

### Week 3: Full Rollout
- [ ] Increase to 100% of users
- [ ] Deprecate JSON session files
- [ ] Plan for future DB-only mode

---

## Benefits

### Immediate (After Phase 1-2)
- ✅ Jobs survive server restarts
- ✅ Multi-instance deployments work
- ✅ HITL responses persist reliably
- ✅ Full backward compatibility

### Medium-term (After Phase 3)
- ✅ Automatic cleanup of expired jobs
- ✅ Better memory utilization
- ✅ Foundation for analytics/auditing
- ✅ No more "session lost" issues

### Long-term (After Phase 4)
- ✅ Fully DB-backed, no in-memory state
- ✅ Horizontal scaling
- ✅ Better observability
- ✅ Complete job history preserved

---

## Estimated Effort

| Phase | Task | Effort | Risk |
|-------|------|--------|------|
| 1 | JobManager facade | 30m | Low |
| 2 | API route updates | 45m | Low |
| 3 | Background cleanup | 15m | Low |
| 4 | App lifespan setup | 10m | Low |
| - | Unit testing | 30m | Low |
| - | Integration testing | 30m | Medium |
| **Total** | - | **3-4h** | **Low** |

---

## Next Steps

Ready to implement Phase 1? Should I:
- [ ] **Create JobManager** (job_manager.py)
- [ ] **Update routes** (jobs.py modifications)
- [ ] **Both** (full implementation + testing)

Which would you prefer?
