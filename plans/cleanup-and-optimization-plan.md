# Skill Fleet Codebase Cleanup & Optimization Plan

**Date**: 2026-01-10
**Status**: Draft
**Priority**: High - Code Quality & DSPy Best Practices Alignment

---

## Executive Summary

This plan addresses code quality issues, optimizes DSPy usage, and aligns the `skill_fleet` codebase with best practices. The recent directory structure refactor (commit `accae91`) provides a clean foundation; this plan builds on that work.

### Key Goals
1. Eliminate code duplication
2. Remove legacy/dead code
3. Improve DSPy patterns consistency
4. Complete incomplete features
5. Enhance type safety across the codebase

---

## Phase 1: Code Deduplication (High Priority)

### 1.1 Extract Common Utilities Module

**Problem**: `safe_json_loads()` and `safe_float()` are duplicated across files.

**Files Affected**:
- `src/skill_fleet/workflow/modules.py`
- `src/skill_fleet/agent/modules.py`

**Solution**: Create `src/skill_fleet/common/utils.py`:

```python
"""Common utility functions for skill_fleet modules."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def safe_json_loads(
    value: str | Any,
    default: dict | list | None = None,
    field_name: str = "unknown",
) -> dict | list:
    """Safely parse JSON string with fallback to default.

    Handles:
    - Already parsed objects (returns as-is)
    - Valid JSON strings (parses and returns)
    - Invalid JSON (returns default with warning)
    - Pydantic models (extracts via model_dump())

    Args:
        value: String to parse or already-parsed object
        default: Default value if parsing fails (dict or list)
        field_name: Field name for logging

    Returns:
        Parsed JSON or default value (never None)
    """
    if default is None:
        default = {}

    # Already parsed (dict, list, or Pydantic model)
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return [item.model_dump() if hasattr(item, "model_dump") else item for item in value]
    if hasattr(value, "model_dump"):  # Pydantic model
        return value.model_dump()

    # Empty or None
    if not value:
        return default

    # Try to parse JSON string
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.warning(
                f"Failed to parse JSON for field '{field_name}': {e}. "
                f"Value preview: {value[:100]}..."
            )
            return default

    # Unknown type
    logger.warning(f"Unexpected type for field '{field_name}': {type(value)}")
    return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float.

    Args:
        value: Value to convert
        default: Default if conversion fails

    Returns:
        Float value
    """
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default
```

**Migration Steps**:
1. Create `src/skill_fleet/common/__init__.py`
2. Create `src/skill_fleet/common/utils.py` with above content
3. Update imports in affected files:
   - `from ..common.utils import safe_json_loads, safe_float` (in workflow/modules.py)
   - `from ...common.utils import safe_json_loads, safe_float` (in agent/modules.py)
4. Remove duplicate implementations
5. Run tests to verify: `uv run pytest`

**Estimated Impact**: ~70 lines of code removed, improved maintainability

---

## Phase 2: Legacy Code Removal (Medium Priority)

### 2.1 Remove Legacy DSPy Signatures

**Problem**: `workflow/signatures.py` contains legacy string-based signatures marked for removal.

**Files Affected**:
- `src/skill_fleet/workflow/signatures.py` (lines 325-383)

**Solution**: Remove the following:
1. `UnderstandTaskForSkillLegacy` class
2. `PlanSkillStructureLegacy` class
3. Associated comment on line 327

**Verification**:
- Search codebase for references to these classes (should be none)
- Run `uv run pytest` to ensure no breaking changes

### 2.2 Clean Up Deprecated CLI Files

**Problem**: Git status shows deleted CLI files that may need formal removal from git history.

**Files Affected** (already deleted):
- `src/skill_fleet/cli_submodules/__init__.py`
- `src/skill_fleet/cli_submodules/main.py`
- `src/skill_fleet/cli_submodules/onboarding_cli.py`

**Solution**: These are already deleted. Ensure no imports reference these paths.

---

## Phase 3: Complete Incomplete Features (Medium Priority)

### 3.1 Incorporate Revision Feedback

**Problem**: TODO comments indicate `revision_feedback` parameter not used.

**Files Affected**:
- `src/skill_fleet/workflow/modules.py` (lines 524, 959)
- `src/skill_fleet/agent/agent.py` (line 1130)

**Solution**: Update `EditSkillContent` signature and `EditModule` to properly incorporate feedback:

**In `workflow/signatures.py`, update `EditSkillContent`:**

```python
class EditSkillContent(dspy.Signature):
    """Generate comprehensive skill content with composition support.

    Creates the main SKILL.md content and supporting documentation.
    Note: YAML frontmatter will be added automatically during registration.

    The skill_content MUST include these sections:
    - # Title (skill name as heading)
    - ## Overview (what the skill does)
    - ## Capabilities (list of discrete capabilities)
    - ## Dependencies (required skills or 'No dependencies')
    - ## Usage Examples (code examples with expected output)
    """

    # Inputs
    skill_skeleton: str = dspy.InputField(desc="JSON skill skeleton structure")
    parent_skills: str = dspy.InputField(
        desc="Content/metadata from parent/sibling skills for context"
    )
    composition_strategy: str = dspy.InputField(desc="How this skill composes with others")
    revision_feedback: str = dspy.InputField(
        default="",
        desc="User feedback from previous revision to incorporate (empty if initial generation)"
    )

    # Outputs - skill_content stays as string for long-form markdown
    skill_content: str = dspy.OutputField(
        desc="""Full SKILL.md markdown body content (frontmatter added automatically).
        Must include: # Title, ## Overview, ## Capabilities, ## Dependencies, ## Usage Examples.
        Include code blocks with syntax highlighting (```python, ```bash, etc.)."""
    )
    capability_implementations: list[CapabilityImplementation] = dspy.OutputField(
        desc="Documentation content for each capability"
    )
    usage_examples: list[UsageExample] = dspy.OutputField(
        desc="Runnable usage examples with code and expected output"
    )
    best_practices: list[BestPractice] = dspy.OutputField(
        desc="Best practice recommendations (3-5 items)"
    )
    integration_guide: str = dspy.OutputField(
        desc="Integration notes and composition patterns (1-2 paragraphs)"
    )
```

**In `workflow/modules.py`, update `EditModule.forward()`:**

```python
def forward(
    self,
    skill_skeleton: dict,
    parent_skills: str,
    composition_strategy: str,
    revision_feedback: str | None = None,
) -> dict:
    """Generate comprehensive skill content.

    Args:
        skill_skeleton: Directory structure
        parent_skills: Context from related skills
        composition_strategy: How skill composes with others
        revision_feedback: Optional feedback for regeneration

    Returns:
        Dict with skill_content, capability_implementations,
        usage_examples, best_practices, and integration_guide
    """
    result = self.edit(
        skill_skeleton=json.dumps(skill_skeleton, indent=2),
        parent_skills=parent_skills,
        composition_strategy=composition_strategy,
        revision_feedback=revision_feedback or "",  # NOW INCORPORATED
    )

    return {
        "skill_content": result.skill_content,
        "capability_implementations": safe_json_loads(
            result.capability_implementations,
            default={},
            field_name="capability_implementations",
        ),
        "usage_examples": safe_json_loads(
            result.usage_examples, default=[], field_name="usage_examples"
        ),
        "best_practices": safe_json_loads(
            result.best_practices, default=[], field_name="best_practices"
        ),
        "integration_guide": result.integration_guide,
    }
```

### 3.2 Fix Hardcoded Evolution Metadata

**File**: `src/skill_fleet/agent/agent.py:1130`

**Problem**: Evolution dict has empty hardcoded values.

**Solution**:
```python
from datetime import datetime

# In _save_skill method:
evolution = EvolutionMetadata(
    skill_id=plan["skill_metadata"]["skill_id"],
    version=plan["skill_metadata"]["version"],
    status="approved",
    timestamp=datetime.now().isoformat(),
    previous_versions=[],
    change_summary=f"Initial creation via conversational agent with TDD verification",
)
```

---

## Phase 4: DSPy Best Practices Alignment (Low-Medium Priority)

### 4.1 Centralize DSPy Configuration

**Problem**: No central DSPy setup; LM configuration scattered across modules.

**Solution**: Create `src/skill_fleet/llm/dspy_config.py`:

```python
"""Centralized DSPy configuration for skill_fleet.

This module provides a single entry point for configuring DSPy settings
across all skill_fleet modules, ensuring consistent LM usage and settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import dspy
import yaml

from .fleet_config import build_lm_for_task, load_fleet_config


def configure_dspy(
    config_path: Path | None = None,
    default_task: str = "skill_understand",
) -> dspy.LM:
    """Configure DSPy with fleet config and return default LM.

    This should be called once at application startup to set up
    DSPy's global settings.

    Args:
        config_path: Path to config/config.yaml (default: project root)
        default_task: Default task to use for dspy.settings.lm

    Returns:
        The configured LM instance (also set as dspy.settings.lm)
    """
    if config_path is None:
        # Default to config/config.yaml in project root
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

    config = load_fleet_config(config_path)
    lm = build_lm_for_task(config, default_task)

    # Set DSPy global settings
    dspy.configure(lm=lm)

    # Set cache directory from environment if specified
    if cache_dir := os.environ.get("DSPY_CACHEDIR"):
        dspy.settings.configure(cache_dir=Path(cache_dir))

    # Set temperature override if specified
    if temp_str := os.environ.get("DSPY_TEMPERATURE"):
        try:
            temp = float(temp_str)
            lm.kwargs["temperature"] = temp
        except ValueError:
            pass

    return lm


def get_task_lm(task_name: str, config_path: Path | None = None) -> dspy.LM:
    """Get an LM for a specific task without changing global settings.

    Use this when you need a task-specific LM temporarily.
    For persistent task-specific LMs, use dspy.context() instead.

    Args:
        task_name: Task name from config (e.g., "skill_understand", "skill_edit")
        config_path: Path to config/config.yaml

    Returns:
        Configured LM for the specified task
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

    config = load_fleet_config(config_path)
    return build_lm_for_task(config, task_name)
```

### 4.2 Update CLI to Use Centralized Configuration

**File**: `src/skill_fleet/cli/main.py`

Add initialization call:
```python
from skill_fleet.llm.dspy_config import configure_dspy

def main():
    # Configure DSPy before any operations
    configure_dspy()
    # ... rest of main logic
```

---

## Phase 5: Type Safety Improvements (Low Priority)

### 5.1 Standardize Parameter Types

**Problem**: Mix of `str | dict` and `str | list` parameters creates complexity.

**Solution**: Standardize on single types with documented conversion:

- Input parameters: Use `str` with JSON, document expected format
- Internal processing: Parse immediately, work with typed objects
- Output parameters: Use Pydantic models for structure

**Example Refactoring**:

```python
# Before (ambiguous):
def forward(self, metadata: dict | str) -> dict:

# After (clear):
def forward(self, metadata_json: str) -> dict:
    """Process skill metadata.

    Args:
        metadata_json: JSON string of skill metadata or dict

    Returns:
        Parsed and validated metadata dict
    """
    metadata = safe_json_loads(metadata_json, default={})
    # ... rest of logic
```

---

## Implementation Checklist

### Phase 1: Code Deduplication
- [ ] Create `src/skill_fleet/common/__init__.py`
- [ ] Create `src/skill_fleet/common/utils.py`
- [ ] Update imports in `workflow/modules.py`
- [ ] Update imports in `agent/modules.py`
- [ ] Remove duplicate utility functions
- [ ] Run tests: `uv run pytest`
- [ ] Run linting: `uv run ruff check .`

### Phase 2: Legacy Removal
- [ ] Search for `UnderstandTaskForSkillLegacy` references
- [ ] Search for `PlanSkillStructureLegacy` references
- [ ] Remove legacy signatures from `workflow/signatures.py`
- [ ] Run tests to verify no breakage

### Phase 3: Complete Features
- [ ] Update `EditSkillContent` signature with `revision_feedback`
- [ ] Update `EditModule.forward()` to pass feedback
- [ ] Update `EditModule.aforward()` to pass feedback
- [ ] Update `EditModuleQA` classes similarly
- [ ] Fix hardcoded evolution metadata in `agent/agent.py`
- [ ] Run tests

### Phase 4: DSPy Best Practices
- [ ] Create `src/skill_fleet/llm/dspy_config.py`
- [ ] Update CLI to call `configure_dspy()`
- [ ] Document DSPy configuration in README
- [ ] Run integration tests

### Phase 5: Type Safety
- [ ] Audit all `str | dict` parameters
- [ ] Standardize on string inputs with clear docs
- [ ] Update type hints accordingly
- [ ] Run `mypy` if configured

---

## Testing Strategy

### Unit Tests
- Test `safe_json_loads()` with all input types
- Test `configure_dspy()` with various config scenarios
- Test revision feedback incorporation

### Integration Tests
- Run full skill creation workflow
- Test conversational agent with feedback loops
- Verify TDD checklist completion

### Regression Tests
- `uv run pytest tests/`
- `uv run ruff check .`
- Manual testing of CLI commands

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing imports | Medium | High | Comprehensive test run before merge |
| DSPy version incompatibility | Low | Medium | Pin DSPy version in requirements |
| Performance regression | Low | Low | Benchmark before/after optimization |
| Incomplete TODO removal | Low | Low | Code review and grep for TODOs |

---

## Success Criteria

1. **No code duplication**: Utilities defined in single location
2. **No legacy code**: All dead/legacy code removed
3. **Complete features**: All TODOs addressed or documented
4. **Consistent DSPy usage**: Centralized configuration, clear patterns
5. **All tests passing**: 100% test pass rate maintained
6. **Type safety improved**: Reduced `str | dict` ambiguity

---

## Timeline Estimate

| Phase | Estimated Time |
|-------|---------------|
| Phase 1: Deduplication | 2-3 hours |
| Phase 2: Legacy Removal | 1-2 hours |
| Phase 3: Complete Features | 2-3 hours |
| Phase 4: DSPy Alignment | 2-3 hours |
| Phase 5: Type Safety | 3-4 hours |
| Testing & Validation | 2-3 hours |
| **Total** | **14-18 hours** |

---

## References

- DSPy Documentation: https://dspy-docs.vercel.app/
- agentskills.io Specification: https://agentskills.io/
- Project README: `docs/overview.md`
- DSPy Configuration: `config/config.yaml`

---

*This plan should be reviewed and approved before implementation. Changes to scope should be documented here.*
