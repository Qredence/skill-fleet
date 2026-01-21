# Skill Template & Python Process Update (v0.2 - Jan 2026)

## Overview

Updated the skill creation template and Python DSPy signatures to reflect the improved approach demonstrated by the `ty-type-checker` skill. Changes enforce agentskills.io compliance, improve agent discovery through CSO (Claude Search Optimization), and separate concerns between discovery and taxonomy.

## What Changed

### 1. SKILL.md Template (`config/templates/SKILL_md_template.md`)

#### Frontmatter (MINIMAL)
**Before**: Supported optional metadata block in frontmatter
```yaml
---
name: skill-name
description: Description
metadata:
  skill_id: category/skill-name
  version: 1.0.0
  type: technical
  weight: medium
---
```

**After**: Minimal frontmatter only (v0.2 standard)
```yaml
---
name: skill-name
description: Use when [triggering conditions]
---
```

**Why**: 
- Separates concerns: SKILL.md is for agent discovery, metadata.json for tooling
- CSO (Claude Search Optimization): Description directly influences agent search behavior
- Simpler, cleaner, easier to maintain

#### New Section: Real-World Impact
Added optional "Real-World Impact" section before Validation:
- Describes measurable outcomes (CI/CD improvements, bug reduction, performance gains)
- Helps agents understand practical value
- Optional but recommended for all skills

#### Updated Validation Section
Now includes:
- `uv run skill-fleet validate` command (specific path)
- `metadata.json` validation example
- `skill-fleet generate-xml` for discovery
- `skill-fleet promote` for draft→taxonomy
- Version note: "v0.2 Changes" callout

### 2. Phase 1: Understanding (`src/skill_fleet/core/dspy/signatures/phase1_understanding.py`)

#### SynthesizePlan Signature
Added docstring note:
- **CSO Emphasis**: Description must focus on WHEN to use (symptoms, triggers), NOT workflow
- **Minimal Frontmatter**: No metadata block in generated SKILL.md
- **Real-World Impact**: Content plan should include this section

Updated `skill_metadata` OutputField:
- Emphasized CSO-optimized description: "Use when... [symptoms/triggers]"
- Noted description is CRITICAL for agent discovery
- Explicit: "focus on WHEN to use, not WHAT it teaches"

### 3. Phase 2: Generation (`src/skill_fleet/core/dspy/signatures/phase2_generation.py`)

#### GenerateSkillContent Signature
Added comprehensive docstring:
- **v0.2 Notation**: Golden Standard updated Jan 2026
- **Frontmatter Rules**: Explicit (name + description ONLY)
- **Required Sections**: When to Use, Quick Start, Core Patterns, Real-World Impact, Validation
- **Quality Indicators**: Core principle, Iron Law style, Good/Bad contrasts

Updated `skill_content` OutputField:
- Emphasized minimal YAML frontmatter
- Added Real-World Impact requirement
- Added Validation section with CLI commands
- Specified 6 required SKILL.md components

### 4. Phase 3: Validation (`src/skill_fleet/core/dspy/modules/phase3_validation.py`)

#### _canonicalize_skill_md_frontmatter Function
**Before**: Built extended_meta block containing skill_id, version, type, weight
```python
if extended_meta:
    frontmatter["metadata"] = extended_meta
```

**After**: Minimal frontmatter only
```python
# Build minimal frontmatter (v0.2: name + description ONLY)
# All tooling metadata belongs in metadata.json (separate concerns)
# This keeps SKILL.md optimized for agent discovery (CSO)
frontmatter: dict[str, Any] = {
    "name": name,
    "description": description[:1024],
}
```

**Why**:
- TaxonomyManager handles metadata.json separately (still creates it)
- Validation normalizes SKILL.md frontmatter to minimal form
- Ensures consistency across all generated skills

## Implementation: ty-type-checker Example

The `ty-type-checker` skill in `skills/_drafts/2c7046b4-1f5d-4574-828a-f92f0ec6db6e/` demonstrates the new approach:

### SKILL.md Changes
```yaml
---
name: ty-type-checker
description: Use when type checking is slow, migrating from Mypy/Pyright, or integrating with the Ruff/UV ecosystem without complex plugin dependencies.
---
```
- ✅ Minimal frontmatter (2 fields only)
- ✅ CSO-optimized description (triggers, not process)
- ✅ Moved metadata to metadata.json

### New Sections
- ✅ Real-World Impact: "CI/CD Speed", "Developer Confidence", "Monorepo Scale"
- ✅ Security Iron Law: "NO untrusted pyproject.toml configs without review"
- ✅ Validation: `uv run skill-fleet validate`, `uv run skill-fleet promote`

### metadata.json
Contains all tooling data:
- `skill_id`, `version`, `type`, `weight`, `load_priority`
- `capabilities`, `tags`, `category`
- Evolution tracking: `created_at`, `last_modified`, `evolution` block

## Impact on Skill Creation Process

### For DSPy Workflows
1. **Phase 1**: Generates CSO-optimized description (WHEN to use, symptoms)
2. **Phase 2**: Generates SKILL.md with minimal frontmatter + Real-World Impact
3. **Phase 3**: Normalizes frontmatter to minimal form, ensures metadata.json created

### For Validators
- Frontmatter MUST have: `name`, `description` (only)
- Optional in frontmatter: `license` (moved to metadata.json)
- No `metadata` block in SKILL.md (validation will reject it)
- metadata.json handled separately by TaxonomyManager

### For Agents (Claude)
- CSO description enables better skill discovery (triggered on symptoms, not summaries)
- Smaller frontmatter = less context bloat
- Real-World Impact section clarifies practical value
- Consistent format across all skills

## Migration Path

### For New Skills
- Use updated template automatically
- DSPy signatures enforce new patterns
- No action needed—creation pipeline is updated

### For Existing Skills (Manual)
1. Remove `metadata:` block from SKILL.md frontmatter
2. Create/update `metadata.json` with tooling data
3. Rewrite description to focus on WHEN to use (symptoms, triggers)
4. Add Real-World Impact section (optional but recommended)
5. Run: `uv run skill-fleet migrate --dry-run` to preview
6. Run: `uv run skill-fleet migrate` to apply

## Files Modified

### Templates
- ✅ `config/templates/SKILL_md_template.md` - Minimal frontmatter, Real-World Impact, v0.2 notes
- ✅ `config/templates/metadata_template.json` - No changes (already correct)

### Python Signatures
- ✅ `src/skill_fleet/core/dspy/signatures/phase1_understanding.py` - SynthesizePlan updated with CSO, v0.2 notes
- ✅ `src/skill_fleet/core/dspy/signatures/phase2_generation.py` - GenerateSkillContent updated, minimal frontmatter emphasis
- ✅ `src/skill_fleet/core/dspy/modules/phase3_validation.py` - _canonicalize_skill_md_frontmatter simplified

## Quality Standards

### CSO (Claude Search Optimization)
- Description = "Use when [symptoms/triggers]"
- NOT "This skill teaches X"
- NOT "Use when implementing X" (process, not condition)
- Examples:
  - ✅ "Use when type checking is slow, migrating from Mypy, or integrating with Ruff/UV"
  - ❌ "Use when implementing, configuring, or optimizing the 'ty' type checker"

### Real-World Impact
- Measurable, concrete outcomes
- Format: "Area: specific improvement (quantified where possible)"
- Examples:
  - ✅ "CI/CD Speed: Reduces pre-commit latency by 5-10x"
  - ✅ "Developer Confidence: Catches 30%+ more issues in typical migrations"
  - ❌ "Helps with performance" (vague)

### Minimal Frontmatter
- REQUIRED: `name`, `description`
- FORBIDDEN: `metadata` block, `skill_id`, `version`, `type`, `weight`
- OPTIONAL: `license`, `compatibility` (if used, move to metadata.json)

## Testing

All changes are integrated into DSPy skill creation pipeline:
1. Phase 1 signatures guide CSO-optimized descriptions
2. Phase 2 signatures generate minimal frontmatter SKILL.md
3. Phase 3 validation normalizes existing frontmatter

No breaking changes—existing skills continue to work; new skills follow v0.2 standards.

## References

- **agentskills.io spec**: https://agentskills.io
- **CSO guidance**: See `config/templates/SKILL_md_template.md` lines 57-80
- **Example skill**: `skills/_drafts/2c7046b4-1f5d-4574-828a-f92f0ec6db6e/python/ty-type-checker/`
- **AGENTS.md**: Full DSPy and architecture documentation
- **Previous fixes**: SKILL.md compliance improvements for quality score (0.70→0.85 target)

---

**Version**: 0.2 | **Date**: Jan 20, 2026 | **Status**: Live in DSPy pipeline
