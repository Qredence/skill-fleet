# Skill Format Migration Guide: v1 → v2 Golden Standard

This guide documents the changes between v1 and v2 skill formats and provides instructions for migrating existing skills.

## Overview

The v2 Golden Standard simplifies skill structure while introducing a progressive disclosure pattern that organizes complex content into subdirectories.

### Key Changes

| Aspect                   | v1 Format                                       | v2 Format                                                       |
| ------------------------ | ----------------------------------------------- | --------------------------------------------------------------- |
| **Required Files**       | `SKILL.md` + `metadata.json`                    | `SKILL.md` only                                                 |
| **Required Directories** | `assets/`, `examples/`                          | **None** (all optional)                                         |
| **Optional Directories** | N/A                                             | `references/`, `guides/`, `templates/`, `scripts/`, `examples/` |
| **Frontmatter**          | Complex (skill_id, version, type, weight, etc.) | Simplified (`name`, `description`, optional `allowed-tools`)    |
| **Required Sections**    | Overview, When to Use, Quick Reference          | Overview, **When to Use This Skill**, Quick Start (recommended) |
| **Skill Styles**         | Not defined                                     | `navigation_hub`, `comprehensive`, `minimal`                    |

## Minimal Skill Structure

The simplest valid v2 skill is just a directory with a single `SKILL.md` file:

```
skill-name/
└── SKILL.md
```

This is perfect for guideline skills like `vibe-coding` or `frontend-ui-integration` where all content fits naturally in a single markdown file. Subdirectories are **only created when there's actual content that benefits from them**.

## Migration Strategy

### Option A: Update to v2 (Recommended for New Skills)

New skills should follow the v2 format:

1. Single `SKILL.md` with simplified frontmatter
2. Use subdirectories **only when needed** for progressive disclosure
3. Include "When to Use This Skill" section

### Option B: Grandfather Existing Skills

Existing v1 skills remain valid and will continue to work. The system supports both formats:

- v1 skills with `metadata.json` are fully supported
- v2 skills without `metadata.json` are also valid

## Frontmatter Changes

### v1 Frontmatter (Deprecated but Supported)

```yaml
---
name: python-async
description: Python async programming patterns
metadata:
  skill_id: python/async
  version: 1.0.0
  type: technical
  weight: medium
  load_priority: on_demand
  category: python
  keywords: [async, await, asyncio]
  dependencies: [python/basics]
  capabilities: [async_syntax, event_loops]
  scope: "Covers asyncio. Does NOT cover threading."
  see_also: [python/threading]
license: MIT
---
```

### v2 Frontmatter (Recommended)

```yaml
---
name: python-async
description: Use when implementing concurrent Python code with asyncio, managing event loops, or building async APIs.
allowed-tools:
  - python_repl
  - web_search
---
```

**Key Differences:**

- `metadata` block is optional (validator extracts from content)
- `description` should follow "Use when..." pattern
- `allowed-tools` is new for MCP tool restrictions

## Directory Structure Changes

### v1 Structure

```
skill-name/
├── SKILL.md
├── metadata.json
├── assets/
│   └── config-file.yaml
└── examples/
    └── example_1.py
```

### v2 Minimal Structure (Most Common)

```
skill-name/
└── SKILL.md          # Everything in one file
```

### v2 Structure with Subdirectories (When Needed)

```
skill-name/
├── SKILL.md
├── references/       # Deep-dive documentation
│   └── advanced.md
├── guides/          # Step-by-step procedures
│   └── setup.md
├── templates/       # Reusable code templates
│   └── starter.py
├── scripts/         # Automation scripts
│   └── setup.sh
└── examples/        # Usage examples (retained from v1)
    └── basic.py
```

### Valid Subdirectories

Only these subdirectories are recognized:

- `references/` - Deep-dive documentation, API references
- `guides/` - Step-by-step procedures, tutorials
- `templates/` - Reusable code snippets, boilerplate
- `scripts/` - Automation scripts, tooling
- `examples/` - Usage examples, sample code

## When to Add Subdirectories

Subdirectories should be added **only when they provide clear organizational benefit**:

### Add Subdirectories When:

- You have multiple long-form reference documents (>2000 words each)
- You need reusable templates that change independently
- You have step-by-step tutorials that would bloat the main file
- Scripts need to be executable or version-controlled separately

### Keep Everything in SKILL.md When:

- The skill is primarily guidance/principles (like `vibe-coding`)
- All content fits comfortably in one readable file
- The skill is focused on a single concept
- You're creating a first draft (add subdirectories later if needed)

**Rule of Thumb:** Start with just `SKILL.md`. Add subdirectories only when you find yourself wanting to link to separate detailed content.

## Skill Styles

v2 introduces three skill styles:

### Navigation Hub

Short SKILL.md (~2000-4000 chars) that acts as an entry point, with most content in subdirectories.

**Characteristics:**

- Concise main file with overview and navigation
- Multiple references to subdirectory files
- Good for complex topics with many aspects

**Example:**

```markdown
---
name: dspy-basics
description: Core DSPy fundamentals. Use when creating signatures or building simple DSPy programs.
---

# DSPy Basics

## Quick Start

[Quick code examples here]

## When to Use This Skill

- Creating new signatures
- Building simple programs

## Core Concepts

### Signatures

See [references/signatures.md](references/signatures.md) for details.

### Modules

See [references/modules.md](references/modules.md) for details.
```

### Comprehensive

Long, self-contained SKILL.md (>8000 chars) with all content inline.

**Characteristics:**

- All content in single file
- Detailed sections with extensive examples
- Good for reference-heavy topics

### Minimal

Focused SKILL.md (~3000-5000 chars) covering a specific capability.

**Characteristics:**

- Single responsibility
- No subdirectories needed
- Good for atomic skills

## Required Sections in v2

### 1. "When to Use This Skill" (Required)

The section header must include "When to Use":

```markdown
## When to Use This Skill

Use this skill when:

- Building async APIs with FastAPI
- Implementing concurrent data processing
- Managing WebSocket connections
```

### 2. Quick Start (Recommended)

```markdown
## Quick Start

### Basic Example

```python
import asyncio

async def main():
    await asyncio.sleep(1)
    return "done"
```
```

### 3. Overview (Required)

```markdown
## Overview

This skill covers Python's asyncio framework for asynchronous programming.
```

## Migration Commands

### Validate a Skill

```bash
# Check if skill meets v2 requirements
uv run skill-fleet validate path/to/skill

# Dry-run migration
uv run skill-fleet migrate --dry-run
```

### Generate Training Data

```bash
# Regenerate training data from .skills golden examples
uv run python scripts/regenerate_training_data.py
```

## Validation Changes

### v1 Validation (Still Supported)

- Requires `SKILL.md` + `metadata.json`
- Validates metadata fields (skill_id, version, type, etc.)
- Checks for Overview section

### v2 Validation

- Requires `SKILL.md` only
- `metadata.json` is optional
- **Requires "When to Use" section**
- Validates subdirectory structure
- Checks for progressive disclosure pattern

## Quality Scoring Changes

v2 adds new quality metrics:

| Metric                        | Weight | Description                               |
| ----------------------------- | ------ | ----------------------------------------- |
| `has_when_to_use_section`     | 6%     | Required "When to Use This Skill" section |
| `has_quick_start`             | 4%     | Recommended Quick Start section           |
| `uses_progressive_disclosure` | 4%     | References to subdirectory files          |

## Backward Compatibility

The system maintains full backward compatibility:

1. **v1 skills continue to work** - No forced migration
2. **Validation accepts both formats** - Detects format automatically
3. **Mixed taxonomy supported** - v1 and v2 skills can coexist
4. **Gradual migration** - Update skills as you edit them

## Dual Metadata Source Strategy

**The system supports reading metadata from both sources simultaneously:**

### Priority Order

1. **Frontmatter (highest priority)** - SKILL.md YAML frontmatter
2. **metadata.json** - Extended metadata file (v1 style)
3. **Inferred values** - Generated from skill_id or file structure

### How It Works

When loading a skill:

```python
# TaxonomyManager uses this priority:
name = frontmatter.get("name") or metadata_json.get("name") or skill_id_to_name(skill_id)
description = frontmatter.get("description") or metadata_json.get("description", "")
version = metadata_json.get("version", "1.0.0")
type = metadata_json.get("type", "technical")
```

### Mixed v1/v2 Skills

A skill can have both frontmatter (in SKILL.md) and metadata.json:

```yaml
# SKILL.md frontmatter (takes precedence)
---
name: python-decorators
description: Use when implementing cross-cutting concerns.
---
```

```json
// metadata.json (provides extended fields, name/description ignored if in frontmatter)
{
  "skill_id": "python/decorators",
  "version": "2.0.0",
  "type": "technical",
  "weight": "lightweight",
  "dependencies": ["python/basics"]
}
```

**Resulting metadata:**
- `name`: "python-decorators" (from frontmatter)
- `description`: "Use when implementing cross-cutting concerns." (from frontmatter)
- `version`: "2.0.0" (from metadata.json)
- `type`: "technical" (from metadata.json)
- `skill_id`, `weight`, `dependencies`: from metadata.json

### Best Practices

**For New Skills (v2 only):**
- Only SKILL.md with frontmatter
- Use `allowed-tools` in frontmatter for MCP restrictions
- No metadata.json needed

**For Existing Skills (v1 with upgrades):**
- Keep metadata.json for extended fields (version, type, weight, dependencies)
- Add frontmatter to SKILL.md for agentskills.io compliance
- Frontmatter name/description will override metadata.json

**For Fully Migrated Skills:**
- All metadata in frontmatter
- No metadata.json file
- Follow v2 Golden Standard structure

### When to Delete metadata.json

You can safely delete `metadata.json` when:

1. All essential fields are in frontmatter:
   - `name` in frontmatter
   - `description` in frontmatter
   - Extended fields (version, type, weight) in frontmatter `metadata:` block
2. Dependencies are documented in SKILL.md body
3. You don't need extended taxonomy management (always_loaded flag, etc.)

**Migration command to check readiness:**
```bash
# Validate to see if all fields are present
uv run skill-fleet validate path/to/skill
```

If validation passes with only warnings (no errors about missing fields), you can delete metadata.json.

## Example: Converting a v1 Skill

### Before (v1)

```
python-decorators/
├── SKILL.md
├── metadata.json
└── examples/
    └── basic.py
```

**metadata.json:**

```json
{
  "skill_id": "python/decorators",
  "name": "python-decorators",
  "version": "1.0.0",
  "type": "technical",
  "weight": "lightweight"
}
```

### After (v2)

```
python-decorators/
├── SKILL.md
├── references/
│   └── advanced-patterns.md
└── examples/
    └── basic.py
```

**SKILL.md frontmatter:**

```yaml
---
name: python-decorators
description: Use when implementing cross-cutting concerns, creating reusable function wrappers, or understanding Python metaprogramming.
---
```

## Troubleshooting

### "Missing When to Use section"

Add a section with the header:

```markdown
## When to Use This Skill
```

### "Invalid subdirectory"

Only use these subdirectory names:

- `references/`
- `guides/`
- `templates/`
- `scripts/`
- `examples/`

### "Validation passed with warnings"

Common warnings:

- Missing Quick Start section (recommended but not required)
- No progressive disclosure (fine for minimal skills)
- Low code example count (add more examples)

## Resources

- [SKILL_md_template.md](../../config/templates/SKILL_md_template.md) - v2 template
- [skill_template.json](../../config/templates/skill_template.json) - Directory structure
- [Golden Examples](../../.skills/) - Reference implementations
