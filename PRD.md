# PRD: Comprehensive Code Review Fixes for Skill Fleet

## What is the API Workflows Process?

The Skill Fleet API follows a synchronous async workflow pattern where skill creation runs within the API/CLI request lifecycle. The "Job" abstraction is used for state tracking during execution, not for background processing:

### Core Workflow Flow

1. **Request Initiation** (`POST /api/v1/skills/` or CLI command)
   - Client submits task description
   - `SkillService.create_skill()` creates a `JobState` with unique `job_id`
   - **Workflow executes synchronously** - the request/CLI waits for completion
   - Job state is persisted to memory + database for durability and progress tracking

2. **Synchronous Execution** (Within Request/CLI Lifecycle)
   - Workflow runs through phases: Understanding → Generation → Validation
   - Each phase can trigger HITL checkpoints (clarifying questions)
   - For HITL: workflow pauses, prompts user, waits for response, then resumes
   - Streaming events emitted via `StreamingWorkflowManager` for real-time feedback
   - **The request/CLI remains active** until skill creation completes or errors

3. **State Management** (Dual-Layer Persistence)
   - **Memory Layer**: `JobMemoryStore` provides fast access during active execution
   - **Database Layer**: PostgreSQL via SQLAlchemy for durability across HITL pauses
   - `JobManager` persists state at checkpoints for recovery
   - Jobs are short-lived (minutes, not hours) - duration of skill creation

4. **HITL Integration** (Within Same Session)
   - When clarification needed, workflow pauses and prompts user
   - For API: client receives SSE events with HITL prompts
   - For CLI: interactive prompts in terminal
   - User responds within the same request/CLI session
   - Workflow resumes immediately after response

5. **Completion** (Request Returns)
   - Final result returned to client: skill path, validation score, content
   - Job state cleaned up from memory (kept in DB for history)
   - Request/CLI command completes

### Critical Concurrency Points

While individual workflow executions are single-threaded within a request, **shared services are accessed concurrently** by multiple simultaneous requests:
- **JobMemoryStore**: Multiple concurrent API requests access/modify job states
- **EventQueueRegistry**: SSE streams register/unregister from different requests
- **TaxonomyManager**: Skill metadata cache updated during concurrent registrations
- **Workflow Managers**: Phase transition events emitted to shared queues

### Current Architecture Issues

The existing implementation has **7 critical race conditions** in shared services:
1. Job lookup falls back to DB without proper locking (TOCTOU)
2. In-memory cache uses plain dict without locks
3. Event registry read operations bypass locks
4. Taxonomy metadata cache mutated concurrently
5. Wrong lock type (threading.RLock in async context)
6. Workflow phase transitions not synchronized
7. Lazy initialization of DSPy refiners racy

These issues can cause:
- Duplicate job entries when multiple requests arrive simultaneously
- State corruption when concurrent requests modify shared caches
- Lost HITL responses in high-concurrency scenarios
- Inconsistent validation results
- Event delivery failures

---

## Overview

This PRD documents the comprehensive fixes required to address 47 code quality issues identified in the Skill Fleet codebase. The issues span concurrency safety, code duplication, complexity reduction, and utility modernization.

**Scope**: All fixes in `src/skill_fleet/` directory
**Priority**: Critical concurrency fixes must be deployed before production
**Impact**: ~40 files modified, ~500 lines changed
**Estimated Effort**: 4-6 hours implementation + 2 hours testing

---

## Goals

### Primary Goals

1. **Eliminate Critical Race Conditions** (7 issues)
   - Fix all shared-state mutation points in async context
   - Ensure thread-safe access to JobMemoryStore, EventQueueRegistry, TaxonomyManager
   - Replace threading.RLock with asyncio.Lock
   - Add proper synchronization for lazy initialization

2. **Centralize Duplicate Code** (3 major patterns)
   - Extract `_sanitize_for_log()` to shared utility (4 implementations → 1)
   - Create `@with_llm_fallback` decorator (7+ occurrences → 1)
   - Create `@timed_execution` decorator (20 occurrences → 1)

3. **Reduce Code Complexity** (3 functions)
   - Break up ValidationWorkflow._execute_workflow (230 lines)
   - Break up UnderstandingWorkflow._execute_workflow (155 lines)
   - Break up SkillService.create_skill (233 lines)

4. **Modernize Utilities** (3 opportunities)
   - Replace custom InMemoryCache with cachetools.TTLCache
   - Replace custom run_async() with anyio.run()
   - Replace serialize_pydantic_object() with Pydantic v2 native

5. **Improve Architecture** (2 structural changes)
   - Create BaseWorkflow class for common workflow patterns
   - Extend BaseModule with validate_with_defaults() helper

### Secondary Goals

6. **Improve Testability**
   - Add concurrency stress tests
   - Make methods async where appropriate for better testability
   - Reduce coupling through dependency injection

7. **Maintain Backward Compatibility**
   - Where possible, preserve existing APIs
   - Update callers to use new async signatures
   - Provide migration path for deprecated utilities

---

## Non-Goals

### Out of Scope

1. **Feature Changes**: No new features or behavior changes - only refactoring
2. **Database Schema**: No database migrations or schema changes
3. **API Contracts**: Public API endpoints remain unchanged
4. **Performance Optimization**: Not focusing on performance gains (though concurrency fixes may improve stability under load)
5. **Major Rewrites**: Keeping changes surgical and focused
6. **Documentation**: API documentation updates are follow-up work

### Explicitly Excluded

- Refactoring CLI UI code (rich text formatting, prompts)
- Changing DSPy signature definitions beyond adding reasoning fields
- Adding new validation rules or quality criteria
- Migrating from Pydantic v1 to v2 (only using existing v2 features)
- Changing error message text or logging formats
- Modifying MLflow integration logic

---

## Technical Requirements

### Phase 1: Critical Concurrency Fixes

#### 1.1 JobManager.get_job() Race Condition
**File**: `src/skill_fleet/api/services/job_manager.py`

```python
# Current (Race Condition):
def get_job(self, job_id: str) -> JobState | None:
    job = self.memory.get(job_id)  # Check
    if job:
        return job
    # ... DB fetch ...
    if not self.memory.get(job_id):  # Second check - TOCTOU gap!
        self.memory.set(job_id, job_state)

# Required:
# - Add _lock = asyncio.Lock()
# - Make method async
# - Wrap check-then-act with lock
```

**Requirements**:
- Add `asyncio.Lock` to `JobManager`
- Convert `get_job()` from sync to async
- Update all callers to use `await`
- Ensure lock is acquired before second check

#### 1.2 JobMemoryStore Synchronization
**File**: `src/skill_fleet/api/services/job_manager.py`

**Requirements**:
- Convert `JobMemoryStore` methods from sync to async
- Add `asyncio.Lock()` instance variable
- Protect all dict operations with lock
- Ensure atomicity of `set()` operations
- Consider lock granularity (one lock vs. fine-grained)

#### 1.3 EventQueueRegistry.get() Lock
**File**: `src/skill_fleet/api/services/event_registry.py`

**Requirements**:
- Add lock protection to `get()` method
- Ensure consistency with `register()`/`unregister()` which already use locks

#### 1.4 TaxonomyManager Cache Lock
**File**: `src/skill_fleet/taxonomy/manager.py`

**Requirements**:
- Add `_cache_lock = asyncio.Lock()`
- Protect `metadata_cache` mutations in:
  - `_load_skill_file()`
  - `_load_skill_dir_metadata()`
  - `register_skill()`
  - `_load_always_loaded_skills()`

#### 1.5 InMemoryCache Lock Type
**File**: `src/skill_fleet/api/cache.py`

**Requirements**:
- Replace `threading.RLock()` with `asyncio.Lock()`
- Convert all methods to async where needed
- Ensure no blocking calls remain

#### 1.6 StreamingWorkflowManager Lock
**File**: `src/skill_fleet/core/workflows/streaming.py`

**Requirements**:
- Add lock for `_current_phase` and `_completed_phases` mutations
- Protect `set_phase()` method
- Ensure event emission is thread-safe

#### 1.7 ValidationWorkflow Lazy Init Lock
**File**: `src/skill_fleet/core/workflows/skill_creation/validation.py`

**Requirements**:
- Add lock for `quality_refiner` lazy initialization
- Create `_get_refiner()` async method
- Ensure only one instance created even with concurrent calls

### Phase 2: Duplicate Code Centralization

#### 2.1 Common Logging Utilities
**New File**: `src/skill_fleet/common/logging_utils.py`

**Requirements**:
```python
def _sanitize_for_log(value: Any, max_length: int = 500) -> str:
    """Sanitize value for logging.

    - Removes newlines and control characters
    - Masks secrets/tokens
    - Truncates to max_length
    - Handles ANSI codes
    """
```

**Migration**:
- Update `job_manager.py`
- Update `jobs.py`
- Update `cached_taxonomy.py`
- Update `taxonomy.py`

#### 2.2 LLM Fallback Decorator
**New File**: `src/skill_fleet/common/llm_fallback.py`

**Requirements**:
```python
def with_llm_fallback(default_return: Any = None, log_message: str = "Module failed"):
    """Decorator for DSPy module methods with LLM fallback.

    Catches exceptions and returns default if llm_fallback_enabled().
    """
```

**Migration** (7+ files):
- `requirements.py`
- `intent.py`
- `taxonomy.py`
- `dependencies.py`
- `plan.py`
- `compliance.py`
- `test_cases.py`

#### 2.3 Timed Execution Decorator
**File**: `src/skill_fleet/common/utils.py`

**Requirements**:
```python
def timed_execution(metric_name: str | None = None):
    """Decorator to time function execution.

    Automatically calculates duration_ms and logs via _log_execution.
    """
```

**Migration** (20+ occurrences):
- All DSPy module `aforward()` methods
- Workflow execution methods
- Validation methods

### Phase 3: Utility Modernization

#### 3.1 Cachetools Integration
**File**: `src/skill_fleet/api/cache.py`

**Requirements**:
- Verify `cachetools` in dependencies
- Replace `InMemoryCache` with `cachetools.TTLCache`
- Maintain same API surface
- Ensure TTL behavior preserved

#### 3.2 Anyio Integration
**File**: `src/skill_fleet/common/async_utils.py`

**Requirements**:
- Verify `anyio` in dependencies
- Replace custom `run_async()` implementation
- Use `anyio.run()` for nested event loops
- Maintain backward compatibility

#### 3.3 Pydantic v2 Native Serialization
**File**: `src/skill_fleet/common/serialization.py`

**Requirements**:
- Replace `serialize_pydantic_object()` with `model_dump()`
- Remove v1 compatibility code if no longer needed
- Update all callers

### Phase 4: Architecture Improvements

#### 4.1 BaseWorkflow Class
**New File**: `src/skill_fleet/core/workflows/base.py`

**Requirements**:
```python
class BaseWorkflow:
    """Base class for skill creation workflows.

    Handles common patterns:
    - Streaming event emission
    - Phase management
    - Error handling
    - HITL checkpointing
    """

    async def execute_streaming(self, ...) -> AsyncIterator[WorkflowEvent]:
        """Template method for streaming execution."""

    async def execute(self, ...) -> dict:
        """Non-streaming wrapper."""
```

**Migration**:
- Refactor `understanding.py`
- Refactor `generation.py`
- Refactor `validation.py`

#### 4.2 BaseModule Extension
**File**: `src/skill_fleet/core/modules/base.py`

**Requirements**:
```python
def validate_with_defaults(
    self,
    output: dict,
    required_defaults: dict[str, Any]
) -> dict:
    """Validate result and apply defaults for missing fields."""
```

**Migration** (6+ files):
- All understanding modules
- All validation modules

#### 4.3 Workflow Phase Extraction

**ValidationWorkflow** (`validation.py`):
- Extract `_step_initial_validation()`
- Extract `_step_quality_refinement()`
- Extract `_step_hitl_checkpoint()`
- Extract `_step_final_validation()`

**UnderstandingWorkflow** (`understanding.py`):
- Extract `_step_gather_requirements()`
- Extract `_step_analyze_intent()`
- Extract `_step_find_taxonomy()`
- Extract `_step_analyze_dependencies()`
- Extract `_step_synthesize_plan()`

**SkillService** (`skill_service.py`):
- Extract `_phase_understanding()`
- Extract `_phase_generation()`
- Extract `_phase_validation()`

### Phase 5: Testing

#### 5.1 Concurrency Stress Tests
**New File**: `tests/integration/test_concurrency.py`

**Requirements**:
```python
async def test_concurrent_job_creation():
    """Create 100 jobs concurrently, verify no duplicates."""

async def test_concurrent_job_access():
    """Multiple readers + writers to same job."""

async def test_taxonomy_cache_concurrent_update():
    """Concurrent skill registrations."""
```

#### 5.2 Regression Tests
**Requirements**:
- Run full test suite
- Verify all existing tests pass
- Fix any broken async/sync transitions

---

## Success Criteria

### Functional Criteria

1. **Concurrency Safety** ✅
   - [ ] No race conditions detected by stress tests
   - [ ] 1000 concurrent job creations complete without duplicates
   - [ ] Concurrent job reads/writes don't corrupt state
   - [ ] Taxonomy cache handles concurrent registrations
   - [ ] Event queues work correctly under concurrent access

2. **Code Quality** ✅
   - [ ] All 7 critical concurrency issues resolved
   - [ ] All 3 duplicate code patterns centralized
   - [ ] Complexity of 3 workflow functions reduced by 50%
   - [ ] No functions >200 lines
   - [ ] No functions with >4 nesting levels (orchestrators exempted)

3. **Functionality Preserved** ✅
   - [ ] All existing tests pass
   - [ ] Skill creation workflow works end-to-end
   - [ ] HITL interactions function correctly
   - [ ] Streaming events delivered properly
   - [ ] No API contract changes

### Technical Criteria

4. **Type Safety** ✅
   - [ ] `ty check` passes with no errors
   - [ ] `ruff check .` passes with no warnings
   - [ ] All new code has proper type hints

5. **Performance** ✅
   - [ ] No significant performance regression (<10% slower)
   - [ ] Lock contention minimal (measured with profiling)
   - [ ] Memory usage stable

6. **Maintainability** ✅
   - [ ] New utilities documented
   - [ ] Code coverage maintained or improved
   - [ ] No new lint warnings introduced
   - [ ] Follows existing code style

### Operational Criteria

7. **Deployment** ✅
   - [ ] Zero-downtime deployment possible
   - [ ] Can be rolled back if issues arise
   - [ ] No database migrations required
   - [ ] Compatible with existing environment variables

---

## Dependencies

### Required Libraries

Verify these are in `pyproject.toml`:
- `cachetools` (likely already present via DSPy)
- `anyio` (may need to add)

### Development Dependencies

For stress testing:
- `pytest-asyncio` (likely already present)
- `pytest-xdist` for parallel test execution

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing tests | High | Run full test suite after each phase; fix immediately |
| Async/sync mismatch | High | Update all callers systematically; type checker will catch |
| Lock contention | Medium | Use fine-grained locks; profile before/after |
| Race conditions not caught | Medium | Comprehensive stress tests; monitor in staging |
| Dependency conflicts | Low | Verify versions before adding new deps |

---

## Timeline

### Phase 1: Critical Concurrency (Day 1)
- Morning: JobManager, JobMemoryStore, EventQueueRegistry
- Afternoon: TaxonomyManager, InMemoryCache, Workflow managers

### Phase 2: Duplicate Code (Day 2)
- Morning: Create utilities, update 4 log sanitization files
- Afternoon: Apply decorators to 7+ DSPy modules

### Phase 3: Utilities (Day 3)
- Morning: Replace InMemoryCache
- Afternoon: Replace run_async and serialization

### Phase 4: Refactoring (Day 4-5)
- Day 4: BaseWorkflow, BaseModule extensions
- Day 5: Extract phase methods from 3 workflow classes

### Phase 5: Testing (Day 6)
- Morning: Write concurrency stress tests
- Afternoon: Full test suite run, bug fixes

**Total: 6 days** (including buffer for unexpected issues)

---

## Appendix: Affected Files

### Critical Changes (~15 files)
- `src/skill_fleet/api/services/job_manager.py`
- `src/skill_fleet/api/services/event_registry.py`
- `src/skill_fleet/api/cache.py`
- `src/skill_fleet/taxonomy/manager.py`
- `src/skill_fleet/core/workflows/streaming.py`
- `src/skill_fleet/core/workflows/skill_creation/validation.py`

### New Files (~5 files)
- `src/skill_fleet/common/logging_utils.py`
- `src/skill_fleet/common/llm_fallback.py`
- `src/skill_fleet/core/workflows/base.py`
- `tests/integration/test_concurrency.py`

### Modified Modules (~20 files)
- All understanding modules (requirements, intent, taxonomy, dependencies, plan)
- All validation modules (compliance, structure, metrics, test_cases, best_of_n)
- Generation modules (content, refined_content)
- API service files (jobs, cached_taxonomy, taxonomy endpoints)
- Common utilities (utils, async_utils, serialization)

---

**Next Step**: Review and approve this PRD, then proceed to TODOS.md creation.
