# Conversational Interface Architecture

**Last Updated**: 2026-01-25

## Overview

The conversational interface provides a real-time chat experience for skill creation and interaction. It uses Server-Sent Events (SSE) for streaming responses, supports multi-turn conversations with session management, and implements intent-based routing for intelligent task handling.

`★ Insight ─────────────────────────────────────`
The conversational interface separates streaming from business logic. A StreamingAssistant handles the SSE mechanics, while ConversationSession manages state and intent routing. This separation allows easy testing and swapping of transport layers (e.g., switching from SSE to WebSockets).
`─────────────────────────────────────────────────`

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Client                                │
│  (Browser, CLI, Mobile App with SSE/EventSource support)    │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/SSE
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Routes (v1)                          │
│  POST /api/v1/chat/stream  - SSE streaming                  │
│  POST /api/v1/chat/sync    - Non-streaming (compatibility)   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 StreamingAssistant                           │
│  • Event generation (thinking, response, error)             │
│  • SSE formatting                                           │
│  • Stream management                                        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│               ConversationSession (State Machine)           │
│  • Session management (ID, user context)                    │
│  • Message history (role-based)                             │
│  • Intent detection & routing                               │
│  • State transitions (idle → active → awaiting_input)       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   Intent Handlers                           │
│  • CreateSkillIntent  - Route to skill creation workflow    │
│  • QueryIntent        - Answer questions about skills       │
│  • RefineIntent       - Refine existing skills              │
│  • ChatIntent         - General conversation                │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    DSPy/LLM Layer                            │
│  • Language model calls                                     │
│  • Prompt engineering                                       │
│  • Response generation                                      │
└─────────────────────────────────────────────────────────────┘
```

## v1 API Endpoints

### 1. Streaming Chat (SSE)

**Endpoint**: `POST /api/v1/chat/stream`

**Content-Type**: `text/event-stream`

```python
import requests
import json

# Start streaming (use SSE client library or raw EventSource)
response = requests.post(
    "http://localhost:8000/api/v1/chat/stream",
    json={"message": "Create a Python decorators skill"},
    stream=True
)

for line in response.iter_lines():
    if line:
        event = json.loads(line.decode('utf-8').split('data: ')[1])
        if event['type'] == 'thinking':
            print(f"Thinking: {event['data']}")
        elif event['type'] == 'response':
            print(f"Response: {event['data']}")
        elif event['type'] == 'complete':
            print("Done!")
            break
```

**Event Types**:
- `thinking` - Intermediate reasoning steps
- `response` - Generated response chunks
- `error` - Error information
- `complete` - Stream finished

### 2. Non-Streaming Chat

**Endpoint**: `POST /api/v1/chat/sync`

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/chat/sync",
    json={"message": "What skills exist for Python?"}
)

result = response.json()
# Returns:
# {
#   "message": "...",
#   "thinking": ["step1", "step2"],
#   "response": "complete response",
#   "thinking_summary": "reasoning summary"
# }
```

### JavaScript Example

```javascript
// Using EventSource for SSE
const eventSource = new EventSource('/api/v1/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Create a skill' })
});

eventSource.addEventListener('thinking', (e) => {
  const data = JSON.parse(e.data);
  console.log('Thinking:', data.content);
});

eventSource.addEventListener('response', (e) => {
  const data = JSON.parse(e.data);
  console.log('Response:', data.content);
});

eventSource.addEventListener('complete', () => {
  eventSource.close();
});
```

## Session Management

### ConversationSession

```python
from skill_fleet.core.services import (
    ConversationSession,
    ConversationMessage,
    MessageRole,
    ConversationState,
)

# Create a new session
session = ConversationSession(
    session_id="sess-123",
    user_id="user-456",
    context={},
)

# Add messages
session.add_message(ConversationMessage(
    role=MessageRole.USER,
    content="Create a Redis caching skill"
))

session.add_message(ConversationMessage(
    role=MessageRole.ASSISTANT,
    content="I'll help you create a Redis caching skill..."
))

# Check state
print(session.state)  # ConversationState.IDLE, ACTIVE, etc.
print(session.message_count)  # 2
```

### Session States

```python
from skill_fleet.core.services import ConversationState

# State transitions
ConversationState.IDLE          # No active conversation
ConversationState.ACTIVE        # Conversation in progress
ConversationState.AWAITING_INPUT # Waiting for user response
ConversationState.COMPLETED     # Conversation finished
ConversationState.ERROR         # Error occurred
```

## Intent-Based Routing

### Intent Detection

The system automatically detects user intent from messages:

```python
# CreateSkillIntent
"Create a Python decorators skill"
"Make a skill for Redis caching"
"Build a new capability"

# QueryIntent
"What skills exist?"
"Show me Python skills"
"List all testing skills"

# RefineIntent
"Improve the decorators skill"
"Fix the async skill"
"Update the caching skill"

# ChatIntent
"Hello"
"How are you?"
"Tell me a joke"
```

### Intent Handlers

```python
from skill_fleet.core.dspy.streaming import StreamingAssistant

assistant = StreamingAssistant()

# Intent is automatically detected and routed
async for event in assistant.forward_streaming(
    user_message="Create a Redis skill",
    context={"user_id": "user-123"}
):
    # Events stream based on detected intent
    print(event)
```

### Custom Intent Handlers

```python
from skill_fleet.core.dspy.streaming import IntentHandler

class CustomIntentHandler(IntentHandler):
    """Handle custom intent type."""

    def can_handle(self, message: str) -> bool:
        return message.startswith("/custom")

    async def handle(self, message: str, context: dict):
        # Your custom logic
        return {
            "type": "response",
            "data": f"Custom handling: {message}"
        }

# Register custom handler
assistant.register_handler(CustomIntentHandler())
```

## Message History

### ConversationMessage

```python
from skill_fleet.core.services import ConversationMessage, MessageRole

# User message
user_msg = ConversationMessage(
    role=MessageRole.USER,
    content="Create a skill",
    metadata={"timestamp": "2026-01-25T10:00:00Z"}
)

# Assistant message
assistant_msg = ConversationMessage(
    role=MessageRole.ASSISTANT,
    content="I'll create that skill for you",
    metadata={"confidence": 0.95}
)

# System message
system_msg = ConversationMessage(
    role=MessageRole.SYSTEM,
    content="Skill creation started"
)
```

### Role Types

```python
from skill_fleet.core.services import MessageRole

MessageRole.USER      # User input
MessageRole.ASSISTANT # AI response
MessageRole.SYSTEM    # System notifications
```

## State Machine

### State Transitions

```
┌──────────┐  message   ┌──────────┐  complete   ┌───────────┐
│  IDLE    │───────────►│  ACTIVE  │─────────────►│ COMPLETED │
└──────────┘            └──────────┘              └───────────┘
     ▲                       │                       │
     │                       │ input                 │
     │         ┌─────────────┴─────────────┐        │
     │         ▼                           ▼        │
     │  ┌──────────────┐            ┌──────────┐   │
     └──│ AWAITING_INPUT│            │  ERROR   │◄──┘
        └──────────────┘            └──────────┘
```

### State Management

```python
from skill_fleet.core.services import ConversationSession, ConversationState

session = ConversationSession(session_id="test", user_id="user")

# Initial state
assert session.state == ConversationState.IDLE

# Start conversation
session.start_conversation()
assert session.state == ConversationState.ACTIVE

# Request input
session.await_input()
assert session.state == ConversationState.AWAITING_INPUT

# Process input
session.process_input("user response")
assert session.state == ConversationState.ACTIVE

# Complete
session.complete()
assert session.state == ConversationState.COMPLETED

# Error handling
session.set_error("Something went wrong")
assert session.state == ConversationState.ERROR
```

## Context Management

### Session Context

```python
# Context persists across turns
context = {
    "user_id": "user-123",
    "preferences": {
        "detail_level": "advanced",
        "include_examples": True,
    },
    "active_job": "job-abc-123",
    "related_skills": ["python-async", "python-decorators"],
}

session = ConversationSession(
    session_id="sess-1",
    user_id="user-123",
    context=context,
)

# Access context
user_id = session.context["user_id"]
job_id = session.context.get("active_job")

# Update context
session.context["turn_count"] = session.message_count
```

## Integration with Workflow

### Chat to Skill Creation

```python
from skill_fleet.core.dspy import SkillCreationProgram
from skill_fleet.core.services import ConversationSession

# 1. User starts chat
session = ConversationSession(session_id="chat-1", user_id="user")

# 2. Detect create intent
message = "Create a Redis caching skill"
intent = detect_intent(message)  # CreateSkillIntent

# 3. Route to skill creation workflow
if intent == "create_skill":
    program = SkillCreationProgram()
    result = await program.aforward(
        task_description="Redis caching skill",
        user_context={"user_id": "user"},
        taxonomy_structure="{}",
        existing_skills="[]",
        hitl_callback=hitl_callback,
        progress_callback=progress_callback,
    )

    # 4. Update session with result
    session.add_result(result)
    session.complete()
```

## Best Practices

### 1. Use Streaming for Real-Time Experience

```python
# ✅ Good: Streaming for real-time feedback
async for event in assistant.forward_streaming(message, context):
    if event['type'] == 'thinking':
        show_thinking(event['data'])
    elif event['type'] == 'response':
        append_response(event['data'])

# ❌ Avoid: Blocking for long-running tasks
result = await assistant.forward(message, context)  # No feedback until complete
```

### 2. Manage Session Lifecycle

```python
# ✅ Good: Explicit session management
session = await get_or_create_session(session_id)
try:
    result = await process_conversation(session, message)
finally:
    await save_session(session)

# ❌ Avoid: Losing session state
result = await process_message(message)  # No session context
```

### 3. Handle Errors Gracefully

```python
# ✅ Good: Error handling with recovery
try:
    async for event in assistant.forward_streaming(message, context):
        yield event
except Exception as e:
    yield {"type": "error", "data": str(e)}
    session.set_error(str(e))
```

## Testing

### Unit Testing Conversation

```python
import pytest
from skill_fleet.core.services import (
    ConversationSession,
    ConversationMessage,
    MessageRole,
)

def test_session_state_transitions():
    session = ConversationSession(session_id="test", user_id="user")

    assert session.state == ConversationState.IDLE

    session.start_conversation()
    assert session.state == ConversationState.ACTIVE

    session.add_message(ConversationMessage(
        role=MessageRole.USER,
        content="test"
    ))
    assert session.message_count == 1

    session.complete()
    assert session.state == ConversationState.COMPLETED
```

### Testing Intent Detection

```python
def test_intent_detection():
    from skill_fleet.core.dspy.streaming import detect_intent

    assert detect_intent("Create a skill") == "create_skill"
    assert detect_intent("List skills") == "query"
    assert detect_intent("Improve the skill") == "refine"
    assert detect_intent("Hello") == "chat"
```

## Configuration

```python
# In skill_fleet/core/dspy/streaming.py
class StreamingConfig:
    """Streaming configuration."""

    # SSE settings
    SSE_RETRY_TIMEOUT = 3000  # milliseconds
    SSE_HEARTBEAT_INTERVAL = 30  # seconds

    # Session settings
    SESSION_TIMEOUT = 3600  # seconds (1 hour)
    MAX_MESSAGE_HISTORY = 100
    MAX_CONTEXT_SIZE = 10000  # characters

    # Intent detection
    INTENT_CONFIDENCE_THRESHOLD = 0.7
```

## See Also

- **[API: Migration Guide](../api/MIGRATION_V1_TO_V2.md)** - v1 vs v2 API comparison
- **[Service Layer](SERVICE_LAYER.md)** - Service architecture
- **[DSPy Overview](../dspy/index.md)** - DSPy integration
