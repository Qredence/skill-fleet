# HITL Checkpoint Manager

The **HITLCheckpointManager** manages human-in-the-loop (HITL) checkpoints throughout the skill creation workflow, enabling interactive refinement and validation.

`★ Insight ─────────────────────────────────────`
HITL uses **adaptive checkpointing** - the strategy for when to interrupt and ask for human input varies based on task complexity and user preferences. Simple tasks may only need final confirmation, while complex tasks get checkpoints at each phase.
`─────────────────────────────────────────────────`

## Overview

The manager handles all HITL interactions:
- **Strategy Determination** - Decide when and how to involve humans
- **Clarifying Questions** - Generate questions to resolve ambiguities
- **Understanding Confirmation** - Verify understanding before proceeding
- **Preview Generation** - Create previews for user review
- **Feedback Analysis** - Process and interpret user feedback
- **Refinement Planning** - Plan changes based on feedback
- **Readiness Assessment** - Check if sufficient information exists to proceed

## Quick Start

```python
from skill_fleet.workflows import HITLCheckpointManager, CheckpointPhase

manager = HITLCheckpointManager()

# Determine HITL strategy
strategy = await manager.determine_strategy(
    task_description="Create async Python skill",
    task_complexity="intermediate",
)

# Generate clarifying questions if needed
if strategy["needs_clarification"]:
    questions = await manager.generate_clarifying_questions(
        task_description="...",
        initial_analysis="...",
        ambiguities=["Which async patterns?", "Target Python version?"],
    )

# Create checkpoint
checkpoint = manager.create_checkpoint(
    phase=CheckpointPhase.PHASE1_UNDERSTANDING,
    checkpoint_type="clarification",
    data={"questions": questions["questions"]},
)

# Wait for user response and update
user_response = get_user_response(questions["questions"])
manager.update_checkpoint_status(
    checkpoint.checkpoint_id,
    "approved",
    user_response={"answers": user_response},
)
```

## API Reference

### `__init__(task_lms=None)`

Initialize the checkpoint manager.

**Parameters:**
- `task_lms` (dict[str, dspy.LM], optional) - Task-specific LMs

### Strategy & Questions

#### `determine_strategy(task_description, task_complexity="intermediate", user_preferences="", enable_mlflow=True)`

Determine optimal HITL strategy for a task.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `task_description` | str | Description of the task |
| `task_complexity` | str | Complexity level: `"beginner"`, `"intermediate"`, `"advanced"` |
| `user_preferences` | str | User preferences for HITL |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "strategy": str,           # "minimal", "standard", "extensive"
    "checkpoints": [str],      # Recommended checkpoint points
    "needs_clarification": bool,
    "ambiguities": [str],      # Identified ambiguities
}
```

#### `generate_clarifying_questions(task_description, initial_analysis, ambiguities, enable_mlflow=True)`

Generate clarifying questions to understand user intent.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `task_description` | str | User's task description |
| `initial_analysis` | str | Initial analysis of the task |
| `ambiguities` | list[str] | List of identified ambiguities |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "questions": [str],
    "priority": str,           # "high", "medium", "low"
    "rationale": str,
}
```

#### `confirm_understanding(task_description, user_clarifications, intent_analysis, taxonomy_path, dependencies, enable_mlflow=True)`

Generate confirmation summary for user.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `task_description` | str | Original task description |
| `user_clarifications` | str | User's clarifications |
| `intent_analysis` | str | Analysis of user intent |
| `taxonomy_path` | str | Determined taxonomy path |
| `dependencies` | list[str] | List of identified dependencies |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "confirmation_summary": str,
    "assumptions": [str],
    "confidence": float,        # 0.0-1.0
}
```

### Preview & Feedback

#### `generate_preview(skill_content, metadata, enable_mlflow=True)`

Generate preview of skill content for user review.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `skill_content` | str | Generated skill content |
| `metadata` | str | Skill metadata |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "preview": str,
    "highlights": [str],
    "potential_issues": [str],
}
```

#### `analyze_feedback(user_feedback, current_content, enable_mlflow=True)`

Analyze user feedback and determine changes needed.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_feedback` | str | User's feedback on the content |
| `current_content` | str | Current content being reviewed |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "change_requests": [
        {
            "type": str,
            "description": str,
            "priority": str,
        }
    ],
    "scope_change": str,       # "none", "minor", "major"
    "estimated_effort": str,   # "low", "medium", "high"
}
```

### Validation & Refinement

#### `format_validation_results(validation_report, skill_content, enable_mlflow=True)`

Format validation results for human-readable display.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `validation_report` | str | Validation report |
| `skill_content` | str | Skill content that was validated |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "formatted_report": str,
    "critical_issues": [...],
    "warnings": [...],
    "auto_fixable": [...],
}
```

#### `plan_refinement(validation_issues, user_feedback, current_skill, enable_mlflow=True)`

Generate refinement plan based on validation and feedback.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `validation_issues` | str | Issues from validation |
| `user_feedback` | str | User feedback for refinement |
| `current_skill` | str | Current skill content |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "refinement_plan": [str],
    "estimated_iterations": int,
    "priority_order": [str],
}
```

#### `assess_readiness(phase, collected_info, min_requirements, enable_mlflow=True)`

Assess readiness to proceed to next phase.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `phase` | str | Current phase |
| `collected_info` | str | Information collected so far |
| `min_requirements` | str | Minimum requirements to proceed |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "ready": bool,
    "readiness_score": float,   # 0.0-1.0
    "missing_info": [str],
}
```

### Checkpoint Management

#### `create_checkpoint(phase, checkpoint_type, data, metadata=None)`

Create a new checkpoint.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `phase` | CheckpointPhase | Phase where checkpoint occurs |
| `checkpoint_type` | str | Type of checkpoint |
| `data` | dict | Data associated with checkpoint |
| `metadata` | dict, optional | Optional metadata |

**Returns:** `Checkpoint` object

#### `get_checkpoint(checkpoint_id)`

Get checkpoint by ID.

**Returns:** `Checkpoint` object or `None`

#### `update_checkpoint_status(checkpoint_id, status, user_response=None)`

Update checkpoint status.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `checkpoint_id` | str | Checkpoint ID |
| `status` | str | New status: `"pending"`, `"waiting"`, `"approved"`, `"rejected"` |
| `user_response` | dict, optional | Optional user response |

**Returns:** `True` if updated, `False` if not found

## Checkpoint Phases

```python
class CheckpointPhase(Enum):
    PHASE1_UNDERSTANDING = "phase1_understanding"
    PHASE2_CONTENT_GENERATION = "phase2_content_generation"
    PHASE3_VALIDATION = "phase3_validation"
```

## Checkpoint Data Structure

```python
@dataclass
class Checkpoint:
    checkpoint_id: str
    phase: CheckpointPhase
    checkpoint_type: str
    status: str                    # pending, waiting, approved, rejected
    created_at: str
    data: dict[str, Any]
    user_response: dict[str, Any] | None
    metadata: dict[str, Any]
```

## Synchronous Usage

All async methods have synchronous wrappers:

```python
manager = HITLCheckpointManager()

# Synchronous usage
strategy = manager.determine_strategy_sync(
    task_description="...",
    task_complexity="intermediate",
)
```

## Examples

### Basic HITL Workflow

```python
from skill_fleet.workflows import HITLCheckpointManager, CheckpointPhase

manager = HITLCheckpointManager()

# Determine strategy
strategy = await manager.determine_strategy(
    task_description="Create async Python skill",
    task_complexity="intermediate",
)

# Generate questions
questions = await manager.generate_clarifying_questions(
    task_description="Create async Python skill",
    initial_analysis="User wants async programming patterns",
    ambiguities=["Which async patterns?", "Target audience?"],
)

# Create checkpoint
checkpoint = manager.create_checkpoint(
    phase=CheckpointPhase.PHASE1_UNDERSTANDING,
    checkpoint_type="clarification",
    data={"questions": questions["questions"]},
)

# In real app: wait for user response
# Then update checkpoint
manager.update_checkpoint_status(
    checkpoint.checkpoint_id,
    "approved",
    user_response={"answers": ["asyncio and trio", "intermediate developers"]},
)
```

### Preview and Feedback

```python
# Generate preview for user review
preview = await manager.generate_preview(
    skill_content=generated_skill,
    metadata="python/async: Async patterns in Python",
)

# Display preview to user
display_preview(preview["preview"])

# Get user feedback
feedback = get_user_feedback()

# Analyze feedback
changes = await manager.analyze_feedback(
    user_feedback=feedback,
    current_content=generated_skill,
)

# Plan refinement
plan = await manager.plan_refinement(
    validation_issues="",
    user_feedback=feedback,
    current_skill=generated_skill,
)
```

### Readiness Assessment

```python
# Check if we have enough info to proceed
readiness = await manager.assess_readiness(
    phase="phase1_understanding",
    collected_info=str(collected_data),
    min_requirements="domain, topics, target_audience",
)

if readiness["ready"]:
    # Proceed to next phase
    pass
else:
    # Ask for missing info
    print(f"Still need: {readiness['missing_info']}")
```

## MLflow Tracking

Each HITL operation logs to MLflow with appropriate experiments:
- `hitl-strategy` - Strategy determination
- `hitl-clarifying-questions` - Question generation
- `hitl-confirm-understanding` - Understanding confirmation
- `hitl-preview` - Preview generation
- `hitl-analyze-feedback` - Feedback analysis
- `hitl-format-validation` - Validation formatting
- `hitl-refinement-planning` - Refinement planning
- `hitl-readiness-assessment` - Readiness checks

## Related Documentation

- [Task Analysis Orchestrator](task-analysis.md) - Phase 1 (often uses HITL)
- [Conversational Orchestrator](conversational.md) - Alternative interactive interface
- [HITL System Overview](../hitl/index.md) - Complete HITL system documentation
