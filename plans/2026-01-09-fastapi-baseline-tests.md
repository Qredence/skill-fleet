# FastAPI Production Patterns - Baseline Test Scenarios (RED Phase)

## Testing Methodology

For technique/reference skills, we test with:
- **Application scenarios:** Can agents apply the techniques correctly?
- **Variation scenarios:** Do they handle edge cases?
- **Missing information tests:** Do instructions have gaps?

These scenarios will be run WITHOUT the skill to document baseline behavior and common mistakes.

---

## Scenario 1: Database Lifecycle (Application)

**Prompt:** "Help me create a FastAPI app with SQLAlchemy async database. I need a `/users` endpoint that returns all users from PostgreSQL."

**Expected baseline failures:**
- Creating engine at import time (not in lifespan)
- Missing `engine.dispose()` in shutdown
- Not setting pool parameters
- Using global `db` variable instead of dependency injection

**Success criteria (WITH skill):**
- Engine created in lifespan context manager
- Proper shutdown with `engine.dispose()`
- Using `Depends(get_db)` pattern
- Pool parameters configured

---

## Scenario 2: Partial Update Endpoint (Application)

**Prompt:** "I have a User model with name, email, and age fields. Create a PATCH endpoint to update users that only updates the fields provided in the request."

**Expected baseline failures:**
- Not using `exclude_unset=True`
- Overwriting unprovided fields with `None`
- Not using Pydantic `Optional` fields
- Missing validation for partial updates

**Success criteria (WITH skill):**
- Using `Optional` fields in Pydantic model
- Using `update.dict(exclude_unset=True)`
- Only updating provided fields
- Proper 404 handling

---

## Scenario 3: Converting Sync Utility to Async (Application)

**Prompt:** "I have this sync function that fetches user data from our database and calls an external API. Convert it to a FastAPI endpoint: [provide sync function using requests and SQLAlchemy sync]"

**Expected baseline failures:**
- Keeping `requests` library (blocking)
- Using `run_in_executor` as band-aid
- Not converting to `AsyncSession`
- Missing `await` keywords
- Not using async-compatible libraries

**Success criteria (WITH skill):**
- Replace `requests` with `httpx.AsyncClient`
- Convert to `AsyncSession` pattern
- Proper `async/await` usage
- No blocking operations

---

## Scenario 4: Testing Async Endpoints (Application)

**Prompt:** "Write tests for my FastAPI user endpoints. I need to test GET, POST, and PATCH operations."

**Expected baseline failures:**
- Using `TestClient` (sync) instead of `AsyncClient`
- Not using `@pytest.mark.asyncio`
- Sync fixtures with async tests
- Tests passing in isolation but failing when run together
- Missing database rollback between tests

**Success criteria (WITH skill):**
- Using `httpx.AsyncClient`
- Proper async fixtures
- `@pytest.mark.asyncio` decorator
- Database isolation between tests

---

## Scenario 5: File Upload Processing (Variation)

**Prompt:** "I have a utility function that processes Excel files using pandas. Convert it to a FastAPI endpoint that accepts file uploads. The files can be up to 50MB."

**Expected baseline failures:**
- Loading entire file into memory first
- Not streaming the file
- Not validating file type/size
- No error handling for malformed files

**Success criteria (WITH skill):**
- Streaming file handling with `UploadFile`
- Not loading entire file into memory
- File validation
- Proper error handling

---

## Scenario 6: Complex Dependency Graph (Variation)

**Prompt:** "I need dependencies that depend on other dependencies. I have `get_current_user` that depends on `get_db`, and `verify_admin` that depends on `get_current_user`. How do I set this up?"

**Expected baseline failures:**
- Trying to chain dependencies manually
- Passing dependencies as function parameters
- Not understanding that FastAPI handles this automatically
- Creating unnecessary complexity

**Success criteria (WITH skill):**
- Understanding that FastAPI auto-resolves dependency trees
- Clean dependency chain using `Depends()`
- Proper type hints
- No manual dependency passing

---

## Scenario 7: Pydantic Validation with Computed Fields (Edge Case)

**Prompt:** "Create a user model where `full_name` is computed from `first_name` and `last_name`, but only `first_name` and `last_name` are stored in the database."

**Expected baseline failures:**
- Not using Pydantic `computed_field`
- Computed field not appearing in response
- Validation running on computed field
- Confusion between input and output models

**Success criteria (WITH skill):**
- Using `@computed_field` decorator
- Separate input/output models if needed
- Computed field in API response
- No validation issues

---

## Scenario 8: Background Task Error Handling (Edge Case)

**Prompt:** "I have a background task that processes payments. How do I handle errors in the task and update the user about failures?"

**Expected baseline failures:**
- Exceptions in background tasks being silently swallowed
- No way to communicate task status back to user
- Not using task status tracking
- Missing retry logic

**Success criteria (WITH skill):**
- Proper exception handling in background tasks
- Task status tracking (database or cache)
- User-facing status endpoint
- Retry mechanism or dead letter queue

---

## Scenario 9: Multiple Database Connections (Edge Case)

**Prompt:** "My app needs to connect to two databases - a primary PostgreSQL for writes and a read replica for reads. How do I set this up?"

**Expected baseline failures:**
- Creating two separate engines incorrectly
- Not managing two separate lifecycles
- Confusion about which dependency to use where
- Connection pool issues with multiple engines

**Success criteria (WITH skill):**
- Separate engines for read/write
- Proper lifespan management for both
- Clear dependency naming (`get_db_read`, `get_db_write`)
- Pool parameters for each

---

## Scenario 10: Converting Legacy Class-Based API (Complex)

**Prompt:** "I have a Flask app with class-based views. Each class has methods for get, post, put, delete. How do I convert this to FastAPI?"

**Expected baseline failures:**
- Trying to maintain class structure in FastAPI
- Not understanding FastAPI's function-based approach
- Mixing patterns incorrectly
- Losing functionality in conversion

**Success criteria (WITH skill):**
- Converting to function-based endpoints
- Proper `APIRouter` organization
- Maintaining all functionality
- Cleaner FastAPI-idiomatic code

---

## Running the Baseline Tests

To run these scenarios and document failures:

```bash
# For each scenario, create a fresh subagent
# Prompt with the scenario WITHOUT access to the skill
# Document:
# 1. What choices did they make?
# 2. What rationalizations did they use (verbatim)?
# 3. Which pressures triggered violations?
# 4. What code patterns emerged (correct vs incorrect)?
```

## Baseline Test Results (Documented Failures)

### Scenario 1: Database Lifecycle - CONFIRMED FAILURES ✅

**Files created:** `examples/fastapi_app/database.py`, `main.py`

**Baseline failures found:**
1. **Line 9-14 (database.py):** Engine created at import time (module-level global)
   ```python
   # ❌ Created at import - runs when module loads
   engine: AsyncEngine = create_async_engine(DATABASE_URL, ...)
   ```

2. **Line 19-23 (main.py):** Using deprecated `@app.on_event("startup")` instead of `lifespan`
   ```python
   # ❌ Deprecated pattern
   @app.on_event("startup")
   async def startup_event():
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
   ```

3. **NO shutdown handler:** No `@app.on_event("shutdown")` to dispose engine
   - **Impact:** Connections never close, workers leak connections forever
   - **Production symptom:** "Too many connections" DB errors under load

4. **Missing pool parameters:** No `pool_size`, `max_overflow`, `pool_recycle`
   - **Impact:** Pool exhaustion with multiple workers
   - **Production symptom:** Connection timeout errors under concurrent load

**Verdict:** Baseline agent creates code that works in dev but will fail in production.

---

### Scenario 2: Partial Updates - BASELINE PASSED ✅

**Result:** Agent correctly used `model_dump(exclude_unset=True)` (Pydantic v2 syntax)

**Note:** This test used in-memory database. Real test would be with SQLAlchemy async to verify proper `exclude_unset` usage with ORM models.

---

## Expected Rationalizations

Based on common patterns, agents might rationalize:

| Rationalization                     | Reality                                         |
|-------------------------------------|-------------------------------------------------|
| "The tutorial did it this way"      | Tutorials skip production concerns              |
| "It works in development"           | Production has different load patterns          |
| "I'll add proper cleanup later"     | Later never comes, production leaks connections |
| "Requests is fine for simple cases" | Blocking kills async performance                |
| "I can fix tests after"             | Tests after don't catch async issues            |
| "This is a simple endpoint"         | Simple endpoints become complex                 |

These rationalizations will inform the "Common Mistakes" and anti-patterns section in the skill.
