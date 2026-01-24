# Task Analysis Orchestrator

The **TaskAnalysisOrchestrator** coordinates **Phase 1** of the skill creation workflow: understanding the user's task, gathering requirements, analyzing dependencies, and creating a comprehensive execution plan.

`★ Insight ─────────────────────────────────────`
The Task Analysis phase is critical because it transforms a vague user request ("make a skill for decorators") into a structured plan with domain, topics, taxonomy path, and prerequisites. This prevents downstream generation from producing misaligned content.
`─────────────────────────────────────────────────`

## Overview

The orchestrator coordinates the following activities:

1. **Gather Requirements** - Extract domain, topics, constraints from task description
2. **Analyze Intent** - Understand user goals and success criteria
3. **Find Taxonomy Path** - Determine optimal placement in the skills taxonomy
4. **Analyze Dependencies** - Identify prerequisites and complementary skills
5. **Synthesize Plan** - Combine findings into a coherent skill creation plan

## Quick Start

```python
from skill_fleet.workflows import TaskAnalysisOrchestrator

orchestrator = TaskAnalysisOrchestrator()

result = await orchestrator.analyze(
    task_description="Create a Python decorators skill",
    user_context="Focus on @property and class decorators",
    taxonomy_structure="python/...",
    existing_skills=["python/async", "python/type-hints"],
)

# Access results
requirements = result["requirements"]      # Domain, topics, constraints
intent = result["intent"]                  # Goals, success criteria
taxonomy = result["taxonomy"]              # Recommended path
dependencies = result["dependencies"]      # Prerequisites, complementary
plan = result["plan"]                      # Synthesized execution plan
```

## API Reference

### `__init__(task_lms=None)`

Initialize the orchestrator.

**Parameters:**
- `task_lms` (dict[str, dspy.LM], optional) - Task-specific LMs for different steps

### `analyze(task_description, user_context="", taxonomy_structure="", existing_skills=None, user_confirmation="", enable_mlflow=True)`

Analyze the task and create a comprehensive understanding and plan.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `task_description` | str | User's task description (what they want to create) |
| `user_context` | str | Additional context about the user's goals |
| `taxonomy_structure` | str | Current taxonomy structure for path finding |
| `existing_skills` | list[str] | List of existing skill paths for dependency analysis |
| `user_confirmation` | str | User's confirmation if this is a refinement |
| `enable_mlflow` | bool | Whether to track with MLflow (default: True) |

**Returns:**
```python
{
    "requirements": {
        "domain": "python",
        "topics": ["decorators", "@property", "classmethod"],
        "constraints": ["Python 3.10+", "intermediate level"],
    },
    "intent": {
        "primary_goal": "Teach practical decorator usage",
        "success_criteria": ["User can create decorators", "User understands when to use them"],
    },
    "taxonomy": {
        "recommended_path": "python/decorators",
        "rationale": "Fits under Python as a specialized technique",
    },
    "dependencies": {
        "prerequisites": ["python/functions", "python/classes"],
        "complementary": ["python/context-managers", "python/async"],
    },
    "plan": {
        "skill_metadata": {
            "name": "python_decorators",
            "type": "technical",
            "taxonomy_path": "python/decorators",
        },
        "execution_steps": [...],
    },
}
```

### `get_requirements(task_description, enable_mlflow=False)`

Quick requirements gathering without full analysis.

**Use case:** When you only need to understand the requirements (domain, topics, constraints) without the full planning workflow.

**Parameters:**
- `task_description` (str) - User's task description
- `enable_mlflow` (bool) - Whether to track with MLflow

**Returns:** Dictionary with requirements information

### `get_taxonomy_path(task_description, taxonomy_structure, existing_skills=None, enable_mlflow=False)`

Get the recommended taxonomy path for a skill.

**Use case:** When you only need to find where in the taxonomy a skill should be placed.

**Parameters:**
- `task_description` (str) - User's task description
- `taxonomy_structure` (str) - Current taxonomy structure
- `existing_skills` (list[str]) - List of existing skill paths
- `enable_mlflow` (bool) - Whether to track with MLflow

**Returns:** Dictionary with recommended taxonomy path

## Synchronous Usage

For synchronous contexts (like CLI):

```python
result = orchestrator.analyze_sync(
    task_description="Create a Python decorators skill",
    user_context="Focus on @property and class decorators",
)
```

## Return Value Details

### Requirements

```python
{
    "domain": str,           # Primary domain (e.g., "python", "javascript")
    "topics": list[str],     # Specific topics covered
    "constraints": list[str],# Technical or pedagogical constraints
}
```

### Intent

```python
{
    "primary_goal": str,           # Main objective
    "success_criteria": list[str], # How to measure success
    "target_audience": str,        # Who this skill is for
}
```

### Taxonomy

```python
{
    "recommended_path": str,  # Suggested taxonomy path
    "rationale": str,         # Why this path was chosen
    "alternatives": list[str],# Alternative paths considered
}
```

### Dependencies

```python
{
    "prerequisites": list[str],     # Skills needed before this one
    "complementary": list[str],     # Related skills to learn next
    "confidence_scores": dict[str, float],  # Confidence in each dependency
}
```

### Plan

```python
{
    "skill_metadata": {
        "name": str,
        "type": str,           # "technical", "conceptual", "hybrid"
        "taxonomy_path": str,
        "estimated_difficulty": str,
    },
    "execution_steps": list[dict],
    "content_outline": dict,
}
```

## Examples

### Basic Usage

```python
from skill_fleet.workflows import TaskAnalysisOrchestrator

orchestrator = TaskAnalysisOrchestrator()

result = await orchestrator.analyze(
    task_description="Create a React hooks skill",
    user_context="Focus on useState and useEffect",
    taxonomy_structure="frontend/react/...",
    existing_skills=["frontend/react/components", "frontend/react/state"],
)

# Get recommended taxonomy path
path = result["taxonomy"]["recommended_path"]
print(f"Skill will be placed at: {path}")

# Get prerequisites
prereqs = result["dependencies"]["prerequisites"]
print(f"User should already know: {', '.join(prereqs)}")
```

### With Task-Specific LMs

```python
import dspy

orchestrator = TaskAnalysisOrchestrator(
    task_lms={
        "requirements": dspy.OpenAI(model="gpt-4"),
        "taxonomy": dspy.OpenAI(model="gpt-3.5-turbo"),
    }
)
```

### Lightweight Requirements Gathering

```python
# Just get requirements without full analysis
requirements = orchestrator.get_requirements_sync(
    task_description="Create a Docker skill"
)

print(f"Domain: {requirements['domain']}")
print(f"Topics: {requirements['topics']}")
```

## MLflow Tracking

When `enable_mlflow=True`, the orchestrator logs:

**Parameters:**
- `task_description` (truncated to 500 chars)
- `user_context_length`
- `existing_skills_count`

**Metrics:**
- `requirements_gathered` (bool)
- `intent_analyzed` (bool)
- `taxonomy_found` (bool)
- `dependencies_analyzed` (bool)
- `plan_synthesized` (bool)

**Artifacts:**
- Skill metadata (name, type, path)

## Error Handling

The orchestrator will raise exceptions for:
- **Invalid task descriptions** - Too vague or ambiguous
- **Taxonomy parsing errors** - Malformed taxonomy structure
- **Dependency analysis failures** - Unable to determine prerequisites

Always wrap in try-except for production:

```python
try:
    result = await orchestrator.analyze(
        task_description=user_input,
        taxonomy_structure=taxonomy,
    )
except Exception as e:
    logger.error(f"Task analysis failed: {e}")
    # Handle error appropriately
```

## Related Documentation

- [Content Generation Orchestrator](content-generation.md) - Phase 2
- [Quality Assurance Orchestrator](quality-assurance.md) - Phase 3
- [DSPy Modules - Understanding](../dspy/modules.md) - Core DSPy modules
