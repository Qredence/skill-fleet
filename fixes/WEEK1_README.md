# Week 1 Critical Fixes

This directory contains scripts to fix the critical issues identified in the code review.

## Quick Start

```bash
# Apply all fixes at once
python fixes/week1_apply_all.py

# Or apply individual fixes
python fixes/week1_fix_1_consolidate_path_validation.py
python fixes/week1_fix_2_async_subprocess.py
python fixes/week1_fix_3_job_store_eviction.py
python fixes/week1_fix_4_todo_implementations.py

# Dry run (see what would change without applying)
python fixes/week1_apply_all.py --dry-run
```

## Fixes Overview

### Fix #1: Consolidate Path Validation Code

**Problem:** Duplicate implementations of `sanitize_taxonomy_path()` in:
- `src/skill_fleet/common/path_validation.py`
- `src/skill_fleet/common/security.py`

**Solution:** 
- Make `security.py` the canonical implementation
- Update `path_validation.py` to re-export from `security.py`
- Add deprecation warning for old imports
- Add TOCTOU-safe `resolve_skill_md_path()` function

**Impact:** Eliminates code duplication, reduces maintenance burden

**Files Modified:**
- `src/skill_fleet/common/security.py` (enhanced)
- `src/skill_fleet/common/path_validation.py` (now re-exports)

---

### Fix #2: Async Subprocess Calls

**Problem:** Blocking `subprocess.run()` calls in async context at:
- `src/skill_fleet/taxonomy/skill_registration.py:577-598`

**Solution:**
- Convert `lint_skill_code()` to async function
- Use `asyncio.create_subprocess_exec()` instead of `subprocess.run()`
- Add proper timeout handling with `asyncio.wait_for()`

**Impact:** Prevents event loop blocking, improves responsiveness

**Files Modified:**
- `src/skill_fleet/taxonomy/skill_registration.py`

**Migration Required:**
Callers of `lint_skill_code()` must now use `await`:
```python
# Before:
lint_skill_code(skill_dir)

# After:
await lint_skill_code(skill_dir)
```

---

### Fix #3: Job Store Eviction

**Problem:** Unbounded in-memory job store (`JOBS` dict) causes memory leaks:
- `src/skill_fleet/app/services/jobs.py:41`

**Solution:**
- Replace dict with `JobStore` class
- Add automatic TTL eviction (24 hour default)
- Add maximum capacity limit (1000 jobs)
- Implement LRU eviction when over capacity

**Impact:** Prevents memory leaks, bounded resource usage

**Files Modified:**
- `src/skill_fleet/app/services/jobs.py`

**Configuration:**
```python
JobStore.MAX_JOBS = 1000       # Adjust as needed
JobStore.MAX_AGE_HOURS = 24    # Adjust as needed
```

---

### Fix #4: TODO Implementations

**Problem:** Multiple unimplemented TODO stubs:
- `src/skill_fleet/app/api/v1/skills/router.py:148` - Update skill endpoint
- `src/skill_fleet/app/api/v1/skills/router.py:291` - Refine skill persistence
- `src/skill_fleet/app/api/v1/taxonomy/router.py:97` - Update taxonomy

**Solution:**
- Implement update_skill with validation and persistence
- Add skill refinement persistence
- Implement taxonomy update with validation

**Impact:** Functional API endpoints, proper error handling

**Files Modified:**
- `src/skill_fleet/app/api/v1/skills/router.py`
- `src/skill_fleet/app/api/v1/taxonomy/router.py`

---

## Testing

After applying fixes, run the test suite:

```bash
# Run all tests
uv run pytest tests/ -x

# Run specific test modules
uv run pytest tests/unit/test_security.py -xvs
uv run pytest tests/unit/test_jobs.py -xvs

# Check for import errors
python -c "from skill_fleet.common.path_validation import sanitize_taxonomy_path; print('OK')"
python -c "from skill_fleet.common.security import sanitize_taxonomy_path; print('OK')"
```

## Rollback

If you need to rollback any fix, restore from the `.bak` files:

```bash
# Restore a specific file
cp src/skill_fleet/common/path_validation.py.bak src/skill_fleet/common/path_validation.py

# Or restore all
cp src/skill_fleet/common/path_validation.py.bak src/skill_fleet/common/path_validation.py
cp src/skill_fleet/taxonomy/skill_registration.py.bak src/skill_fleet/taxonomy/skill_registration.py
cp src/skill_fleet/app/services/jobs.py.bak src/skill_fleet/app/services/jobs.py
cp src/skill_fleet/app/api/v1/skills/router.py.bak src/skill_fleet/app/api/v1/skills/router.py
cp src/skill_fleet/app/api/v1/taxonomy/router.py.bak src/skill_fleet/app/api/v1/taxonomy/router.py
```

## Verification Checklist

- [ ] All imports work without errors
- [ ] Tests pass
- [ ] No duplicate path validation code
- [ ] Subprocess calls are non-blocking
- [ ] Job store has eviction limits
- [ ] TODO endpoints are implemented
- [ ] Backup files can be removed after verification

## Next Steps (Week 2)

After Week 1 fixes are verified:
1. Split `core/models.py` into separate modules
2. Remove silent exception swallowing
3. Wrap file I/O in async wrappers
4. DRY forward/aforward methods

See the code review report for full details.
