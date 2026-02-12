# Taxonomy System Architecture

## Overview

The Taxonomy System provides hierarchical organization of skills with efficient discovery, dependency resolution, and agentskills.io compliance. It bridges filesystem storage with logical organization.

## Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     TaxonomyManager                              │
│  (skills_root, metadata_cache, index, meta)                     │
└─────────────────────────────────────────────────────────────────┘
     │                    │                    │
     ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  TaxonomyPath │   │ TaxonomyIndex │   │taxonomy_meta │
│  (value obj)  │   │  (JSON index) │   │   (JSON)     │
└──────────────┘   └──────────────┘   └──────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Skill Loading Layer                           │
│  (load_skill_file, load_skill_dir_metadata,                     │
│   parse_skill_frontmatter, load_skill_for_discovery)            │
└─────────────────────────────────────────────────────────────────┘
```

## TaxonomyManager

**Location:** `src/skill_fleet/taxonomy/manager.py:104`

Central coordinator for taxonomy operations.

### Initialization

```python
class TaxonomyManager:
    _ALWAYS_LOADED_DIRS = ("_core", "mcp_capabilities", "memory_blocks")

    def __init__(self, skills_root: Path):
        self.skills_root = Path(skills_root).resolve()
        self.meta_path = self.skills_root / "taxonomy_meta.json"
        self.index_path = self.skills_root / "taxonomy_index.json"
        self.metadata_cache: dict[str, InfrastructureSkillMetadata] = {}
        self.meta: dict[str, Any] = {}
        self.index: TaxonomyIndex = TaxonomyIndex()

        self.load_taxonomy_meta()
        self.load_index()
        self._load_always_loaded_skills()
```

### Always-Loaded Skills

Core skills loaded at startup:

```python
def _load_always_loaded_skills(self) -> None:
    for relative_dir in self._ALWAYS_LOADED_DIRS:
        skills_dir = resolve_path_within_root(self.skills_root, relative_dir)
        if not skills_dir.exists():
            continue
        for skill_file in skills_dir.glob("*.json"):
            self._load_skill_file(skill_file)
```

**Purpose:** Ensure essential skills (core reasoning, MCP capabilities, memory) are always available.

## TaxonomyPath Value Object

**Location:** `src/skill_fleet/taxonomy/manager.py:48`

Immutable, validated path representation.

```python
@dataclass(frozen=True)
class TaxonomyPath:
    path: str

    def __post_init__(self) -> None:
        safe = sanitize_taxonomy_path(self.path)
        if not safe:
            raise ValueError(f"Invalid taxonomy path: {self.path}")
        object.__setattr__(self, "path", safe)

    def parent(self) -> TaxonomyPath | None:
        parts = self.path.split("/")
        if len(parts) <= 1:
            return None
        return TaxonomyPath("/".join(parts[:-1]))

    def child(self, segment: str) -> TaxonomyPath:
        return TaxonomyPath(f"{self.path}/{segment}")

    def depth(self) -> int:
        return len(self.path.split("/"))
```

**Benefits:**
- Prevents path traversal attacks via sanitization
- Immutable = hashable and safe for caching
- Provides taxonomy-specific operations (parent, child, depth)

## TaxonomyIndex

**Location:** `src/skill_fleet/taxonomy/models.py`

JSON-based index for fast skill resolution.

```python
class SkillEntry(BaseModel):
    canonical_path: str           # Primary filesystem path
    taxonomy_location: str        # Dot-notation path in tree
    aliases: list[str] = []       # Legacy/alternative paths
    facets: dict[str, str] = {}   # Key-value tags
    status: Literal["active", "deprecated", "draft"] = "active"

class TaxonomyIndex(BaseModel):
    version: str = "1.0"
    skills: dict[str, SkillEntry] = {}  # skill_id -> entry
    aliases: dict[str, str] = {}        # alias -> canonical_id
```

### Index File Location

```
skills/
├── taxonomy_index.json    # Index for skill resolution
├── taxonomy_meta.json     # Statistics and metadata
└── ...
```

### Resolution Strategy

The `resolve_skill_location()` function implements polyfill resolution:

```python
def resolve_skill_location(skill_identifier: str, skills_root: Path, index: TaxonomyIndex) -> str:
    # 1. Check Index (canonical ID or alias)
    if skill_identifier in index.skills:
        return index.skills[skill_identifier].canonical_path
    if skill_identifier in index.aliases:
        canonical_id = index.aliases[skill_identifier]
        return index.skills[canonical_id].canonical_path

    # 2. Direct filesystem check (legacy support)
    direct_path = skills_root / skill_identifier
    if direct_path.exists():
        return skill_identifier

    # 3. Try with .json extension
    json_path = skills_root / f"{skill_identifier}.json"
    if json_path.exists():
        return f"{skill_identifier}.json"

    raise FileNotFoundError(f"Skill not found: {skill_identifier}")
```

## Skill Loading

### Single-File Skills (Legacy)

```python
def _load_skill_file(self, skill_file: Path) -> InfrastructureSkillMetadata:
    """Load skill from JSON file."""
    metadata = load_skill_file(skill_file)
    self.metadata_cache[metadata.skill_id] = metadata
    return metadata
```

**Format:**
```json
{
  "skill_id": "_core/reasoning",
  "version": "1.0.0",
  "type": "cognitive",
  "weight": "lightweight",
  "load_priority": "always",
  "dependencies": [],
  "capabilities": ["step_by_step_reasoning"],
  "content": "..."
}
```

### Directory-Based Skills

```python
def _load_skill_dir_metadata(self, skill_dir: Path) -> InfrastructureSkillMetadata:
    """Load skill from directory with metadata.json."""
    metadata = load_skill_dir_metadata(skill_dir)
    self.metadata_cache[metadata.skill_id] = metadata
    return metadata
```

**Structure:**
```
skill-name/
├── SKILL.md
├── metadata.json
└── examples/
    └── README.md
```

### agentskills.io Compliant Skills (v2)

```python
def _load_skill_for_discovery(self, skill_dir: Path) -> InfrastructureSkillMetadata:
    """Load skill from SKILL.md with YAML frontmatter only."""
    skill_md_path = skill_dir / "SKILL.md"
    frontmatter = self.parse_skill_frontmatter(skill_md_path)

    metadata = InfrastructureSkillMetadata(
        skill_id=skill_id,
        version="1.0.0",
        type="technical",
        weight="medium",
        load_priority="on_demand",
        dependencies=[],
        capabilities=[],
        path=skill_md_path,
        always_loaded=False,
        name=frontmatter.get("name", ""),
        description=frontmatter.get("description", ""),
    )
    return metadata
```

**SKILL.md Format:**
```markdown
---
name: dspy-basics
description: Fundamental DSPy patterns for prompt engineering
---

# DSPy Basics
...
```

## Discovery System

### XML Generation

Generate `<available_skills>` XML for prompt injection:

```python
def generate_available_skills_xml(self, user_id: str | None = None) -> str:
    ensure_all_skills_loaded(self.skills_root, self.metadata_cache, self._load_skill_for_discovery)

    if user_id is None:
        return generate_available_skills_xml(self.metadata_cache, self.skills_root, user_id)

    mounted_skills = set(self.get_mounted_skills(user_id))
    filtered_cache = {
        skill_id: metadata
        for skill_id, metadata in self.metadata_cache.items()
        if skill_id in mounted_skills
    }
    return generate_available_skills_xml(filtered_cache, self.skills_root, user_id)
```

**Output Format:**
```xml
<available_skills>
  <skill id="dspy-basics" name="dspy-basics">
    <description>Fundamental DSPy patterns...</description>
  </skill>
  ...
</available_skills>
```

### Relevant Branches

Keyword-based branch selection for task routing:

```python
def get_relevant_branches(self, task_description: str) -> dict[str, dict[str, str]]:
    branches: dict[str, dict[str, str]] = {}
    keywords = task_description.lower().split()

    if any(k in keywords for k in ["code", "program", "develop", "script"]):
        branches["technical_skills/programming"] = self._get_branch_structure("technical_skills/programming")

    if any(k in keywords for k in ["data", "analyze", "statistics"]):
        branches["domain_knowledge"] = self._get_branch_structure("domain_knowledge")

    return branches
```

## Dependency Management

### Validation

```python
def validate_dependencies(self, dependencies: list[str]) -> tuple[bool, list[str]]:
    missing: list[str] = []
    for dep_id in dependencies:
        if dep_id in self.metadata_cache:
            continue
        if self._try_load_skill_by_id(dep_id) is None:
            missing.append(dep_id)
    return len(missing) == 0, missing
```

### Circular Detection

```python
def detect_circular_dependencies(
    self,
    skill_id: str,
    dependencies: list[str],
    visited: set[str] | None = None,
) -> tuple[bool, list[str] | None]:
    if visited is None:
        visited = set()

    if skill_id in visited:
        return True, [*visited, skill_id]

    visited.add(skill_id)

    for dep_id in dependencies:
        dep_meta = self.get_skill_metadata(dep_id) or self._try_load_skill_by_id(dep_id)
        if dep_meta is None:
            continue

        has_cycle, cycle_path = self.detect_circular_dependencies(
            dep_id, dep_meta.dependencies, visited.copy()
        )
        if has_cycle:
            return True, cycle_path

    return False, None
```

## Skill Registration

### Creating New Skills

```python
async def register_skill(
    self,
    path: str,
    metadata: dict[str, Any],
    content: str,
    evolution: dict[str, Any],
    extra_files: dict[str, Any] | None = None,
    overwrite: bool = False,
) -> bool:
    """Register a new skill in the taxonomy."""
    skill_metadata = register_skill(
        skills_root=self.skills_root,
        path=path,
        metadata=metadata,
        content=content,
        evolution=evolution,
        extra_files=extra_files,
        overwrite=overwrite,
    )

    # Update cache with lock protection
    async with self._cache_lock:
        self.metadata_cache[skill_metadata.skill_id] = skill_metadata

    # Update taxonomy stats
    self._update_taxonomy_stats(metadata)
    return True
```

### Directory Structure (v2 Golden Standard)

Created skills follow this structure:

```
skill-name/
├── SKILL.md                    # Main documentation with YAML frontmatter
├── metadata.json               # Extended metadata (optional in v2)
├── references/                 # Deep technical docs
│   └── README.md
├── guides/                     # Step-by-step workflows
│   └── README.md
├── templates/                  # Code templates
│   └── README.md
├── scripts/                    # Utility scripts
│   └── README.md
├── examples/                   # Usage examples
│   └── README.md
├── tests/                      # Integration tests
│   └── README.md
└── assets/                     # Static assets
    └── README.md
```

## Statistics Tracking

```python
def _update_taxonomy_stats(self, metadata: dict[str, Any]) -> None:
    stats = self.meta.setdefault("statistics", {})
    by_type = stats.setdefault("by_type", {})
    by_weight = stats.setdefault("by_weight", {})
    by_priority = stats.setdefault("by_priority", {})

    self.meta["total_skills"] = int(self.meta.get("total_skills", 0)) + 1
    self.meta["generation_count"] = int(self.meta.get("generation_count", 0)) + 1
    self.meta["last_updated"] = datetime.now(tz=UTC).isoformat()

    skill_type = str(metadata.get("type", "unknown"))
    by_type[skill_type] = int(by_type.get(skill_type, 0)) + 1

    skill_weight = str(metadata.get("weight", "unknown"))
    by_weight[skill_weight] = int(by_weight.get(skill_weight, 0)) + 1

    skill_priority = str(metadata.get("load_priority", "unknown"))
    by_priority[skill_priority] = int(by_priority.get(skill_priority, 0)) + 1

    self.meta_path.write_text(json.dumps(self.meta, indent=2) + "\n", encoding="utf-8")
```

## Security

### Path Traversal Protection

All filesystem operations use `resolve_path_within_root()`:

```python
from ..common.security import resolve_path_within_root

safe_path = resolve_path_within_root(self.skills_root, relative_path)
```

### Containment Checks

```python
def _resolve_existing_path_within_dir(
    self, *, base_dir: Path, relative_path: str, label: str
) -> tuple[Path | None, str | None]:
    base_dir_resolved = base_dir.resolve()
    sanitized = sanitize_relative_file_path(relative_path)

    candidate = base_dir_resolved.joinpath(sanitized)

    # Security: verify containment BEFORE resolving
    base_str = os.fspath(base_dir_resolved)
    candidate_str = os.fspath(candidate)
    if os.path.commonpath([base_str, candidate_str]) != base_str:
        return None, f"{label} path not allowed"

    resolved = candidate.resolve(strict=True)
    return resolved, None
```

## Async Support

The manager provides async wrappers for I/O operations:

```python
async def aload_skill_dir_metadata(self, skill_dir: Path) -> InfrastructureSkillMetadata:
    """Async version of _load_skill_dir_metadata."""
    return await asyncio.to_thread(self._load_skill_dir_metadata, skill_dir)

async def aresolve_skill_location(
    self, skill_identifier: str, progress_callback: Any | None = None
) -> str:
    """Async version with optional progress reporting."""
    if progress_callback:
        await progress_callback(f"Resolving skill: {skill_identifier}")

    result = await asyncio.to_thread(
        resolve_skill_location, skill_identifier, self.skills_root, self.index
    )
    return result
```

## Related Components

- `SkillValidator` - Validates taxonomy paths and skill structure
- `SkillService` - Uses TaxonomyManager for skill operations
- `TaxonomyCategory` (DB) - Database taxonomy representation
- `SkillAlias` (DB) - Database alias storage

## References

- `src/skill_fleet/taxonomy/manager.py` - TaxonomyManager
- `src/skill_fleet/taxonomy/models.py` - TaxonomyIndex, SkillEntry
- `src/skill_fleet/taxonomy/skill_loader.py` - Loading functions
- `src/skill_fleet/taxonomy/skill_registration.py` - Registration logic
- `src/skill_fleet/taxonomy/discovery.py` - XML generation
- `src/skill_fleet/common/security.py` - Path security utilities
