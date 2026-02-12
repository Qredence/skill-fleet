# Database Relationships Architecture

## Overview

Skill Fleet uses SQLAlchemy ORM with a comprehensive database schema supporting skills taxonomy, dependency graphs, usage analytics, and workflow tracking. The schema is designed for PostgreSQL with SQLite fallback for development.

## Core Entity: `Skill`

**Location:** `src/skill_fleet/infrastructure/db/models.py:220`

The `Skill` entity is the central domain object with rich relationships to support discovery, dependencies, and lifecycle management.

### Skill Relationships Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           Skill                                  │
│  (skill_id, skill_path, name, description, content, ...)        │
└─────────────────────────────────────────────────────────────────┘
     │           │           │           │           │
     ▼           ▼           ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│Capability│ │SkillFile│ │SkillTag │ │SkillAlias│ │SkillFacet│
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
     │           │           │
     ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│SkillKeyword│ │SkillCategory│ │SkillAllowedTool│
└─────────┘ └─────────┘ └─────────┘
                 │
                 ▼
          ┌──────────────┐
          │TaxonomyCategory│
          └──────────────┘
```

### Self-Referential Relationships

```
┌─────────┐         parent_version_id         ┌─────────┐
│  Skill  │◄─────────────────────────────────►│  Skill  │
│ (child) │         child_versions             │ (parent)│
└─────────┘                                     └─────────┘
```

Used for skill versioning and evolution tracking.

## Relationship Details

### 1. Capabilities (One-to-Many)

**Entity:** `Capability` (`models.py:571`)

A skill can have multiple discrete capabilities.

```python
class Skill(Base):
    capabilities: Mapped[list["Capability"]] = relationship(
        "Capability", back_populates="skill", cascade="all, delete-orphan"
    )

class Capability(Base):
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id"))
    skill: Mapped["Skill"] = relationship("Skill", back_populates="capabilities")
    name: Mapped[str]
    description: Mapped[str]
    test_criteria: Mapped[str | None]
```

### 2. Dependencies (Many-to-Many via Association)

**Entity:** `SkillDependency` (`models.py:597`)

Skills can depend on other skills with typed relationships.

```python
class Skill(Base):
    # Skills this skill depends on
    dependencies_as_dependent: Mapped[list["SkillDependency"]] = relationship(
        "SkillDependency",
        foreign_keys="SkillDependency.dependent_id",
        back_populates="dependent"
    )
    # Skills that depend on this skill
    dependencies_as_dependency: Mapped[list["SkillDependency"]] = relationship(
        "SkillDependency",
        foreign_keys="SkillDependency.dependency_skill_id",
        back_populates="dependency_skill"
    )

class SkillDependency(Base):
    dependent_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id"))
    dependency_skill_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id"))
    dependency_type: Mapped[str]  # REQUIRED, RECOMMENDED, CONFLICT
    justification: Mapped[str | None]

    dependent: Mapped["Skill"] = relationship(..., foreign_keys=[dependent_id])
    dependency_skill: Mapped["Skill"] = relationship(..., foreign_keys=[dependency_skill_id])
```

**Dependency Types:**
- `REQUIRED` - Must have this skill loaded
- `RECOMMENDED` - Enhances functionality but optional
- `CONFLICT` - Incompatible with this skill

### 3. Files (One-to-Many)

**Entity:** `SkillFile` (`models.py:751`)

Associated resources and documentation files.

```python
class SkillFile(Base):
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id"))
    skill: Mapped["Skill"] = relationship("Skill", back_populates="files")
    file_type: Mapped[str]  # REFERENCE, GUIDE, TEMPLATE, SCRIPT, EXAMPLE, ASSET, TEST
    relative_path: Mapped[str]
    content: Mapped[str | None]
    binary_data: Mapped[bytes | None]
```

### 4. Discovery Fields

#### Keywords (One-to-Many)
**Entity:** `SkillKeyword` - Search terms with weights

#### Tags (One-to-Many)
**Entity:** `SkillTag` - User-defined categorization

#### Aliases (One-to-Many)
**Entity:** `SkillAlias` - Legacy path support for backward compatibility

#### Facets (One-to-Many)
**Entity:** `SkillFacet` - Multi-dimensional filtering (key-value pairs)

### 5. Categories (Many-to-Many)

**Entities:** `SkillCategory`, `TaxonomyCategory`

Hierarchical categorization with closure table for efficient tree queries.

```python
class SkillCategory(Base):  # Join table
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id"), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("taxonomy_categories.category_id"), primary_key=True)
    is_primary: Mapped[bool] = mapped_column(default=False)

class TaxonomyCategory(Base):
    category_id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(unique=True)  # e.g., "technical_skills/programming"
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("taxonomy_categories.category_id"))
    parent: Mapped[Optional["TaxonomyCategory"]] = relationship(remote_side=[category_id])
```

## Taxonomy Closure Table

**Entity:** `TaxonomyClosure` (`models.py:456`)

Enables efficient tree traversal queries.

```python
class TaxonomyClosure(Base):
    ancestor_id: Mapped[int] = mapped_column(ForeignKey("taxonomy_categories.category_id"), primary_key=True)
    descendant_id: Mapped[int] = mapped_column(ForeignKey("taxonomy_categories.category_id"), primary_key=True)
    depth: Mapped[int] = mapped_column(primary_key=True)
```

**Example Usage:**
```sql
-- Get all descendants of a category
SELECT descendant_id FROM taxonomy_closure WHERE ancestor_id = ?

-- Get all ancestors of a category
SELECT ancestor_id FROM taxonomy_closure WHERE descendant_id = ?
```

## Dependency Closure Table

**Entity:** `DependencyClosure` (`models.py:640`)

Pre-computed transitive dependencies for fast resolution.

```python
class DependencyClosure(Base):
    ancestor_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id"), primary_key=True)
    descendant_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id"), primary_key=True)
    min_depth: Mapped[int]
    dependency_types: Mapped[list[str]]
```

## Workflow Tracking

### Jobs

**Entity:** `Job` (`models.py:828`)

Background job tracking for skill creation workflows.

```python
class Job(Base):
    job_id: Mapped[UUID] = mapped_column(primary_key=True)
    status: Mapped[str]  # PENDING, RUNNING, PENDING_HITL, COMPLETED, FAILED, CANCELLED
    task_description: Mapped[str]
    result: Mapped[dict | None]
    error: Mapped[str | None]
    hitl_type: Mapped[str | None]
    hitl_data: Mapped[dict | None]

    hitl_interactions: Mapped[list["HITLInteraction"]] = relationship(...)
```

### HITL Interactions

**Entity:** `HITLInteraction` (`models.py:906`)

Tracks human-in-the-loop interactions.

```python
class HITLInteraction(Base):
    interaction_id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.job_id"))
    interaction_type: Mapped[str]  # CLARIFY, CONFIRM, PREVIEW, VALIDATE, TDD_RED, TDD_GREEN, TDD_REFACTOR
    round_number: Mapped[int]
    prompt_data: Mapped[dict]
    response_data: Mapped[dict | None]
```

### Conversation Sessions

**Entity:** `ConversationSession` (`models.py:1196`)

Persistent chat session storage.

```python
class ConversationSession(Base):
    session_id: Mapped[UUID] = mapped_column(primary_key=True)
    state: Mapped[str]  # EXPLORING, DEEP_UNDERSTANDING, CREATING, COMPLETE, etc.
    messages: Mapped[list] = mapped_column(JSONType())
    skill_draft: Mapped[dict | None]
    checklist_state: Mapped[dict]
```

## Validation & Quality

### Validation Reports

**Entity:** `ValidationReport` (`models.py:1006`)

Stores validation results with detailed check items.

```python
class ValidationReport(Base):
    report_id: Mapped[int] = mapped_column(primary_key=True)
    skill_id: Mapped[int | None] = mapped_column(ForeignKey("skills.skill_id"))
    job_id: Mapped[UUID | None] = mapped_column(ForeignKey("jobs.job_id"))
    status: Mapped[str]  # PASSED, FAILED, WARNINGS
    passed: Mapped[bool]
    score: Mapped[float]
    errors: Mapped[list[str] | None]
    warnings: Mapped[list[str] | None]

    checks: Mapped[list["ValidationCheck"]] = relationship(...)
```

### Test Coverage

**Entity:** `SkillTestCoverage` (`models.py:1093`)

Test coverage metrics per skill.

```python
class SkillTestCoverage(Base):
    coverage_id: Mapped[int] = mapped_column(primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id"))
    total_tests: Mapped[int]
    passing_tests: Mapped[int]
    failing_tests: Mapped[int]
    coverage_percent: Mapped[float | None]
```

## Analytics

### Usage Events

**Entity:** `UsageEvent` (`models.py:1129`)

Skill usage tracking for analytics.

```python
class UsageEvent(Base):
    event_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.skill_id"))
    user_id: Mapped[str]
    task_id: Mapped[UUID | None]
    success: Mapped[bool]
    duration_ms: Mapped[int | None]
    error_type: Mapped[str | None]
    occurred_at: Mapped[datetime]
```

### Tag Statistics

**Entity:** `TagStats` (`models.py:733`)

Tag popularity tracking.

```python
class TagStats(Base):
    tag: Mapped[str] = mapped_column(primary_key=True)
    usage_count: Mapped[int]
    last_used_at: Mapped[datetime | None]
```

## Enum Types

The schema uses SQLAlchemy enums for type safety:

```python
class SkillTypeEnum:
    COGNITIVE = "cognitive"
    TECHNICAL = "technical"
    DOMAIN = "domain"
    TOOL = "tool"
    MCP = "mcp"
    SPECIALIZATION = "specialization"
    TASK_FOCUS = "task_focus"
    MEMORY = "memory"

class SkillStatusEnum:
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class SkillWeightEnum:
    LIGHTWEIGHT = "lightweight"
    MEDIUM = "medium"
    HEAVYWEIGHT = "heavyweight"

class LoadPriorityEnum:
    ALWAYS = "always"
    TASK_SPECIFIC = "task_specific"
    ON_DEMAND = "on_demand"
    DORMANT = "dormant"
```

## Custom Types

### JSONType

Maps to JSONB on PostgreSQL, JSON on SQLite:

```python
class JSONType(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB)
        return dialect.type_descriptor(JSON)
```

### StringArrayType

Maps to ARRAY(String) on PostgreSQL, JSON on SQLite:

```python
class StringArrayType(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_ARRAY(String))
        return dialect.type_descriptor(JSON)
```

## Indexes

Key indexes for query performance:

```python
# Skills
Index("idx_skills_path", "skill_path")
Index("idx_skills_status", "status")
Index("idx_skills_status_type", "status", "type")
Index("idx_skills_version_lookup", "skill_path", "version")

# Taxonomy
Index("idx_taxonomy_path", "path")
Index("idx_taxonomy_closure_ancestor", "ancestor_id")
Index("idx_taxonomy_closure_descendant", "descendant_id")

# Dependencies
Index("idx_dependencies_dependent", "dependent_id")
Index("idx_dependencies_dependency", "dependency_skill_id")

# Jobs
Index("idx_jobs_status", "status")
Index("idx_jobs_user", "user_id")
Index("idx_jobs_polling", "user_id", "created_at")

# Usage
Index("idx_usage_events_skill", "skill_id")
Index("idx_usage_events_occurred_at", "occurred_at")
```

## Check Constraints

```python
# Skills
CheckConstraint("skill_path ~ '^[a-z0-9_-]+(?:/[a-z0-9_-]+)*$'", name="skill_path_format")
CheckConstraint("name ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="name_kebab_case")
CheckConstraint("version ~ '^\\d+\\.\\d+\\.\\d+$'", name="version_format")

# Dependencies
CheckConstraint("dependent_id != dependency_skill_id", name="no_self_dependency")

# Categories
CheckConstraint("parent_id IS NULL OR parent_id != category_id", name="category_no_loop")
```

## Related Components

- `SkillRepository` - Repository pattern for Skill CRUD
- `JobRepository` - Job persistence
- `SkillValidator` - Validation report storage
- `UsageTracker` - Usage event recording

## References

- `src/skill_fleet/infrastructure/db/models.py` - All database models
- `src/skill_fleet/infrastructure/db/repositories.py` - Repository implementations
- `migrations/` - Alembic migration files
