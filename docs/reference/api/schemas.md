# API Schemas Reference

**Last Updated**: 2026-01-31
**Location**: `src/skill_fleet/api/schemas/`

## Overview

The API uses Pydantic models for request/response validation, ensuring type safety and providing automatic OpenAPI documentation.

`★ Insight ─────────────────────────────────────`
Schemas serve as the contract between clients and the API. By using Pydantic models, we get automatic validation, serialization, and OpenAPI schema generation. This makes the API self-documenting and type-safe.
`─────────────────────────────────────────────────`

## Request Schemas

### CreateSkillRequest

Request schema for creating a new skill.

```python
class CreateSkillRequest(BaseModel):
    task_description: str = Field(
        ...,
        description="Description of the skill to create",
        min_length=10,
        max_length=5000
    )
    user_id: str = Field(
        default="default",
        description="User identifier for tracking"
    )
    auto_approve: bool = Field(
        default=False,
        description="Skip HITL checkpoints and auto-approve"
    )
```

**Example:**
```json
{
    "task_description": "Create a Python async/await programming skill with examples",
    "user_id": "user_123",
    "auto_approve": false
}
```

---

### RefineSkillRequest

Request schema for refining an existing skill.

```python
class RefineSkillRequest(BaseModel):
    feedback: str = Field(
        ...,
        description="User feedback for refinement"
    )
    focus_areas: list[str] = Field(
        default=[],
        description="Specific areas to focus on"
    )
```

---

### ValidateSkillRequest

Request schema for validating skill content.

```python
class ValidateSkillRequest(BaseModel):
    content: str = Field(
        ...,
        description="Skill content to validate"
    )
    validation_type: str = Field(
        default="full",
        description="Validation level: basic, full, strict"
    )
```

---

### HITLResponseRequest

Request schema for submitting HITL responses.

```python
class HITLResponseRequest(BaseModel):
    question_id: str = Field(..., description="Question being answered")
    response: str | dict = Field(..., description="User's response")
    response_type: str = Field(..., description="Type of response")
```

**Example:**
```json
{
    "question_id": "q1",
    "response": "Python 3.11",
    "response_type": "single_choice"
}
```

---

## Response Schemas

### CreateSkillResponse

Response schema for skill creation request.

```python
class CreateSkillResponse(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: accepted, running, etc.")
    message: str = Field(..., description="Status message")
```

**Example:**
```json
{
    "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "accepted",
    "message": "Skill creation started"
}
```

---

### SkillDetailResponse

Detailed skill information response.

```python
class SkillDetailResponse(BaseModel):
    skill_id: str
    name: str
    description: str
    content: str
    metadata: SkillMetadata
    created_at: datetime
    updated_at: datetime
```

---

### JobStatusResponse

Job status and progress information.

```python
class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # pending, running, pending_hitl, completed, failed
    type: str
    progress: int  # 0-100
    result: dict | None
    error: str | None
    created_at: datetime
    updated_at: datetime
```

**Example:**
```json
{
    "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "pending_hitl",
    "type": "skill_creation",
    "progress": 45,
    "result": null,
    "error": null,
    "created_at": "2026-01-31T10:00:00Z",
    "updated_at": "2026-01-31T10:02:30Z"
}
```

---

### HITLPromptResponse

HITL prompt for user interaction.

```python
class HITLPromptResponse(BaseModel):
    has_prompt: bool
    prompt_type: str | None
    data: dict | None
```

**Example (with prompt):**
```json
{
    "has_prompt": true,
    "prompt_type": "clarifying_questions",
    "data": {
        "questions": [
            {
                "id": "q1",
                "text": "What Python version should this target?",
                "type": "single_choice",
                "options": ["3.9", "3.10", "3.11", "3.12"]
            }
        ]
    }
}
```

**Example (no prompt):**
```json
{
    "has_prompt": false,
    "prompt_type": null,
    "data": null
}
```

---

### ValidationReportResponse

Skill validation results.

```python
class ValidationReportResponse(BaseModel):
    passed: bool
    score: float
    errors: list[str]
    warnings: list[str]
    checks_performed: list[str]
```

**Example:**
```json
{
    "passed": true,
    "score": 0.92,
    "errors": [],
    "warnings": ["Description could be more specific"],
    "checks_performed": [
        "structure_validation",
        "compliance_check",
        "quality_assessment"
    ]
}
```

---

### QualityAssessmentResponse

Quality assessment metrics.

```python
class QualityAssessmentResponse(BaseModel):
    overall_score: float
    completeness: float
    clarity: float
    usefulness: float
    word_count: int
    size_assessment: str  # optimal, acceptable, too_large
    verbosity_score: float
    recommendations: list[str]
```

**Example:**
```json
{
    "overall_score": 0.88,
    "completeness": 0.92,
    "clarity": 0.85,
    "usefulness": 0.90,
    "word_count": 2500,
    "size_assessment": "optimal",
    "verbosity_score": 0.3,
    "recommendations": [
        "Consider adding more edge case examples"
    ]
}
```

---

### TaxonomyResponse

Taxonomy structure response.

```python
class TaxonomyResponse(BaseModel):
    categories: list[TaxonomyCategory]
    skills_count: int
    version: str
```

---

### ConversationalMessageResponse

Conversational interaction response.

```python
class ConversationalMessageResponse(BaseModel):
    response: str
    session_id: str
    requires_action: bool
    action_type: str | None
    action_data: dict | None
```

---

## Common Data Models

### SkillMetadata

Metadata for a skill.

```python
class SkillMetadata(BaseModel):
    version: str = "1.0.0"
    author: str
    created_at: datetime
    updated_at: datetime
    tags: list[str] = []
    category: str
    difficulty: str  # beginner, intermediate, advanced
```

---

### ValidationCheckItem

Individual validation check result.

```python
class ValidationCheckItem(BaseModel):
    check_name: str
    passed: bool
    message: str
    severity: str  # error, warning, info
```

---

### HITLQuestion

HITL question structure.

```python
class HITLQuestion(BaseModel):
    id: str
    text: str
    type: str  # single_choice, multiple_choice, text, confirm
    options: list[QuestionOption] | None
    allows_other: bool = False
    rationale: str | None
```

---

## Schema Categories

### Core Schemas

Located in: `src/skill_fleet/api/schemas/models.py`

- `CreateSkillRequest/Response`
- `SkillDetailResponse`
- `RefineSkillRequest/Response`
- `ValidateSkillRequest/Response`

### Job Schemas

Located in: `src/skill_fleet/api/schemas/models.py`

- `JobStatusResponse`
- `JobListResponse`
- `JobFilterRequest`

### HITL Schemas

Located in: `src/skill_fleet/api/schemas/hitl.py`

- `HITLPromptResponse`
- `HITLResponseRequest`
- `HITLQuestion`
- `HITLSessionResponse`

### Validation Schemas

Located in: `src/skill_fleet/api/schemas/models.py`

- `ValidationReportResponse`
- `ValidationCheckItem`
- `QualityAssessmentResponse`
- `AutoFixRequest/Response`

### Taxonomy Schemas

Located in: `src/skill_fleet/api/schemas/models.py`

- `TaxonomyResponse`
- `TaxonomyCategory`
- `UserTaxonomyResponse`
- `AdaptTaxonomyRequest`

### Conversational Schemas

Located in: `src/skill_fleet/api/schemas/conversational.py`

- `SendMessageRequest/Response`
- `SessionHistoryResponse`
- `StreamingRequest`

---

## Validation Rules

### String Lengths

| Field | Min | Max |
|-------|-----|-----|
| `task_description` | 10 | 5000 |
| `skill_name` | 3 | 100 |
| `description` | 50 | 2000 |
| `user_id` | 1 | 100 |

### Enumerations

**Skill Types**: `how_to`, `reference`, `concept`, `workflow`, `checklist`

**Difficulty Levels**: `beginner`, `intermediate`, `advanced`

**Job Status**: `pending`, `running`, `pending_hitl`, `completed`, `failed`

**Validation Types**: `basic`, `full`, `strict`

---

## Related Documentation

- [Endpoints](endpoints.md) - API endpoint reference
- [Jobs](jobs.md) - Background job system
- [Migration Guide](migration-v1-v2.md) - Version migration
