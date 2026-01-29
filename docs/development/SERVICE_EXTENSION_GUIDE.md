# Service Extension Guide

**Last Updated**: 2026-01-25

## Overview

This guide explains how to extend the Skills Fleet service layer with custom services, add new service methods, implement dependency injection patterns, and write tests for services.

`★ Insight ─────────────────────────────────────`
Services should be thin orchestrators that coordinate domain objects. Put business logic in domain entities, domain services, or specifications. Services are about workflow orchestration, not business rules.
`─────────────────────────────────────────────────`

## Table of Contents

- [Service Architecture](#service-architecture)
- [Creating a Custom Service](#creating-a-custom-service)
- [Adding Service Methods](#adding-service-methods)
- [Dependency Injection](#dependency-injection)
- [Testing Services](#testing-services)
- [Best Practices](#best-practices)

---

## Service Architecture

### BaseService

All services inherit from `BaseService`, which provides:

```python
class BaseService:
    """Base service with common dependencies."""

    def __init__(
        self,
        skill_repository: SkillRepository = None,
        job_repository: JobRepository = None,
        taxonomy_repository: TaxonomyRepository = None,
        lm_client: LMClient = None,
        config: Config = None,
    ):
        self.skill_repository = skill_repository or get_default_skill_repository()
        self.job_repository = job_repository or get_default_job_repository()
        self.taxonomy_repository = taxonomy_repository or get_default_taxonomy_repository()
        self.lm_client = lm_client or get_default_lm_client()
        self.config = config or get_config()
        self.logger = get_logger(self.__class__.__name__)
```

### Available Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| `skill_repository` | `SkillRepository` | Skill data access |
| `job_repository` | `JobRepository` | Job data access |
| `taxonomy_repository` | `TaxonomyRepository` | Taxonomy data access |
| `lm_client` | `LMClient` | LLM API client |
| `config` | `Config` | Application configuration |
| `logger` | `Logger` | Logging instance |

---

## Creating a Custom Service

### Step 1: Define the Service Class

```python
# src/skill_fleet/services/analytics.py
from skill_fleet.core.services import BaseService
from skill_fleet.domain import SkillRepository

class AnalyticsService(BaseService):
    """Service for analytics and metrics."""

    def __init__(
        self,
        skill_repository: SkillRepository = None,
        job_repository: JobRepository = None,
    ):
        super().__init__(
            skill_repository=skill_repository,
            job_repository=job_repository,
        )
        # Custom initialization
        self.analytics_db = None  # Could inject another dependency
```

### Step 2: Add Service Methods

```python
class AnalyticsService(BaseService):
    """Service for analytics and metrics."""

    async def get_skill_usage_stats(
        self,
        skill_id: str,
        time_range: str = "7d"
    ) -> dict:
        """
        Get usage statistics for a skill.

        Args:
            skill_id: Skill identifier
            time_range: Time range for stats (1d, 7d, 30d)

        Returns:
            Dictionary with usage statistics
        """
        # Validate input
        skill = await self.skill_repository.get(skill_id)
        if not skill:
            raise ValidationError(f"Skill not found: {skill_id}")

        # Business logic
        stats = await self._calculate_stats(skill_id, time_range)

        # Return result
        return {
            "skill_id": skill_id,
            "time_range": time_range,
            "usage_count": stats["count"],
            "last_used": stats["last_used"],
        }
```

### Step 3: Export from Services Package

```python
# src/skill_fleet/services/__init__.py
from .analytics import AnalyticsService

__all__ = [
    "BaseService",
    "AnalyticsService",
    # ... other exports
]
```

---

## Adding Service Methods

### Method Patterns

#### 1. Simple Query Method

```python
async def get_skill_count(self) -> int:
    """Get total number of skills."""
    return await self.skill_repository.count()
```

#### 2. Validation + Business Logic Method

```python
async def promote_skill(self, skill_id: str) -> Skill:
    """Promote a skill to published status."""
    # Get skill
    skill = await self.skill_repository.get(skill_id)
    if not skill:
        raise NotFoundException("Skill", skill_id)

    # Use specification for validation
    from skill_fleet.domain import SkillIsReadyForPublication
    if not SkillIsReadyForPublication().is_satisfied_by(skill):
        raise ValidationError("Skill is not ready for publication")

    # Business logic
    skill.mark_as_published()
    await self.skill_repository.save(skill)

    return skill
```

#### 3. Orchestrating Multiple Domain Objects

```python
async def create_skill_with_dependencies(
    self,
    main_skill_data: dict,
    dependencies: list[str]
) -> Skill:
    """Create a skill with dependency resolution."""
    # Validate dependencies exist
    for dep_id in dependencies:
        dep = await self.skill_repository.get(dep_id)
        if not dep:
            raise ValidationError(f"Dependency not found: {dep_id}")

    # Create main skill
    skill = Skill(
        metadata=SkillMetadata(**main_skill_data),
        dependencies=dependencies,
    )

    # Save
    await self.skill_repository.save(skill)

    return skill
```

#### 4. Async Job Orchestration

```python
async def execute_skill_creation_workflow(
    self,
    task_description: str,
    user_id: str
) -> Job:
    """Execute the full skill creation workflow."""
    # Create job
    job = Job(
        task_description=task_description,
        user_id=user_id,
        status=JobStatus.PENDING,
    )
    await self.job_repository.save(job)

    # Execute workflow (async)
    try:
        job.status = JobStatus.RUNNING
        await self.job_repository.save(job)

        # Phase 1: Understanding
        result = await self._phase1_understand(job)

        # Phase 2: Generation
        result = await self._phase2_generate(job, result)

        # Phase 3: Validation
        result = await self._phase3_validate(job, result)

        job.mark_completed(result)
    except Exception as e:
        job.mark_failed(str(e))

    await self.job_repository.save(job)
    return job
```

---

## Dependency Injection

### Constructor Injection

```python
class MyService(BaseService):
    def __init__(
        self,
        skill_repository: SkillRepository = None,
        custom_dependency: CustomService = None,
    ):
        super().__init__(skill_repository=skill_repository)
        self.custom = custom_dependency or CustomService()
```

### Using in API Routes

```python
from fastapi import Depends
from skill_fleet.api.dependencies import get_analytics_service

@router.get("/analytics/{skill_id}")
async def get_analytics(
    skill_id: str,
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Get analytics for a skill."""
    return await analytics.get_skill_usage_stats(skill_id)
```

### Creating Dependency Providers

```python
# src/skill_fleet/api/dependencies.py
from fastapi import Depends
from skill_fleet.services import AnalyticsService

async def get_analytics_service() -> AnalyticsService:
    """Provide analytics service instance."""
    return AnalyticsService()

# Or with singleton pattern
_analytics_service: AnalyticsService | None = None

async def get_analytics_service_singleton() -> AnalyticsService:
    """Provide singleton analytics service."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
```

---

## Testing Services

### Unit Testing with Mocks

```python
import pytest
from unittest.mock import Mock
from skill_fleet.services import AnalyticsService
from skill_fleet.domain import Skill, SkillMetadata

@pytest.mark.asyncio
async def test_get_skill_usage_stats():
    # Arrange
    mock_repo = Mock()
    mock_repo.get.return_value = Skill(
        metadata=SkillMetadata(
            skill_id="test-skill",
            name="test",
            description="Test skill"
        ),
        content="content"
    )

    service = AnalyticsService(skill_repository=mock_repo)

    # Act
    result = await service.get_skill_usage_stats("test-skill", "7d")

    # Assert
    assert result["skill_id"] == "test-skill"
    assert "usage_count" in result
    mock_repo.get.assert_called_once_with("test-skill")
```

### Integration Testing with Fixtures

```python
@pytest.fixture
async def skill_service(test_db):
    """Provide service with test database."""
    repo = TestSkillRepository(test_db)
    service = SkillService(skill_repository=repo)
    yield service
    # Cleanup
    await repo.close()

@pytest.mark.asyncio
async def test_create_skill_integration(skill_service):
    """Test skill creation with real dependencies."""
    result = await skill_service.create_skill(
        task_description="Test skill",
        user_id="test-user"
    )

    assert result.job_id is not None
    assert result.status == JobStatus.PENDING
```

### Testing Error Handling

```python
@pytest.mark.asyncio
async def test_promote_nonexistent_skill():
    """Test promoting non-existent skill raises error."""
    mock_repo = Mock()
    mock_repo.get.return_value = None

    service = SkillService(skill_repository=mock_repo)

    with pytest.raises(ValidationError, match="not found"):
        await service.promote_skill("nonexistent")
```

---

## Best Practices

### 1. Keep Services Thin

```python
# ✅ Good: Service orchestrates
class SkillService(BaseService):
    async def publish_skill(self, skill_id: str) -> Skill:
        skill = await self.skill_repository.get(skill_id)
        # Domain logic in domain layer
        if not SkillIsReadyForPublication().is_satisfied_by(skill):
            raise ValidationError("Not ready")
        return await self.skill_domain_service.publish(skill)

# ❌ Avoid: Business logic in service
class SkillService(BaseService):
    async def is_skill_valid(self, skill: Skill) -> bool:
        # This belongs in domain specifications
        return bool(skill.name and len(skill.name) > 3)
```

### 2. Use Domain Services for Complex Logic

```python
# ✅ Good: Delegate to domain service
class SkillService(BaseService):
    async def calculate_overlap(self, skill1: Skill, skill2: Skill):
        from skill_fleet.domain import SkillDomainService
        domain_service = SkillDomainService(self.skill_repository)
        return await domain_service.calculate_overlap(skill1, skill2)
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
```

### 4. Log Important Operations

```python
async def create_skill(self, task_description: str, user_id: str):
    self.logger.info(
        f"Creating skill for user {user_id}",
        extra={"user_id": user_id, "description": task_description}
    )
    # ... service logic
    self.logger.info(f"Skill created with job_id: {job.job_id}")
```

### 5. Use Type Hints

```python
async def get_skill(self, skill_id: str) -> Skill:
    """Get a skill by ID.

    Returns:
        The skill entity
    """
    return await self.skill_repository.get(skill_id)
```

---

## Common Patterns

### Pagination

```python
async def list_skills(
    self,
    page: int = 1,
    page_size: int = 20
) -> list[Skill]:
    """List skills with pagination."""
    offset = (page - 1) * page_size
    return await self.skill_repository.find_all(
        limit=page_size,
        offset=offset
    )
```

### Bulk Operations

```python
async def bulk_validate(self, skill_ids: list[str]) -> dict[str, bool]:
    """Validate multiple skills."""
    results = {}
    for skill_id in skill_ids:
        try:
            skill = await self.skill_repository.get(skill_id)
            results[skill_id] = SkillIsComplete().is_satisfied_by(skill)
        except Exception as e:
            self.logger.error(f"Error validating {skill_id}: {e}")
            results[skill_id] = False
    return results
```

### Caching

```python
from functools import lru_cache

class SkillService(BaseService):
    @lru_cache(maxsize=128)
    def _get_skill_type_weights(self) -> dict[str, float]:
        """Get cached skill type weights."""
        return self.config.get("skill_type_weights", {})
```

---

## See Also

- **[Domain Layer](../architecture/DOMAIN_LAYER.md)** - Domain entities and specifications
- **[Import Path Guide](IMPORT_PATH_GUIDE.md)** - Service import patterns
- **[Service Layer Architecture](../architecture/SERVICE_LAYER.md)** - Service layer overview
