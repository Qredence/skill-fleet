# Architecture Cleanup: Legacy Code Removal

**Date**: February 9, 2026
**Status**: ✅ **Complete** (Phase 1: Bridge Removal + Phase 2: Deprecated Code Removal)

---

## 🎯 Objective

Eliminate all legacy code, bridge/adapter layers, and deprecated APIs in favor of the modern `ValidationWorkflow` implementation.

**Before**: Dual-path validation (legacy + modern) with bridge layers and deprecated compatibility shims
**After**: Single modern validation path using DSPy workflows; clean codebase with no deprecated code

---

## ✅ Phase 1: Bridge/Adapter Removal

### Deleted Bridge/Adapter Files

```bash
src/skill_fleet/validators/dspy_bridge.py     # Legacy → DSPy bridge
src/skill_fleet/validators/models.py          # Duplicate validation models
src/skill_fleet/taxonomy/dspy_adapters.py     # Legacy taxonomy adapters
```

### Updated API to Use Modern Validation

**File**: `src/skill_fleet/api/v1/skills.py`

```python
# Modern validation path (current)
from ...core.workflows.skill_creation.validation import ValidationWorkflow
from ...core.models import ValidationReport

workflow = ValidationWorkflow()
async for event in workflow.execute_streaming(
    skill_content=content,
    plan={},
    taxonomy_path=skill_path,
):
    if event.event_type == "phase_complete":
        validation_report = event.data["validation_report"]
```

---

## ✅ Phase 2: Deprecated Code Removal

### Deleted Files

| File          | Reason                                                                                   |
| ------------- | ---------------------------------------------------------------------------------------- |
| `cli/main.py` | Deprecated `create_skill()` / `validate_skill()` entrypoints (replaced by API-first CLI) |

### Cleaned: `validators/skill_validator.py`

- ✅ Removed `.. deprecated::` module docstring → clean description
- ✅ Removed `import warnings` (no longer needed)
- ✅ Removed `use_llm` parameter from `__init__`
- ✅ Removed deprecation warning block and `self.use_llm = False`
- ✅ Removed `_validate_with_dspy_if_available()` method and its call site
- ✅ `SkillValidator` is now a clean rule-based validator, no deprecated cruft

### Cleaned: `validators/__init__.py`

- ✅ Replaced deprecation docstring with clean module description
- ✅ Exports only `SkillValidator` (no deprecation notice)

### Cleaned: `core/models.py`

- ✅ Removed `DictLikeAccessMixin` class entirely (~35 lines)
- ✅ Removed `DictLikeAccessMixin` from `SkillMetadata` and `ValidationReport` base classes
- ✅ Removed `from_validation_result()` classmethod from `ValidationReport` (~45 lines)
- ✅ Removed legacy `capabilities/` and `resources/` from `SkillSkeleton` defaults

### Cleaned: `api/schemas/skills.py`

- ✅ Removed deprecated `issues` field from `ValidateSkillResponse`
- ✅ Cleaned "DSPy bridge" reference from `use_llm` description

### Cleaned: `api/v1/skills.py`

- ✅ Removed `issues=[]` from validation responses
- ✅ Cleaned fallback validation path to use `errors`/`warnings`/`checks` directly
- ✅ Removed unused `warnings_list` variable

### Cleaned: `cli/client.py`

- ✅ Removed "via DSPy bridge" from `validate_skill()` docstring

### Cleaned: `infrastructure/db/database.py`

- ✅ Removed deprecated `get_db_context_manager()` function (use `get_db_context()` instead)

### Cleaned: `taxonomy/skill_registration.py`

- ✅ Removed legacy `capabilities/` and `resources/` subdirectory creation from new skills
- ✅ New skills now create only v2 Golden Standard directories

### Cleaned: `api/services/job_manager.py`

- ✅ Removed deprecated `set_db_repo()` method (use `enable_persistence()` instead)

### Updated Tests

- ✅ `tests/cli/test_cli_commands.py` — removed `TestCreateSkillCommand` class that tested deleted `cli/main.py`

---

## 📊 Impact

### Code Reduction

- **Phase 1**: ~500 lines of bridge/adapter code deleted
- **Phase 2**: ~200 lines of deprecated code removed across 9 files + 1 file deleted
- **Total**: ~700+ lines of dead/deprecated code eliminated

### Architecture Simplification

- **Single validation path**: `ValidationWorkflow` (DSPy-based) for API/CLI
- **Clean rule-based validator**: `SkillValidator` for basic structure checks (no deprecated params)
- **No compatibility shims**: `DictLikeAccessMixin`, `from_validation_result`, `get_db_context_manager`, `set_db_repo` all removed
- **v2 Golden Standard only**: New skills no longer create legacy `capabilities/` / `resources/` directories

### Validation Flow (Current)

```
API/CLI
  ↓
ValidationWorkflow (DSPy)
  ↓
DSPy Modules (Compliance, Quality, Structure, TestCases)
  ↓
ValidationReport
  ↓
Response
```

For basic rule-based checks:

```
SkillValidator (no deprecated params)
  ↓
ValidationResult (simple container)
  ↓
dict
```

---

## ⚠️ Breaking Changes

### For API Consumers

- ✅ **No breaking changes** in request format
- ⚠️ `issues` field removed from `ValidateSkillResponse` — use `errors` and `warnings` instead

### For Direct Code Users

- ⚠️ `SkillValidator(skills_root, use_llm=True)` → remove `use_llm` param (no longer accepted)
- ⚠️ `from skill_fleet.cli.main import create_skill, validate_skill` → deleted, use API
- ⚠️ `from skill_fleet.core.models import DictLikeAccessMixin` → removed
- ⚠️ `ValidationReport.from_validation_result()` → removed, construct `ValidationReport` directly
- ⚠️ `get_db_context_manager()` → use `get_db_context()`
- ⚠️ `job_manager.set_db_repo()` → use `job_manager.enable_persistence()`

### Migration Examples

```python
# Validation (OLD → NEW)
# OLD: from skill_fleet.validators import SkillValidator
#      validator = SkillValidator(root, use_llm=True)
# NEW:
from skill_fleet.core.workflows.skill_creation.validation import ValidationWorkflow
workflow = ValidationWorkflow()
async for event in workflow.execute_streaming(
    skill_content=content, plan={}, taxonomy_path=path,
):
    if event.event_type == "phase_complete":
        report = event.data["validation_report"]

# Rule-based only (OLD → NEW)
# OLD: SkillValidator(root, use_llm=False)
# NEW:
from skill_fleet.validators import SkillValidator
validator = SkillValidator(root)  # No use_llm param

# Database context (OLD → NEW)
# OLD: with get_db_context_manager() as db: ...
# NEW:
from skill_fleet.infrastructure.db.database import get_db_context
with get_db_context() as db: ...
```

---

## ✅ Testing

### Verified

- ✅ All 23 relevant tests pass (`test_skill_validator`, `test_cli_commands`, `test_skills`)
- ✅ All modified files pass `py_compile` syntax check
- ✅ All modified files pass `ruff check` lint

---

## 📝 Files Changed (All Phases)

| File                             | Status      | Changes                                                                    |
| -------------------------------- | ----------- | -------------------------------------------------------------------------- |
| `validators/dspy_bridge.py`      | **DELETED** | Bridge removed (Phase 1)                                                   |
| `validators/models.py`           | **DELETED** | Duplicate models removed (Phase 1)                                         |
| `taxonomy/dspy_adapters.py`      | **DELETED** | Adapters removed (Phase 1)                                                 |
| `cli/main.py`                    | **DELETED** | Deprecated entrypoints removed (Phase 2)                                   |
| `validators/skill_validator.py`  | **CLEANED** | Removed `use_llm`, `_validate_with_dspy_if_available`, deprecation notices |
| `validators/__init__.py`         | **CLEANED** | Clean docstring, no deprecation warnings                                   |
| `core/models.py`                 | **CLEANED** | Removed `DictLikeAccessMixin`, `from_validation_result`, legacy dirs       |
| `api/schemas/skills.py`          | **CLEANED** | Removed `issues` field, cleaned descriptions                               |
| `api/v1/skills.py`               | **CLEANED** | Uses `ValidationWorkflow`, removed `issues`                                |
| `cli/client.py`                  | **CLEANED** | Removed "DSPy bridge" reference                                            |
| `infrastructure/db/database.py`  | **CLEANED** | Removed `get_db_context_manager()`                                         |
| `taxonomy/skill_registration.py` | **CLEANED** | Removed legacy `capabilities/` / `resources/` creation                     |
| `api/services/job_manager.py`    | **CLEANED** | Removed `set_db_repo()`                                                    |
| `tests/cli/test_cli_commands.py` | **UPDATED** | Removed tests for deleted `cli/main.py`                                    |

---

## 🚀 Remaining Work

### Testing

- [ ] Run full test suite: `uv run pytest tests/ -v`
- [ ] Add integration tests for `ValidationWorkflow`
- [ ] Add tests for new v2 Golden Standard directory structure

### Documentation

- [ ] Update `docs/how-to-guides/cli.md` (CLI requires API server)
- [ ] Update `docs/reference/api.md` (new endpoints, removed `issues` field)
- [ ] Update migration guide with breaking changes

---

**Last Updated**: February 9, 2026
**Phases Completed**: Phase 1 (Bridge Removal) + Phase 2 (Deprecated Code Removal)
**Next Steps**: Full test suite, integration tests, documentation updates
