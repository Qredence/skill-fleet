# HITL Callbacks Reference

**Last Updated**: 2026-01-12

## Overview

HITL callbacks are the interface between the skill creation workflow and user interaction systems (CLI, API, webhooks). The callback function is invoked at each checkpoint to collect user input.

`★ Insight ─────────────────────────────────────`
The callback interface is **universal**—it works with CLI, API, and webhook integrations. By defining a standard callback signature, the workflow remains agnostic to the frontend implementation.
`─────────────────────────────────────────────────`

## Callback Signature

```python
async def hitl_callback(
    checkpoint: str,
    payload: dict[str, Any]
) -> dict[str, Any]:
    """Handle Human-in-the-Loop interactions during skill creation.

    Args:
        checkpoint: Checkpoint type ('clarify', 'confirm', 'preview', 'validate')
        payload: Checkpoint-specific data

    Returns:
        Dict with:
            - 'action': 'proceed' | 'revise' | 'refine' | 'cancel'
            - 'response': User response (for clarify)
            - 'feedback': User feedback (for revise/refine)
            - 'answers': Structured answers (for clarify)

    Raises:
        TimeoutError: If user takes too long to respond
    """
```

## Checkpoint Types

### clarify

Ask clarifying questions to resolve ambiguities.

**Payload:**
```python
{
    "questions": [
        {
            "question": "What level of detail?",
            "options": ["beginner", "intermediate", "advanced"],
            "rationale": "Need to understand target audience"
        }
    ],
    "rationale": "Why we're asking these questions"
}
```

**Response:**
```python
{
    "answers": {
        "response": "Intermediate level with practical examples"
    }
    # OR structured
    "answers": {
        "level": "intermediate",
        "focus": "practical"
    }
}
```

---

### confirm

Confirm understanding before proceeding to generation.

**Payload:**
```python
{
    "summary": "• Skill: Python async programming\n• Target: Intermediate developers\n• Path: technical_skills/python/async",
    "path": "technical_skills/python/async",
    "key_assumptions": ["Users know basic Python", "Focus on async/await syntax"]
}
```

**Response:**
```python
{
    "action": "proceed",  # or "revise" or "cancel"
    "feedback": "Make it more advanced"  # Only if action="revise"
}
```

---

### preview

Show generated content preview for feedback.

**Payload:**
```python
{
    "content": "## Overview\nPython async/await provides...\n\n## Key Concepts\n- Coroutines\n- Event loops",
    "highlights": [
        "Clear explanations of async/await",
        "Practical examples throughout",
        "Common pitfalls covered"
    ]
}
```

**Response:**
```python
{
    "action": "proceed",  # or "refine" or "cancel"
    "feedback": "Add more error handling examples"
}
```

---

### validate

Show validation results and ask for acceptance.

**Payload:**
```python
{
    "report": "Status: PASSED\n\nAll checks passed:\n✓ YAML frontmatter valid\n✓ Documentation complete",
    "passed": true,
    "skill_content": "Full skill content...",
    "saved_path": "/path/to/skill"
}
```

**Response:**
```python
{
    "action": "proceed",  # or "refine" or "cancel"
    "feedback": "Add one more example to meet the minimum"
}
```

## Action Types

| Action | Description | Used In |
|--------|-------------|---------|
| `proceed` | Continue to next phase | All checkpoints |
| `revise` | Restart current phase with feedback | confirm |
| `refine` | Apply changes and continue | preview, validate |
| `cancel` | Cancel skill creation | All checkpoints |

## Implementation Examples

### CLI Implementation

```python
async def cli_hitl_callback(checkpoint: str, payload: dict) -> dict:
    """CLI HITL callback using Rich prompts."""
    from rich.prompt import Prompt
    from rich.console import Console

    console = Console()

    if checkpoint == "clarify":
        # Display questions
        for i, q in enumerate(payload["questions"], 1):
            console.print(f"{i}. {q['question']}")

        # Collect response
        response = Prompt.ask("Your answers", default="")
        return {"answers": {"response": response}}

    elif checkpoint == "confirm":
        # Display summary
        console.print(payload["summary"])
        console.print(f"Path: {payload['path']}")

        # Ask for action
        action = Prompt.ask(
            "Proceed?",
            choices=["proceed", "revise", "cancel"],
            default="proceed"
        )

        result = {"action": action}
        if action == "revise":
            result["feedback"] = Prompt.ask("What should change?")
        return result
```

### API Implementation

```python
async def api_hitl_callback(checkpoint: str, payload: dict) -> dict:
    """API HITL callback using polling."""
    job.hitl_type = checkpoint
    job.hitl_data = payload

    # Wait for client to POST response
    try:
        response = await wait_for_hitl_response(job.job_id, timeout=3600)
        return response
    except TimeoutError:
        job.status = "failed"
        job.error = "HITL interaction timed out"
        raise
```

### Webhook Implementation

```python
async def webhook_hitl_callback(checkpoint: str, payload: dict) -> dict:
    """Webhook HITL callback."""
    # Send webhook to user's endpoint
    async with httpx.AsyncClient() as client:
        webhook_response = await client.post(
            user.webhook_url,
            json={
                "checkpoint": checkpoint,
                "payload": payload,
                "job_id": job.job_id
            },
            timeout=30.0
        )

        if webhook_response.status_code != 200:
            raise Exception("Webhook delivery failed")

        # Wait for webhook response (separate endpoint)
        response = await wait_for_webhook_response(job.job_id)
        return response
```

## Best Practices

1. **Timeout Handling**: Always set reasonable timeouts (1 hour default)
2. **Error Handling**: Catch and handle user cancellations gracefully
3. **Validation**: Validate user responses before submitting
4. **Progress Feedback**: Show users what's happening
5. **State Management**: Clear responses after processing to avoid confusion

## Testing HITL Callbacks

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_clarify_callback():
    """Test clarify checkpoint handling."""
    callback = AsyncMock(return_value={
        "answers": {"response": "intermediate level"}
    })

    result = await callback("clarify", {
        "questions": [{"question": "What level?"}]
    })

    assert result["answers"]["response"] == "intermediate level"

@pytest.mark.asyncio
async def test_confirm_revise():
    """Test confirm with revision."""
    callback = AsyncMock(return_value={
        "action": "revise",
        "feedback": "Make it more advanced"
    })

    result = await callback("confirm", {"summary": "..."})

    assert result["action"] == "revise"
    assert result["feedback"] == "Make it more advanced"
```

## See Also

- **[HITL Overview](index.md)** - System overview
- **[Interactions Documentation](interactions.md)** - Interaction types
- **[Runner Documentation](runner.md)** - Runner implementation
- **[DSPy HITL Signatures](../dspy/signatures.md#hitl-signatures)** - DSPy signatures
