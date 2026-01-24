# Conversational Orchestrator

The **ConversationalOrchestrator** manages multi-turn conversational workflow for skill creation, providing an interactive alternative to the three-phase workflow.

`★ Insight ─────────────────────────────────────`
The Conversational Orchestrator uses a **state machine pattern** - each user message triggers a state transition (e.g., INTERPRETING_INTENT → CLARIFYING → DEEP_UNDERSTANDING). This allows the system to handle interruptions, clarifications, and refinements naturally.
`─────────────────────────────────────────────────`

## Overview

The orchestrator manages:
- **Intent Interpretation** - Understand what the user wants
- **Clarification** - Ask questions when needed
- **Deep Understanding** - Gather comprehensive requirements
- **Confirmation** - Verify understanding before proceeding
- **Feedback Collection** - Process user feedback on generated content
- **Test Suggestions** - Recommend tests for the skill

## Quick Start

```python
from skill_fleet.workflows import ConversationalOrchestrator, ConversationState

orchestrator = ConversationalOrchestrator()

# Initialize conversation
context = await orchestrator.initialize_conversation(
    initial_message="Create a Python decorators skill",
)

# Interpret intent
intent = await orchestrator.interpret_intent(
    user_message="Focus on @property and class decorators",
    context=context,
)

# Generate clarifying question if needed
if intent["intent_type"] == "create_skill":
    question = await orchestrator.generate_clarifying_question(context)
    print(question["question"])

# Deep understanding
understanding = await orchestrator.deep_understanding(context)

# Confirm understanding
confirmation = await orchestrator.confirm_understanding(context)
print(confirmation["confirmation_summary"])
```

## API Reference

### `__init__(task_lms=None)`

Initialize the orchestrator.

**Parameters:**
- `task_lms` (dict[str, dspy.LM], optional) - Task-specific LMs

### Conversation Lifecycle

#### `initialize_conversation(initial_message="", metadata=None, enable_mlflow=True)`

Initialize a new conversation context.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `initial_message` | str | Optional initial user message |
| `metadata` | dict, optional | Optional metadata for the conversation |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:** `ConversationContext` object

#### `interpret_intent(user_message, context, enable_mlflow=True)`

Interpret user intent from their message.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_message` | str | User's message |
| `context` | ConversationContext | Current conversation context |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "intent_type": str,       # "create_skill", "clarify", "refine", "multi_skill", "unknown"
    "extracted_task": str,
    "confidence": float,      # 0.0-1.0
    "updated_state": str,     # New conversation state
}
```

### Clarification & Understanding

#### `generate_clarifying_question(context, enable_mlflow=True)`

Generate a clarifying question for the user.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `context` | ConversationContext | Current conversation context |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "question": str,
    "question_options": [str],   # Optional multiple choice options
    "reasoning": str,
}
```

#### `deep_understanding(context, research_findings=None, enable_mlflow=True)`

Perform deep understanding of user requirements.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `context` | ConversationContext | Current conversation context |
| `research_findings` | dict, optional | Optional research findings |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "enhanced_understanding": str,
    "understanding_quality": float,   # 0.0-1.0
    "sufficient": bool,
    "additional_queries_needed": [str],
}
```

#### `confirm_understanding(context, enable_mlflow=True)`

Generate confirmation summary for user.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `context` | ConversationContext | Current conversation context |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "confirmation_summary": str,
    "key_points": [str],
    "completeness_score": float,   # 0.0-1.0
}
```

### Feedback & Testing

#### `process_feedback(user_feedback, skill_content, context, enable_mlflow=True)`

Process user feedback on skill content.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_feedback` | str | User's feedback |
| `skill_content` | str | Current skill content |
| `context` | ConversationContext | Current conversation context |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "actionable_changes": [
        {
            "type": str,
            "description": str,
            "priority": str,
        }
    ],
    "sentiment": str,        # "positive", "neutral", "negative"
    "requires_refinement": bool,
}
```

#### `suggest_tests(skill_content, skill_metadata, enable_mlflow=True)`

Suggest tests for the skill.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `skill_content` | str | Skill content |
| `skill_metadata` | dict | Skill metadata |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "test_suggestions": [
        {
            "description": str,
            "type": str,        # "unit", "integration", "example"
            "priority": str,
        }
    ],
    "coverage_areas": [str],
}
```

## Conversation States

```python
class ConversationState(Enum):
    INITIALIZING = "initializing"
    INTERPRETING_INTENT = "interpreting_intent"
    CLARIFYING = "clarifying"
    DEEP_UNDERSTANDING = "deep_understanding"
    CONFIRMING_UNDERSTANDING = "confirming_understanding"
    CREATING_SKILL = "creating_skill"
    PRESENTING_SKILL = "presenting_skill"
    COLLECTING_FEEDBACK = "collecting_feedback"
    REFINING = "refining"
    TESTING = "testing"
    COMPLETED = "completed"
```

## Intent Types

```python
class IntentType(Enum):
    CREATE_SKILL = "create_skill"
    CLARIFY = "clarify"
    REFINE = "refine"
    MULTI_SKILL = "multi_skill"
    UNKNOWN = "unknown"
```

## Data Structures

### ConversationMessage

```python
@dataclass
class ConversationMessage:
    role: str                   # "user", "assistant", "system"
    content: str
    timestamp: str
    metadata: dict[str, Any]
```

### ConversationContext

```python
@dataclass
class ConversationContext:
    conversation_id: str
    state: ConversationState
    messages: list[ConversationMessage]
    collected_examples: list[dict]
    current_understanding: str
    task_description: str
    user_confirmations: dict[str, Any]
    created_at: str
    metadata: dict[str, Any]
```

## Synchronous Usage

```python
orchestrator = ConversationalOrchestrator()

# Synchronous usage
context = orchestrator.initialize_conversation_sync(
    initial_message="Create a Python decorators skill",
)
```

## Examples

### Basic Conversation Flow

```python
from skill_fleet.workflows import ConversationalOrchestrator, ConversationState

orchestrator = ConversationalOrchestrator()

# Initialize
context = await orchestrator.initialize_conversation(
    initial_message="Create a Python decorators skill",
)

# Interactive loop
while context.state != ConversationState.COMPLETED:
    user_message = input("You: ")

    # Interpret intent
    intent = await orchestrator.interpret_intent(user_message, context)

    # Handle based on intent
    if intent["intent_type"] == "create_skill":
        question = await orchestrator.generate_clarifying_question(context)
        print(f"Bot: {question['question']}")

    elif intent["intent_type"] == "clarify":
        understanding = await orchestrator.deep_understanding(context)
        if understanding["sufficient"]:
            confirmation = await orchestrator.confirm_understanding(context)
            print(f"Bot: {confirmation['confirmation_summary']}")

    # ... handle other intents
```

### Processing Feedback

```python
# After presenting skill
skill_content = """# Python Decorators
..."""

feedback = "The examples section needs more practical use cases"

# Process feedback
changes = await orchestrator.process_feedback(
    user_feedback=feedback,
    skill_content=skill_content,
    context=context,
)

print(f"Actionable changes: {len(changes['actionable_changes'])}")
for change in changes['actionable_changes']:
    print(f"  - {change['description']} ({change['priority']})")
```

### Suggesting Tests

```python
# Suggest tests for the skill
tests = await orchestrator.suggest_tests(
    skill_content=skill_content,
    skill_metadata={
        "name": "python_decorators",
        "type": "technical",
        "taxonomy_path": "python/decorators",
    },
)

print(f"Suggested {len(tests['test_suggestions'])} tests")
for test in tests['test_suggestions']:
    print(f"  - {test['description']} ({test['type']})")

print(f"\nCoverage areas: {tests['coverage_areas']}")
```

## MLflow Tracking

When `enable_mlflow=True`, the orchestrator logs to experiment `conversational-interface` with metrics:
- `conversation_id`
- `intent_type`
- `confidence`
- `understanding_quality`
- `completeness_score`
- `test_count`

## Integration Example

```python
from skill_fleet.workflows import ConversationalOrchestrator

async def chat_loop():
    orchestrator = ConversationalOrchestrator()
    context = await orchestrator.initialize_conversation()

    print("Skill Fleet Chat (type 'quit' to exit)")

    while True:
        user_message = input("\nYou: ")

        if user_message.lower() == 'quit':
            break

        # Interpret intent
        intent = await orchestrator.interpret_intent(user_message, context)

        # Handle different intents
        if intent["intent_type"] == "create_skill":
            await handle_create_skill(orchestrator, context)

        elif intent["intent_type"] == "refine":
            await handle_refinement(orchestrator, context, user_message)

        else:
            print(f"Bot: I understand you want to: {intent['extracted_task']}")
            question = await orchestrator.generate_clarifying_question(context)
            print(f"Bot: {question['question']}")

async def handle_create_skill(orchestrator, context):
    # Deep understanding
    understanding = await orchestrator.deep_understanding(context)

    # Confirm
    confirmation = await orchestrator.confirm_understanding(context)
    print(f"\n{confirmation['confirmation_summary']}")

    # Generate skill (would integrate with ContentGenerationOrchestrator)
    # ...

    # Suggest tests
    tests = await orchestrator.suggest_tests(
        skill_content=skill_content,
        skill_metadata=metadata,
    )
    print(f"\nSuggested tests: {len(tests['test_suggestions'])}")

# Run the chat loop
import asyncio
asyncio.run(chat_loop())
```

## Related Documentation

- [Task Analysis Orchestrator](task-analysis.md) - Phase 1 workflow
- [HITL Checkpoint Manager](hitl.md) - Structured human-in-the-loop
- [CLI Interactive Chat](../cli/interactive-chat.md) - CLI chat interface
