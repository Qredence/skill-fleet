# Dual Metadata Model Architecture

## Overview

Skill Fleet uses a **dual metadata model** pattern to separate domain concerns from infrastructure concerns. This architectural decision keeps the business logic clean while enabling efficient filesystem operations.

## The Two Metadata Classes

### 1. `SkillMetadata` - Domain Model

**Location:** `src/skill_fleet/core/models.py:285`

**Purpose:** Rich domain model following the agentskills.io specification. Used throughout business logic, API responses, and workflow orchestration.

**Key Characteristics:**
- Pydantic `BaseModel` with full validation
- No filesystem/path awareness (pure business logic)
- Includes v2 Golden Standard fields (`allowed_tools`, `skill_style`)
- Supports dict-like access via `DictLikeAccessMixin`

**Core Fields:**
```python
skill_id: str          # Path-style identifier (e.g., 'technical_skills/programming/python')
name: str              # Kebab-case name (pattern: ^[a-z0-9]+(-[a-z0-9]+)*$)
description: str       # 1-1024 character triggering description
version: str           # Semantic version (default: "1.0.0")
type: Literal[...]     # cognitive, technical, domain, tool, mcp, etc.
weight: Literal[...]   # lightweight, medium, heavyweight
load_priority: str     # always, task_specific, on_demand, dormant
dependencies: list[str]
capabilities: list[str]

# Scalable discovery fields
category: str
keywords: list[str]
scope: str
see_also: list[str]

# v2 Golden Standard
allowed_tools: list[str] | None
skill_style: Literal["navigation_hub", "comprehensive", "minimal"] | None
```

**Usage Contexts:**
- Workflow results (`PlanResult`, `SkillCreationResult`)
- API request/response schemas
- DSPy signature inputs/outputs
- Business logic validation

### 2. `InfrastructureSkillMetadata` - Infrastructure Model

**Location:** `src/skill_fleet/taxonomy/metadata.py:22`

**Purpose:** Lightweight, immutable dataclass for loading skills from disk. Used by the taxonomy manager for filesystem operations.

**Key Characteristics:**
- Frozen dataclass with `slots=True` (memory-efficient)
- Includes `path: Path` field for filesystem operations
- Immutable (prevents accidental modification during caching)
- Minimal validation (assumes pre-validated data)

**Core Fields:**
```python
skill_id: str
version: str
type: str
weight: str
load_priority: str
dependencies: list[str]
capabilities: list[str]
path: Path              # Filesystem path to metadata.json or SKILL.md
always_loaded: bool = False
name: str = ""          # agentskills.io compliant kebab-case name
description: str = ""  # Brief description
```

**Usage Contexts:**
- `TaxonomyManager` metadata cache
- Skill loading from disk (`skill_loader.py`)
- Filesystem discovery operations
- XML generation for agentskills.io

## Why Two Classes?

### Separation of Concerns

| Aspect | `SkillMetadata` | `InfrastructureSkillMetadata` |
|--------|-----------------|------------------------------|
| **Primary Role** | Business logic | Filesystem I/O |
| **Validation** | Strict Pydantic validation | Minimal (assumes valid) |
| **Mutability** | Mutable (evolves during workflow) | Immutable (frozen dataclass) |
| **Path Awareness** | No path fields | Has `path: Path` |
| **Memory** | Standard Pydantic overhead | Optimized with `slots=True` |
| **Usage** | Workflows, APIs, validation | Caching, loading, discovery |

### Architectural Benefits

1. **Clean Domain Model:** `SkillMetadata` has no filesystem dependencies, making it testable and portable
2. **Performance:** `InfrastructureSkillMetadata` uses frozen dataclasses with slots for memory efficiency when caching hundreds of skills
3. **Security:** Path operations are isolated to the infrastructure layer with proper path traversal protection
4. **Flexibility:** The domain model can evolve without affecting filesystem serialization

## Conversion Between Models

### Domain → Infrastructure

When saving a skill to disk:

```python
# In TaxonomyManager.register_skill()
skill_metadata = InfrastructureSkillMetadata(
    skill_id=metadata["skill_id"],
    version=metadata.get("version", "1.0.0"),
    type=metadata["type"],
    weight=metadata["weight"],
    load_priority=metadata.get("load_priority", "task_specific"),
    dependencies=metadata.get("dependencies", []),
    capabilities=metadata.get("capabilities", []),
    path=skill_dir / "metadata.json",
    always_loaded=metadata.get("always_loaded", False),
    name=metadata.get("name", ""),
    description=metadata.get("description", ""),
)
```

### Infrastructure → Domain

When loading for workflow operations:

```python
# Implicit conversion via dict unpacking
skill_metadata = SkillMetadata(
    skill_id=infra_metadata.skill_id,
    name=infra_metadata.name,
    description=infra_metadata.description,
    version=infra_metadata.version,
    type=infra_metadata.type,
    weight=infra_metadata.weight,
    load_priority=infra_metadata.load_priority,
    dependencies=infra_metadata.dependencies,
    capabilities=infra_metadata.capabilities,
    # ... additional fields
)
```

## Cache Architecture

The `TaxonomyManager` maintains a metadata cache:

```python
class TaxonomyManager:
    def __init__(self, skills_root: Path):
        self.metadata_cache: dict[str, InfrastructureSkillMetadata] = {}
        # ...

    def _load_skill_file(self, skill_file: Path) -> InfrastructureSkillMetadata:
        metadata = load_skill_file(skill_file)
        self.metadata_cache[metadata.skill_id] = metadata
        return metadata
```

**Cache Benefits:**
- Avoids repeated filesystem I/O
- Immutable cached objects prevent accidental corruption
- Frozen dataclass = thread-safe for reads
- Async-safe with `_cache_lock` for updates

## File Format Support

### Single-File Skills (Legacy)

```
skills/
└── _core/
    └── reasoning.json      # Contains embedded metadata
```

Loaded via `load_skill_file()` → returns `InfrastructureSkillMetadata`

### Directory-Based Skills (Current)

```
skills/
└── technical_skills/
    └── programming/
        └── python/
            ├── SKILL.md          # YAML frontmatter + content
            └── metadata.json     # Extended metadata
```

Loaded via `load_skill_dir_metadata()` → returns `InfrastructureSkillMetadata`

### agentskills.io Compliant (v2 Golden Standard)

```
skills/
└── dspy-basics/
    └── SKILL.md              # YAML frontmatter ONLY
```

Parsed via `parse_skill_frontmatter()` → constructs `InfrastructureSkillMetadata`

## Key Design Decisions

### 1. Why Frozen Dataclass for Infrastructure?

- **Thread Safety:** Immutable objects are inherently thread-safe
- **Cache Safety:** Prevents accidental mutation of cached metadata
- **Memory Efficiency:** `slots=True` reduces per-instance overhead
- **Intent Communication:** Frozen signals "this is read-only infrastructure data"

### 2. Why Pydantic for Domain?

- **Validation:** Automatic validation of field types and formats
- **Serialization:** Easy JSON conversion for API responses
- **Documentation:** Self-documenting field types and constraints
- **Ecosystem:** Integration with FastAPI and DSPy

### 3. Why No Automatic Conversion?

- **Explicit Boundaries:** Forces developers to think about which layer they're in
- **Performance:** Avoids unnecessary object churn
- **Flexibility:** Allows partial conversions (only fields needed)

## Related Components

- `TaxonomyManager` - Manages skill loading and caching
- `SkillValidator` - Validates skills using both models
- `SkillService` - Uses domain model for workflow orchestration
- `SkillRepository` - Database layer with its own SQLAlchemy models

## References

- `src/skill_fleet/core/models.py` - Domain models
- `src/skill_fleet/taxonomy/metadata.py` - Infrastructure metadata
- `src/skill_fleet/taxonomy/skill_loader.py` - Loading logic
- `src/skill_fleet/taxonomy/manager.py` - Taxonomy management
