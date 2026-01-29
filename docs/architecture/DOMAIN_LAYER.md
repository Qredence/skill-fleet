# Domain Layer Architecture

**Last Updated**: 2026-01-25

## Overview

The Domain Layer implements Domain-Driven Design (DDD) patterns to separate core business logic from infrastructure and API concerns. It provides a rich domain model with entities, value objects, specifications, and domain services.

`★ Insight ─────────────────────────────────────`
The domain layer is the heart of the application, independent of frameworks and databases. By using DDD patterns like Specifications and Domain Events, we can express complex business rules explicitly and test them in isolation without external dependencies.
`─────────────────────────────────────────────────`

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       API Layer                              │
│                   (FastAPI Routes)                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│            (Application Services, Orchestration)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Domain Layer                               │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Domain Models │  │ Specifications│  │Domain Services│  │
│  │  (Entities,     │  │  (Business    │  │ (Business     │  │
│  │   Value Objects)│  │   Rules)     │  │  Logic)      │  │
│  └─────────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               Infrastructure Layer                           │
│         (Repositories, Database, External APIs)              │
└─────────────────────────────────────────────────────────────┘
```

## Domain Models

### Entities

#### Skill

The core entity representing a skill in the taxonomy.

```python
from skill_fleet.domain import Skill, SkillMetadata, TaxonomyPath

# Create a skill
skill = Skill(
    metadata=SkillMetadata(
        skill_id="python-async-await",
        name="python-async-await",
        description="Proficiency with Python's async/await syntax",
        version="1.0.0",
        type=SkillType.GUIDE,
        weight=SkillWeight.MEDIUM,
        taxonomy_path="python/async-await",
    ),
    content="# Python Async/Await\n\n...",
)

# Access properties
skill_id = skill.skill_id  # From metadata
path = skill.taxonomy_path  # Returns TaxonomyPath value object
is_ready = skill.is_always_loaded()  # Domain behavior
```

**Key Properties**:
- `metadata`: SkillMetadata (name, description, type, etc.)
- `content`: Markdown content
- `extra_files`: Additional files (assets, examples)
- `path`: File system location (infrastructure concern)

**Domain Behaviors**:
- `has_capability(capability)`: Check if skill has a capability
- `has_dependency(skill_id)`: Check if skill depends on another
- `is_always_loaded()`: Check if skill should be auto-loaded

#### Job

Entity representing a background skill creation job.

```python
from skill_fleet.domain import Job, JobStatus

# Create a job
job = Job(
    job_id="abc-123",
    task_description="Create a Redis caching skill",
    user_id="user_456",
    status=JobStatus.PENDING,
)

# Domain behaviors
if job.is_running():
    print("Job is in progress")

if job.is_terminal():
    if job.status == JobStatus.COMPLETED:
        print(f"Success: {job.result}")
    else:
        print(f"Failed: {job.error}")

# Update progress
job.update_progress("generation", "Creating skill content...")

# Mark as completed
job.mark_completed(result=skill_creation_result)
```

**Status Lifecycle**:
```
PENDING → RUNNING → PENDING_HITL → RUNNING → COMPLETED
                        ↓
                      FAILED
```

### Value Objects

#### TaxonomyPath

Immutable value object representing a path in the skill taxonomy.

```python
from skill_fleet.domain import TaxonomyPath

# Create a path (validates and sanitizes)
path = TaxonomyPath("python/async-await")

# Path operations
parent = path.parent()  # TaxonomyPath("python")
child = path.child("basics")  # TaxonomyPath("python/async-await/basics")
depth = path.depth()  # 2

# String representation
str(path)  # "python/async-await"
```

**Validation**:
- Path cannot be empty
- Sanitized to prevent directory traversal attacks
- Uses kebab-case formatting

#### SkillMetadata

Value object containing skill metadata.

```python
from skill_fleet.domain import SkillMetadata, SkillType, SkillWeight, LoadPriority

metadata = SkillMetadata(
    skill_id="python-decorators",
    name="python-decorators",
    description="Ability to design and implement Python decorators",
    version="1.0.0",
    type=SkillType.GUIDE,
    weight=SkillWeight.MEDIUM,
    load_priority=LoadPriority.ON_DEMAND,
    dependencies=["python-functions", "python-closures"],
    capabilities=["code-generation", "code-review"],
)
```

### Enums

```python
from skill_fleet.domain import SkillType, SkillWeight, LoadPriority, JobStatus

# Skill Type
SkillType.GUIDE             # Educational content
SkillType.TOOL_INTEGRATION  # External tool integration
SkillType.WORKFLOW          # Multi-step process
SkillType.REFERENCE         # Reference material
SkillType.MEMORY_BLOCK      # Knowledge base

# Skill Weight (contribution/importance)
SkillWeight.LIGHT    # Small, focused skill
SkillWeight.MEDIUM   # Standard skill
SkillWeight.HEAVY    # Large, comprehensive skill

# Load Priority
LoadPriority.ALWAYS_LOADED  # Load at startup
LoadPriority.ON_DEMAND      # Load when needed
LoadPriority.LAZY           # Lazy loading

# Job Status
JobStatus.PENDING       # Queued
JobStatus.RUNNING       # In progress
JobStatus.PENDING_HITL  # Awaiting human input
JobStatus.COMPLETED     # Finished successfully
JobStatus.FAILED        # Failed with error
```

## Specifications

The Specification pattern encapsulates business rules as composable predicates.

### Base Specification

```python
from skill_fleet.domain import Specification

class CustomSpecification(Specification):
    def is_satisfied_by(self, candidate: Any) -> bool:
        # Your business rule logic
        return True
```

### Composable Specifications

```python
from skill_fleet.domain import (
    SkillIsReadyForPublication,
    SkillHasValidName,
    SkillHasValidType,
    AndSpecification,
    OrSpecification,
)

# Single specification
spec = SkillIsReadyForPublication(require_content=True)
if spec.is_satisfied_by(skill):
    print("Skill is ready to publish")

# Composed with AND
ready_and_valid = SkillIsReadyForPublication().and_spec(SkillHasValidName())

# Composed with OR
complete_or_draft = SkillIsComplete().or_spec(SkillIsDraft())
```

### Built-in Specifications

#### Skill Specifications

```python
from skill_fleet.domain import (
    SkillHasValidName,
    SkillHasValidType,
    SkillHasValidTaxonomyPath,
    SkillIsComplete,
    SkillIsReadyForPublication,
)

# Name validation (1-64 chars, kebab-case)
SkillHasValidName().is_satisfied_by(skill)  # bool

# Type validation
SkillHasValidType().is_satisfied_by(skill)  # bool

# Taxonomy path validation
SkillHasValidTaxonomyPath().is_satisfied_by(skill)  # bool

# Completeness check
SkillIsComplete().is_satisfied_by(skill)  # bool

# Publication readiness (composite spec)
SkillIsReadyForPublication(require_content=True).is_satisfied_by(skill)
```

#### Job Specifications

```python
from skill_fleet.domain import (
    JobHasValidDescription,
    JobIsPending,
    JobIsRunning,
    JobIsTerminal,
    JobCanBeStarted,
    JobCanBeRetried,
    JobRequiresHITL,
    JobIsStale,
)

# Check if job can be started
JobCanBeStarted().is_satisfied_by(job)  # True if pending + valid description

# Check if job needs human input
JobRequiresHITL().is_satisfied_by(job)  # True if status is PENDING_HITL

# Check if job is stale (running too long)
JobIsStale(max_age_seconds=3600).is_satisfied_by(job)

# Check if job can be retried
JobCanBeRetried().is_satisfied_by(job)  # True if failed
```

### Creating Custom Specifications

```python
from skill_fleet.domain import SkillSpecification, Skill

class SkillHasMinimumCapability(SkillSpecification):
    """Specification for skills with required capability."""

    def __init__(self, capability: str):
        self.capability = capability

    def _is_satisfied_by(self, skill: Skill) -> bool:
        return skill.has_capability(self.capability)

# Use it
spec = SkillHasMinimumCapability("code-generation")
if spec.is_satisfied_by(skill):
    print("Skill can generate code")
```

## Domain Services

Domain services contain business logic that doesn't naturally fit within a single entity.

```python
from skill_fleet.domain import (
    SkillDomainService,
    JobDomainService,
    TaxonomyDomainService,
)

# Skill Domain Service
skill_service = SkillDomainService(skill_repository)
can_publish = skill_service.can_publish(skill)
overlap_score = skill_service.calculate_overlap(skill1, skill2)

# Job Domain Service
job_service = JobDomainService(job_repository)
can_start = job_service.can_start(job)

# Taxonomy Domain Service
taxonomy_service = TaxonomyDomainService(taxonomy_repository)
path_exists = taxonomy_service.path_exists(taxonomy_path)
```

## Domain Events

Domain events represent something that happened in the domain that other parts of the system may need to react to.

```python
from skill_fleet.domain import SkillCreatedEvent, JobCompletedEvent
from datetime import datetime, UTC

# Skill created event
event = SkillCreatedEvent(
    event_id="evt-123",
    occurred_at=datetime.now(UTC),
    skill_id="python-async",
    taxonomy_path="python/async",
    user_id="user-456",
)

# Job completed event
event = JobCompletedEvent(
    event_id="evt-456",
    occurred_at=datetime.now(UTC),
    job_id="job-abc",
    status=JobStatus.COMPLETED,
    result=skill_result,
)
```

**Usage Pattern** (future enhancement):
```python
# In domain service
def publish_skill(self, skill: Skill) -> Skill:
    skill.mark_as_published()
    # Publish event
    self.event_dispatcher.dispatch(SkillPublishedEvent(
        skill_id=skill.skill_id,
        user_id=skill.user_id,
    ))
    return skill
```

## Repository Interfaces

The domain layer defines repository interfaces that infrastructure implementations must fulfill.

```python
from skill_fleet.domain import SkillRepository, JobRepository, TaxonomyRepository

# These are interfaces - implementations are in infrastructure layer

class SkillRepository(ABC):
    @abstractmethod
    async def get(self, skill_id: str) -> Skill | None:
        pass

    @abstractmethod
    async def save(self, skill: Skill) -> None:
        pass

    @abstractmethod
    async def find_by_path(self, path: TaxonomyPath) -> Skill | None:
        pass

class JobRepository(ABC):
    @abstractmethod
    async def get(self, job_id: str) -> Job | None:
        pass

    @abstractmethod
    async def save(self, job: Job) -> None:
        pass

class TaxonomyRepository(ABC):
    @abstractmethod
    async def get_path(self, path: str) -> TaxonomyPath | None:
        pass
```

## Import Guidelines

```python
# Import all domain components from one place
from skill_fleet.domain import (
    # Models
    Skill,
    SkillMetadata,
    Job,
    JobStatus,
    TaxonomyPath,
    SkillType,
    # Specifications
    SkillIsReadyForPublication,
    JobCanBeStarted,
    AndSpecification,
    # Domain Services
    SkillDomainService,
    # Repository Interfaces
    SkillRepository,
)
```

## Best Practices

1. **Keep domain logic pure**: Domain models should not depend on external services
2. **Use specifications for rules**: Business rules should be encapsulated in specifications
3. **Value objects are immutable**: They should not be modified after creation
4. **Entities have identity**: Entities are identified by their ID, not their attributes
5. **Domain services for cross-entity logic**: Logic that involves multiple entities goes in domain services

## Testing Domain Logic

```python
import pytest
from skill_fleet.domain import Skill, SkillMetadata, SkillIsReadyForPublication

def test_skill_is_ready_for_publication():
    skill = Skill(
        metadata=SkillMetadata(
            skill_id="test-skill",
            name="test-skill",
            description="A test skill",
        ),
        content="# Test\n\nContent here",
    )

    spec = SkillIsReadyForPublication(require_content=True)
    assert spec.is_satisfied_by(skill) is True
```

## See Also

- **[Import Path Guide](../development/IMPORT_PATH_GUIDE.md)** - Import patterns for domain layer
- **[Service Layer](SERVICE_LAYER.md)** - Application service architecture
- **[Restructuring Status](restructuring-status.md)** - Architecture evolution
