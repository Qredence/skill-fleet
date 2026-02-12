# Validation Architecture

## Overview

Skill validation ensures agentskills.io compliance through a multi-layered approach combining rule-based checks (fast) and LLM-based validation (comprehensive).

## Validation Layers

```
Layer 1: Structure Validation
- Required files/directories
- Naming conventions
- Security checks (symlinks, path traversal)

Layer 2: Metadata Validation
- Field presence and types
- Format validation (semver, kebab-case)
- Value constraints (enums)

Layer 3: Documentation Validation
- Required sections ("When to Use")
- YAML frontmatter compliance
- Content structure

Layer 4: Subdirectory Validation
- v2 Golden Standard structure
- Legacy directory warnings

Layer 5: Quality Assessment
- Word count analysis
- Verbosity scoring
- Trigger phrase coverage

Layer 6: LLM-Based Validation (optional)
- Semantic quality evaluation
- agentskills.io compliance
- Improvement suggestions
```

## SkillValidator

**Location:** `src/skill_fleet/validators/skill_validator.py:62`

Primary rule-based validator implementing v2 Golden Standard.

### v2 Golden Standard Changes

| Aspect | Legacy | v2 Golden Standard |
|--------|--------|-------------------|
| Required files | metadata.json, SKILL.md | SKILL.md only |
| Required directories | capabilities/, resources/ | None (lazy creation) |
| Required sections | Overview, Capabilities | "When to Use" |
| Subdirectories | capabilities/, resources/ | references/, guides/, templates/ |
| Metadata location | metadata.json | YAML frontmatter in SKILL.md |

## Layer 1: Structure Validation

Validates file/directory presence and security.

**Security Checks:**
- Path traversal prevention via `resolve_path_within_root()`
- Symlink rejection for security
- Component validation via `_is_safe_path_component()`

## Layer 2: Metadata Validation

Validates metadata fields and formats:
- Skill ID format (path-style)
- Semantic versioning
- Enum validation (type, weight, load_priority)
- Weight-capability balance

## Layer 3: Documentation Validation

Validates SKILL.md content structure.

### Required Sections (v2)

- "## When to Use" - **REQUIRED**
- "## Quick Start" or "## Quick Examples" - **RECOMMENDED**
- Code blocks presence
- Minimum content length (100 chars)

### Frontmatter Validation

Required fields per agentskills.io spec:
- `name`: 1-64 chars, kebab-case
- `description`: 1-1024 chars

Optional fields:
- `license`: string
- `compatibility`: max 500 chars
- `metadata`: key-value mapping
- `allowed-tools`: space-delimited string

## Layer 4: Subdirectory Validation

Validates v2 Golden Standard directory structure.

**Valid subdirectories:**
- `references/` - Deep technical documentation
- `guides/` - Step-by-step workflows
- `templates/` - Boilerplate code
- `scripts/` - Runnable utilities
- `examples/` - Demo projects
- `assets/`, `images/`, `static/` - Documentation assets

**Legacy (deprecated):**
- `capabilities/`
- `resources/`
- `tests/` (grandfathered)

## Layer 5: Quality Assessment

**Location:** `ValidationWorkflow` (`core/workflows/skill_creation/validation.py`)

**Quality Metrics:**

| Metric | Description | Target |
|--------|-------------|--------|
| `word_count` | Total words | 500-5000 |
| `verbosity_score` | 0=concise, 1=verbose | < 0.7 |
| `trigger_coverage` | % trigger phrases covered | > 0.8 |
| `overall_score` | Weighted composite | > 0.75 |

## Layer 6: LLM-Based Validation

**Module:** `ValidateSkillModule` (`core/modules/validation/validate_skill.py`)

DSPy-based semantic validation using `ValidateSkillStructure` signature.

## ValidationResult Structure

```python
class ValidationReport(BaseModel):
    passed: bool
    status: Literal["passed", "failed", "warnings"]
    score: float  # 0.0 - 1.0
    errors: list[str]
    warnings: list[str]
    checks_performed: list[str]

    # Structure validation
    structure_valid: bool
    name_errors: list[str]
    description_errors: list[str]
    security_issues: list[str]

    # Quality metrics
    word_count: int
    size_assessment: str
    verbosity_score: float
```

## Security Validation

### Path Traversal Prevention

```python
def _is_safe_path_component(self, component: str) -> bool:
    if not component:
        return False
    if "\0" in component:
        return False
    if "/" in component or "\\" in component:
        return False
    if component in (".", ".."):
        return False
    if ".." in component:
        return False
    return bool(self._SAFE_PATH_PATTERN.fullmatch(component))
```

### Symlink Protection

Files must not be symlinks (prevents reading outside skills_root).

## CLI Integration

```bash
# Validate a skill
uv run skill-fleet validate skills/_drafts/<job_id>/<skill-name>

# Validate without LLM (faster)
uv run skill-fleet validate <skill_path> --no-llm

# JSON output
uv run skill-fleet validate <skill_path> --json
```

## References

- `src/skill_fleet/validators/skill_validator.py`
- `src/skill_fleet/core/workflows/skill_creation/validation.py`
- `src/skill_fleet/core/modules/validation/`
