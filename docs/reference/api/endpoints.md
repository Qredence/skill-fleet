# API Endpoints Reference

**Last Updated**: 2026-01-31
**Base URL**: `http://localhost:8000/api/v1`
**Status**: Production/Stable

## Overview

The Skills Fleet API provides programmatic access to skill creation, taxonomy management, validation, and Human-in-the-Loop (HITL) workflows. The API uses a job-based pattern for long-running skill creation operations.

`★ Insight ─────────────────────────────────────`
Skill creation is asynchronous because it involves multiple LLM calls and potential HITL checkpoints. When you create a skill, you receive a `job_id` immediately and poll for status. This prevents HTTP timeouts and enables interactive workflows.
`─────────────────────────────────────────────────`

## Table of Contents

- [Health](#health)
- [Skills](#skills)
- [Jobs](#jobs)
- [HITL](#hitl)
- [Taxonomy](#taxonomy)
- [Quality](#quality)
- [Optimization](#optimization)
- [Drafts](#drafts)
- [Conversational](#conversational)

---

## Health

### GET /health

Check API availability.

**Response (200 OK)**:
```json
{
    "status": "ok"
}
```

---

## Skills

### POST /api/v1/skills

Create a new skill asynchronously.

**Request**:
```http
POST /api/v1/skills
Content-Type: application/json

{
    "task_description": "Create a Python async/await programming skill",
    "user_id": "user_123",
    "auto_approve": false
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_description` | `string` | Yes | Description of the skill to create (min 10 chars) |
| `user_id` | `string` | No | User identifier (default: "default") |
| `auto_approve` | `bool` | No | Skip HITL checkpoints (default: false) |

**Response (202 Accepted)**:
```json
{
    "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "accepted",
    "message": "Skill creation started"
}
```

**Error Response (400)**:
```json
{
    "detail": "task_description is required and must be at least 10 characters"
}
```

---

### GET /api/v1/skills/{skill_id}

Get skill details by ID or path.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `skill_id` | `string` | Skill ID, path, or alias |

**Response (200 OK)**:
```json
{
    "skill_id": "python-async-await",
    "name": "python-async-await",
    "description": "Python async/await programming patterns",
    "content": "# Python Async/Await...",
    "metadata": {
        "version": "1.0.0",
        "author": "user_123",
        "created_at": "2026-01-31T10:00:00Z"
    }
}
```

---

### PUT /api/v1/skills/{skill_id}

Update an existing skill.

**Request**:
```json
{
    "content": "# Updated skill content...",
    "metadata": {
        "version": "1.1.0"
    }
}
```

**Response (200 OK)**:
```json
{
    "status": "updated",
    "skill_id": "python-async-await"
}
```

---

### POST /api/v1/skills/{skill_id}/validate

Validate a skill's content and structure.

**Request**:
```json
{
    "content": "# Skill content to validate...",
    "validation_type": "full"
}
```

**Response (200 OK)**:
```json
{
    "validation_report": {
        "passed": true,
        "score": 0.92,
        "errors": [],
        "warnings": ["Description could be more specific"]
    }
}
```

---

### POST /api/v1/skills/{skill_id}/refine

Refine a skill based on feedback.

**Request**:
```json
{
    "feedback": "Add more examples about error handling",
    "focus_areas": ["examples", "edge_cases"]
}
```

**Response (202 Accepted)**:
```json
{
    "job_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "status": "accepted"
}
```

---

## Jobs

### GET /api/v1/jobs/{job_id}

Get job status and details.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | `string` | Job UUID |

**Response (200 OK)**:
```json
{
    "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "running",
    "type": "skill_creation",
    "progress": 45,
    "created_at": "2026-01-31T10:00:00Z",
    "updated_at": "2026-01-31T10:02:30Z"
}
```

**Job Status Values**:
- `pending` - Waiting to start
- `running` - Actively processing
- `pending_hitl` - Waiting for human input
- `completed` - Successfully finished
- `failed` - Error occurred

---

## HITL

### GET /api/v1/hitl/{job_id}/prompt

Get the current HITL prompt for a job.

**Response (200 OK)**:
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

**Response (200 OK - No prompt)**:
```json
{
    "has_prompt": false
}
```

---

### POST /api/v1/hitl/{job_id}/response

Submit a response to a HITL prompt.

**Request**:
```json
{
    "question_id": "q1",
    "response": "3.11",
    "response_type": "single_choice"
}
```

**Response (200 OK)**:
```json
{
    "status": "received",
    "job_status": "running"
}
```

---

### GET /api/v1/hitl/config

Get HITL configuration.

**Response (200 OK)**:
```json
{
    "enabled": true,
    "default_timeout": 3600,
    "max_questions": 10
}
```

---

## Taxonomy

### GET /api/v1/taxonomy

Get the full taxonomy structure.

**Response (200 OK)**:
```json
{
    "categories": [
        {
            "id": "technical",
            "name": "Technical Skills",
            "children": ["programming", "devops", "data"]
        }
    ],
    "skills_count": 150,
    "version": "2.1.0"
}
```

---

### POST /api/v1/taxonomy

Create or update a taxonomy category.

**Request**:
```json
{
    "id": "machine-learning",
    "name": "Machine Learning",
    "parent": "technical",
    "description": "ML and AI skills"
}
```

---

### GET /api/v1/taxonomy/user/{user_id}

Get a user's adapted taxonomy.

**Response (200 OK)**:
```json
{
    "user_id": "user_123",
    "adapted_taxonomy": {
        "priorities": ["python", "async-programming"],
        "hidden": ["cobol", "fortran"]
    }
}
```

---

### POST /api/v1/taxonomy/user/{user_id}/adapt

Adapt taxonomy for a user.

**Request**:
```json
{
    "priorities": ["python", "web-development"],
    "experience_level": "intermediate"
}
```

---

## Quality

### POST /api/v1/quality/validate

Validate skill content for compliance.

**Request**:
```json
{
    "content": "# Skill content...",
    "taxonomy_path": "technical/programming/python"
}
```

**Response (200 OK)**:
```json
{
    "passed": true,
    "compliance_score": 0.95,
    "issues": [],
    "warnings": ["Consider adding more examples"]
}
```

---

### POST /api/v1/quality/assess

Assess skill quality metrics.

**Request**:
```json
{
    "content": "# Skill content...",
    "plan": {"success_criteria": ["Clear examples", "Best practices"]}
}
```

**Response (200 OK)**:
```json
{
    "overall_score": 0.88,
    "completeness": 0.92,
    "clarity": 0.85,
    "word_count": 2500,
    "size_assessment": "optimal",
    "verbosity_score": 0.3
}
```

---

### POST /api/v1/quality/fix

Auto-fix skill issues.

**Request**:
```json
{
    "content": "# Skill content...",
    "issues": ["missing_examples", "unclear_description"]
}
```

**Response (200 OK)**:
```json
{
    "fixed_content": "# Improved skill content...",
    "fixes_applied": ["Added examples section", "Clarified description"]
}
```

---

## Optimization

### POST /api/v1/optimization/analyze

Analyze optimization opportunities.

**Request**:
```json
{
    "skill_id": "python-async-await",
    "metrics": ["trigger_rate", "token_usage"]
}
```

**Response (200 OK)**:
```json
{
    "analysis": {
        "trigger_rate": 0.75,
        "token_efficiency": 0.82,
        "recommendations": ["Add more trigger phrases"]
    }
}
```

---

### POST /api/v1/optimization/improve

Improve a skill via optimization.

**Request**:
```json
{
    "skill_id": "python-async-await",
    "target_metric": "trigger_rate",
    "target_value": 0.9
}
```

**Response (202 Accepted)**:
```json
{
    "job_id": "b2c3d4e5-6789-01bc-defa-2345678901bc",
    "status": "accepted"
}
```

---

### POST /api/v1/optimization/compare

Compare skill versions.

**Request**:
```json
{
    "baseline_skill_id": "python-async-await",
    "improved_skill_id": "python-async-await-v2"
}
```

**Response (200 OK)**:
```json
{
    "comparison": {
        "trigger_rate_improvement": 0.15,
        "token_reduction": 0.2,
        "overall_better": true
    }
}
```

---

## Drafts

### POST /api/v1/drafts/{job_id}/promote

Promote a draft skill to the taxonomy.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | `string` | Job UUID of completed skill creation |

**Request**:
```json
{
    "taxonomy_path": "technical/programming/python",
    "make_active": true
}
```

**Response (200 OK)**:
```json
{
    "status": "promoted",
    "skill_id": "python-async-await",
    "taxonomy_path": "technical/programming/python"
}
```

---

## Conversational

### POST /api/v1/conversational/message

Send a message in a conversational session.

**Request**:
```json
{
    "session_id": "sess_123",
    "message": "Create a skill for Python async programming",
    "context": {}
}
```

**Response (200 OK)**:
```json
{
    "response": "I'll help you create a Python async programming skill. First, let me understand your requirements...",
    "session_id": "sess_123",
    "requires_action": false
}
```

---

### POST /api/v1/conversational/session/{session_id}

Create or continue a conversational session.

**Response (200 OK)**:
```json
{
    "session_id": "sess_123",
    "status": "active",
    "created_at": "2026-01-31T10:00:00Z"
}
```

---

### GET /api/v1/conversational/session/{session_id}/history

Get conversation history.

**Response (200 OK)**:
```json
{
    "session_id": "sess_123",
    "messages": [
        {"role": "user", "content": "Create a skill..."},
        {"role": "assistant", "content": "I'll help you..."}
    ]
}
```

---

### GET /api/v1/conversational/sessions

List active sessions.

**Response (200 OK)**:
```json
{
    "sessions": [
        {"id": "sess_123", "status": "active", "created_at": "2026-01-31T10:00:00Z"}
    ]
}
```

---

### POST /api/v1/conversational/stream

Stream conversational responses (SSE).

**Request**:
```json
{
    "session_id": "sess_123",
    "message": "Continue with the skill creation"
}
```

**Response**: Server-Sent Events stream

---

## Error Handling

All errors follow the standard FastAPI error format:

```json
{
    "detail": "Error description"
}
```

**Common Status Codes**:
- `200` - Success
- `202` - Accepted (async operation started)
- `400` - Bad Request (invalid input)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

---

## Related Documentation

- [Schemas](schemas.md) - Request/response models
- [Jobs](jobs.md) - Background job system details
- [Migration Guide](migration-v1-v2.md) - Version migration information
