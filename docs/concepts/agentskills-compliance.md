# agentskills.io Compliance Guide

This guide explains how the skill-fleet system implements the [agentskills.io](https://agentskills.io) specification for skill discoverability and standardization.

## Overview

The agentskills.io specification provides a standardized format for defining agent skills that can be discovered, validated, and integrated across different agentic systems.

**Note:** skill-fleet is aligning newly generated skills to match the published spec requirements; some legacy skills may require migration (directory/name alignment) to be strictly spec-compliant.

## What is agentskills.io?

agentskills.io is an open specification that defines:

- **Standard skill format**: YAML frontmatter in SKILL.md files with required metadata
- **Naming conventions**: kebab-case skill names for consistency
- **Discoverability**: XML format for injecting available skills into agent prompts
- **Validation rules**: Constraints on name format, description length, and required fields

## SKILL.md Format with YAML Frontmatter

All skills now include YAML frontmatter at the beginning of their `SKILL.md` files. This frontmatter provides machine-readable metadata about the skill.

### Required Fields

Per the agentskills.io spec, every skill must have:

- **`name`**: Kebab-case identifier (1-64 characters, lowercase alphanumeric + hyphens)
  - Example: `python-decorators`, `fastapi-development`, `code-quality-analysis`
  - **Must match the skill directory name** (the directory that contains `SKILL.md`)
- **`description`**: Human-readable description (1-1024 characters)

### Optional Fields

- **`license`**: License information (e.g., `MIT`, `Apache-2.0`)
- **`compatibility`**: Compatibility notes (max 500 characters)
- **`metadata`**: Extended metadata as key-value pairs
- **`allowed-tools`**: Space-delimited list of allowed tools

### Example Frontmatter

```yaml
---
name: python-decorators
description: Ability to design, implement, and apply higher-order functions to extend or modify the behavior of functions and classes in Python.
metadata:
  skill_id: technical_skills/programming/languages/python/python-decorators
  version: 1.0.0
  type: technical
  weight: medium
---
```

## Kebab-Case Naming Convention

### What is Kebab-Case?

Kebab-case uses lowercase letters with hyphens separating words:
- ✅ `python-decorators`
- ✅ `async-programming`
- ✅ `fastapi-development`
- ❌ `PythonDecorators` (PascalCase)
- ❌ `python_decorators` (snake_case)
- ❌ `pythonDecorators` (camelCase)

### Name Generation

The system automatically generates kebab-case names from path-style skill IDs using the `skill_id_to_name()` function.

Because the spec requires the `name` to match the skill directory name, the function derives the name from the **last path segment**:

```python
# Examples:
'technical_skills/programming/languages/python/python-decorators' → 'python-decorators'
'_core/reasoning' → 'core-reasoning'
'mcp_capabilities/tool_integration' → 'tool-integration'
'task_focus_areas/debug_fix' → 'debug-fix'
```

**Algorithm:**
1. Takes the last path segment (directory name)
2. Removes leading underscores
3. Converts underscores to hyphens
4. Returns lowercase kebab-case name

## Migration Guide

If you have existing skills without YAML frontmatter, use the migration command to update them:

### Migration Command

```bash
# Migrate all skills to agentskills.io format
uv run skill-fleet migrate

# Preview changes without writing (dry-run)
uv run skill-fleet migrate --dry-run

# Specify custom skills directory
uv run skill-fleet migrate --skills-root /path/to/skills

# Output results as JSON
uv run skill-fleet migrate --json
```

### What the Migration Does

The migration tool:

1. **Reads** existing `metadata.json` files
2. **Generates** kebab-case names from skill IDs
3. **Extracts** descriptions (from metadata or SKILL.md content)
4. **Creates** YAML frontmatter with required fields
5. **Prepends** frontmatter to existing SKILL.md content
6. **Updates** `metadata.json` with name and description if missing
7. **Validates** that existing frontmatter is compliant

### Migration Safety

- **Non-destructive**: Preserves existing content
- **Idempotent**: Safe to run multiple times (skips already-migrated skills)
- **Dry-run mode**: Preview changes before applying
- **Validation**: Checks frontmatter validity

### Migration Output

```bash
$ uv run skill-fleet migrate

============================================================
Migrating skills to agentskills.io format
Skills root: /path/to/skills
============================================================

Migrated: technical_skills/programming/languages/python/decorators -> python-decorators
  - Added YAML frontmatter
  - Added name to metadata.json

Migrated: task_focus_areas/debug_fix -> debug-fix
  - Added YAML frontmatter

Skipped: _core/reasoning -> core-reasoning
  - Frontmatter already present and valid

============================================================
Migration Summary:
  Total skills: 15
  Successful: 12
  Skipped (already compliant): 3
  Failed: 0
```

## XML Discoverability

The system can generate an `<available_skills>` XML block that follows the agentskills.io integration standard. This XML is designed to be injected into agent system prompts for skill discovery.

### Generate XML Command

```bash
# Print XML to stdout
uv run skill-fleet generate-xml

# Save to file
uv run skill-fleet generate-xml -o available_skills.xml

# Specify custom skills directory
uv run skill-fleet generate-xml --skills-root /path/to/skills
```

### XML Format

```xml
<available_skills>
  <skill>
    <name>python-decorators</name>
    <description>Ability to design, implement, and apply higher-order functions to extend or modify the behavior of functions and classes in Python.</description>
    <location>/path/to/skills/technical_skills/programming/languages/python/decorators/SKILL.md</location>
  </skill>
  <skill>
    <name>fastapi-development</name>
    <description>Build high-performance async web APIs with FastAPI framework.</description>
    <location>/path/to/skills/technical_skills/programming/web_frameworks/python/fastapi/SKILL.md</location>
  </skill>
  <!-- ... more skills ... -->
</available_skills>
```

### XML Use Cases

1. **Agent Context Injection**: Include in system prompts to inform agents of available skills
2. **Skill Discovery**: Parse to find skills matching specific criteria
3. **Documentation Generation**: Extract metadata for documentation systems
4. **Integration**: Share skill catalog with other agentskills.io-compliant systems

### API Usage

```python
from pathlib import Path
from skill_fleet.taxonomy.manager import TaxonomyManager

# Initialize taxonomy manager
taxonomy = TaxonomyManager(Path("skills"))

# Generate XML
xml = taxonomy.generate_available_skills_xml()

# Optionally filter by user (future feature)
xml = taxonomy.generate_available_skills_xml(user_id="developer_123")

# Write to file
Path("available_skills.xml").write_text(xml)
```

## Validation

The system validates agentskills.io compliance through the `SkillValidator.validate_frontmatter()` method.

### What is Validated

- ✅ SKILL.md file exists
- ✅ Frontmatter is present (starts with `---`)
- ✅ Frontmatter is valid YAML
- ✅ Required fields present (`name`, `description`)
- ✅ Name format is valid kebab-case (1-64 chars, lowercase alphanumeric + hyphens)
- ✅ Description length is 1-1024 characters
- ✅ Optional fields meet constraints (e.g., `compatibility` ≤ 500 chars)

### Validation Command

Validation is part of the standard `validate-skill` command:

```bash
# Validate a single skill
uv run skill-fleet validate-skill skills/technical_skills/programming/languages/python/decorators

# The output includes frontmatter validation results
```

### Validation in Code

```python
from pathlib import Path
from skill_fleet.validators.skill_validator import SkillValidator

validator = SkillValidator(Path("skills"))
result = validator.validate_frontmatter(
    Path("path/to/skill/SKILL.md")
)

if result.passed:
    print("✅ Frontmatter is valid")
else:
    print("❌ Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
```

### Validation Result Structure

```python
@dataclass
class ValidationResult:
    passed: bool
    errors: list[str]
    warnings: list[str]
```

## Extended Metadata

While agentskills.io requires only `name` and `description`, skill-fleet stores extended metadata in the `metadata` field:

```yaml
---
name: python-decorators
description: Ability to design, implement
metadata:
  skill_id: technical_skills/programming/languages/python/decorators
  version: 1.0.0
  type: technical
  weight: medium
  load_priority: task_specific
---
```

### Extended Fields

These fields are specific to skill-fleet but don't violate the agentskills.io spec:

- **`skill_id`**: Internal path-style identifier
- **`version`**: Semantic version (e.g., `1.0.0`)
- **`type`**: Skill category (`cognitive`, `technical`, `domain`, etc.)
- **`weight`**: Resource intensity (`lightweight`, `medium`, `heavyweight`)
- **`load_priority`**: When to load (`always`, `task_specific`, `on_demand`, `dormant`)

These fields are also maintained in `metadata.json` for backward compatibility and internal use.

## Creating New Skills

When using the skill creator workflow, skills are automatically created with compliant frontmatter:

```bash
uv run skill-fleet create-skill --task "Create a Python async programming skill"
```

The generated SKILL.md will include:
- ✅ Valid YAML frontmatter
- ✅ Kebab-case name
- ✅ Appropriate description
- ✅ Extended metadata

### Template Updates

The SKILL.md template (`src/skill_fleet/config/templates/SKILL_md_template.md`) now includes frontmatter placeholders:

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
...
```

## Benefits of Compliance

### Interoperability
- Skills can be shared across different agentskills.io-compliant systems
- Standard format enables tool integration

### Discoverability
- XML generation for agent context injection
- Machine-readable metadata for automated discovery
- Consistent naming for easier search

### Validation
- Automated checks ensure quality
- Prevents malformed skills from entering the taxonomy
- Reduces debugging time

### Maintainability
- Consistent structure across all skills
- Clear separation of metadata and content
- Version tracking in frontmatter

### Community
- Follows open specification
- Enables collaboration across projects
- Standard format familiar to other developers

## Backward Compatibility

The migration maintains backward compatibility:

- ✅ `metadata.json` files are preserved and updated
- ✅ Existing SKILL.md content is kept intact
- ✅ Extended metadata continues to work
- ✅ Non-frontmatter skills still load (with warnings)

## Best Practices

### 1. Use Migration Tool
Always migrate existing skills rather than manually editing:
```bash
uv run skill-fleet migrate
```

### 2. Validate After Creation
Check compliance after creating or modifying skills:
```bash
uv run skill-fleet validate-skill path/to/skill
```

### 3. Keep Descriptions Concise
- Aim for 50-200 characters when possible
- Front-load important information
- Use active voice

### 4. Use Meaningful Names
- Choose names that clearly indicate the skill's purpose
- Be specific: `python-async` not just `async`
- Use domain context: `fastapi-auth` not just `auth`

### 5. Maintain metadata.json
While frontmatter is the source of truth for agentskills.io compliance, `metadata.json` should be kept in sync for internal functionality.

## Troubleshooting

### Issue: Migration fails with "Invalid JSON"
**Solution**: Fix syntax errors in `metadata.json` before migrating

### Issue: Name contains uppercase or underscores
**Solution**: The migration automatically converts to kebab-case. Run with `--dry-run` first to preview changes.

### Issue: Description too long (>1024 chars)
**Solution**: The migration truncates automatically, but manually edit for better quality. Detailed information belongs in the main SKILL.md content.

### Issue: Frontmatter already exists but is invalid
**Solution**: Migration will detect and replace invalid frontmatter. Use `--dry-run` to preview.

### Issue: XML generation shows paths instead of names
**Solution**: Ensure frontmatter is present. Run migration first.

## Technical Details

### TaxonomyManager Methods

```python
class TaxonomyManager:
    def generate_available_skills_xml(self, user_id: str | None = None) -> str:
        """Generate <available_skills> XML for agent context injection.
        
        Returns XML following agentskills.io integration standard.
        """
```

### Migration Functions

```python
def migrate_skill_to_agentskills_format(
    skill_dir: Path,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict[str, Any]:
    """Migrate a single skill to agentskills.io format."""

def migrate_all_skills(
    skills_root: Path,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict[str, Any]:
    """Migrate all skills in taxonomy to agentskills.io format."""

def validate_migration(skills_root: Path) -> dict[str, Any]:
    """Validate that all skills have valid agentskills.io frontmatter."""
```

### Validator Methods

```python
class SkillValidator:
    def validate_frontmatter(self, skill_md_path: Path) -> ValidationResult:
        """Validate SKILL.md has valid agentskills.io compliant YAML frontmatter.
        
        Checks:
        - name: 1-64 chars, lowercase alphanumeric + hyphens
        - description: 1-1024 chars
        - Optional fields meet constraints
        """
```

## References

- **agentskills.io specification**: https://agentskills.io
- **Migration module**: `src/skill_fleet/migration.py`
- **Validator**: `src/skill_fleet/validators/skill_validator.py`
- **Taxonomy manager**: `src/skill_fleet/taxonomy/manager.py`
- **Template**: `src/skill_fleet/config/templates/SKILL_md_template.md`

## Future Enhancements

- [ ] User-specific skill filtering in XML generation
- [ ] Automated compliance checking in CI/CD
- [ ] Integration with agentskills.io registry
- [ ] Support for skill versioning and deprecation
- [ ] Enhanced metadata validation rules

---

## Related Documentation

### System Documentation

| Topic | Description |
|-------|-------------|
| **[System Overview](overview.md)** - High-level architecture and taxonomy |
| **[Getting Started](getting-started/)** - Installation and quick start guide |
| **[CLI Documentation](cli/)** - `migrate` and `generate-xml` command reference |
| **[API Documentation](api/)** - Taxonomy and validation endpoints |

### Validation & Templates

- **[Developer Reference](concepts/developer-reference.md)** - Development workflows
- **Templates** - `config/templates/SKILL_md_template.md`, `config/templates/metadata_template.json`
