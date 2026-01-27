# Code Review: Week 1 Critical Fixes (Uncommitted Changes)

## Overview

This review covers the Week 1 critical fixes applied to the codebase. These changes address:
1. Duplicate path validation code
2. Blocking subprocess calls in async context
3. Memory leaks in job store
4. Unimplemented TODO stubs

---

## Fix #1: Consolidate Path Validation Code

### Files Modified
- `src/skill_fleet/common/path_validation.py`
- `src/skill_fleet/common/security.py`

### Changes

**path_validation.py** - Now a re-export module:
```python
# Before: 217 lines of implementation
# After: 56 lines re-exporting from security.py

from .security import (
    is_safe_path_component,
    resolve_path_within_root,
    sanitize_relative_file_path,
    sanitize_taxonomy_path,
)
```

**security.py** - Added TOCTOU-safe function:
```python
def resolve_skill_md_path(skills_root: Path, taxonomy_path: str) -> Path:
    """Atomic skill path resolution with TOCTOU protection."""
    # Uses resolve(strict=True) for atomic check
    # Prevents symlink-based path traversal
```

### Review

✅ **Good:**
- Eliminates 161 lines of duplicate code (74% reduction)
- Maintains full backward compatibility
- TOCTOU-safe implementation
- Clear deprecation message

⚠️ **Suggestions:**
1. Add type hints to the deprecated wrapper function
2. Consider adding a removal version for the deprecation

```python
# Suggested improvement:
def resolve_skill_md_path(
    skills_root: Path, 
    taxonomy_path: str
) -> Path:
    """
    Resolve the path to a skill's SKILL.md file.
    
    DEPRECATED: Will be removed in v2.0. 
    Use resolve_path_within_root() directly instead.
    """
    warnings.warn(
        "resolve_skill_md_path is deprecated and will be removed in v2.0. "
        "Use resolve_path_within_root() directly instead.",
        DeprecationWarning,
        stacklevel=2
    )
```

---

## Fix #2: Async Subprocess Calls

### Files Modified
- `src/skill_fleet/taxonomy/skill_registration.py`

### Changes

```python
# Before: Blocking subprocess.run()
def lint_and_format_skill(skill_dir: Path) -> None:
    result = subprocess.run([...], timeout=30)

# After: Non-blocking asyncio.create_subprocess_exec()
async def lint_and_format_skill(skill_dir: Path) -> None:
    proc = await asyncio.create_subprocess_exec(...)
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
```

### Review

✅ **Good:**
- Properly converts to async function
- Uses modern `asyncio.create_subprocess_exec()` API
- Handles timeouts correctly
- Proper process cleanup on timeout

⚠️ **Issues Found:**
1. **Missing import** - `import asyncio` was added, but verify it's at the top
2. **Type hint missing** - Return type should be `-> None` but docstring needs update

```python
# Missing proper exception handling for proc.kill():
except asyncio.TimeoutError:
    proc.kill()
    await proc.wait()  # Good - waits for process to terminate
    logger.warning(f"Linting timed out for skill {skill_dir.name}")
# Missing: Handle case where proc.wait() itself times out
```

⚠️ **Suggestion:** Add defensive code:
```python
except asyncio.TimeoutError:
    try:
        proc.kill()
        await asyncio.wait_for(proc.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        logger.error(f"Failed to terminate linting process for {skill_dir.name}")
```

---

## Fix #3: Job Store Eviction

### Files Modified
- `src/skill_fleet/app/services/jobs.py` (NEW FILE)

### Changes

```python
# Before: Unbounded dict
JOBS: dict[str, JobState] = {}

# After: Managed store with TTL + LRU
class JobStore:
    MAX_JOBS = 1000
    MAX_AGE_HOURS = 24
    
    def __init__(self):
        self._jobs: dict[str, JobState] = {}
        self._access_times: dict[str, float] = {}
```

### Review

✅ **Good:**
- Properly encapsulates job storage
- TTL eviction prevents stale data
- LRU eviction when over capacity
- Updates access time on get/set/contains

⚠️ **Issues Found:**

1. **Thread-safety claim is misleading** - The docstring says "Thread-safe" but there's no locking:
```python
class JobStore:
    """
    Thread-safe job store with automatic TTL eviction.
    # ^^^^^^^^^^^^ NOT ACTUALLY THREAD-SAFE
```

**Fix:** Either add threading lock or remove claim:
```python
# Option 1: Add threading lock
import threading

class JobStore:
    def __init__(self):
        self._lock = threading.Lock()
        # ...
    
    def __setitem__(self, job_id: str, job: JobState):
        with self._lock:
            self._evict_if_needed()
            self._jobs[job_id] = job
            self._access_times[job_id] = time.time()

# Option 2: Remove thread-safety claim (acceptable since it's asyncio context)
class JobStore:
    """Job store with automatic TTL eviction (asyncio context only)."""
```

2. **Potential race in eviction** - `min()` on empty dict raises ValueError:
```python
def _evict_if_needed(self):
    while len(self._jobs) > self.MAX_JOBS:
        oldest_job = min(self._access_times, key=self._access_times.get)
        # ^^^^ ValueError if _access_times is empty
```

**Fix:** Add guard:
```python
def _evict_if_needed(self):
    while len(self._jobs) > self.MAX_JOBS and self._access_times:
        oldest_job = min(self._access_times, key=self._access_times.get)
        self._evict_job(oldest_job)
```

3. **Missing `items()` and `__iter__` methods** - Dict-like interface is incomplete

**Fix:** Add missing methods:
```python
def items(self):
    """Return job items."""
    return self._jobs.items()

def __iter__(self):
    """Iterate over job IDs."""
    return iter(self._jobs)
```

---

## Fix #4: TODO Implementations

### Files Modified
- `src/skill_fleet/app/api/v1/skills/router.py`
- `src/skill_fleet/app/api/v1/taxonomy/router.py`

### Changes

**update_skill endpoint:**
```python
# Before: TODO stub
# TODO: Implement actual update logic with request body
return {"skill_id": skill_id, "status": "updated"}

# After: Full implementation
try:
    skill_path = skill_service.get_skill_by_path(skill_id)
    
    if request.content:
        skill_md_path = skill_path / "SKILL.md"
        if skill_md_path.exists():
            skill_md_path.write_text(request.content, encoding="utf-8")
    
    if request.metadata:
        # Merge metadata with existing
        ...
```

### Review

✅ **Good:**
- Proper error handling with specific exceptions
- Metadata merging logic
- File existence checks

⚠️ **Issues Found:**

1. **Type mismatch** - `get_skill_by_path()` returns dict, not Path:
```python
skill_path = skill_service.get_skill_by_path(skill_id)  # Returns dict!
skill_md_path = skill_path / "SKILL.md"  # TypeError!
```

**Fix:** Need to extract path from dict:
```python
skill_data = skill_service.get_skill_by_path(skill_id)
skill_path = skill_service.skills_root / skill_id.replace(".", "/")
# Or use taxonomy_manager to resolve
```

2. **Missing `import json`** - Used but not imported at module level

3. **No transaction safety** - If SKILL.md write succeeds but metadata fails, inconsistent state

4. **update_taxonomy complexity** - Function is now 70+ lines, consider extracting helpers:
```python
async def _update_single_path(taxonomy_manager, path, update_data) -> tuple[bool, str]:
    """Update a single path. Returns (success, error_message)."""
    ...
```

---

## Testing Status

| Component | Tests | Status |
|-----------|-------|--------|
| Path validation | 38 tests | ✅ PASS |
| Taxonomy manager | 6 tests | ✅ PASS |
| Job store | 0 direct tests | ⚠️ MISSING |
| Async subprocess | 0 direct tests | ⚠️ MISSING |
| API endpoints | 2 pre-existing failures | ⚠️ UNRELATED |

**Recommendation:** Add tests for JobStore and async subprocess.

---

## Security Review

| Check | Status |
|-------|--------|
| Path traversal protection | ✅ Good |
| TOCTOU protection | ✅ Good |
| Input validation | ✅ Good |
| Error message safety | ✅ No sensitive data leaked |
| Exception handling | ⚠️ Could be more specific |

---

## Action Items

### Must Fix Before Commit:
1. [ ] Fix `update_skill` - `get_skill_by_path()` returns dict, not Path
2. [ ] Add missing `import json` at module level in skills/router.py
3. [ ] Fix JobStore thread-safety claim (remove or add locking)
4. [ ] Add guard for empty `_access_times` in JobStore

### Should Fix:
5. [ ] Add defensive timeout for `proc.wait()` in subprocess fix
6. [ ] Break up `update_taxonomy` into smaller functions
7. [ ] Add `items()` and `__iter__` to JobStore
8. [ ] Add version to deprecation warning

### Nice to Have:
9. [ ] Add unit tests for JobStore
10. [ ] Add unit tests for async subprocess
11. [ ] Add integration tests for update endpoints

---

## Verdict

**Status:** ⚠️ **APPROVED WITH CHANGES**

The fixes address the critical issues but need minor corrections before merging:
- 4 must-fix items (mostly type issues)
- 4 should-fix items (code quality)
- Overall architecture is sound

**Estimated fix time:** 30 minutes
