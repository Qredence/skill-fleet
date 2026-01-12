# API Schemas Reference

**Last Updated**: 2026-01-12
**Location**: `src/skill_fleet/api/schemas/`

## Overview

The API uses Pydantic models for request/response validation, ensuring type safety and providing automatic OpenAPI documentation. This document describes the key schemas used throughout the API.

`★ Insight ─────────────────────────────────────`
Schemas serve as the contract between clients and the API. By using Pydantic models, we get automatic validation, serialization, and OpenAPI schema generation. This makes the API self-documenting and type-safe.
`─────────────────────────────────────────────────`

## Request Schemas

### CreateSkillRequest

Request schema for creating a new skill.

```python
from pydantic import BaseModel, Field

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

### ValidateSkillRequest

Request schema for validating a skill.

```python
class ValidateSkillRequest(BaseModel):
    skill_path: str = Field(
        ...,
        description="Path to the skill directory"
    )
    strict: bool = Field(
        default=False,
        description="Treat warnings as errors"
    )
```

**Example:**
```json
{
    "skill_path": "skills/technical_skills/programming/python/decorators",
    "strict": false
}
```

---

### ValidateFrontmatterRequest

Request schema for validating YAML frontmatter.

```python
class ValidateFrontmatterRequest(BaseModel):
    content: str = Field(
        ...,
        description="Full SKILL.md content including frontmatter"
    )
```

**Example:**
```json
{
    "content": "---\nname: python-decorators\ndescription: Ability to design and implement Python decorators\n---\n\n# Python Decorators\n..."
}
```

---

### HITLResponseRequest

Request schema for submitting HITL responses.

```python
from typing import Literal

class HITLResponseRequest(BaseModel):
    action: Literal["proceed", "revise", "refine", "cancel"] = Field(
        ...,
        description="Action to take based on HITL prompt"
    )
    response: str | None = Field(
        default=None,
        description="User's response to the prompt"
    )
    feedback: str | None = Field(
        default=None,
        description="Additional feedback for revise/refine actions"
    )
```

**Example:**
```json
{
    "action": "refine",
    "response": "Add more examples",
    "feedback": "The examples section should have at least 5 code examples"
}
```

---

## Response Schemas

### CreateSkillResponse

Response schema for skill creation initiation.

```python
class CreateSkillResponse(BaseModel):
    job_id: str = Field(
        ...,
        description="Unique job identifier for tracking"
    )
    status: Literal["accepted", "rejected"] = Field(
        ...,
        description="Whether the job was accepted"
    )
```

**Example:**
```json
{
    "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "accepted"
}
```

---

### JobStatusResponse

Response schema for job status queries.

```python
class JobStatusResponse(BaseModel):
    job_id: str
    status: Literal["pending", "running", "pending_hitl", "completed", "failed"]
    hitl_type: str | None = None
    hitl_data: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    saved_path: str | None = None
    created_at: str
    updated_at: str
```

**Example:**
```json
{
    "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "pending_hitl",
    "hitl_type": "clarify",
    "hitl_data": {
        "questions": ["What level of detail?"],
        "rationale": "Need target audience info"
    },
    "result": null,
    "error": null,
    "saved_path": null,
    "created_at": "2026-01-12T10:30:00Z",
    "updated_at": "2026-01-12T10:31:00Z"
}
```

---

### HITLPromptResponse

Response schema for HITL prompts.

```python
class HITLPromptResponse(BaseModel):
    status: str
    type: str | None = None
    questions: list[dict] | None = None
    rationale: str | None = None
    summary: str | None = None
    path: str | None = None
    content: str | None = None
    highlights: list[str] | None = None
    report: str | None = None
    passed: bool | None = None
    skill_content: str | None = None
    saved_path: str | None = None
    error: str | None = None
```

---

### ValidationResponse

Response schema for validation results.

```python
from typing import Literal

class ValidationCheck(BaseModel):
    name: str
    status: Literal["pass", "fail", "warning"]
    message: str | None = None

class ValidationIssue(BaseModel):
    check: str
    message: str
    severity: Literal["error", "warning"]

class ValidationResponse(BaseModel):
    status: Literal["pass", "fail"]
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    checks: list[ValidationCheck]
```

**Example:**
```json
{
    "status": "pass",
    "errors": [],
    "warnings": [
        {
            "check": "examples_count",
            "message": "Only 2 examples found",
            "severity": "warning"
        }
    ],
    "checks": [
        {"name": "metadata_exists", "status": "pass"},
        {"name": "frontmatter_valid", "status": "pass"},
        {"name": "examples_present", "status": "warning"}
    ]
}
```

---

### TaxonomyResponse

Response schema for taxonomy structure.

```python
class TaxonomyResponse(BaseModel):
    taxonomy: dict[str, Any]
    total_skills: int
    last_updated: str
```

**Example:**
```json
{
    "taxonomy": {
        "technical_skills": {
            "programming": {
                "languages": {
                    "python": {
                        "async": {...},
                        "decorators": {...}
                    }
                }
            }
        }
    },
    "total_skills": 42,
    "last_updated": "2026-01-12T10:00:00Z"
}
```

---

## Internal Schemas

### JobState

Internal job state (not directly exposed in API responses, but used internally).

```python
from pydantic import BaseModel

class JobState(BaseModel):
    job_id: str
    status: str = "pending"
    hitl_type: str | None = None
    hitl_data: dict[str, Any] | None = None
    hitl_response: dict[str, Any] | None = None
    result: Any | None = None
    error: str | None = None
    saved_path: str | None = None
```

**Status Values:**
- `pending`: Job queued
- `running`: Job processing
- `pending_hitl`: Awaiting human input
- `completed`: Job finished successfully
- `failed`: Job failed

---

## Auto-Generated Schemas

DSPy module signatures are automatically converted to Pydantic models via the discovery system.

**Example:**
```python
# DSPy signature
class AnalyzeIntent(dspy.Signature):
    task_description: str = dspy.InputField(desc="...")
    user_context: str = dspy.InputField(desc="...")
    task_intent: TaskIntent = dspy.OutputField(desc="...")

# Auto-generated Pydantic model
class AnalyzeIntentRequest(BaseModel):
    task_description: str
    user_context: str

class AnalyzeIntentResponse(BaseModel):
    task_intent: TaskIntent
```

---

## Schema Validation

Schemas are validated automatically by FastAPI. Invalid requests return:

```json
{
    "detail": [
        {
            "loc": ["body", "task_description"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

---

## Custom Validators

Add custom validation to schemas:

```python
from pydantic import validator

class CreateSkillRequest(BaseModel):
    task_description: str

    @validator('task_description')
    def validate_task_description(cls, v):
        if "test" in v.lower():
            raise ValueError("task_description cannot contain 'test'")
        if len(v.split()) < 3:
            raise ValueError("task_description must be at least 3 words")
        return v
```

---

## See Also

- **[API Overview](index.md)** - Architecture and setup
- **[Endpoints Documentation](endpoints.md)** - Endpoint reference
- **[DSPy Signatures](../dspy/signatures.md)** - DSPy signature contracts
