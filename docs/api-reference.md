# API Reference

Python API reference for programmatic interaction with the skill-fleet system.

## Core Classes

### TaxonomyManager

Central class for managing the skills taxonomy.

**Import:**
```python
from pathlib import Path
from skill_fleet.taxonomy.manager import TaxonomyManager
```

**Constructor:**
```python
TaxonomyManager(skills_root: Path)
```

**Parameters:**
- `skills_root` (Path): Root directory of the skills taxonomy

**Example:**
```python
from pathlib import Path
from skill_fleet.taxonomy.manager import TaxonomyManager

manager = TaxonomyManager(
    Path("skills")
)
```

---

#### Methods

##### `generate_available_skills_xml()`

Generate `<available_skills>` XML for agent context injection following agentskills.io standard.

**Signature:**
```python
def generate_available_skills_xml(self, user_id: str | None = None) -> str
```

**Parameters:**
- `user_id` (str | None): Optional user ID to filter skills (not yet implemented)

**Returns:**
- `str`: XML string in agentskills.io format

**Example:**
```python
# Generate XML for all skills
xml = manager.generate_available_skills_xml()

# Write to file
Path("available_skills.xml").write_text(xml)

# Future: Filter by user
xml = manager.generate_available_skills_xml(user_id="developer_123")
```

**Output Format:**
```xml
<available_skills>
  <skill>
    <name>python-decorators</name>
    <description>Ability to design, implement...</description>
    <location>/path/to/SKILL.md</location>
  </skill>
  <!-- more skills -->
</available_skills>
```

---

##### `load_skill()`

Load a skill's metadata from the taxonomy.

**Signature:**
```python
def load_skill(self, skill_id: str) -> SkillMetadata
```

**Parameters:**
- `skill_id` (str): Path-style skill identifier (e.g., `technical_skills/programming/languages/python`)

**Returns:**
- `SkillMetadata`: Skill metadata object

**Raises:**
- `FileNotFoundError`: If skill doesn't exist

**Example:**
```python
metadata = manager.load_skill("technical_skills/programming/languages/python/decorators")

print(f"Name: {metadata.name}")
print(f"Version: {metadata.version}")
print(f"Capabilities: {metadata.capabilities}")
```

---

##### `get_skill_path()`

Get the file system path for a skill.

**Signature:**
```python
def get_skill_path(self, skill_id: str) -> Path
```

**Parameters:**
- `skill_id` (str): Path-style skill identifier

**Returns:**
- `Path`: Path to the skill directory or file

**Example:**
```python
skill_path = manager.get_skill_path("technical_skills/programming/languages/python")
print(skill_path)  # /path/to/skills/technical_skills/programming/languages/python
```

---

##### `list_all_skills()`

List all skills in the taxonomy.

**Signature:**
```python
def list_all_skills(self) -> list[str]
```

**Returns:**
- `list[str]`: List of skill IDs

**Example:**
```python
all_skills = manager.list_all_skills()
for skill_id in all_skills:
    print(skill_id)
```

---

### SkillValidator

Validates skills against taxonomy standards and agentskills.io compliance.

**Import:**
```python
from pathlib import Path
from skill_fleet.validators.skill_validator import SkillValidator
```

**Constructor:**
```python
SkillValidator(skills_root: Path)
```

**Example:**
```python
validator = SkillValidator(
    Path("skills")
)
```

---

#### Methods

##### `validate_frontmatter()`

Validate SKILL.md has valid agentskills.io-compliant YAML frontmatter.

**Signature:**
```python
def validate_frontmatter(self, skill_md_path: Path) -> ValidationResult
```

**Parameters:**
- `skill_md_path` (Path): Path to SKILL.md file

**Returns:**
- `ValidationResult`: Result object with `passed`, `errors`, and `warnings`

**Validation Checks:**
- Frontmatter exists (starts with `---`)
- Valid YAML syntax
- Required fields present (`name`, `description`)
- Name format: 1-64 chars, kebab-case
- Description length: 1-1024 chars
- Optional fields meet constraints

**Example:**
```python
result = validator.validate_frontmatter(
    Path("path/to/skill/SKILL.md")
)

if result.passed:
    print("✅ Frontmatter is valid")
else:
    print("❌ Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
    
    if result.warnings:
        print("⚠️ Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
```

---

##### `validate_skill()`

Comprehensive validation of an entire skill directory.

**Signature:**
```python
def validate_skill(self, skill_path: Path) -> dict[str, Any]
```

**Parameters:**
- `skill_path` (Path): Path to skill directory

**Returns:**
- `dict`: Validation results with checks, errors, and warnings

**Validates:**
- Directory structure
- Metadata completeness
- Frontmatter compliance
- Dependencies validity
- Examples presence
- Tests presence
- Resources structure

**Example:**
```python
result = validator.validate_skill(Path("path/to/skill"))

print(f"Status: {result['status']}")
print(f"Errors: {len(result['errors'])}")
print(f"Warnings: {len(result['warnings'])}")

for check in result['checks']:
    status_icon = "✅" if check['status'] == 'pass' else "❌"
    print(f"{status_icon} {check['name']}")
```

---

### Migration Functions

Functions for migrating skills to agentskills.io format.

**Import:**
```python
from pathlib import Path
from skill_fleet.migration import (
    migrate_skill_to_agentskills_format,
    migrate_all_skills,
    validate_migration,
)
```

---

#### `migrate_skill_to_agentskills_format()`

Migrate a single skill to agentskills.io format.

**Signature:**
```python
def migrate_skill_to_agentskills_format(
    skill_dir: Path,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict[str, Any]
```

**Parameters:**
- `skill_dir` (Path): Path to skill directory
- `dry_run` (bool): If True, preview changes without writing
- `verbose` (bool): If True, print progress

**Returns:**
- `dict`: Migration result with `success`, `skill_id`, `name`, `changes`, and `errors`

**Example:**
```python
result = migrate_skill_to_agentskills_format(
    Path("path/to/skill"),
    dry_run=True,  # Preview first
    verbose=True
)

if result['success']:
    print(f"✅ Migrated: {result['skill_id']} -> {result['name']}")
    for change in result['changes']:
        print(f"  - {change}")
else:
    print(f"❌ Migration failed:")
    for error in result['errors']:
        print(f"  - {error}")
```

---

#### `migrate_all_skills()`

Migrate all skills in taxonomy to agentskills.io format.

**Signature:**
```python
def migrate_all_skills(
    skills_root: Path,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict[str, Any]
```

**Parameters:**
- `skills_root` (Path): Root of skills taxonomy
- `dry_run` (bool): If True, preview changes without writing
- `verbose` (bool): If True, print progress

**Returns:**
- `dict`: Summary with `total`, `successful`, `failed`, `skipped`, and `results`

**Example:**
```python
summary = migrate_all_skills(
    Path("skills"),
    dry_run=False,
    verbose=True
)

print(f"Total: {summary['total']}")
print(f"Successful: {summary['successful']}")
print(f"Skipped: {summary['skipped']}")
print(f"Failed: {summary['failed']}")

# Process individual results
for result in summary['results']:
    if not result['success']:
        print(f"Failed: {result['skill_id']}")
        for error in result['errors']:
            print(f"  - {error}")
```

---

#### `validate_migration()`

Validate that all skills have valid agentskills.io frontmatter.

**Signature:**
```python
def validate_migration(skills_root: Path) -> dict[str, Any]
```

**Parameters:**
- `skills_root` (Path): Root of skills taxonomy

**Returns:**
- `dict`: Validation results with `total`, `valid`, `invalid`, and `issues`

**Example:**
```python
results = validate_migration(
    Path("skills")
)

print(f"Total skills: {results['total']}")
print(f"Valid: {results['valid']}")
print(f"Invalid: {results['invalid']}")

if results['invalid'] > 0:
    print("\nIssues found:")
    for issue in results['issues']:
        print(f"Skill: {issue['skill']}")
        for error in issue['errors']:
            print(f"  - {error}")
```

---

### Utility Functions

#### `skill_id_to_name()`

Convert path-style skill_id to kebab-case name per agentskills.io spec.

**Import:**
```python
from skill_fleet.taxonomy.manager import skill_id_to_name
```

**Signature:**
```python
def skill_id_to_name(skill_id: str) -> str
```

**Parameters:**
- `skill_id` (str): Path-style skill identifier

**Returns:**
- `str`: Kebab-case name

**Examples:**
```python
name = skill_id_to_name("technical_skills/programming/languages/python/decorators")
# Returns: "python-decorators"

name = skill_id_to_name("_core/reasoning")
# Returns: "core-reasoning"

name = skill_id_to_name("mcp_capabilities/tool_integration")
# Returns: "tool-integration"

name = skill_id_to_name("general/testing")
# Returns: "testing"
```

**Algorithm:**
1. Removes leading underscores from path segments
2. Takes last 1-2 segments for context
3. Converts underscores to hyphens
4. Returns lowercase kebab-case name

---

## Data Classes

### SkillMetadata

Represents skill metadata.

**Fields:**
```python
@dataclass
class SkillMetadata:
    skill_id: str                  # Path-style identifier
    name: str                      # Kebab-case name
    description: str               # 1-1024 char description
    version: str                   # Semantic version
    type: str                      # Skill category
    weight: str                    # Resource intensity
    load_priority: str             # When to load
    dependencies: list[str]        # Required skills
    capabilities: list[str]        # Discrete capabilities
    path: Path                     # File system path
    always_loaded: bool = False    # Load at startup?
```

**Example:**
```python
metadata = manager.load_skill("technical_skills/programming/languages/python/decorators")

print(f"ID: {metadata.skill_id}")
print(f"Name: {metadata.name}")
print(f"Type: {metadata.type}")
print(f"Weight: {metadata.weight}")
print(f"Capabilities: {', '.join(metadata.capabilities)}")
```

---

### ValidationResult

Represents validation result.

**Fields:**
```python
@dataclass
class ValidationResult:
    passed: bool              # Overall pass/fail
    errors: list[str]        # Critical errors
    warnings: list[str]      # Non-critical issues
```

**Example:**
```python
result = validator.validate_frontmatter(Path("path/to/SKILL.md"))

if result.passed:
    print("✅ Validation passed")
else:
    print("❌ Validation failed")
    
for error in result.errors:
    print(f"Error: {error}")
    
for warning in result.warnings:
    print(f"Warning: {warning}")
```

---

## Complete Example

Full workflow using the Python API:

```python
from pathlib import Path
from skill_fleet.taxonomy.manager import TaxonomyManager
from skill_fleet.validators.skill_validator import SkillValidator
from skill_fleet.migration import migrate_all_skills

# Initialize
skills_root = Path("skills")
manager = TaxonomyManager(skills_root)
validator = SkillValidator(skills_root)

# 1. Migrate all skills to agentskills.io format
print("Migrating skills...")
migration_summary = migrate_all_skills(
    skills_root,
    dry_run=False,
    verbose=True
)

if migration_summary['failed'] > 0:
    print(f"⚠️ {migration_summary['failed']} skills failed to migrate")
else:
    print(f"✅ All skills migrated successfully")

# 2. Validate a specific skill
print("\nValidating specific skill...")
skill_id = "technical_skills/programming/languages/python/decorators"
metadata = manager.load_skill(skill_id)

skill_path = manager.get_skill_path(skill_id)
validation_result = validator.validate_skill(skill_path)

if validation_result['status'] == 'pass':
    print(f"✅ {metadata.name} is valid")
else:
    print(f"❌ {metadata.name} has issues:")
    for error in validation_result['errors']:
        print(f"  - {error}")

# 3. Generate XML catalog
print("\nGenerating XML catalog...")
xml = manager.generate_available_skills_xml()

output_path = Path("available_skills.xml")
output_path.write_text(xml)
print(f"✅ XML catalog written to {output_path}")

# 4. List all skills
print("\nAll skills in taxonomy:")
all_skills = manager.list_all_skills()
for skill in all_skills[:5]:  # Show first 5
    meta = manager.load_skill(skill)
    print(f"  - {meta.name} ({skill})")
print(f"  ... and {len(all_skills) - 5} more")
```

---

## Integration Examples

### CI/CD Pipeline

```python
import sys
from pathlib import Path
from skill_fleet.validators.skill_validator import SkillValidator

def validate_all_skills(skills_root: Path) -> int:
    """Validate all skills, return 0 if all pass, 1 otherwise."""
    validator = SkillValidator(skills_root)
    failed = []
    
    for metadata_path in skills_root.rglob("metadata.json"):
        skill_dir = metadata_path.parent
        
        # Skip template/special directories
        if any(part.startswith("_") for part in skill_dir.relative_to(skills_root).parts):
            continue
        
        result = validator.validate_skill(skill_dir)
        if result['status'] != 'pass':
            failed.append(skill_dir)
            print(f"❌ {skill_dir.name}: {len(result['errors'])} errors")
    
    if failed:
        print(f"\n{len(failed)} skills failed validation")
        return 1
    else:
        print(f"\n✅ All skills passed validation")
        return 0

if __name__ == "__main__":
    skills_root = Path("skills")
    sys.exit(validate_all_skills(skills_root))
```

### Custom Migration Script

```python
from pathlib import Path
from skill_fleet.migration import migrate_skill_to_agentskills_format

def migrate_with_custom_logic(skill_dir: Path):
    """Custom migration with additional processing."""
    
    # Pre-migration custom logic
    print(f"Processing {skill_dir.name}...")
    
    # Run migration
    result = migrate_skill_to_agentskills_format(
        skill_dir,
        dry_run=False,
        verbose=False
    )
    
    if result['success']:
        # Post-migration custom logic
        skill_md = skill_dir / "SKILL.md"
        content = skill_md.read_text()
        
        # Add custom footer
        if "## References" not in content:
            content += "\n\n## References\n\n- Internal wiki: https://wiki.example.com\n"
            skill_md.write_text(content)
        
        print(f"✅ {result['name']} migrated with custom processing")
    else:
        print(f"❌ {result['skill_id']} failed: {result['errors']}")

# Usage
skills_root = Path("skills")
for skill_dir in skills_root.rglob("metadata.json"):
    migrate_with_custom_logic(skill_dir.parent)
```

---

## Error Handling

### Common Exceptions

```python
from pathlib import Path
from skill_fleet.taxonomy.manager import TaxonomyManager

manager = TaxonomyManager(Path("skills"))

try:
    metadata = manager.load_skill("nonexistent/skill")
except FileNotFoundError as e:
    print(f"Skill not found: {e}")

try:
    metadata = manager.load_skill("invalid_json/skill")
except json.JSONDecodeError as e:
    print(f"Invalid JSON in metadata: {e}")

try:
    yaml_content = Path("invalid.yaml").read_text()
    import yaml
    data = yaml.safe_load(yaml_content)
except yaml.YAMLError as e:
    print(f"Invalid YAML: {e}")
```

---

## Type Hints

All functions and methods include comprehensive type hints for IDE support:

```python
from pathlib import Path
from typing import Any

def migrate_skill_to_agentskills_format(
    skill_dir: Path,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict[str, Any]:
    ...

def generate_available_skills_xml(
    self,
    user_id: str | None = None
) -> str:
    ...
```

Use with mypy for static type checking:
```bash
mypy src/skill_fleet/
```

---

## Further Reading

- [CLI Reference](cli-reference.md) - Command-line equivalents
- [agentskills.io Compliance](agentskills-compliance.md) - Specification details
- [Skill Creator Guide](skill-creator-guide.md) - Creating skills programmatically
