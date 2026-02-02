# Core Workflows Reference

**Last Updated**: 2026-02-02
**Location**: `src/skill_fleet/core/workflows/skill_creation/`

## Overview

The skill creation system uses three coordinated workflows that execute sequentially:

1. **UnderstandingWorkflow** - Phase 1: Requirements analysis and planning
2. **GenerationWorkflow** - Phase 2: Content creation
3. **ValidationWorkflow** - Phase 3: Quality assurance

---

## UnderstandingWorkflow

**Class**: `UnderstandingWorkflow`
**File**: `src/skill_fleet/core/workflows/skill_creation/understanding.py`

Orchestrates the understanding phase of skill creation.

### Constructor

```python
workflow = UnderstandingWorkflow()
```

Initializes all required modules:
- `GatherRequirementsModule`
- `AnalyzeIntentModule`
- `FindTaxonomyPathModule`
- `AnalyzeDependenciesModule`
- `SynthesizePlanModule`
- `GenerateClarifyingQuestionsModule`
- `ValidateStructureModule`

### Methods

#### execute()

```python
async def execute(
    self,
    task_description: str,
    user_context: dict | None = None,
    taxonomy_structure: dict | None = None,
    existing_skills: list[str] | None = None,
) -> dict[str, Any]
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_description` | `str` | Yes | User's task description |
| `user_context` | `dict` | No | User preferences and history |
| `taxonomy_structure` | `dict` | No | Current taxonomy tree |
| `existing_skills` | `list[str]` | No | List of existing skill paths |

**Returns:**

Success case:
```python
{
    "status": "completed",
    "plan": {
        "skill_name": str,
        "skill_description": str,
        "taxonomy_path": str,
        "content_outline": list[str],
        "generation_guidance": str,
        "success_criteria": list[str],
        "estimated_length": str,
        "tags": list[str],
        "trigger_phrases": list[str],
        "negative_triggers": list[str],
        "skill_category": str,
    },
    "requirements": dict,
    "intent": dict,
    "taxonomy": dict,
    "dependencies": dict,
}
```

HITL case (structure fix):
```python
{
    "status": "pending_hitl",
    "hitl_type": "structure_fix",
    "hitl_data": {
        "suggested_name": str,
        "name_errors": list[str],
        "suggested_description": str,
        "description_errors": list[str],
    },
    "context": dict,  # For resumption
}
```

HITL case (questions):
```python
{
    "status": "pending_hitl",
    "hitl_type": "questions",
    "hitl_data": {
        "questions": list[dict],
        "priority": str,
        "rationale": str,
    },
    "context": dict,  # For resumption
}
```

**Execution Order:**
1. Gather requirements
2. Validate structure (early validation)
3. Analyze intent (parallel with taxonomy)
4. Find taxonomy path
5. Analyze dependencies (depends on intent)
6. Synthesize plan

**Raises:**
- `ValueError` - Invalid task description
- `WorkflowError` - Module execution failure

---

## GenerationWorkflow

**Class**: `GenerationWorkflow`
**File**: `src/skill_fleet/core/workflows/skill_creation/generation.py`

Generates skill content based on Phase 1 output.

### Constructor

```python
workflow = GenerationWorkflow()
```

### Methods

#### execute()

```python
async def execute(
    self,
    plan: dict,
    understanding: dict,
    enable_hitl_preview: bool = False,
    skill_style: str = "comprehensive",
    quality_threshold: float | None = None,
    manager: StreamingWorkflowManager | None = None,
) -> dict[str, Any]
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `plan` | `dict` | Yes | Plan from UnderstandingWorkflow |
| `understanding` | `dict` | Yes | Understanding results |
| `enable_hitl_preview` | `bool` | No | Show preview for feedback |
| `skill_style` | `str` | No | `minimal`, `comprehensive`, `navigation_hub` |
| `quality_threshold` | `float \| None` | No | Minimum quality score (uses `DEFAULT_QUALITY_THRESHOLDS` if None) |
| `manager` | `StreamingWorkflowManager` | No | Optional streaming manager |

**Returns:**

Success case:
```python
{
    "status": "completed",
    "skill_content": str,  # Full SKILL.md content
    "sections_generated": list[str],
    "code_examples_count": int,
    "estimated_reading_time": int,
}
```

HITL case (preview):
```python
{
    "status": "pending_hitl",
    "hitl_type": "preview",
    "hitl_data": {
        "skill_content": str,
        "sections_count": int,
        "examples_count": int,
        "reading_time": int,
    },
    "context": {
        "plan": dict,
        "understanding": dict,
        "skill_style": str,
    },
}
```

**Skill Styles:**

| Style | Description | Best For |
|-------|-------------|----------|
| `minimal` | Concise (~50-150 lines) | Simple tools, single patterns |
| `comprehensive` | Detailed (~400-800 lines) | Procedures, workflows, checklists |
| `navigation_hub` | Short with subdirectories | Complex skills, many patterns |

#### incorporate_feedback()

```python
async def incorporate_feedback(
    self,
    current_content: str,
    feedback: str,
    change_requests: list[str],
) -> dict[str, Any]
```

Applies user feedback to generated content.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `current_content` | `str` | Current SKILL.md content |
| `feedback` | `str` | General feedback text |
| `change_requests` | `list[str]` | Specific changes to make |

**Returns:**
```python
{
    "status": "completed",
    "skill_content": str,  # Updated content
    "changes_made": list[str],
    "sections_generated": list[str],
}
```

---

## ValidationWorkflow

**Class**: `ValidationWorkflow`
**File**: `src/skill_fleet/core/workflows/skill_creation/validation.py`

Validates skill content for compliance and quality.

### Constructor

```python
workflow = ValidationWorkflow()
```

### Methods

#### execute()

```python
async def execute(
    self,
    skill_content: str,
    plan: dict,
    taxonomy_path: str,
    enable_hitl_review: bool = False,
    quality_threshold: float | None = None,
    manager: StreamingWorkflowManager | None = None,
) -> dict[str, Any]
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skill_content` | `str` | Yes | Generated SKILL.md content |
| `plan` | `dict` | Yes | Original plan with success criteria |
| `taxonomy_path` | `str` | Yes | Expected taxonomy path |
| `enable_hitl_review` | `bool` | No | Show for human review |
| `quality_threshold` | `float \| None` | No | Minimum quality score (uses `DEFAULT_QUALITY_THRESHOLDS` if None) |
| `manager` | `StreamingWorkflowManager` | No | Optional streaming manager |

**Returns:**

Success case:
```python
{
    "status": "completed",
    "passed": True,
    "skill_content": str,  # May be refined
    "validation_report": {
        "passed": True,
        "score": float,
        "errors": list[str],
        "warnings": list[str],
        "checks_performed": list[str],
        "structure_valid": bool,
        "name_errors": list[str],
        "test_cases": dict,
        "trigger_coverage": float,
        "word_count": int,
        "size_assessment": str,
        "verbosity_score": float,
    },
}
```

Needs improvement:
```python
{
    "status": "needs_improvement",
    "passed": False,
    "skill_content": str,  # Refined content
    "validation_report": {
        "passed": False,
        "score": float,  # Below threshold
        "errors": list[str],
        "warnings": list[str],
    },
}
```

HITL case (review):
```python
{
    "status": "pending_hitl",
    "hitl_type": "review",
    "hitl_data": {
        "skill_content_preview": str,
        "compliance_score": float,
        "quality_score": float,
        "strengths": list[str],
        "weaknesses": list[str],
    },
    "context": dict,
}
```

**Quality Thresholds:**

| Threshold | Behavior |
|-----------|----------|
| `score >= threshold` | Pass through unchanged |
| `score < threshold` | Trigger refinement loop |
| `max iterations` | Return best effort |

**Validation Checks:**

1. **Structure Validation**
   - Kebab-case name
   - Description requirements
   - Security checks

2. **Test Case Generation**
   - Positive trigger tests
   - Negative trigger tests
   - Edge cases
   - Functional tests

3. **Compliance Check**
   - agentskills.io format
   - YAML frontmatter
   - Required sections

4. **Quality Assessment**
   - Completeness
   - Clarity
   - Usefulness
   - Size metrics
   - Verbosity

---

## Workflow Orchestration

### Sequential Execution

```python
# Phase 1: Understanding
understanding = UnderstandingWorkflow()
result1 = await understanding.execute(task_description="...")

if result1["status"] == "pending_hitl":
    # Handle HITL, then resume
    pass

# Phase 2: Generation
generation = GenerationWorkflow()
result2 = await generation.execute(
    plan=result1["plan"],
    understanding=result1,
)

if result2["status"] == "pending_hitl":
    # Handle preview feedback
    pass

# Phase 3: Validation
validation = ValidationWorkflow()
result3 = await validation.execute(
    skill_content=result2["skill_content"],
    plan=result1["plan"],
    taxonomy_path=result1["plan"]["taxonomy_path"],
)
```

### HITL Resume Pattern

```python
# Store context when suspending
context = result["context"]
hitl_data = result["hitl_data"]

# Later, resume with user response
if result["hitl_type"] == "questions":
    # Add answers to context
    context["user_answers"] = answers
    # Re-run workflow
    result = await workflow.execute(**context)
```

---

## Error Handling

### Common Errors

```python
try:
    result = await workflow.execute(...)
except WorkflowError as e:
    # Workflow-level error
    logger.error(f"Workflow failed: {e}")
except ModuleError as e:
    # Module execution error
    logger.error(f"Module failed: {e}")
except Exception as e:
    # Unexpected error
    logger.exception("Unexpected workflow error")
```

### HITL Timeouts

```python
if result["status"] == "pending_hitl":
    # Set timeout for user response
    timeout = 3600  # 1 hour
    # Schedule timeout handler
```

---

## Type Definitions

### Plan Structure

```python
Plan = {
    "skill_name": str,              # Kebab-case
    "skill_description": str,       # With trigger phrases
    "taxonomy_path": str,           # e.g., "technical/python"
    "content_outline": list[str],   # Section headers
    "generation_guidance": str,     # Instructions for LLM
    "success_criteria": list[str],  # Validation criteria
    "estimated_length": str,        # "short", "medium", "long"
    "tags": list[str],              # Search tags
    "trigger_phrases": list[str],   # Positive triggers
    "negative_triggers": list[str], # Negative triggers
    "skill_category": str,          # Template category
}
```

### Validation Report Structure

```python
ValidationReport = {
    "passed": bool,
    "score": float,                 # 0-1
    "errors": list[str],
    "warnings": list[str],
    "checks_performed": list[str],
    "structure_valid": bool,
    "name_errors": list[str],
    "description_errors": list[str],
    "security_issues": list[str],
    "test_cases": {
        "positive_tests": list[str],
        "negative_tests": list[str],
        "edge_cases": list[str],
        "total_tests": int,
    },
    "trigger_coverage": float,      # 0-1
    "word_count": int,
    "size_assessment": str,         # "optimal", "acceptable", "too_large"
    "verbosity_score": float,       # 0-1
    "size_recommendations": list[str],
    "conciseness_recommendations": list[str],
}
```

---

## Typed Output Models

**File**: `src/skill_fleet/core/workflows/models.py`

The workflows now have typed Pydantic models for all inputs and outputs, providing:
- Type safety and validation
- IDE autocompletion
- Clear documentation of data contracts

### QualityThresholds

Centralized configuration for all quality-related thresholds. Use `DEFAULT_QUALITY_THRESHOLDS` to access the global instance:

```python
from skill_fleet.core.workflows.models import DEFAULT_QUALITY_THRESHOLDS

# Available thresholds
DEFAULT_QUALITY_THRESHOLDS.validation_pass_threshold    # 0.75 - Validation must meet this score
DEFAULT_QUALITY_THRESHOLDS.refinement_target_quality    # 0.80 - Target quality for content refinement
DEFAULT_QUALITY_THRESHOLDS.taxonomy_confidence_threshold # 0.60 - Minimum confidence for taxonomy path
DEFAULT_QUALITY_THRESHOLDS.trigger_coverage_target      # 0.90 - Target coverage of trigger phrases in tests
DEFAULT_QUALITY_THRESHOLDS.optimal_word_count_min       # 500  - Minimum words for optimal size
DEFAULT_QUALITY_THRESHOLDS.optimal_word_count_max       # 3000 - Maximum words for optimal size
DEFAULT_QUALITY_THRESHOLDS.acceptable_word_count_max    # 5000 - Maximum before size warning
DEFAULT_QUALITY_THRESHOLDS.verbosity_warning_threshold  # 0.70 - Threshold for verbosity warnings
```

**Usage in Workflows:**

Workflows automatically use centralized thresholds when not explicitly provided:

```python
# Uses DEFAULT_QUALITY_THRESHOLDS.refinement_target_quality (0.80)
result = await generation.execute(
    plan=plan_data,
    understanding=understanding_data,
    quality_threshold=None  # Falls back to default
)

# Uses DEFAULT_QUALITY_THRESHOLDS.validation_pass_threshold (0.75)
result = await validation.execute(
    skill_content=content,
    plan=plan_data,
    taxonomy_path="technical/python",
    quality_threshold=None  # Falls back to default
)
```

### Phase Output Models

All phase workflows return typed Pydantic models (in addition to dict-based returns for backward compatibility).

#### Phase1UnderstandingOutput

```python
from skill_fleet.core.workflows.models import Phase1UnderstandingOutput

class Phase1UnderstandingOutput(BaseModel):
    status: Literal["completed", "pending_user_input", "failed"]
    requirements: RequirementsOutput
    intent: IntentOutput
    taxonomy: TaxonomyOutput
    dependencies: DependencyOutput
    plan: PlanOutput | None
    structure_validation: StructureValidationOutput | None
    hitl_type: str | None
    hitl_data: dict[str, Any] | None
    execution_time_ms: float | None

    # Methods for workflow continuation
    def is_ready_for_generation(self) -> bool:
        """Check if phase 1 completed successfully."""
        return self.status == "completed" and self.plan is not None

    def to_generation_input(self) -> dict[str, Any]:
        """Convert to input format for GenerationWorkflow."""
```

**Usage:**

```python
from skill_fleet.core.workflows.models import (
    Phase1UnderstandingOutput,
    dict_to_requirements,
    dict_to_plan,
)

# Convert dict to typed model for better IDE support
phase1_dict = await understanding.execute(task_description="...")
phase1_output = Phase1UnderstandingOutput(
    status="completed",
    requirements=dict_to_requirements(phase1_dict.get("requirements", {})),
    intent=dict_to_intent(phase1_dict.get("intent", {})),
    plan=dict_to_plan(phase1_dict.get("plan", {})),
    # ... other fields
)

if phase1_output.is_ready_for_generation():
    gen_input = phase1_output.to_generation_input()
```

#### Phase2GenerationOutput

```python
class Phase2GenerationOutput(BaseModel):
    status: Literal["completed", "pending_user_input", "failed"]
    skill_content: str
    sections_generated: list[str]
    code_examples_count: int
    estimated_reading_time: int
    initial_quality_score: float | None
    final_quality_score: float | None
    refinement_iterations: int
    hitl_type: str | None
    hitl_data: dict[str, Any] | None
    execution_time_ms: float | None

    def is_ready_for_validation(self) -> bool:
        """Check if ready for validation phase."""
        return self.status == "completed" and bool(self.skill_content)
```

#### Phase3ValidationOutput

```python
class Phase3ValidationOutput(BaseModel):
    status: Literal["completed", "needs_improvement", "pending_user_input", "failed"]
    passed: bool
    validation_report: ValidationReportOutput
    skill_content: str
    was_refined: bool
    refinement_improvements: list[str]
    hitl_type: str | None
    hitl_data: dict[str, Any] | None
    execution_time_ms: float | None
```

### Helper Functions

For gradual migration from dict-based to typed outputs:

```python
from skill_fleet.core.workflows.models import (
    dict_to_requirements,
    dict_to_intent,
    dict_to_taxonomy,
    dict_to_dependencies,
    dict_to_plan,
)

# Convert dict results to typed models
requirements = dict_to_requirements(phase1_result["requirements"])
intent = dict_to_intent(phase1_result["intent"])
taxonomy = dict_to_taxonomy(phase1_result["taxonomy"])
dependencies = dict_to_dependencies(phase1_result["dependencies"])
plan = dict_to_plan(phase1_result["plan"])
```

These helper functions provide safe defaults and validation, making it easy to work with both old dict-based code and new typed code simultaneously.

---

## Related Documentation

- [Workflow Engine Architecture](../../explanation/architecture/workflow-engine.md) - Detailed architecture
- [Module Reference](modules.md) - Individual module documentation
- [API Jobs](../../reference/api/jobs.md) - Job-based execution
- [HITL System](../../explanation/architecture/hitl-system.md) - Human-in-the-loop
