# Content Generation Orchestrator

The **ContentGenerationOrchestrator** coordinates **Phase 2** of the skill creation workflow: generating skill content based on the understanding and plan from Phase 1.

`★ Insight ─────────────────────────────────────`
The Content Generation phase supports different **skill styles** (navigation_hub, comprehensive, minimal). This allows the same underlying task to generate different types of skills depending on use case - a navigation hub for discovery vs a comprehensive skill for deep learning.
`─────────────────────────────────────────────────`

## Overview

The orchestrator coordinates:
- **Main Content Generation** - SKILL.md with all sections
- **Extra Files** - Examples, best practices, common patterns
- **Style Adaptation** - Different formats for different use cases
- **Feedback Integration** - Refinement based on user input

## Quick Start

```python
from skill_fleet.workflows import ContentGenerationOrchestrator

orchestrator = ContentGenerationOrchestrator()

result = await orchestrator.generate(
    understanding=phase1_result["understanding"],
    plan=phase1_result["plan"],
    skill_style="comprehensive",  # or "navigation_hub" or "minimal"
)

# Access results
skill_content = result["skill_content"]       # Main SKILL.md
extra_files = result["extra_files"]           # Supporting files
validation_report = result["validation_report"] # Initial validation
```

## API Reference

### `__init__(task_lms=None)`

Initialize the orchestrator.

**Parameters:**
- `task_lms` (dict[str, dspy.LM], optional) - Task-specific LMs

### `generate(understanding, plan, skill_style=DEFAULT_SKILL_STYLE, user_feedback="", enable_mlflow=True)`

Generate skill content based on understanding and plan.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `understanding` | dict | Phase 1 understanding result |
| `plan` | dict | Synthesized plan from Phase 1 |
| `skill_style` | SkillStyle | Style of skill: `"navigation_hub"`, `"comprehensive"`, or `"minimal"` |
| `user_feedback` | str | Optional feedback for refinement |
| `enable_mlflow` | bool | Whether to track with MLflow (default: True) |

**Returns:**
```python
{
    "skill_content": str,      # Main SKILL.md content
    "extra_files": {           # Supporting files
        "examples.md": str,
        "best_practices.md": str,
        "common_patterns.md": str,
    },
    "validation_report": {     # Initial validation results
        "passed": bool,
        "issues": list[str],
    },
}
```

## Skill Styles

### `navigation_hub`

A concise skill that links to related skills and provides high-level overview.

**Use case:** Discovery and navigation within the skills taxonomy.

**Characteristics:**
- Brief descriptions
- Links to related skills
- High-level concepts
- Minimal examples

### `comprehensive`

A full-featured skill with in-depth coverage.

**Use case:** Primary learning resource for a topic.

**Characteristics:**
- Detailed explanations
- Multiple examples
- Best practices
- Common patterns
- Test suggestions

### `minimal`

A lightweight skill with just the essentials.

**Use case:** Quick reference or supplementary material.

**Characteristics:**
- Core concepts only
- Essential examples
- No extensive elaboration

## Synchronous Usage

```python
result = orchestrator.generate_sync(
    understanding=phase1_result["understanding"],
    plan=phase1_result["plan"],
    skill_style="comprehensive",
)
```

## Examples

### Basic Usage

```python
from skill_fleet.workflows import ContentGenerationOrchestrator

orchestrator = ContentGenerationOrchestrator()

result = await orchestrator.generate(
    understanding={
        "domain": "python",
        "topics": ["decorators", "@property", "classmethod"],
    },
    plan={
        "skill_metadata": {
            "name": "python_decorators",
            "type": "technical",
        },
    },
    skill_style="comprehensive",
)

# Save the skill content
with open("python_decorators/SKILL.md", "w") as f:
    f.write(result["skill_content"])

# Save extra files
for filename, content in result["extra_files"].items():
    with open(f"python_decorators/{filename}", "w") as f:
        f.write(content)
```

### Different Skill Styles

```python
# Navigation hub - for discovery
hub_result = await orchestrator.generate(
    understanding=understanding,
    plan=plan,
    skill_style="navigation_hub",
)

# Comprehensive - for deep learning
comprehensive_result = await orchestrator.generate(
    understanding=understanding,
    plan=plan,
    skill_style="comprehensive",
)

# Minimal - for quick reference
minimal_result = await orchestrator.generate(
    understanding=understanding,
    plan=plan,
    skill_style="minimal",
)
```

### With User Feedback

```python
# Initial generation
result = await orchestrator.generate(
    understanding=understanding,
    plan=plan,
    skill_style="comprehensive",
)

# User provides feedback
feedback = "Add more practical examples for @property"

# Refined generation
refined_result = await orchestrator.generate(
    understanding=understanding,
    plan=plan,
    skill_style="comprehensive",
    user_feedback=feedback,
)
```

## Return Value Details

### `skill_content`

The main SKILL.md file content, following the [agentskills.io](../concepts/agentskills-compliance.md) schema:

```markdown
# Skill Name

Brief description of what this skill teaches.

## Description

Detailed description of the skill content.

## Capabilities

- Capability 1
- Capability 2

## Examples

### Example 1
...
```

### `extra_files`

Dictionary of supporting file names to content:

```python
{
    "examples.md": str,          # Practical examples
    "best_practices.md": str,    # Best practices
    "common_patterns.md": str,   # Common usage patterns
    "common_pitfalls.md": str,   # Pitfalls to avoid (optional)
}
```

### `validation_report`

Initial validation results:

```python
{
    "passed": bool,
    "issues": [
        {
            "severity": "error" | "warning" | "info",
            "message": str,
            "location": str,  # File/section reference
        }
    ],
}
```

## MLflow Tracking

When `enable_mlflow=True`, the orchestrator logs:

**Parameters:**
- `skill_style`
- `has_user_feedback` (bool)

**Metrics:**
- `content_generated` (bool)
- `extra_files_generated` (bool)
- `validation_performed` (bool)

## Error Handling

The orchestrator will raise exceptions for:
- **Invalid understanding** - Missing required fields
- **Invalid plan** - Malformed plan structure
- **Unknown skill style** - Style not in navigation_hub/comprehensive/minimal
- **Generation failures** - Underlying LLM errors

```python
try:
    result = await orchestrator.generate(
        understanding=understanding,
        plan=plan,
    )
except ValueError as e:
    logger.error(f"Invalid input: {e}")
except Exception as e:
    logger.error(f"Generation failed: {e}")
```

## Integration with Three-Phase Workflow

```python
from skill_fleet.workflows import (
    TaskAnalysisOrchestrator,
    ContentGenerationOrchestrator,
    QualityAssuranceOrchestrator,
)

task_orchestrator = TaskAnalysisOrchestrator()
content_orchestrator = ContentGenerationOrchestrator()
qa_orchestrator = QualityAssuranceOrchestrator()

# Phase 1
analysis = await task_orchestrator.analyze(task_description="...")

# Phase 2
content = await content_orchestrator.generate(
    understanding=analysis["understanding"],
    plan=analysis["plan"],
    skill_style="comprehensive",
)

# Phase 3
validation = await qa_orchestrator.validate_and_refine(
    skill_content=content["skill_content"],
    skill_metadata=analysis["plan"]["skill_metadata"],
    content_plan=analysis["plan"],
    validation_rules="...",
)
```

## Related Documentation

- [Task Analysis Orchestrator](task-analysis.md) - Phase 1
- [Quality Assurance Orchestrator](quality-assurance.md) - Phase 3
- [DSPy Modules - Generation](../dspy/modules.md) - Core DSPy modules
