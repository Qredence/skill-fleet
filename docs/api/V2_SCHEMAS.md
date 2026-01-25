# v2 API Schemas

**Last Updated**: 2026-01-25

## Overview

This document describes the Pydantic schemas (request/response models) used by the v2 API endpoints. All schemas use Pydantic for validation and serialization.

`★ Insight ─────────────────────────────────────`
Pydantic schemas provide automatic validation, type coercion, and OpenAPI documentation generation. The same models are used for both request validation and response serialization, ensuring consistency across the API.
`─────────────────────────────────────────────────`

## Table of Contents

- [Skill Schemas](#skill-schemas)
- [HITL Schemas](#hitl-schemas)
- [Taxonomy Schemas](#taxonomy-schemas)
- [Validation Schemas](#validation-schemas)
- [Quality Schemas](#quality-schemas)
- [Optimization Schemas](#optimization-schemas)
- [Job Schemas](#job-schemas)
- [Common Schemas](#common-schemas)

---

## Skill Schemas

### CreateSkillRequest

Request schema for creating a new skill.

```python
from pydantic import BaseModel, Field

class CreateSkillRequest(BaseModel):
    """Request body for creating a new skill."""

    task_description: str = Field(
        ...,
        description="Description of the skill to create",
        min_length=10,
        max_length=10000
    )
    user_id: str = Field(
        default="default",
        description="User ID for context"
    )
```

**Example**:
```json
{
    "task_description": "Create a Python async/await programming skill",
    "user_id": "user_123"
}
```

---

### CreateSkillResponse

Response schema for skill creation initiation.

```python
class CreateSkillResponse(BaseModel):
    """Response model for skill creation."""

    job_id: str = Field(..., description="Unique identifier for the background job")
    status: str = Field(default="accepted", description="Initial job status")
```

**Example**:
```json
{
    "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "accepted"
}
```

---

### SkillDetailResponse

Detailed skill information response.

```python
from typing import Any, Optional

class SkillDetailResponse(BaseModel):
    """Detailed information about a skill."""

    skill_id: str
    name: str
    description: str
    version: str
    type: str
    metadata: dict[str, Any]
    content: Optional[str] = None
```

**Example**:
```json
{
    "skill_id": "python-async-await",
    "name": "python-async-await",
    "description": "Proficiency with Python's async/await syntax",
    "version": "1.0.0",
    "type": "guide",
    "metadata": {
        "weight": "medium",
        "load_priority": "on_demand",
        "dependencies": [],
        "capabilities": ["code-generation"]
    },
    "content": "# Python Async/Await\n\n..."
}
```

---

## HITL Schemas

### HitlPromptResponse

HITL prompt response schema.

```python
from typing import Any

class HitlPromptResponse(BaseModel):
    """HITL prompt response."""

    status: str = Field(..., description="Job status")
    type: str = Field(..., description="HITL interaction type")
    questions: list[dict[str, Any]] = Field(default_factory=list)
    summary: Optional[str] = None
    path: Optional[str] = None
    content: Optional[str] = None
    highlights: list[str] = Field(default_factory=list)
    report: Optional[dict[str, Any]] = None
    passed: Optional[bool] = None
    skill_content: Optional[str] = None
    rationale: Optional[str] = None
```

**Examples** by type:

**Clarify**:
```json
{
    "status": "pending_hitl",
    "type": "clarify",
    "questions": [
        {
            "question": "What level of detail?",
            "options": ["beginner", "intermediate", "advanced"]
        }
    ],
    "rationale": "Need to understand target audience"
}
```

**Confirm**:
```json
{
    "status": "pending_hitl",
    "type": "confirm",
    "summary": "Creating a Python decorators skill",
    "path": "python/decorators"
}
```

**Preview**:
```json
{
    "status": "pending_hitl",
    "type": "preview",
    "content": "# Python Decorators\n\n...",
    "highlights": ["Core principle: Decorators wrap functions", "3 examples provided"]
}
```

---

### HitlResponseRequest

HITL response request schema.

```python
class HitlResponseRequest(BaseModel):
    """Request for submitting HITL response."""

    action: str = Field(..., description="Action to take")
    response: str = Field(default="", description="User response")
```

**Actions**:
- `proceed` - Continue to next phase
- `revise` - Restart current phase with feedback
- `refine` - Run refinement with feedback
- `cancel` - Cancel skill creation

**Example**:
```json
{
    "action": "proceed",
    "response": "intermediate"
}
```

---

## Taxonomy Schemas

### TaxonomyResponse

Taxonomy structure response.

```python
from typing import Any

class TaxonomyResponse(BaseModel):
    """Taxonomy structure response."""

    taxonomy: dict[str, Any] = Field(..., description="Hierarchical taxonomy structure")
    total_skills: int = Field(..., description="Total number of skills")
```

**Example**:
```json
{
    "taxonomy": {
        "python": {
            "async-await": { ... },
            "decorators": { ... }
        }
    },
    "total_skills": 2
}
```

---

## Validation Schemas

### ValidateSkillRequest

Skill validation request schema.

```python
class ValidateSkillRequest(BaseModel):
    """Request for skill validation."""

    skill_path: str = Field(..., description="Path to the skill directory")
    strict: bool = Field(default=False, description="Treat warnings as errors")
```

**Example**:
```json
{
    "skill_path": "python/decorators",
    "strict": false
}
```

---

### ValidationReport

Validation report response schema.

```python
class ValidationCheck(BaseModel):
    """Individual validation check result."""

    name: str
    status: str  # "pass", "fail", "warning"

class ValidationReport(BaseModel):
    """Skill validation report."""

    status: str  # "pass", "fail"
    errors: list[str] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)
    checks: list[ValidationCheck] = Field(default_factory=list)
```

**Example**:
```json
{
    "status": "pass",
    "errors": [],
    "warnings": [
        {
            "check": "examples_count",
            "message": "Only 2 examples found"
        }
    ],
    "checks": [
        {"name": "metadata_exists", "status": "pass"},
        {"name": "examples_present", "status": "warning"}
    ]
}
```

---

### ValidateFrontmatterRequest

Frontmatter validation request schema.

```python
class ValidateFrontmatterRequest(BaseModel):
    """Request for frontmatter validation."""

    content: str = Field(..., description="Full SKILL.md content including frontmatter")
```

---

### FrontmatterValidationResponse

Frontmatter validation response schema.

```python
class FrontmatterValidationResponse(BaseModel):
    """Frontmatter validation response."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    parsed: Optional[dict[str, Any]] = None
```

---

## Quality Schemas

### EvaluateSkillRequest

Skill evaluation request schema.

```python
class EvaluateSkillRequest(BaseModel):
    """Request for skill evaluation."""

    path: str = Field(..., description="Taxonomy-relative path to the skill")
    weights: Optional[dict[str, float]] = Field(
        default=None,
        description="Custom metric weights"
    )
```

---

### QualityMetricsResponse

Quality metrics response schema.

```python
class QualityMetricsResponse(BaseModel):
    """Skill quality metrics response."""

    overall_score: float
    frontmatter_completeness: float
    has_overview: bool
    has_when_to_use: bool
    has_quick_reference: bool
    pattern_count: int
    has_anti_patterns: bool
    has_production_patterns: bool
    has_key_insights: bool
    has_common_mistakes: bool
    has_red_flags: bool
    has_real_world_impact: bool
    code_examples_count: int
    code_examples_quality: float
    quality_indicators: dict[str, Any]
    issues: list[str]
    strengths: list[str]
```

---

## Optimization Schemas

### OptimizationStartRequest

Optimization job start request schema.

```python
class OptimizationStartRequest(BaseModel):
    """Request to start optimization."""

    optimizer: str = Field(default="miprov2", description="Optimizer type")
    training_paths: list[str] = Field(
        default_factory=list,
        description="Paths to training skills"
    )
    auto: str = Field(default="medium", description="MIPROv2 auto setting")
    max_bootstrapped_demos: int = Field(default=4, description="Max bootstrapped demos")
    max_labeled_demos: int = Field(default=4, description="Max labeled demos")
    save_path: str = Field(
        default="skill_creator_optimized.json",
        description="Path to save optimized program"
    )
```

---

### OptimizationStatusResponse

Optimization job status response schema.

```python
class OptimizationStatusResponse(BaseModel):
    """Optimization job status response."""

    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    message: Optional[str] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
```

---

## Job Schemas

### JobStatusResponse

Job status response schema.

```python
from datetime import datetime

class JobStatusResponse(BaseModel):
    """Job status response."""

    job_id: str
    status: str  # "pending", "running", "pending_hitl", "completed", "failed"
    task_description: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    current_phase: str = Field(default="")
    progress_message: str = Field(default="")
    error: Optional[str] = None
    draft_path: Optional[str] = None
    intended_taxonomy_path: Optional[str] = None
    validation_passed: Optional[bool] = None
    validation_score: Optional[float] = None
```

---

## Common Schemas

### ErrorResponse

Standard error response schema.

```python
class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error message")
    request_id: Optional[str] = Field(None, description="Request identifier for tracing")
```

**Example**:
```json
{
    "detail": "Skill not found",
    "request_id": "req-123"
}
```

---

### HealthResponse

Health check response schema.

```python
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="ok")
    version: str = Field(..., description="API version")
```

**Example**:
```json
{
    "status": "ok",
    "version": "2.0.0"
}
```

---

## Type Definitions

### SkillType

Skill type enum.

```python
from enum import Enum

class SkillType(str, Enum):
    """Type of skill per agentskills.io specification."""

    GUIDE = "guide"
    TOOL_INTEGRATION = "tool_integration"
    WORKFLOW = "workflow"
    REFERENCE = "reference"
    MEMORY_BLOCK = "memory_block"
```

---

### SkillWeight

Skill weight enum.

```python
class SkillWeight(str, Enum):
    """Relative weight/contribution of a skill."""

    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
```

---

### LoadPriority

Load priority enum.

```python
class LoadPriority(str, Enum):
    """When to load the skill."""

    ALWAYS_LOADED = "always_loaded"
    ON_DEMAND = "on_demand"
    LAZY = "lazy"
```

---

### JobStatus

Job status enum.

```python
class JobStatus(str, Enum):
    """Status of a skill creation job."""

    PENDING = "pending"
    RUNNING = "running"
    PENDING_HITL = "pending_hitl"
    COMPLETED = "completed"
    FAILED = "failed"
```

---

## Schema Locations

The schemas are defined in:
- `src/skill_fleet/api/schemas/models.py` - Main API schemas
- `src/skill_fleet/api/schemas/hitl.py` - HITL-specific schemas

## See Also

- **[v2 Endpoints](V2_ENDPOINTS.md)** - Complete endpoint reference
- **[API Overview](index.md)** - API architecture and setup
- **[HITL System](../hitl/)** - Human-in-the-Loop details
