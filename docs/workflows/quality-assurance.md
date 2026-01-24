# Quality Assurance Orchestrator

The **QualityAssuranceOrchestrator** coordinates **Phase 3** of the skill creation workflow: validating skill content against quality rules and refining based on validation feedback.

`★ Insight ─────────────────────────────────────`
Quality Assurance uses **adaptive validation** - the rigor of validation scales with the target level. A "beginner" skill gets stricter pedagogical checks, while an "advanced" skill focuses on technical accuracy and edge cases.
`─────────────────────────────────────────────────`

## Overview

The orchestrator coordinates:
- **Validation** - Check content against quality rules
- **Issue Detection** - Identify critical and minor issues
- **Refinement** - Improve content based on feedback
- **Quality Assessment** - Score content against target level

## Quick Start

```python
from skill_fleet.workflows import QualityAssuranceOrchestrator

orchestrator = QualityAssuranceOrchestrator()

result = await orchestrator.validate_and_refine(
    skill_content=skill_md_content,
    skill_metadata=metadata,
    content_plan=phase1_plan,
    validation_rules="agentskills.io compliance",
    target_level="intermediate",
)

# Access results
validation_report = result["validation_report"]     # Detailed validation
refined_content = result["refined_content"]         # Improved content
critical_issues = result["critical_issues"]         # Must-fix issues
warnings = result["warnings"]                       # Nice-to-fix issues
quality_assessment = result["quality_assessment"]   # Quality score
```

## API Reference

### `__init__(task_lms=None)`

Initialize the orchestrator.

**Parameters:**
- `task_lms` (dict[str, dspy.LM], optional) - Task-specific LMs

### `validate_and_refine(skill_content, skill_metadata, content_plan, validation_rules, user_feedback="", target_level="intermediate", enable_mlflow=True)`

Validate and refine skill content.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `skill_content` | str | The SKILL.md content to validate |
| `skill_metadata` | Any | Skill metadata for context |
| `content_plan` | str | Original content plan for comparison |
| `validation_rules` | str | Validation rules and criteria |
| `user_feedback` | str | Optional user feedback for refinement |
| `target_level` | str | Target complexity: `"beginner"`, `"intermediate"`, `"advanced"` |
| `enable_mlflow` | bool | Whether to track with MLflow (default: True) |

**Returns:**
```python
{
    "validation_report": {
        "passed": bool,
        "score": float,
        "checks": {
            "schema_compliance": bool,
            "content_completeness": bool,
            "pedagogical_soundness": bool,
            "technical_accuracy": bool,
        },
    },
    "refined_content": str,          # Refined skill content (if needed)
    "critical_issues": [
        {
            "type": str,
            "message": str,
            "location": str,
            "suggestion": str,
        }
    ],
    "warnings": [...],               # Non-critical issues
    "quality_assessment": {
        "calibrated_score": float,
        "audience_alignment": float,
        "completeness": float,
        "clarity": float,
    },
}
```

## Target Levels

### `beginner`

Stricter pedagogical validation:
- Clear explanations
- Minimal jargon
- Progressive difficulty
- Extensive examples

### `intermediate`

Balanced validation:
- Technical accuracy
- Clear examples
- Practical focus
- Some depth

### `advanced`

Focus on depth and correctness:
- Comprehensive coverage
- Edge cases addressed
- Performance considerations
- Advanced patterns

## Synchronous Usage

```python
result = orchestrator.validate_and_refine_sync(
    skill_content=skill_md_content,
    skill_metadata=metadata,
    content_plan=plan,
    validation_rules="...",
    target_level="intermediate",
)
```

## Examples

### Basic Validation

```python
from skill_fleet.workflows import QualityAssuranceOrchestrator

orchestrator = QualityAssuranceOrchestrator()

result = await orchestrator.validate_and_refine(
    skill_content=skill_md,
    skill_metadata={
        "name": "python_decorators",
        "type": "technical",
    },
    content_plan=phase1_plan,
    validation_rules="agentskills.io schema compliance",
    target_level="intermediate",
)

# Check if validation passed
if result["validation_report"]["passed"]:
    print("Content is ready!")
else:
    print(f"Found {len(result['critical_issues'])} critical issues")
    for issue in result["critical_issues"]:
        print(f"  - {issue['message']}")
```

### With User Feedback

```python
# User has specific concerns
feedback = """
The examples section is too sparse.
Add more practical use cases for @property.
"""

result = await orchestrator.validate_and_refine(
    skill_content=skill_md,
    skill_metadata=metadata,
    content_plan=plan,
    validation_rules="...",
    user_feedback=feedback,
    target_level="intermediate",
)

# User feedback is incorporated into refined content
refined = result["refined_content"]
```

### Different Target Levels

```python
# Beginner skill - stricter pedagogical validation
beginner_result = await orchestrator.validate_and_refine(
    skill_content=skill_md,
    skill_metadata=metadata,
    content_plan=plan,
    validation_rules="...",
    target_level="beginner",
)

# Advanced skill - focus on technical depth
advanced_result = await orchestrator.validate_and_refine(
    skill_content=skill_md,
    skill_metadata=metadata,
    content_plan=plan,
    validation_rules="...",
    target_level="advanced",
)
```

## Return Value Details

### `validation_report`

```python
{
    "passed": bool,            # Overall pass/fail
    "score": float,            # Overall score (0.0-1.0)
    "checks": {
        "schema_compliance": bool,     # Follows agentskills.io schema
        "content_completeness": bool,  # All required sections present
        "pedagogical_soundness": bool, # Good teaching approach
        "technical_accuracy": bool,    # Technically correct
    },
}
```

### `critical_issues`

List of issues that must be fixed:

```python
{
    "type": "missing_section" | "invalid_format" | "technical_error",
    "message": str,
    "location": str,          # File/section reference
    "suggestion": str,        # How to fix
}
```

### `warnings`

List of non-critical issues:

```python
{
    "type": "style" | "clarity" | "completeness",
    "message": str,
    "location": str,
    "suggestion": str,
}
```

### `quality_assessment`

```python
{
    "calibrated_score": float,       # Overall quality (0.0-1.0)
    "audience_alignment": float,     # Matches target level (0.0-1.0)
    "completeness": float,           # Content coverage (0.0-1.0)
    "clarity": float,                # Explanations clarity (0.0-1.0)
}
```

## MLflow Tracking

When `enable_mlflow=True`, the orchestrator logs:

**Parameters:**
- `target_level`
- `has_user_feedback` (bool)

**Metrics:**
- `validation_passed` (bool)
- `quality_score` (float)
- `issues_count` (int)
- `refinement_performed` (bool)

## Validation Rules

Common validation rules include:

### Schema Compliance
- Required sections present (Description, Capabilities, Examples)
- Proper heading hierarchy
- Valid markdown formatting

### Content Completeness
- All capabilities documented
- Sufficient examples
- Clear prerequisites

### Pedagogical Soundness
- Progressive complexity
- Clear explanations
- Practical relevance

### Technical Accuracy
- Correct code examples
- Accurate descriptions
- No factual errors

## Error Handling

```python
try:
    result = await orchestrator.validate_and_refine(
        skill_content=skill_md,
        skill_metadata=metadata,
        content_plan=plan,
        validation_rules="...",
    )
except ValueError as e:
    logger.error(f"Invalid input: {e}")
except Exception as e:
    logger.error(f"Validation failed: {e}")
```

## Integration with Three-Phase Workflow

```python
from skill_fleet.workflows import (
    TaskAnalysisOrchestrator,
    ContentGenerationOrchestrator,
    QualityAssuranceOrchestrator,
)

# Phase 1
task_orchestrator = TaskAnalysisOrchestrator()
analysis = await task_orchestrator.analyze(task_description="...")

# Phase 2
content_orchestrator = ContentGenerationOrchestrator()
content = await content_orchestrator.generate(
    understanding=analysis["understanding"],
    plan=analysis["plan"],
)

# Phase 3
qa_orchestrator = QualityAssuranceOrchestrator()
validation = await qa_orchestrator.validate_and_refine(
    skill_content=content["skill_content"],
    skill_metadata=analysis["plan"]["skill_metadata"],
    content_plan=analysis["plan"],
    validation_rules="agentskills.io compliance",
    target_level="intermediate",
)

# Check results
if validation["validation_report"]["passed"]:
    # Use refined content
    final_content = validation.get("refined_content", content["skill_content"])
else:
    # Handle critical issues
    print(f"Please fix: {validation['critical_issues']}")
```

## Related Documentation

- [Task Analysis Orchestrator](task-analysis.md) - Phase 1
- [Content Generation Orchestrator](content-generation.md) - Phase 2
- [agentskills.io Compliance](../concepts/agentskills-compliance.md) - Schema details
