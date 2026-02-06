# PRD: API-CLI Communication Optimization

**Status:** Draft
**Author:** Engineering
**Created:** 2026-02-04
**Last Updated:** 2026-02-04

---

## Problem Statement

The Skill Fleet API and client layer (CLI/TUI) exhibit significant communication inefficiencies that degrade user experience and system reliability:

1. **Excessive HITL Polling**: Clients poll `GET /api/v1/hitl/{job_id}/prompt` every ~1 second during HITL states, generating 100+ redundant requests per interaction
2. **Streaming Timeouts**: "No events for 5.0s" warnings flood logs during long-running LLM operations
3. **Critical Validation Crash**: Jobs fail with `validation_report.passed Field required` error when validation phase doesn't complete
4. **Resource Leaks**: Event queues are never cleaned up if jobs crash mid-execution
5. **Silent Failures**: Background task errors don't propagate to streaming clients

### Evidence from Terminal Logs

```
WARNING:skill_fleet.api.v1.streaming:Job b079ff87...: No events for 5.0s, falling back to status
(repeated 50+ times)

ERROR:skill_fleet.api.v1.skills:Skill creation job b079ff87... failed:
1 validation error for SkillCreationResult
validation_report.passed
  Field required [type=missing, input_value={}, input_type=dict]
```

---

## Goals

| Goal                       | Metric                              | Target            |
| -------------------------- | ----------------------------------- | ----------------- |
| Reduce HITL polling        | Requests per HITL interaction       | < 5 (from 100+)   |
| Eliminate timeout warnings | Warning log entries per job         | 0                 |
| Fix validation crashes     | Job failure rate from schema errors | 0%                |
| Clean up stale resources   | Orphaned event queues               | 0 after 5 minutes |

## Non-Goals

- WebSocket implementation (SSE is sufficient)
- Real-time collaborative editing
- Mobile TUI support

---

## Client Strategy: CLI vs TUI

### Option A: Focus on Python CLI (`src/skill_fleet/cli/`)

**Pros:**

- Same language as API (Python) - easier debugging
- Mature codebase with established patterns
- `streaming_runner.py` already handles SSE consumption
- Typer-based, well-tested command structure
- HITL handlers in `cli/hitl/` are comprehensive

**Cons:**

- Terminal UI limitations (Rich/Textual)
- Less interactive than TUI

### Option B: Focus on OpenTUI (`cli/tui/`)

**Pros:**

- Modern React-like component model
- Rich interactive UI (dialogs, panels)
- Streaming markdown rendering

**Cons:**

- TypeScript/Bun stack separate from main codebase
- OpenTUI is newer, less battle-tested
- Requires maintaining two SSE parsers
- Current implementation has polling patterns baked in

### Recommendation: **Prioritize CLI, keep TUI compatible**

The Python CLI at `src/skill_fleet/cli/streaming_runner.py` is the more stable foundation. Fixes should:

1. Land in the API first (backend-driven)
2. Be consumed by CLI automatically via existing SSE
3. TUI can adopt the improved events without code changes (if event schema is stable)

---

## Technical Design

### Step 1: Fix Validation Error Crash (Critical)

**Problem**: `ValidationReport.passed` has no default; when validation doesn't run, `{}` is passed and Pydantic fails.

**Files**:

- `src/skill_fleet/core/models.py#L584`
- `src/skill_fleet/api/services/skill_service.py#L521`
- `src/skill_fleet/api/v1/skills.py#L313`
- `src/skill_fleet/api/v1/quality.py#L109, L280`
- `src/skill_fleet/cli/streaming_runner.py#L559`

**Changes**:

```python
# models.py - Add default
passed: bool = Field(default=False, description="Whether all required checks passed")

# All consumers - Return None instead of {}
validation_report = phase3_result.get("validation_report") or None
```

**Why CLI benefits**: `streaming_runner.py#L559` has the same pattern and will crash on the same error.

---

### Step 2: Push HITL Prompt via SSE (Backend)

**Problem**: Stream only sends `{"type": "hitl_pause"}` without prompt data, forcing clients to poll.

**Files**:

- `src/skill_fleet/api/v1/streaming.py#L167`
- `src/skill_fleet/api/v1/hitl.py#L127`

**Changes**:

1. Extract `build_hitl_prompt_response(job_id)` from GET endpoint into shared function
2. Emit full prompt in `hitl_pause` event:

```python
# streaming.py
if status in HITL_STATUSES:
    prompt_data = await build_hitl_prompt_response(job_id)
    yield f"data: {json.dumps({'type': 'hitl_pause', 'status': status, 'prompt': prompt_data})}\n\n"
```

**Why CLI benefits**: `streaming_runner.py` can display HITL prompts directly from stream without extra fetch.

---

### Step 3: CLI Streaming Runner Update

**Problem**: CLI's `streaming_runner.py` may still poll or miss prompt data.

**Files**:

- `src/skill_fleet/cli/streaming_runner.py`
- `src/skill_fleet/cli/hitl/runner.py`

**Changes**:

1. Handle `hitl_pause` event with embedded prompt:

```python
elif event_type == "hitl_pause":
    prompt = event.get("prompt")
    if prompt:
        # Directly invoke HITL handler without fetch
        await handle_hitl_prompt(job_id, prompt)
    else:
        # Fallback to fetch (backward compat)
        prompt = await fetch_hitl_prompt(job_id)
```

2. Remove redundant polling loop if prompt is embedded

---

### Step 4: Add Heartbeat Events (Backend)

**Problem**: Empty event queue during LLM calls triggers timeout warnings.

**Files**:

- `src/skill_fleet/api/v1/streaming.py#L163`
- `src/skill_fleet/core/workflows/streaming.py`

**Changes**:

```python
# streaming.py
HEARTBEAT_INTERVAL = 3.0
last_heartbeat = time.monotonic()

# In event loop timeout handler:
if (time.monotonic() - last_heartbeat) >= HEARTBEAT_INTERVAL:
    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
    last_heartbeat = time.monotonic()
    timeout_count = 0  # Reset counter

# Rate-limit warning
if timeout_count >= MAX_CONSECUTIVE_TIMEOUTS and not logged_timeout_warning:
    logger.warning(f"Job {job_id}: No events for extended period")
    logged_timeout_warning = True
```

**Why CLI benefits**: Prevents stream disconnection during long LLM operations.

---

### Step 5: Implement Event Queue Cleanup (Backend)

**Problem**: `cleanup_expired()` is a placeholder; crashed jobs leak queues.

**Files**:

- `src/skill_fleet/api/services/event_registry.py#L72`
- `src/skill_fleet/api/lifespan.py`

**Changes**:

```python
# event_registry.py
class EventQueueRegistry:
    def __init__(self):
        self._queues: dict[str, tuple[asyncio.Queue, float]] = {}  # (queue, created_at)

    async def cleanup_expired(self, max_age: int = 3600, job_manager=None) -> int:
        async with self._lock:
            now = time.monotonic()
            to_remove = []
            for job_id, (queue, created_at) in self._queues.items():
                # Remove if too old
                if (now - created_at) > max_age:
                    to_remove.append(job_id)
                    continue
                # Remove if job is terminal
                if job_manager:
                    job = await job_manager.get_job(job_id)
                    if not job or job.status in TERMINAL_STATUSES:
                        to_remove.append(job_id)
            for job_id in to_remove:
                del self._queues[job_id]
            return len(to_remove)

# lifespan.py - Add background task
async def cleanup_task():
    while True:
        await asyncio.sleep(300)  # 5 minutes
        cleaned = await get_event_registry().cleanup_expired(job_manager=get_job_manager())
        if cleaned:
            logger.info(f"Cleaned up {cleaned} stale event queues")
```

---

### Step 6: Propagate Errors to Stream (Backend)

**Problem**: Background task exceptions don't reach streaming clients.

**Files**:

- `src/skill_fleet/api/v1/skills.py#L130-L155`

**Changes**:

```python
# skills.py - Background task wrapper
async def run_skill_creation_bg(job_id: str, request: CreateSkillRequest):
    event_registry = get_event_registry()
    try:
        result = await skill_service.create_skill(request, job_id)
        # Emit completion
        queue = await event_registry.get(job_id)
        if queue:
            await queue.put(WorkflowEvent(
                event_type=WorkflowEventType.COMPLETED,
                phase="complete",
                message="Skill creation finished",
                data={"result": result.model_dump()}
            ))
    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        queue = await event_registry.get(job_id)
        if queue:
            await queue.put(WorkflowEvent(
                event_type=WorkflowEventType.ERROR,
                phase="error",
                message=str(e),
                data={"error": str(e)}
            ))
        raise
    finally:
        await event_registry.unregister(job_id)
```

**Why CLI benefits**: `streaming_runner.py` will receive ERROR events instead of timing out.

---

### Step 7: Suppress MLflow Git Warning (Backend)

**Problem**: MLflow auto-detects git and fails on truncated commit hash.

**Files**:

- `src/skill_fleet/infrastructure/tracing/mlflow.py#L298`

**Changes**:

```python
import warnings

def start_parent_run(...):
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*Can't locate revision.*")
        # existing mlflow.start_run() call
```

---

## TUI Compatibility Notes

If the TUI (`cli/tui/`) is kept, these changes ensure compatibility:

1. **Event schema unchanged**: `hitl_pause` gains optional `prompt` field - TUI can ignore it and keep polling
2. **Heartbeat events**: TUI should ignore `keepalive` type (no-op)
3. **Error events**: TUI already handles `error` type in `handleStreamEvent()`

Future TUI optimization (optional):

- Update `AppShell.tsx#L159-205` to use embedded prompt from `hitl_pause` event
- Remove `fetchHitlPrompt()` calls when prompt is present in event

---

## Verification Plan

```bash
# 1. Run API server
uv run skill-fleet dev

# 2. Create skill via CLI (tests Steps 1-6)
uv run skill-fleet create "Create a Python logging skill" --auto-approve

# 3. Verify in logs:
#    - No "validation_report.passed" errors (Step 1)
#    - HITL prompt data in stream events (Step 2)
#    - Keepalive events every 3s during LLM calls (Step 4)
#    - No "No events for 5.0s" warnings (Step 4)
#    - ERROR event on forced failure (Step 6)

# 4. Test cleanup (Step 5)
#    - Start job, kill API mid-execution
#    - Restart API, wait 5 minutes
#    - Check orphaned queues are cleaned

# 5. Run unit tests
uv run pytest tests/unit/ -v
uv run pytest tests/integration/test_hitl_integration.py -v
```

---

## Decisions Log

| Decision                     | Rationale                                                |
| ---------------------------- | -------------------------------------------------------- |
| Prioritize CLI over TUI      | Same language, mature codebase, single SSE parser        |
| SSE push over WebSocket      | Unidirectional events suffice; WebSocket adds complexity |
| `default=False` for `passed` | Prevents crash while maintaining type safety             |
| 3s heartbeat interval        | Balances responsiveness vs. network overhead             |
| Backend-first changes        | CLI/TUI benefit automatically from improved events       |

---

## Risks & Mitigations

| Risk                          | Impact | Mitigation                                            |
| ----------------------------- | ------ | ----------------------------------------------------- |
| Breaking existing CLI clients | Medium | Event schema is additive (new fields optional)        |
| Heartbeats increase bandwidth | Low    | 3s interval = ~20 events/min, negligible              |
| Cleanup deletes active queues | High   | Only clean jobs in TERMINAL_STATUSES; add 5min buffer |
| TUI falls further behind      | Low    | TUI can ignore new fields; document upgrade path      |

---

## Timeline Estimate

| Step                       | Effort | Dependencies |
| -------------------------- | ------ | ------------ |
| 1. Fix validation crash    | 1h     | None         |
| 2. Push HITL via SSE       | 2h     | None         |
| 3. CLI streaming update    | 1h     | Step 2       |
| 4. Add heartbeat events    | 1h     | None         |
| 5. Event queue cleanup     | 2h     | None         |
| 6. Propagate errors        | 1h     | None         |
| 7. Suppress MLflow warning | 0.5h   | None         |

**Total**: ~8.5 hours

**Parallelization**: Steps 1, 4, 5, 6, 7 can run in parallel (no dependencies)

---

## Appendix: File Reference

### Backend (API)

| File                                               | Purpose                             |
| -------------------------------------------------- | ----------------------------------- |
| `src/skill_fleet/api/v1/streaming.py`              | SSE endpoint, heartbeat, event loop |
| `src/skill_fleet/api/v1/hitl.py`                   | HITL prompt GET/POST endpoints      |
| `src/skill_fleet/api/v1/skills.py`                 | Skill creation, background task     |
| `src/skill_fleet/api/services/event_registry.py`   | Event queue management              |
| `src/skill_fleet/api/services/skill_service.py`    | Workflow orchestration              |
| `src/skill_fleet/core/models.py`                   | Pydantic models (ValidationReport)  |
| `src/skill_fleet/infrastructure/tracing/mlflow.py` | MLflow integration                  |

### CLI

| File                                      | Purpose                     |
| ----------------------------------------- | --------------------------- |
| `src/skill_fleet/cli/streaming_runner.py` | SSE consumer, event handler |
| `src/skill_fleet/cli/hitl/runner.py`      | HITL prompt handling        |
| `src/skill_fleet/cli/commands/create.py`  | Create skill command        |

### TUI (Optional)

| File                           | Purpose                 |
| ------------------------------ | ----------------------- |
| `cli/tui/src/app/AppShell.tsx` | Main UI, event handling |
| `cli/tui/src/api.ts`           | API client, SSE parser  |
| `cli/tui/src/types.ts`         | TypeScript types        |
