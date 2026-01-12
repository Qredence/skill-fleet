# Skills Fleet: Skill Creation Guidelines

## 1. Purpose & Scope

### Why This Document Exists

This document provides **comprehensive, domain-agnostic guidelines** for creating skills in the Skills Fleet system. It bridges the gap between:

- **Theoretical architecture** (covered in `overview.md`)
- **Practical implementation** (this document)
- **CLI operations** (covered in `getting-started/index.md` and `cli-reference.md`)
- **DSPy workflow** (covered in `skill-creator-guide.md`)

### Who Should Use This

- **Skill Creators**: People using the skill-fleet system to create new skills
- **Maintainers**: People evolving the skill taxonomy and quality standards
- **AI Agents**: Systems that need to understand skill creation patterns
- **Reviewers**: People validating and approving new skills

### What Skills Are in This System

Skills are **first-class, versioned artifacts** stored in:

```
skills/
```

Each skill represents a discrete capability that can be:

- **Technical**: Programming languages, frameworks, tools
- **Domain**: Subject matter expertise (medical, legal, etc.)
- **Cognitive**: Thinking patterns and reasoning approaches
- **Tool**: Proficiency with specific software or platforms
- **MCP**: Model Context Protocol capabilities
- **Specialization**: Advanced or focused applications
- **Task Focus**: Problem-solving methodologies
- **Memory**: Memory management patterns

### Relationship to Other Documentation

| Document                           | Purpose                                   | Use When                            |
| ---------------------------------- | ----------------------------------------- | ----------------------------------- |
| `overview.md`                      | System architecture and taxonomy design   | Understanding the big picture       |
| `getting-started/index.md`         | Installation, CLI workflow, and templates | Getting started quickly             |
| `skill-creator-guide.md`           | 6-step DSPy workflow overview             | Understanding automated creation    |
| `**skill-creation-guidelines.md**` | **Practical creation guidelines**         | **Creating or modifying skills**    |
| `cli-reference.md`                 | Complete CLI command reference            | Looking up specific commands        |
| `agentskills-compliance.md`        | agentskills.io specification              | Ensuring cross-system compatibility |

---

## 2. Skill Philosophy & Principles

### Core Principles

#### 1. Skills as First-Class Artifacts

Skills are **stable, versioned entities** on disk, not ephemeral prompts. This means:

- Each skill has a unique `skill_id` (path-style)
- Each skill has semantic versioning (`1.0.0`)
- Each skill has evolution metadata tracking changes
- Skills are discoverable via taxonomy paths
- Skills are composable via dependencies

**Why?** Stability and auditability. You can trace when a skill was created, how it evolved, and what depends on it.

#### 2. Taxonomy-Driven Organization

Skills live in a **hierarchical, path-addressable taxonomy**:

```
technical_skills/programming/languages/python/fastapi
domain_knowledge/medical/terminology
tool_proficiency/version_control/git
```

**Why?**

- **Discoverability**: Predictable paths make skills easy to find
- **Semantic meaning**: Paths encode domain, category, and specificity
- **Composability**: Dependencies can reference paths directly
- **Scalability**: New branches can be added without restructuring

#### 3. Capability Granularity

Each skill should have **3-7 atomic capabilities**.

**Why 3-7?**

- **< 3**: Too narrow, consider merging with related skill
- **> 7**: Too broad, consider splitting into multiple skills
- **3-7**: Sweet spot for focus and comprehensiveness

Each capability must be:

- **Atomic**: Can be understood and tested independently
- **Cohesive**: Relates to a single responsibility
- **Testable**: Has clear input/output contracts
- **Cross-referencable**: Can be linked from other capabilities

#### 4. Production-Ready Patterns

Skills should emphasize **patterns that work in production**, not just examples that work in tutorials.

**What this means:**

- Document anti-patterns and silent failures
- Show both wrong (❌) and right (✅) approaches
- Include error handling and edge cases
- Specify version requirements
- Provide performance considerations

**Why?** Code that "works locally" but breaks under load is NOT production-ready. Skills should prevent these failures.

### Why This Structure?

#### File-Based vs Database

**Choice:** File system storage, not a database.

**Benefits:**

- **Inspectability**: Use `git`, `grep`, `find` to explore skills
- **Version control**: Track changes with standard VCS tools
- **Editable**: Use any text editor, no special tools required
- **Transparent**: No black box, everything is visible

**Trade-offs:**

- Slower lookups than database for large fleets
- Requires manual consistency checks (validation CLI)

#### Path-Style IDs

**Choice:** Path-style IDs with slashes (`technical/programming/languages/python/fastapi`), not dots or UUIDs.

**Benefits:**

- **Human-readable**: IDs explain what the skill is
- **Composable**: Can reference parent paths for dependencies
- **Navigable**: File system structure mirrors skill hierarchy
- **Semantic**: Paths encode domain knowledge

**Trade-offs:**

- Requires governance to avoid naming conflicts
- Path changes break references (use aliases for migrations)

#### Strict Metadata

**Choice:** Required metadata fields with validation.

**Benefits:**

- **Prevents drift**: Enforces consistency as taxonomy grows
- **Enables discovery**: Search by type, weight, tags
- **Supports composition**: Dependencies and capabilities are explicit
- **Tracks evolution**: Version history and change logs

**Trade-offs:**

- More friction when creating skills
- Requires maintenance when standards evolve

#### agentskills.io Compliance

**Choice:** Follow [agentskills.io](https://agentskills.io) specification.

**Benefits:**

- **Cross-system compatibility**: Skills work across different agent platforms
- **XML generation**: Automatic generation of agent context injection
- **Standardization**: Industry-wide format for skill definitions
- **Future-proof**: Aligns with emerging standards

**Trade-offs:**

- Additional frontmatter requirements
- Must maintain compliance as spec evolves

---

## 3. Skill Creation Interrogations (Discovery Questions)

Before creating a skill, ask these questions to ensure proper scoping and avoid duplication.

### Phase 1: Understanding the Need

#### Questions to Ask

1. **What problem does this skill solve?**

- Be specific: "Handle async database connections in FastAPI" not "database stuff"
- Identify the pain point this skill addresses

2. **Is this a new skill or enhancement to existing?**

- Search existing taxonomy first
- Check if capability fits in existing skill

3. **Does it overlap with existing skills?**

- Use `find` and `grep` to search for related terms
- Check dependency graph for related skills

4. **What domain does it belong to?**

- `cognitive`: Thinking patterns, reasoning approaches
- `technical`: Programming, frameworks, tools
- `domain`: Subject matter expertise
- `tool`: Software/platform proficiency
- `mcp`: Model Context Protocol
- `specialization`: Advanced/focused applications
- `task_focus`: Problem-solving methodologies
- `memory`: Memory management patterns

#### Decision Points

**Search existing taxonomy:**

```bash
# Search for related terms
find skills -name "*.md" | xargs grep -l "database"

# Check for similar capabilities
find skills -name "metadata.json" | xargs grep -l "sql"
```

**Determine appropriate branch:**

- If it's programming-related: `technical_skills/programming/`
- If it's subject matter: `domain_knowledge/`
- If it's a tool: `tool_proficiency/`
- If it's thinking patterns: `cognitive/`

**Output of Phase 1:**

- Clear problem statement
- Decision: new skill vs enhancement
- Domain classification
- Taxonomy path draft

### Phase 2: Scope & Boundaries

#### Questions to Ask

1. **What type of skill?**

- Review the 8 types and choose the best fit
- Use the [Type Determination Matrix](#type-determination-matrix) below

2. **What weight?**

- `lightweight`: Small, focused, 1-3 capabilities
- `medium`: Multi-capability, 4-7 capabilities
- `heavyweight`: Complex workflows, 8+ capabilities (rare)

3. **What load priority?**

- `always`: Core skills loaded at startup
- `task_specific`: Loaded when task matches intent
- `on_demand`: Loaded only when referenced
- `dormant`: Archived or experimental

4. **How many capabilities?**

- Target 3-7 capabilities
- Each capability should be atomic and testable
- Use the [Capability Design Principles](#capability-design-principles) below

5. **What dependencies on other skills?**

- List skills this one builds upon
- Avoid circular dependencies
- Use the [Dependency Composition Rules](#dependency-composition-rules) below

#### Decision Framework

##### Type Determination Matrix

| Skill Characteristics                  | Best Type   |
| -------------------------------------- | ----------- |
| Implementation patterns, code examples | `technical` |
| Subject matter, terminology, facts     | `domain`    |

- Thinking strategies, reasoning methods | `cognitive` |
- Software/platform proficiency | `tool` |
- MCP server/protocol related | `mcp` |
- Advanced application of other skills | `specialization` |
- Problem-solving methodologies | `task_focus` |
- Memory management patterns | `memory` |

##### Weight Guidelines

| Factor        | Lightweight     | Medium              | Heavyweight       |
| ------------- | --------------- | ------------------- | ----------------- |
| Capabilities  | 1-3             | 4-7                 | 8+                |
| Documentation | < 500 lines     | 500-2000 lines      | > 2000 lines      |
| Examples      | 1-2             | 3-5                 | 6+                |
| Dependencies  | 0-2             | 3-5                 | 6+                |
| Complexity    | Simple concepts | Moderate complexity | Complex workflows |

**Rule of thumb:** Start with `lightweight` or `medium`. Use `heavyweight` sparingly.

##### Load Priority Decision Tree

```
Is this a core/foundational skill?
├─ Yes → load_priority: "always"
└─ No
   ├─ Is this commonly used across tasks?
   │  ├─ Yes → load_priority: "task_specific"
   │  └─ No
   │     ├─ Is this rarely needed or experimental?
   │     │  ├─ Yes → load_priority: "on_demand" or "dormant"
   │     │  └─ No → load_priority: "task_specific"
```

**Examples:**

- `technical/programming/languages/python` → `always` (foundational)
- `technical/programming/web_frameworks/python/fastapi` → `task_specific` (common but not universal)
- `domain_knowledge/medical/neurosurgery` → `on_demand` (rarely needed)
- `experimental/new_technology` → `dormant` (experimental)

##### Dependency Composition Rules

1. **No cycles**: If A depends on B, B cannot depend on A
2. **Prefer abstractions**: If multiple skills need X, extract X into a shared skill
3. **Specify versions**: For external dependencies, always specify versions
4. **Minimize depth**: Dependency trees should be shallow (prefer 2-3 levels max)
5. **Document why**: Explain why each dependency is needed

**Good dependency:**

```json
{
  "dependencies": [
    "technical/programming/languages/python" // Reason: Uses Python syntax
  ]
}
```

**Bad dependency (too specific):**

```json
{
  "dependencies": [
    "technical/programming/web_frameworks/python/fastapi" // Too narrow
  ]
}
```

**Output of Phase 2:**

- Skill type determined
- Weight assigned
- Load priority chosen
- Capability count estimated
- Dependencies listed

### Phase 3: Capability Breakdown

#### Questions to Ask

1. **What are the atomic capabilities?**

- Break down into smallest testable units
- Each capability should solve one specific problem

2. **Can each be tested independently?**

- Write a test for each capability
- If you can't test it independently, it's not atomic

3. **Are they cohesive (single responsibility)?**

- Each capability should have one clear purpose
- If it does multiple things, split it

4. **Do they have clear boundaries?**

- No overlap between capabilities
- Clear distinction where one ends and another begins

#### Capability Design Principles

1. **Atomic and Testable**

- Each capability is independently testable
- Has clear inputs and outputs
- Can be demonstrated in isolation

2. **Single Responsibility**

- Each capability does one thing well
- Avoid multi-purpose capabilities

3. **Clear Input/Output Contracts**

- Specify what the capability requires
- Specify what the capability produces
- Document edge cases

4. **Cross-Referencable**

- Other skills can reference this capability
- Has a stable identifier (kebab-case name)
- Related capabilities are linked

#### Example: Breaking Down a Skill

**Initial idea:** "FastAPI database skill"

**Too broad - contains multiple capabilities:**

- Connection lifecycle management
- Query execution
- Transaction handling
- Migration management
- Testing utilities

**Better breakdown:**

1. `database-lifecycle-management` - Engine creation, pooling, shutdown
2. `async-query-execution` - Running async queries
3. `transaction-management` - Commit/rollback handling
4. `async-testing` - Testing async endpoints with databases

**Output of Phase 3:**

- List of atomic capabilities
- Test plan for each capability
- Clear boundaries between capabilities
- Cross-references to related capabilities

---

## 4. Structure & Format Requirements

### Directory Structure

Every skill directory MUST follow this structure:

```
skill-name/
├── metadata.json          # Required: Internal metadata
├── SKILL.md              # Required: Main doc with YAML frontmatter
├── capabilities/         # Required: Detailed capability docs
│   ├── capability-1.md
│   ├── capability-2.md
│   └── ...
├── references/
├── scripts/
├── examples/             # Required: Usage examples
│   ├── 01-example-name/
│   │   ├── README.md
│   │   ├── example.py
│   │   └── test_example.py
│   └── 02-example-name/
├── tests/                # Required: Test files
│   └── test_skill.py
└── resources/            # Required: Additional resources
    ├── requirements.json
    ├── config.yaml
    ├── reference.md
    └── ...
```

**Required files:**

- `metadata.json` - Internal metadata for the skill-fleet system
- `SKILL.md` - Main documentation with agentskills.io-compliant YAML frontmatter
- `capabilities/` - At least one capability file
- `examples/` - At least one example
- `tests/` - At least one test file
- `resources/` - Additional resources (minimum: requirements.json or equivalent)

**Optional files:**

- `best_practices.md` - Additional best practices
- `integration.md` - Integration patterns with other skills
- `troubleshooting.md` - Common issues and solutions

### Naming Conventions

#### Directory Names

Use **kebab-case** (lowercase with hyphens):

```
✅ fastapi-production-patterns
✅ python-decorators
✅ medical-terminology

❌ FastAPI_Patterns (camelCase)
❌ python_decorators (snake_case)
❌ python decorators (spaces)
```

#### SKILL.md Name

The `name` field in YAML frontmatter must match the directory name:

```
Directory: fastapi-production-patterns/
SKILL.md name: fastapi-production-patterns
```

#### Capability Files

Use **kebab-case** for capability files:

```
✅ database-lifecycle-management.md
✅ async-query-execution.md
✅ partial-updates.md

❌ DB_Lifecycle.md (mixed case)
❌ async_query.md (snake_case)
```

#### skill_id

Use **path-style with slashes**:

```
✅ technical/programming/web-frameworks/python/fastapi
✅ domain_knowledge/medical/terminology
✅ tool_proficiency/version_control/git

❌ technical.programming.web-frameworks (dots)
❌ technical_programming_web_frameworks (underscores)
```

### metadata.json Format

Every skill must have a `metadata.json` file:

```json
{
  "skill_id": "technical/programming/web-frameworks/python/fastapi",
  "name": "fastapi-production-patterns",
  "description": "Use when building FastAPI apps with async database operations, complex dependency injection, partial update endpoints, async testing, or converting Python utilities to API endpoints",
  "version": "1.0.0",
  "type": "technical",
  "weight": "medium",
  "load_priority": "task_specific",
  "dependencies": [],
  "capabilities": [
    "database-lifecycle-management",
    "pydantic-partial-updates",
    "async-conversion",
    "dependency-injection",
    "async-testing",
    "file-upload-handling",
    "background-tasks",
    "python-to-api-conversion"
  ],
  "category": "Web Development",
  "tags": [
    "python",
    "fastapi",
    "rest-api",
    "asyncio",
    "pydantic",
    "sqlalchemy",
    "production",
    "async"
  ],
  "created_at": "2026-01-07T02:34:11.401895+00:00",
  "last_modified": "2026-01-09T16:45:00.000000+00:00",
  "evolution": {
    "version": "1.0.0",
    "parent_id": null,
    "evolution_path": "initial_release",
    "change_log": "Initial packaging of FastAPI skill set with production patterns following TDD methodology.",
    "validation_score": 1.0,
    "integrity_hash": "a1b2c3d4e5f6g7h8"
  }
}
```

**Field descriptions:**

| Field           | Type   | Required | Description                                                                         |
| --------------- | ------ | -------- | ----------------------------------------------------------------------------------- |
| `skill_id`      | string | Yes      | Path-style identifier                                                               |
| `name`          | string | Yes      | Kebab-case name (matches directory)                                                 |
| `description`   | string | Yes      | 1-1024 character description                                                        |
| `version`       | string | Yes      | Semantic version (X.Y.Z)                                                            |
| `type`          | string | Yes      | One of: cognitive, technical, domain, tool, mcp, specialization, task_focus, memory |
| `weight`        | string | Yes      | One of: lightweight, medium, heavyweight                                            |
| `load_priority` | string | Yes      | One of: always, task_specific, on_demand, dormant                                   |
| `dependencies`  | array  | Yes      | List of skill_id strings (can be empty)                                             |
| `capabilities`  | array  | Yes      | List of capability name strings                                                     |
| `category`      | string | No       | Broad category for grouping                                                         |
| `tags`          | array  | No       | List of tag strings for search                                                      |
| `created_at`    | string | Yes      | ISO-8601 timestamp                                                                  |
| `last_modified` | string | Yes      | ISO-8601 timestamp                                                                  |
| `evolution`     | object | Yes      | Evolution tracking metadata                                                         |

### SKILL.md Format (agentskills.io compliant)

Every skill must have a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: skill-name
description: 1-1024 character description
license: MIT|Apache-2.0|BSD-3-Clause|etc
compatibility: Requirements and constraints (e.g., "Requires Python 3.8+, FastAPI 0.128.0+")
metadata:
  skill_id: path/to/skill
  version: 1.0.0
  type: technical
  weight: medium
  load_priority: task_specific
---

# Skill Title

## Overview

High-level description of what this skill does (2-3 sentences).

## When to Use

Decision framework for when to apply this skill.

**When to use:**

- Condition 1
- Condition 2
- Condition 3

**When NOT to use:**

- Condition 1
- Condition 2

## Quick Reference

| Problem   | Solution   | Keywords           |
| --------- | ---------- | ------------------ |
| Problem 1 | Solution 1 | keyword1, keyword2 |
| Problem 2 | Solution 2 | keyword3, keyword4 |

## Core Patterns/Capabilities

### Capability 1

**Problem:** What problem does it solve?
**Solution:** How does it solve it?
**Example:** Code or usage example

### Capability 2

...

## Common Mistakes

| Mistake   | Why It's Wrong | Fix      |
| --------- | -------------- | -------- |
| Mistake 1 | Explanation    | Solution |
| Mistake 2 | Explanation    | Solution |

## Real-World Impact

- **Metric 1**: Description → measurable outcome
- **Metric 2**: Description → measurable outcome

## See Also

- [Related Skill 1](../related-skill-1/SKILL.md)
- [Related Skill 2](../related-skill-2/SKILL.md)
```

**agentskills.io frontmatter requirements:**

| Field                    | Required | Format          | Description              |
| ------------------------ | -------- | --------------- | ------------------------ |
| `name`                   | Yes      | kebab-case      | Skill identifier         |
| `description`            | Yes      | 1-1024 chars    | What this skill does     |
| `license`                | No       | SPDX identifier | License type             |
| `compatibility`          | No       | Free text       | Requirements/constraints |
| `metadata.skill_id`      | Yes      | path-style      | Full path identifier     |
| `metadata.version`       | Yes      | semver          | Semantic version         |
| `metadata.type`          | Yes      | enum            | Skill type               |
| `metadata.weight`        | Yes      | enum            | Skill weight             |
| `metadata.load_priority` | Yes      | enum            | Load priority            |

### Capability Files Format

Each capability should have its own markdown file in `capabilities/`:

````markdown
# Capability Name

## Overview

What this capability does in 1-2 sentences.

## Problem Statement

**Silent failures that cause problems:**

- Issue 1
- Issue 2
- Issue 3

## Pattern/Solution

### ❌ Broken (Baseline Failure)

```python
# Show what NOT to do
problematic_code_here
```
````

### ✅ Production Pattern

```python
# Show the RIGHT way
correct_code_here
```

## Key Parameters/Concepts

| Parameter/Concept | Purpose      | Typical Value/Usage |
| ----------------- | ------------ | ------------------- |
| Param 1           | What it does | Example             |
| Param 2           | What it does | Example             |

## Symptoms of Misconfiguration

| Symptom   | Root Cause | Fix   |
| --------- | ---------- | ----- |
| Symptom 1 | Cause 1    | Fix 1 |
| Symptom 2 | Cause 2    | Fix 2 |

## Testing

```python
# Example test
def test_capability():
    # Test code here
    assert expected_behavior
```

## See Also

- [Related Capability](capability-name.md)
- [Parent SKILL.md](../SKILL.md)

```

### Examples Format

Each example should be in its own directory under `examples/`:

```

examples/
├── 01-example-name/
│ ├── README.md # Explanation of the example
│ ├── example.py # The example code
│ └── test_example.py # Test for the example
├── 02-another-example/
│ ├── README.md
│ ├── example.py
│ └── test_example.py

````

**README.md format:**
```markdown
# Example Name

## What This Demonstrates
Brief description of what this example shows.

## Running the Example
```bash
# Commands to run the example
python example.py
````

## Key Concepts

- Concept 1
- Concept 2
- Concept 3

## Expected Output

```
# What you should see when running it
```

## See Also

- [Related Capability](../../capabilities/capability-name.md)

````

**Numbering:** Use `01-`, `02-`, etc. for ordering.

**Self-contained:** Each example should run independently without needing other examples.

---

## 5. Content Guidelines

### Documentation Style

#### Problem → Solution Format

Structure documentation to match how developers think:

1. **State the problem** - What issue are we solving?
2. **Show the solution** - How do we solve it?
3. **Provide an example** - Concrete code or usage
4. **Explain why** - Why this solution works

**Example:**
```markdown
## Connection Pool Exhaustion

**Problem:** Under load, applications run out of database connections and fail with "too many connections" errors.

**Solution:** Create the database engine in the lifespan context manager with proper pool parameters.

**Example:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
    )
    yield
    await engine.dispose()
````

**Why this works:** The engine is created once at startup, properly configured with pool limits, and disposed of at shutdown, preventing connection leaks.

````

#### ❌/✅ Patterns

Show both wrong and right approaches:

```markdown
### ❌ Common Mistake
```python
# Engine created at import time - never closes!
engine = create_async_engine(DATABASE_URL)
````

### ✅ Production Pattern

```python
# Engine created in lifespan, properly disposed
@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(DATABASE_URL)
    yield
    await engine.dispose()
```

````

**Why?** Visual distinction makes patterns memorable. Shows what to avoid AND what to do.

#### Quick Reference Tables

Include tables for fast lookup:

```markdown
## Quick Reference

| Problem | Solution | Keywords |
|---------|----------|----------|
| Connections not closing | Use `lifespan` with `engine.dispose()` | connection leak, pool |
| Pool exhaustion | Set `pool_size` and `max_overflow` | concurrent, load |
| Tests fail together | Use async fixtures with rollback | isolation, flaky |
````

**Why?** Enables quick scanning and problem-solving.

#### Code Examples

Follow these guidelines for code examples:

1. **Include type hints:**

```python
 async def get_user(user_id: int) -> Optional[User]:
```

2. **Add explanatory comments:**

```python
 # CRITICAL: Only update provided fields
 update_data = update.model_dump(exclude_unset=True)
```

3. **Show imports:**

```python
 from typing import Optional
 from pydantic import BaseModel
```

4. **Use meaningful variable names:**

```python
 # Good
 async_connection_pool = create_async_engine(url)

 # Bad
 x = create_async_engine(url)
```

5. **Handle errors:**

```python
 try:
     result = await operation()
 except SpecificError as e:
     logger.error(f"Operation failed: {e}")
     raise
```

#### Cross-References

Link to related skills and capabilities:

```markdown
## See Also

- [Database Lifecycle Management](database-lifecycle-management.md)
- [Async Testing](async-testing.md)
- [Dependency Injection](dependency-injection.md)
- [Python Language](../../languages/python/SKILL.md)
```

**Why?** Enables navigation and shows relationships.

### Writing Principles

1. **Be Specific**
   ❌ "Handle errors properly"
   ✅ "Return HTTPException with status_code 404 and detail message"
2. **Show, Don't Just Tell**
   ❌ "Use the lifespan context manager"
   ✅ "`python  @asynccontextmanager  async def lifespan(app: FastAPI):      engine = create_async_engine(DATABASE_URL)      yield      await engine.dispose()` "
3. **Explain Why**
   Don't just say what to do - explain why it matters:
   ❌ "Create the engine in lifespan"
   ✅ "Create the engine in lifespan so it's disposed on shutdown, preventing connection leaks"
4. **Be Concise**
   Respect the reader's time. Remove fluff:
   ❌ "In this section, we're going to talk about how you can go about creating a database engine..."
   ✅ "Create the database engine in lifespan:"
5. **Be Complete**
   Cover edge cases and common pitfalls:
   ✅ "Note: If you're using multiple workers, stagger startup to prevent connection pool exhaustion."

### Version & Dependency Management

#### Specify Versions

Always specify versions for external dependencies:

```json
{
  "core_libraries": [
    "fastapi>=0.128.0",
    "uvicorn[standard]>=0.23.0",
    "pydantic>=2.0.0"
  ]
}
```

**Why?** Prevents breaking changes when dependencies update.

#### Document Minimum Requirements

```markdown
## Requirements

- Python 3.8+
- FastAPI 0.128.0+
- SQLAlchemy 2.0+
```

#### Note Breaking Changes

```markdown
## Version Notes

### 0.128.0 Breaking Changes

- `@app.on_event` is deprecated, use `lifespan` instead
- New CLI: `fastapi dev` replaces `uvicorn --reload`
```

#### Update Examples When Versions Change

When a dependency updates:

1. Test all examples with new version
2. Update version specifications
3. Document any breaking changes
4. Add migration notes if needed

---

## 6. Process Workflow

Follow this 5-step process to create a new skill from concept to validated artifact.

### Step 1: Discovery

**Goal:** Understand what problem you're solving and ensure it doesn't duplicate existing work.

**Actions:**

1. **Ask interrogation questions** (see [Section 3](#3-skill-creation-interrogations-discovery-questions))

- Phase 1: Understanding the Need
- Phase 2: Scope & Boundaries
- Phase 3: Capability Breakdown

2. **Search existing taxonomy:**

```bash
 # Search for related terms
 find skills -name "*.md" | xargs grep -l "search_term"

 # Check metadata for related skills
 find skills -name "metadata.json" | xargs grep -l "keyword"
```

3. **Define scope and boundaries:**

- Determine skill type, weight, load priority
- List dependencies
- Break down into capabilities (3-7)

**Outputs:**

- Skill concept document
- Taxonomy path
- Type, weight, priority assignments
- Capability list
- Dependency analysis

**Checkpoint:** Can you answer "yes" to these?

- Problem statement is clear and specific
- No existing skill covers this
- Capabilities are atomic and testable
- Dependencies are identified
- Taxonomy path is determined

### Step 2: Planning

**Goal:** Create a complete plan for the skill structure and metadata.

**Actions:**

1. **Determine metadata fields:**

- Finalize `skill_id`, `name`, `description`
- Choose `type`, `weight`, `load_priority`
- List `dependencies` and `capabilities`

2. **Plan directory structure:**

```
 skill-name/
 ├── metadata.json
 ├── SKILL.md
 ├── capabilities/
 │   ├── capability-1.md
 │   ├── capability-2.md
 │   └── ...
 ├── examples/
 │   ├── 01-example-1/
 │   └── 02-example-2/
 ├── tests/
 │   └── test_skill.py
 └── resources/
     ├── requirements.json
     └── reference.md
```

3. **Plan content for each file:**

- SKILL.md sections and examples
- Each capability's content
- Examples to demonstrate each capability
- Tests for validation

**Outputs:**

- Complete `metadata.json` draft
- Directory structure plan
- Content outline for each file
- Test plan

**Checkpoint:** Can you answer "yes" to these?

- metadata.json is complete and valid
- Directory structure is planned
- All capabilities have content outlines
- Examples are planned for each capability
- Tests are planned

### Step 3: Creation

**Goal:** Create the skill directory and all required files.

**Actions:**

1. **Create directory structure:**

```bash
 mkdir -p skills/path/to/skill-name
 mkdir -p skills/path/to/skill-name/capabilities
 mkdir -p skills/path/to/skill-name/examples/01-first-example
 mkdir -p skills/path/to/skill-name/tests
 mkdir -p skills/path/to/skill-name/resources
```

2. **Write metadata.json:**

- Use the draft from Step 2
- Ensure all required fields are present
- Validate JSON syntax

3. **Write SKILL.md:**

- Add YAML frontmatter (agentskills.io compliant)
- Write Overview section
- Write When to Use section
- Write Quick Reference table
- Write Core Patterns/Capabilities sections
- Write Common Mistakes table
- Write Real-World Impact section
- Add See Also links

4. **Create capability files:**

- One file per capability in `capabilities/`
- Follow the [Capability File Format](#capability-files-format)
- Include problem statement, pattern, examples
- Add cross-references

5. **Add examples:**

- Create at least one example per capability
- Include README.md, example code, test
- Ensure examples are runnable
- Test each example

6. **Add resources:**

- requirements.json or equivalent
- Config files if applicable
- Reference materials
- Troubleshooting guide

**Outputs:**

- Complete skill directory
- All required files present and valid
- Examples tested and working
- Resources documented

**Checkpoint:** Can you answer "yes" to these?

- All required directories exist
- metadata.json is valid JSON
- SKILL.md has YAML frontmatter
- All capabilities are documented
- At least one example per capability
- Examples run successfully
- Tests pass

### Step 4: Validation

**Goal:** Ensure the skill meets all quality and compliance standards.

**Actions:**

1. **Check agentskills.io compliance:**

```bash
 # Verify YAML frontmatter
 # Check required fields
 # Validate naming conventions
```

2. **Run validation CLI:**

```bash
 uv run skill-fleet validate-skill skills/path/to/skill-name
```

3. **Test examples:**

```bash
 # Run each example
 for example in examples/*; do
     cd $example
     python example.py
     python test_example.py
 done
```

4. **Verify cross-references:**

- Check all links work
- Verify referenced skills exist
- Ensure no circular dependencies

5. **Run tests:**

```bash
 cd tests/
 pytest test_skill.py -v
```

**Outputs:**

- Validation report
- List of any issues found
- Fixes applied

**Checkpoint:** Can you answer "yes" to these?

- agentskills.io compliance verified
- Validation CLI passes
- All examples run successfully
- All cross-references work
- All tests pass

### Step 5: Review & Evolution

**Goal:** Final review and documentation of the skill's evolution.

**Actions:**

1. **Self-review using checklist:**

- Use the [Validation Checklist](#9-validation-checklist)
- Verify all sections are complete
- Check for consistency

2. **Peer review (if applicable):**

- Submit for review
- Address feedback
- Update documentation

3. **Update evolution metadata:**

```json
{
  "evolution": {
    "version": "1.0.0",
    "parent_id": null,
    "evolution_path": "initial_release",
    "change_log": "Initial skill creation with N capabilities",
    "validation_score": 1.0,
    "integrity_hash": "sha256_hash"
  }
}
```

4. **Update taxonomy_meta.json:**

- Add skill to taxonomy
- Update dependencies
- Increment version

5. **Commit to version control:**

```bash
 git add skills/path/to/skill-name
 git commit -m "Add skill-name: description of capabilities"
```

**Outputs:**

- Validated skill
- Evolution record updated
- Taxonomy metadata updated
- Version control commit

**Checkpoint:** Can you answer "yes" to these?

- Self-review complete
- Peer review complete (if applicable)
- Evolution metadata updated
- Taxonomy metadata updated
- Committed to version control

---

## 7. Common Patterns & Anti-Patterns

### Always Do

These practices ensure quality and consistency:

1. **Use kebab-case for names**

- Directories: `fastapi-production-patterns`
- Capabilities: `database-lifecycle-management`
- Examples: `01-partial-updates`

2. **Include all required directories**

- `capabilities/`, `examples/`, `tests/`, `resources/`

3. **Specify versions in dependencies**

- `"fastapi>=0.128.0"` not `"fastapi"`

4. **Write testable examples**

- Each example should run independently
- Include test files

5. **Cross-reference related skills**

- Link to related capabilities
- Link to parent/child skills

6. **Document breaking changes**

- Note version requirements
- Explain migration paths

7. **Update taxonomy_meta.json**

- Keep taxonomy in sync
- Track dependencies

8. **Show both wrong and right approaches**

- Use ❌/✅ pattern
- Explain why

9. **Include quick reference tables**

- Problem → Solution mappings
- Common mistakes and fixes

10. **Write descriptive commit messages**

- `Add skill-name: brief description`
  - Include capability list

### Never Do

These practices cause problems:

1. **Create circular dependencies**

- A depends on B, B depends on A
- Use shared abstractions instead

2. **Use camelCase or snake_case for names**

- ❌ `FastAPI_Patterns`, `fastapi_patterns`
- ✅ `fastapi-patterns`

3. **Forget to update metadata**

- Always update `metadata.json`
- Always update `last_modified`

4. **Skip validation**

- Always run `skill-fleet validate-skill`
- Fix issues before committing

5. **Duplicate existing capabilities**

- Search existing skills first
- Enhance existing skill if appropriate

6. **Make capabilities too broad**

- > 7 capabilities → split into multiple skills
- Each capability should be atomic

7. **Mix multiple domains in one skill**

- Keep skills focused on one domain
- Use dependencies to compose

8. **Write vague descriptions**

- ❌ "Database utilities"
- ✅ "Async database connection lifecycle management for FastAPI"

9. **Forget to dispose resources**

- Always clean up in shutdown
- Use context managers

10. **Hardcode paths or configurations**

- Use environment variables
  - Provide config templates

### Red Flags

Watch for these warning signs:

| Red Flag                     | Why It's a Problem          | What to Do                          |
| ---------------------------- | --------------------------- | ----------------------------------- |
| Skill has >10 capabilities   | Too broad, hard to navigate | Split into multiple skills          |
| Skill has 1-2 capabilities   | Too narrow, low value       | Merge with related skill or expand  |
| No dependencies but complex  | Missing abstractions        | Extract common patterns             |
| Circular dependency detected | Breaks composition          | Refactor to use shared abstractions |
| Examples don't run           | Invalid skill               | Fix examples before committing      |
| No version specified         | Breaking changes risk       | Always specify versions             |
| Duplicate capability names   | Confusion                   | Ensure unique names                 |
| Long capability names        | Hard to reference           | Keep names concise                  |
| Missing tests                | Unknown validity            | Add tests for all capabilities      |
| No See Also sections         | Poor discoverability        | Add cross-references                |

---

## 8. Examples

### Example 1: Creating a Technical Skill

**Task:** Create a skill for Python decorators.

#### Step 1: Discovery

**Questions:**

- What problem? Understanding and implementing Python decorators
- New or existing? New (no existing decorator skill)
- Domain? Technical → Programming → Languages → Python
- Type? `technical`
- Weight? `medium` (multiple decorator patterns)
- Capabilities?
  1. Basic function decorators
  2. Class decorators
  3. Decorators with arguments
  4. Property decorators
  5. Decorator composition

#### Step 2: Planning

**Metadata:**

```json
{
  "skill_id": "technical/programming/languages/python/decorators",
  "name": "python-decorators",
  "description": "Create and apply Python decorators for functions and classes, including decorators with arguments, property decorators, and decorator composition patterns.",
  "version": "1.0.0",
  "type": "technical",
  "weight": "medium",
  "load_priority": "task_specific",
  "dependencies": ["technical/programming/languages/python"],
  "capabilities": [
    "basic-function-decorators",
    "class-decorators",
    "decorators-with-arguments",
    "property-decorators",
    "decorator-composition"
  ]
}
```

#### Step 3: Creation

Create directory structure and files:

```
python-decorators/
├── metadata.json
├── SKILL.md
├── capabilities/
│   ├── basic-function-decorators.md
│   ├── class-decorators.md
│   ├── decorators-with-arguments.md
│   ├── property-decorators.md
│   └── decorator-composition.md
├── examples/
│   ├── 01-basic-logging-decorator/
│   ├── 02-timing-decorator/
│   └── 03-property-decorators/
├── tests/
│   └── test_decorators.py
└── resources/
    └── requirements.json
```

#### Step 4: Validation

```bash
uv run skill-fleet validate-skill skills/technical/programming/languages/python/decorators
```

#### Step 5: Review

Commit to version control:

```bash
git add skills/technical/programming/languages/python/decorators
git commit -m "Add python-decorators: basic and class decorators, decorators with arguments, property decorators, and composition patterns"
```

### Example 2: Creating a Domain Knowledge Skill

**Task:** Create a skill for medical terminology.

#### Step 1: Discovery

**Questions:**

- What problem? Understanding medical terminology and abbreviations
- New or existing? New
- Domain? Domain Knowledge → Medical
- Type? `domain`
- Weight? `heavyweight` (large terminology set)
- Capabilities?
  1. Common medical abbreviations
  2. Anatomy terminology
  3. Pharmacology terms
  4. Clinical terminology
  5. Medical coding systems

#### Step 2: Planning

**Metadata:**

```json
{
  "skill_id": "domain_knowledge/medical/terminology",
  "name": "medical-terminology",
  "description": "Understand and use medical terminology including common abbreviations, anatomical terms, pharmacology vocabulary, clinical terminology, and medical coding systems.",
  "version": "1.0.0",
  "type": "domain",
  "weight": "heavyweight",
  "load_priority": "on_demand",
  "dependencies": [],
  "capabilities": [
    "medical-abbreviations",
    "anatomy-terminology",
    "pharmacology-terms",
    "clinical-terminology",
    "medical-coding-systems"
  ]
}
```

#### Step 3-5: Follow same process as Example 1

### Example 3: Adding a Capability to Existing Skill

**Task:** Add "Rate Limiting" capability to FastAPI skill.

#### Step 1: Discovery

**Questions:**

- What problem? Rate limiting for FastAPI endpoints
- New or existing? Add to existing `fastapi-production-patterns`
- Fit? Yes, related to production patterns
- Atomic? Yes, rate limiting is standalone

#### Step 2: Planning

**Capability structure:**

- Name: `rate-limiting`
- Content: Problem statement, pattern, examples
- Tests: Rate limit tests

#### Step 3: Creation

Create file:

```
fastapi-production-patterns/capabilities/rate-limiting.md
```

Add example:

```
fastapi-production-patterns/examples/09-rate-limiting/
```

Update metadata.json:

```json
{
  "capabilities": [
    ...existing...,
    "rate-limiting"
  ]
}
```

#### Step 4: Validation

```bash
uv run skill-fleet validate-skill skills/technical/programming/web-frameworks/python/fastapi
```

#### Step 5: Review

Commit:

```bash
git add skills/technical/programming/web-frameworks/python/fastapi
git commit -m "Add rate-limiting capability to fastapi-production-patterns"
```

---

## 9. Validation Checklist

Use this checklist before committing any skill.

### Structure

- All required directories exist (`capabilities/`, `examples/`, `tests/`, `resources/`)
- `metadata.json` present and valid JSON
- `SKILL.md` present with YAML frontmatter
- At least one capability file in `capabilities/`
- At least one example in `examples/`
- At least one test file in `tests/`
- Naming conventions followed (kebab-case)

### Content

- agentskills.io compliant (YAML frontmatter complete)
- Version specified in `metadata.json`
- Description is 1-1024 characters
- All capabilities listed in `metadata.json` are documented
- All examples are runnable
- All tests pass
- No broken cross-references

### Metadata

- `skill_id` uses path format with slashes
- `name` matches directory name
- `type` is one of: cognitive, technical, domain, tool, mcp, specialization, task_focus, memory
- `weight` is one of: lightweight, medium, heavyweight
- `load_priority` is one of: always, task_specific, on_demand, dormant
- `dependencies` list is valid (no circular dependencies)
- `capabilities` list matches actual capabilities
- `created_at` and `last_modified` are ISO-8601 timestamps
- `evolution` object is complete

### Cross-References

- No circular dependencies in dependency graph
- All referenced skills exist
- `taxonomy_meta.json` updated
- Related skills linked in `See Also` sections
- Internal links work

### Quality

- Code examples have type hints
- Anti-patterns documented (❌/✅ format)
- Quick reference table included
- `See Also` sections complete
- Examples are self-contained
- Tests are comprehensive

### Compliance

- `uv run skill-fleet validate-skill` passes
- agentskills.io validation passes
- No deprecated patterns used
- Version requirements specified

---

## 10. Troubleshooting

### Common Issues

#### Validation Fails

**Symptoms:**

```
❌ Validation failed: Missing required field 'type'
❌ Validation failed: Invalid naming convention
```

**Causes:**

- Missing required fields in `metadata.json`
- Invalid naming (not kebab-case)
- Missing directories
- Invalid JSON syntax

**Fixes:**

1. Check `metadata.json` has all required fields
2. Verify naming uses kebab-case
3. Ensure all required directories exist
4. Validate JSON syntax: `python -m json.tool metadata.json`

#### Examples Don't Run

**Symptoms:**

```
ModuleNotFoundError: No module named 'fastapi'
ImportError: cannot import name 'X'
```

**Causes:**

- Missing dependencies
- Wrong versions
- Missing imports in examples

**Fixes:**

1. Check `resources/requirements.json` for dependencies
2. Install dependencies: `uv sync`
3. Verify imports in example files
4. Check version specifications

#### Circular Dependency Detected

**Symptoms:**

```
❌ Validation failed: Circular dependency detected
A → B → A
```

**Causes:**

- Skill A depends on B, B depends on A
- Usually indicates missing abstraction

**Fixes:**

1. Identify the circular dependency
2. Extract common functionality into shared skill
3. Update both skills to depend on shared skill
4. Remove circular references

#### Taxonomy Conflicts

**Symptoms:**

```
❌ Validation failed: Duplicate skill_id found
❌ Validation failed: Taxonomy path already exists
```

**Causes:**

- Skill with same `skill_id` already exists
- Taxonomy path conflicts

**Fixes:**

1. Search for existing skill: `find skills -name "metadata.json" | xargs grep "skill_id"`
2. If duplicate, merge or choose different path
3. If conflict, reorganize taxonomy

#### Capability Mismatch

**Symptoms:**

```
❌ Validation failed: Capability 'X' listed but not found
❌ Validation failed: Capability file 'Y' not in metadata
```

**Causes:**

- Capability listed in `metadata.json` but no file
- Capability file exists but not listed in `metadata.json`

**Fixes:**

1. List capabilities in `capabilities/` directory
2. Compare with `metadata.json` capabilities list
3. Ensure exact match (kebab-case)

### Getting Help

#### CLI Help

```bash
# General help
uv run skill-fleet --help

# Command-specific help
uv run skill-fleet validate-skill --help
uv run skill-fleet create-skill --help
```

#### Documentation

- [Overview](overview.md) - System architecture
- [Getting Started Guide](getting-started/index.md) - Installation & CLI workflow
- [Skill Creator Guide](skill-creator-guide.md) - DSPy workflow
- [CLI Reference](cli-reference.md) - Command reference
- [agentskills.io Compliance](agentskills-compliance.md) - Specification

#### Validation

```bash
# Validate a skill
uv run skill-fleet validate-skill path/to/skill

# Validate all skills
find skills -name "metadata.json" | while read meta; do
  uv run skill-fleet validate-skill "$(dirname "$meta")"
done
```

#### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL="DEBUG"
uv run skill-fleet validate-skill path/to/skill
```

---

## Appendix A: Quick Reference

### Skill Types

| Type             | Description                   | Examples                             |
| ---------------- | ----------------------------- | ------------------------------------ |
| `cognitive`      | Thinking patterns, reasoning  | Logical reasoning, Creative thinking |
| `technical`      | Programming, frameworks       | Python, FastAPI, Git                 |
| `domain`         | Subject matter expertise      | Medical, Legal, Financial            |
| `tool`           | Software/platform proficiency | Docker, AWS, VS Code                 |
| `mcp`            | Model Context Protocol        | MCP servers, protocol handlers       |
| `specialization` | Advanced applications         | Advanced ML, Security auditing       |
| `task_focus`     | Problem-solving methodologies | Debug-fix, Code review               |
| `memory`         | Memory management             | Context management, Retrieval        |

### Weight Guidelines

| Weight        | Capabilities | Documentation  | Examples |
| ------------- | ------------ | -------------- | -------- |
| `lightweight` | 1-3          | < 500 lines    | 1-2      |
| `medium`      | 4-7          | 500-2000 lines | 3-5      |
| `heavyweight` | 8+           | > 2000 lines   | 6+       |

### Load Priority

| Priority        | Description                 | Examples               |
| --------------- | --------------------------- | ---------------------- |
| `always`        | Core skills, always loaded  | Python, Git, Reasoning |
| `task_specific` | Loaded when task matches    | FastAPI, Docker        |
| `on_demand`     | Loaded only when referenced | Medical terminology    |
| `dormant`       | Archived/experimental       | Deprecated skills      |

### Naming Examples

| Type       | ✅ Correct                               | ❌ Incorrect                   |
| ---------- | ---------------------------------------- | ------------------------------ |
| Directory  | `fastapi-production-patterns`            | `FastAPI_Patterns`             |
| Capability | `database-lifecycle-management`          | `DB_Lifecycle`                 |
| skill_id   | `technical/programming/languages/python` | `technical.programming.python` |

### File Templates

#### metadata.json Template

```json
{
  "skill_id": "path/to/skill",
  "name": "skill-name",
  "description": "1-1024 character description",
  "version": "1.0.0",
  "type": "technical",
  "weight": "medium",
  "load_priority": "task_specific",
  "dependencies": [],
  "capabilities": [],
  "category": "category",
  "tags": [],
  "created_at": "2026-01-09T00:00:00.000000+00:00",
  "last_modified": "2026-01-09T00:00:00.000000+00:00",
  "evolution": {
    "version": "1.0.0",
    "parent_id": null,
    "evolution_path": "initial_release",
    "change_log": "Initial skill creation",
    "validation_score": 1.0,
    "integrity_hash": "sha256"
  }
}
```

#### SKILL.md Template

```markdown
---
name: skill-name
description: 1-1024 character description
license: MIT
compatibility: Requirements
metadata:
  skill_id: path/to/skill
  version: 1.0.0
  type: technical
  weight: medium
  load_priority: task_specific
---

# Skill Title

## Overview

Description of what this skill does.

## When to Use

**When to use:**

- Condition 1
- Condition 2

**When NOT to use:**

- Condition 1

## Quick Reference

| Problem   | Solution   | Keywords |
| --------- | ---------- | -------- |
| Problem 1 | Solution 1 | keywords |

## Core Patterns/Capabilities

### Capability 1

**Problem:** What problem does it solve?
**Solution:** How to solve it

## Common Mistakes

| Mistake   | Fix   |
| --------- | ----- |
| Mistake 1 | Fix 1 |

## Real-World Impact

- **Metric**: Description → outcome

## See Also

- [Related Skill](../related-skill/SKILL.md)
```

---

**Next Steps:**

1. Review the [Getting Started Guide](getting-started/index.md) for CLI usage
2. Read the [Skill Creator Guide](skill-creator-guide.md) for DSPy workflow
3. Explore existing skills to see patterns in action
4. Start creating your first skill!

**For questions or issues:**

- Use `uv run skill-fleet --help` for CLI assistance
- Run `uv run skill-fleet validate-skill` to validate your work
- Check existing skills for examples and patterns

Happy skill building! 🚀
