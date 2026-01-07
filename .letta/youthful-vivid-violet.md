# Implementation Plan: agentskills.io Compliance for skills-fleet

## Overview

This plan transforms the skills-fleet system to be fully compliant with the [agentskills.io](https://agentskills.io/specification) standard while preserving the valuable extended features (DSPy workflow, hierarchical taxonomy, analytics).

## Goal

Make skills-fleet skills discoverable and usable by any Agent Skills-compatible agent (Claude Code, Claude.ai, etc.) while maintaining backward compatibility with existing functionality.

---

## Phase 1: Core Format Changes (SKILL.md + Metadata)

### 1.1 Update SKILL.md Template with YAML Frontmatter

**File**: `src/agentic_fleet/agentic_skills_system/config/templates/SKILL_md_template.md`

**Changes**:
- Add required YAML frontmatter (`name`, `description`)
- Add optional metadata fields
- Keep existing rich content structure

**New Format**:
```markdown
---
name: {{skill_name_kebab}}
description: {{description}}
metadata:
  skill_id: {{skill_id}}
  version: {{version}}
  type: {{type}}
  weight: {{weight}}
---

# {{skill_name}}

## Overview
{{overview_description}}

## Capabilities
...
```

### 1.2 Add Name Conversion Utilities

**File**: `src/agentic_fleet/agentic_skills_system/taxonomy/manager.py`

**New Functions**:
```python
def skill_id_to_name(skill_id: str) -> str:
    """Convert path-style skill_id to kebab-case name.
    
    'technical_skills/programming/languages/python/decorators' -> 'python-decorators'
    """

def name_to_skill_id(name: str, taxonomy_path: str) -> str:
    """Convert kebab-case name back to skill_id given taxonomy context."""
```

### 1.3 Update TaxonomyManager.register_skill()

**File**: `src/agentic_fleet/agentic_skills_system/taxonomy/manager.py`

**Changes**:
- Generate SKILL.md with YAML frontmatter
- Keep metadata.json for extended features (backward compatible)
- Add `name` field derived from skill_id

---

## Phase 2: Discoverability Implementation

### 2.1 Add XML Generation for Agent Prompts

**File**: `src/agentic_fleet/agentic_skills_system/taxonomy/manager.py`

**New Method**:
```python
def generate_available_skills_xml(self, user_id: str | None = None) -> str:
    """Generate <available_skills> XML for agent context injection.
    
    Returns:
        XML string following agentskills.io format:
        <available_skills>
          <skill>
            <name>python-decorators</name>
            <description>Design and implement decorators...</description>
            <location>/path/to/SKILL.md</location>
          </skill>
          ...
        </available_skills>
    """
```

### 2.2 Add Frontmatter Parsing

**File**: `src/agentic_fleet/agentic_skills_system/taxonomy/manager.py`

**New Method**:
```python
def parse_skill_frontmatter(self, skill_path: Path) -> dict:
    """Parse YAML frontmatter from SKILL.md file.
    
    Used for lightweight metadata loading at startup.
    """
```

### 2.3 Update Skill Loading to Use Frontmatter

**Changes to `_load_skill_dir_metadata()`**:
- First try to parse frontmatter from SKILL.md
- Fall back to metadata.json for extended fields
- Merge both for complete metadata

---

## Phase 3: Validator Updates

### 3.1 Update SkillValidator for agentskills.io Compliance

**File**: `src/agentic_fleet/agentic_skills_system/validators/skill_validator.py`

**New Validations**:
```python
def validate_frontmatter(self, skill_md_path: Path) -> ValidationResult:
    """Validate SKILL.md has valid agentskills.io frontmatter.
    
    Checks:
    - name: 1-64 chars, lowercase, hyphens only
    - description: 1-1024 chars, non-empty
    - Optional: license, compatibility, metadata
    """

def validate_name_format(self, name: str) -> ValidationResult:
    """Validate name follows agentskills.io naming convention.
    
    Pattern: ^[a-z0-9]+(-[a-z0-9]+)*$
    """
```

**Update existing validations**:
- `validate_documentation()` - check for frontmatter presence
- `validate_complete()` - include frontmatter validation

---

## Phase 4: DSPy Signature Updates

### 4.1 Update EditSkillContent Signature

**File**: `src/agentic_fleet/agentic_skills_system/workflow/signatures.py`

**Changes to `EditSkillContent`**:
```python
skill_content: str = dspy.OutputField(
    desc="""Full SKILL.md content WITH YAML frontmatter. Format:
    ---
    name: kebab-case-name (derived from taxonomy path)
    description: 1-2 sentence description of what skill does and when to use it
    metadata:
      skill_id: full/taxonomy/path
      version: 1.0.0
    ---
    
    # Skill Title
    
    ## Overview
    ...
    """
)
```

### 4.2 Update PlanSkillStructure Signature

**File**: `src/agentic_fleet/agentic_skills_system/workflow/signatures.py`

**Add `skill_name` output**:
```python
skill_name: str = dspy.OutputField(
    desc="Kebab-case name for the skill (e.g., 'python-decorators'). Max 64 chars, lowercase letters/numbers/hyphens only."
)
```

---

## Phase 5: Migration of Existing Skills

### 5.1 Create Migration Script

**New File**: `src/agentic_fleet/agentic_skills_system/cli/migrate_skills.py`

**Functionality**:
```python
def migrate_skill_to_agentskills_format(skill_dir: Path) -> bool:
    """Migrate a single skill directory to agentskills.io format.
    
    1. Read existing metadata.json
    2. Generate kebab-case name from skill_id
    3. Read existing SKILL.md content
    4. Prepend YAML frontmatter
    5. Write updated SKILL.md
    6. Keep metadata.json for extended features
    """

def migrate_all_skills(skills_root: Path) -> dict:
    """Migrate all skills in taxonomy to new format."""
```

### 5.2 Add CLI Command

**File**: `src/agentic_fleet/agentic_skills_system/cli.py`

**New Command**:
```bash
uv run skills-fleet migrate --skills-root ./skills
```

---

## Phase 6: Fix Existing Issues

### 6.1 Remove Duplicate Path

**Manual fix**: Remove or relocate `skills/skills/` directory

### 6.2 Fix Metadata Quality

**Update DSPy signatures** to enforce required metadata fields with strict type constraints.

### 6.3 Clean Up Empty Categories

**Options**:
- Remove empty .gitkeep directories
- Or populate with placeholder README explaining the category

---

## File Changes Summary

| File | Type | Changes |
|------|------|---------|
| `taxonomy/manager.py` | Modify | Add XML generation, frontmatter parsing, name conversion |
| `validators/skill_validator.py` | Modify | Add frontmatter validation, name format validation |
| `workflow/signatures.py` | Modify | Update EditSkillContent, add skill_name field |
| `workflow/modules.py` | Modify | Handle new signature outputs |
| `config/templates/SKILL_md_template.md` | Modify | Add YAML frontmatter template |
| `cli.py` | Modify | Add migrate command |
| `cli/migrate_skills.py` | Create | Migration script |

---

## Testing Strategy

1. **Unit Tests**: Validate frontmatter parsing, name conversion, XML generation
2. **Integration Tests**: Create skill end-to-end, verify output format
3. **Migration Tests**: Migrate existing skills, verify no data loss
4. **Compatibility Test**: Load skills in Claude Code (if available)

---

## Rollout Plan

1. **Phase 1-2**: Core changes (format + discoverability) - **Day 1**
2. **Phase 3-4**: Validators + DSPy updates - **Day 1**
3. **Phase 5**: Migration script + migrate existing skills - **Day 2**
4. **Phase 6**: Cleanup + testing - **Day 2**

---

## Backward Compatibility

- **metadata.json preserved**: Extended features (type, weight, dependencies, capabilities, evolution) remain in metadata.json
- **Dual loading**: System loads from both frontmatter (agentskills.io) and metadata.json (extended)
- **No breaking changes**: Existing code continues to work, new format is additive

---

## Success Criteria

1. All SKILL.md files have valid YAML frontmatter
2. `generate_available_skills_xml()` produces valid output
3. Skills pass `skills-ref validate` (agentskills.io reference library)
4. Existing functionality (skill creation, validation, analytics) unchanged
5. All tests pass
