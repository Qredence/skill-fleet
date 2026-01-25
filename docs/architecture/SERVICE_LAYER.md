# Service Layer Architecture

**Last Updated**: 2026-01-25

## Overview

The Service Layer sits between the API routes and the domain layer, orchestrating business logic and coordinating domain objects to accomplish use cases. It provides application-level services that encapsulate workflows and coordinate interactions between multiple domain objects.

`★ Insight ─────────────────────────────────────`
Services are stateful coordinators, not just function containers. They inherit from BaseService which provides dependency injection for repositories, LLM clients, and configuration. This makes services testable with mocks and allows easy swapping of implementations.
`─────────────────────────────────────────────────`

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      API Routes                              │
│                   (FastAPI Endpoints)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ SkillService   │  │JobService    │  │ TaxonomyService │ │
│  │                │  │              │  │                │ │
│  │ • Create       │  │ • Execute    │  │ • Navigate     │ │
│  │ • Validate     │  │ • Poll       │  │ • Search       │ │
│  │ • Refine       │  │ • HITL       │  │ • Update       │ │
│  └────────────────┘  └──────────────┘  └────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                             │
│  • Entities (Skill, Job)                                    │
│  • Value Objects (TaxonomyPath, SkillMetadata)              │
│  • Specifications (business rules)                          │
│  • Domain Services (business logic)                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  • Repositories (data access)                               │
│  • External APIs (LLM providers)                            │
│  • File System (skills storage)                             │
└─────────────────────────────────────────────────────────────┘
```

## BaseService

All application services inherit from `BaseService`, which provides:

### Dependency Injection

```python
from skill_fleet.core.services import BaseService

class CustomService(BaseService):
    """Custom service with injected dependencies."""

    async def initialize(self):
        """Initialize service (called by constructor)."""
        # Access injected dependencies
        self.skill_repo = self.skill_repository
        self.job_repo = self.job_repository
        self.lm_client = self.lm_client
        self.config = self.config
```

### Available Dependencies

```python
# In BaseService
self.skill_repository  # SkillRepository instance
self.job_repository    # JobRepository instance
self.taxonomy_repository  # TaxonomyRepository instance
self.lm_client        # LLM client (DSPy)
self.config           # Application configuration
self.logger           # Logger instance
```

## Service Types

### 1. SkillService

Orchestrates skill-related operations.

```python
from skill_fleet.services import SkillService  # Future: from core.services

service = SkillService()

# Create skill with workflow
job = await service.create_skill(
    task_description="Create a Redis caching skill",
    user_id="user-123",
    taxonomy_path="redis/caching",
)

# Validate skill
report = await service.validate_skill(skill_id="redis-caching")

# Refine skill
result = await service.refine_skill(
    skill_id="redis-caching",
    feedback="Add more pipeline examples",
)

# Search skills
skills = await service.search_skills(query="caching", limit=10)
```

### 2. JobService

Manages background job lifecycle.

```python
from skill_fleet.core.services import JobService

service = JobService()

# Execute job
job = await service.execute_job(
    task_description="Create skill",
    user_id="user-123",
)

# Poll job status
status = await service.get_job_status(job_id="job-123")

# Handle HITL
prompt = await service.get_hitl_prompt(job_id="job-123")
await service.submit_hitl_response(
    job_id="job-123",
    action="proceed",
    response="intermediate",
)

# Retry failed job
job = await service.retry_job(job_id="job-123")
```

### 3. ConversationService

Manages conversational interactions.

```python
from skill_fleet.core.services import ConversationService

service = ConversationService()

# Create or get session
session = await service.get_or_create_session(
    session_id="sess-123",
    user_id="user-456",
)

# Process message
response = await service.process_message(
    session=session,
    message="Create a Python decorators skill",
    context={},
)

# Stream response
async for event in service.stream_response(
    session=session,
    message="Help me with caching",
):
    yield event
```

## Dependency Injection

### Constructor Injection

```python
from skill_fleet.core.services import BaseService

class MyService(BaseService):
    def __init__(
        self,
        skill_repository=None,
        job_repository=None,
        lm_client=None,
    ):
        super().__init__(
            skill_repository=skill_repository,
            job_repository=job_repository,
            lm_client=lm_client,
        )
        # Custom initialization
        self.custom_state = {}
```

### Usage in API Routes

```python
from fastapi import Depends
from skill_fleet.api.dependencies import get_skill_service

@router.post("/skills")
async def create_skill(
    request: CreateSkillRequest,
    skill_service: SkillService = Depends(get_skill_service),
):
    """Create skill using injected service."""
    job = await skill_service.create_skill(
        task_description=request.task_description,
        user_id=request.user_id,
    )
    return {"job_id": job.job_id}
```

## MLflow Integration

Services automatically integrate with MLflow for tracking:

### Hierarchical Runs

```python
# Parent run
with mlflow.start_run(run_name="skill_creation"):
    mlflow.set_tag("user_id", "user-123")
    mlflow.set_tag("job_id", "job-456")

    # Child runs for each phase
    with mlflow.start_run(run_name="understanding", nested=True):
        # Phase 1 tracking
        mlflow.set_tag("phase", "understanding")
        mlflow.log_metric("llm_calls", 5)

    with mlflow.start_run(run_name="generation", nested=True):
        # Phase 2 tracking
        mlflow.set_tag("phase", "generation")
        mlflow.log_metric("llm_calls", 3)

    with mlflow.start_run(run_name="validation", nested=True):
        # Phase 3 tracking
        mlflow.set_tag("phase", "validation")
        mlflow.log_metric("quality_score", 0.85)
```

### Automatic Tagging

```python
# BaseService automatically tags runs
mlflow.set_tag("service", self.__class__.__name__)
mlflow.set_tag("user_id", user_id)
mlflow.set_tag("skill_type", skill_type)
mlflow.set_tag("model", model_name)
```

### Artifact Logging

```python
# Log skill content as artifact
mlflow.log_text(
    skill_content,
    artifact_file="skill_content.md"
)

# Log metadata
mlflow.log_dict(
    metadata_dict,
    artifact_file="metadata.json"
)

# Log validation report
mlflow.log_dict(
    validation_report,
    artifact_file="validation_report.json"
)
```

## Extension Points

### Adding New Service Methods

```python
from skill_fleet.core.services import SkillService

class ExtendedSkillService(SkillService):
    """Extended skill service with custom methods."""

    async def bulk_validate(self, skill_ids: list[str]) -> dict:
        """Validate multiple skills in parallel."""
        results = {}
        for skill_id in skill_ids:
            results[skill_id] = await self.validate_skill(skill_id)
        return results

    async def export_skill(self, skill_id: str, format: str) -> str:
        """Export skill in specified format."""
        skill = await self.skill_repository.get(skill_id)
        if format == "json":
            return skill.metadata.to_dict()
        elif format == "markdown":
            return skill.content
        else:
            raise ValueError(f"Unknown format: {format}")
```

### Custom Service with Dependencies

```python
from skill_fleet.core.services import BaseService
from skill_fleet.domain import SkillRepository

class AnalyticsService(BaseService):
    """Analytics service with custom dependencies."""

    def __init__(self, skill_repository: SkillRepository = None):
        super().__init__(skill_repository=skill_repository)
        self.analytics_db = None  # Custom dependency

    async def get_skill_usage_stats(self, skill_id: str) -> dict:
        """Get usage statistics for a skill."""
        skill = await self.skill_repository.get(skill_id)
        # Analytics logic
        return {
            "skill_id": skill_id,
            "usage_count": 42,
            "last_used": "2026-01-25",
        }
```

## Error Handling

### Service Errors

```python
from skill_fleet.core.services import ServiceError, ValidationError

class SkillService(BaseService):
    async def create_skill(self, task_description: str, user_id: str):
        # Validation
        if len(task_description) < 10:
            raise ValidationError(
                "Task description must be at least 10 characters"
            )

        # Business logic
        try:
            job = await self._execute_workflow(task_description, user_id)
        except Exception as e:
            self.logger.error(f"Skill creation failed: {e}")
            raise ServiceError(f"Failed to create skill: {e}")

        return job
```

### Error Types

```python
from skill_fleet.core.services import (
    ServiceError,       # Base service error
    ValidationError,    # Input validation failed
    ConfigurationError, # Configuration issue
)

# Usage
raise ValidationError("Invalid skill ID format")
raise ConfigurationError("LLM client not configured")
raise ServiceError("Failed to process skill creation")
```

## Testing Services

### Unit Testing with Mocks

```python
import pytest
from skill_fleet.core.services import SkillService
from skill_fleet.domain import Skill, SkillMetadata

@pytest.mark.asyncio
async def test_create_skill():
    # Arrange
    mock_repo = Mock(spec=SkillRepository)
    mock_repo.save.return_value = Skill(
        metadata=SkillMetadata(
            skill_id="test",
            name="test",
            description="Test skill"
        ),
        content="content"
    )

    service = SkillService(skill_repository=mock_repo)

    # Act
    skill = await service.create_skill(
        task_description="Test skill",
        user_id="user-123"
    )

    # Assert
    assert skill.skill_id == "test"
    mock_repo.save.assert_called_once()
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_skill_creation_workflow():
    # Use real repositories with test database
    service = SkillService(
        skill_repository=TestSkillRepository(),
        job_repository=TestJobRepository(),
    )

    job = await service.create_skill(
        task_description="Create a test skill",
        user_id="test-user"
    )

    assert job.status == JobStatus.PENDING
```

## Configuration

### Service Configuration

```python
# In config/config.yaml
services:
  skill_service:
    cache_ttl: 300
    max_concurrent_jobs: 10
    default_skill_type: "guide"

  job_service:
    job_timeout: 3600
    cleanup_interval: 300
    max_retries: 3

  conversation_service:
    session_timeout: 3600
    max_message_history: 100
```

### Accessing Configuration

```python
class MyService(BaseService):
    async def initialize(self):
        # Access service-specific config
        cache_ttl = self.config.get("services.skill_service.cache_ttl", 300)
        self.cache_ttl = cache_ttl
```

## Best Practices

### 1. Keep Services Thin

```python
# ✅ Good: Service orchestrates, domain has logic
class SkillService(BaseService):
    async def create_skill(self, description: str):
        # Validation
        self._validate_description(description)

        # Orchestrate
        skill = self._build_skill(description)
        await self.skill_repository.save(skill)

        # Domain logic in domain layer
        if not SkillIsReadyForPublication().is_satisfied_by(skill):
            raise ValidationError("Skill not ready")

# ❌ Avoid: Business logic in service
class SkillService(BaseService):
    async def is_skill_valid(self, skill: Skill) -> bool:
        # This belongs in domain specifications
        return bool(skill.name and skill.description and len(skill.name) > 3)
```

### 2. Use Domain Services for Complex Logic

```python
# ✅ Good: Delegate to domain service
class SkillService(BaseService):
    async def calculate_overlap(self, skill1: Skill, skill2: Skill):
        domain_service = SkillDomainService(self.skill_repository)
        return await domain_service.calculate_overlap(skill1, skill2)

# ❌ Avoid: Implementing domain logic in application service
class SkillService(BaseService):
    async def calculate_overlap(self, skill1: Skill, skill2: Skill):
        # Complex overlap calculation belongs in domain
        # This is domain logic, not application orchestration
        ...
```

### 3. Handle Errors Appropriately

```python
# ✅ Good: Specific error handling
try:
    job = await self.job_repository.get(job_id)
except NotFoundError:
    raise NotFoundException("Job", job_id)
except DatabaseError as e:
    self.logger.error(f"Database error: {e}")
    raise ServiceError("Failed to retrieve job")

# ❌ Avoid: Generic error handling
try:
    job = await self.job_repository.get(job_id)
except Exception:
    raise ServiceError("Something went wrong")  # Not helpful
```

## See Also

- **[Domain Layer](DOMAIN_LAYER.md)** - Domain entities and specifications
- **[Import Path Guide](../development/IMPORT_PATH_GUIDE.md)** - Service import patterns
- **[Service Extension Guide](../development/SERVICE_EXTENSION_GUIDE.md)** - Extending services
