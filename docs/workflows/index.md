# Workflow Layer

The Workflow Layer provides clean, high-level orchestrators that coordinate DSPy modules for skill creation. These orchestrators serve as the primary interface for both the FastAPI application and CLI, abstracting away the complexity of individual DSPy modules.

**Architecture Overview:**

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│                   (FastAPI / CLI)                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Workflow Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Phase 1    │  │   Phase 2    │  │   Phase 3    │     │
│  │   Analysis   │→ │   Generate   │→ │   Validate   │     │
│  │              │  │              │  │              │     │
│  │ TaskAnalysis │  │   Content    │  │  Quality     │     │
│  │ Orchestrator │  │ Orchestrator │  │   Assurance  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     HITL     │  │Conversational│  │   Signature  │     │
│  │   Checkpoint │  │ Orchestrator │  │     Tuning   │     │
│  │   Manager    │  │              │  │ Orchestrator │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      DSPy Module Layer                       │
│              (Signatures & Implementation)                   │
└─────────────────────────────────────────────────────────────┘
```

## Orchestrators

### Phase-Based Orchestrators

These orchestrators correspond to the three main phases of skill creation:

#### 1. TaskAnalysisOrchestrator (Phase 1)

**Purpose:** Analyze user requirements and create a comprehensive skill creation plan.

**Location:** `src/skill_fleet/workflows/task_analysis_planning/orchestrator.py`

**Key Methods:**
- `analyze()` - Full async analysis workflow
- `analyze_sync()` - Synchronous wrapper
- `get_requirements()` - Quick requirements gathering
- `get_taxonomy_path()` - Taxonomy path recommendation

**Responsibilities:**
- Gather requirements from task description
- Analyze user intent and success criteria
- Find optimal taxonomy path
- Analyze dependencies (prerequisites, complementary skills)
- Synthesize coherent execution plan

**MLflow Tracking:**
- Experiment: `task-analysis-workflow`
- Metrics: Requirements gathered, intent analyzed, taxonomy found, etc.

**Example:**
```python
orchestrator = TaskAnalysisOrchestrator()
result = await orchestrator.analyze(
    task_description="Create a Python decorators skill",
    user_context="I want to teach about @property and class decorators",
    taxonomy_structure="...",
    existing_skills=["python/async", "python/type-hints"],
)
```

**Output Structure:**
```python
{
    "requirements": {...},  # Domain, topics, constraints
    "intent": {...},        # Task intent, success criteria
    "taxonomy": {...},      # Recommended path
    "dependencies": {...},  # Prerequisites, complementary skills
    "plan": {...}          # Synthesized execution plan
}
```

---

#### 2. ContentGenerationOrchestrator (Phase 2)

**Purpose:** Generate skill content based on understanding and plan.

**Location:** `src/skill_fleet/workflows/content_generation/orchestrator.py`

**Key Methods:**
- `generate()` - Full async generation workflow
- `generate_sync()` - Synchronous wrapper

**Responsibilities:**
- Generate main SKILL.md content
- Create supporting files (examples, best practices)
- Support different skill styles:
  - `navigation_hub` - Concise overview with links
  - `comprehensive` - Full detailed content
  - `minimal` - Essential information only
- Incorporate user feedback for refinement

**MLflow Tracking:**
- Experiment: `content-generation-workflow`
- Metrics: Content generated, extra files, validation performed

**Example:**
```python
orchestrator = ContentGenerationOrchestrator()
result = await orchestrator.generate(
    understanding=phase1_result,
    plan=phase1_result["plan"],
    skill_style="comprehensive",
    user_feedback="",
)
```

**Output Structure:**
```python
{
    "content": "...",           # Main SKILL.md content
    "extra_files": {...},       # Supporting files
    "validation_report": {...}  # Initial validation
}
```

---

#### 3. QualityAssuranceOrchestrator (Phase 3)

**Purpose:** Validate and refine skill content to ensure quality.

**Location:** `src/skill_fleet/workflows/quality_assurance/orchestrator.py`

**Key Methods:**
- `validate_and_refine()` - Full async validation workflow
- `validate_and_refine_sync()` - Synchronous wrapper

**Responsibilities:**
- Validate content against quality rules
- Identify critical issues and warnings
- Refine content based on validation feedback
- Assess overall quality and audience alignment
- Handle iterative refinement when needed

**MLflow Tracking:**
- Experiment: `quality-assurance-workflow`
- Metrics: Validation passed, quality score, issues count

**Example:**
```python
orchestrator = QualityAssuranceOrchestrator()
result = await orchestrator.validate_and_refine(
    skill_content=generated_skill,
    skill_metadata={...},
    content_plan=plan,
    validation_rules=rules,
    target_level="intermediate",
)
```

**Output Structure:**
```python
{
    "validation_report": {...},    # Detailed validation results
    "refined_content": "...",      # Improved content
    "critical_issues": [...],      # List of critical issues
    "warnings": [...],             # List of warnings
    "quality_assessment": {...}    # Quality metrics
}
```

---

### Cross-Phase Orchestrators

These orchestrators provide specialized functionality across phases:

#### 4. HITLCheckpointManager

**Purpose:** Manage human-in-the-loop interactions throughout skill creation.

**Location:** `src/skill_fleet/workflows/human_in_the_loop/checkpoint_manager.py`

**Key Methods:**
- `determine_strategy()` - Determine optimal HITL approach
- `generate_clarifying_questions()` - Create clarification questions
- `confirm_understanding()` - Generate confirmation summary
- `generate_preview()` - Create content preview for review
- `analyze_feedback()` - Process user feedback
- `format_validation_results()` - Format validation for display
- `plan_refinement()` - Create refinement plan
- `assess_readiness()` - Check readiness to proceed

**Checkpoint Phases:**
- `PHASE1_UNDERSTANDING` - During requirements gathering
- `PHASE2_CONTENT_GENERATION` - During content creation
- `PHASE3_VALIDATION` - During quality assurance

**Checkpoint State Management:**
```python
@dataclass
class Checkpoint:
    checkpoint_id: str
    phase: CheckpointPhase
    checkpoint_type: str
    status: str  # pending, waiting, approved, rejected
    data: dict[str, Any]
    user_response: dict[str, Any] | None
    metadata: dict[str, Any]
```

**Example:**
```python
manager = HITLCheckpointManager()

# Determine strategy
strategy = await manager.determine_strategy(
    task_description="Create async Python skill",
    task_complexity="intermediate",
)

# Generate questions
questions = await manager.generate_clarifying_questions(
    task_description=...,
    initial_analysis=...,
    ambiguities=[...],
)

# Create and manage checkpoints
checkpoint = manager.create_checkpoint(
    phase=CheckpointPhase.PHASE1_UNDERSTANDING,
    checkpoint_type="confirm_requirements",
    data={...},
)
```

**MLflow Tracking:**
- Experiments: `hitl-strategy`, `hitl-clarifying-questions`, etc.
- Metrics: Strategy type, question count, confidence scores

---

#### 5. ConversationalOrchestrator

**Purpose:** Manage multi-turn conversational workflow for skill creation.

**Location:** `src/skill_fleet/workflows/conversational_interface/orchestrator.py`

**Key Methods:**
- `initialize_conversation()` - Create new conversation context
- `interpret_intent()` - Interpret user intent from message
- `generate_clarifying_question()` - Generate clarification questions
- `deep_understanding()` - Perform deep requirement analysis
- `confirm_understanding()` - Generate confirmation summary
- `process_feedback()` - Process user feedback
- `suggest_tests()` - Suggest tests for the skill

**Conversation States:**
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

**Intent Types:**
```python
class IntentType(Enum):
    CREATE_SKILL = "create_skill"
    CLARIFY = "clarify"
    REFINE = "refine"
    MULTI_SKILL = "multi_skill"
    UNKNOWN = "unknown"
```

**Example:**
```python
orchestrator = ConversationalOrchestrator()

# Initialize conversation
context = await orchestrator.initialize_conversation(
    initial_message="Create a skill for Python decorators",
)

# Interpret intent
intent = await orchestrator.interpret_intent(
    user_message="Make it more advanced",
    context=context,
)

# Generate clarifying question
question = await orchestrator.generate_clarifying_question(
    context=context,
)
```

**MLflow Tracking:**
- Experiment: `conversational-interface`
- Metrics: Intent type, confidence, understanding quality

---

#### 6. SignatureTuningOrchestrator

**Purpose:** Optimize DSPy signatures to improve skill quality scores.

**Location:** `src/skill_fleet/workflows/signature_optimization/tuner.py`

**Key Methods:**
- `tune_signature()` - Single tuning iteration
- `tune_iteratively()` - Iterative tuning until target reached
- `get_version_history()` - Retrieve signature version history

**Configuration Parameters:**
- `improvement_threshold` - Minimum improvement to accept (default: 0.05)
- `max_iterations` - Maximum iterations per session (default: 3)
- `quality_threshold` - Score triggering tuning (default: 0.75)

**Example:**
```python
orchestrator = SignatureTuningOrchestrator(
    improvement_threshold=0.05,
    max_iterations=3,
    quality_threshold=0.75,
)

# Single tuning pass
result = await orchestrator.tune_signature(
    skill_content=generated_skill,
    current_signature=current_sig,
    metric_score=0.65,
    target_score=0.80,
    skill_type="comprehensive",
)

# Iterative tuning
result = await orchestrator.tune_iteratively(
    skill_content=generated_skill,
    current_signature=current_sig,
    metric_score=0.65,
    target_score=0.80,
)
```

**Output Structure:**
```python
{
    "tuning_needed": bool,
    "proposed_signature": str,      # Improved signature
    "failure_analysis": {...},       # Why tuning was needed
    "version_history": {...},        # Version tracking
    "iterations_used": int,          # For iterative tuning
    "target_reached": bool,          # For iterative tuning
}
```

**MLflow Tracking:**
- Experiments: `signature-tuning`, `signature-tuning-iterative`
- Metrics: Tuning needed, improvement accepted, iterations used

---

## Common Patterns

### Async/Sync Interface

All orchestrators provide both async and sync methods:

```python
# Async usage (recommended for FastAPI)
result = await orchestrator.analyze(...)

# Sync usage (for CLI or blocking contexts)
result = orchestrator.analyze_sync(...)
```

The sync methods use `run_async()` to execute the async workflow in an event loop.

### MLflow Integration

All orchestrators integrate with MLflow for experiment tracking:

```python
result = await orchestrator.analyze(
    ...,
    enable_mlflow=True,  # Default: True
)
```

**Common MLflow Functions:**
- `setup_mlflow_experiment(experiment_name)` - Initialize tracking
- `log_parameter(name, value)` - Log parameters
- `log_phase_metrics(metrics_dict)` - Log metrics
- `end_mlflow_run()` - End tracking

### Task-Specific LMs

Orchestrators support task-specific language models:

```python
orchestrator = TaskAnalysisOrchestrator(
    task_lms={
        "gather_requirements": dspy.LM("gemini-2.5-flash"),
        "analyze_intent": dspy.LM("gemini-2.5-pro"),
        # ...
    }
)
```

### Error Handling

All orchestrators use consistent error handling:

```python
try:
    result = await orchestrator.analyze(...)
except Exception as e:
    logger.exception(f"Error in workflow: {e}")
    raise
finally:
    if enable_mlflow:
        end_mlflow_run()
```

---

## Integration Guide

### FastAPI Integration

```python
from skill_fleet.workflows.task_analysis_planning import TaskAnalysisOrchestrator

router = APIRouter()
orchestrator = TaskAnalysisOrchestrator()

@router.post("/analyze")
async def analyze_task(request: AnalysisRequest):
    result = await orchestrator.analyze(
        task_description=request.task_description,
        user_context=request.user_context,
        taxonomy_structure=request.taxonomy_structure,
        existing_skills=request.existing_skills,
        enable_mlflow=True,
    )
    return result
```

### CLI Integration

```python
from skill_fleet.workflows.task_analysis_planning import TaskAnalysisOrchestrator

orchestrator = TaskAnalysisOrchestrator()

def analyze_command(task_description: str):
    result = orchestrator.analyze_sync(
        task_description=task_description,
        enable_mlflow=True,
    )
    print(json.dumps(result, indent=2))
```

---

## Design Principles

1. **Clean Interface:** Orchestrators provide simple, high-level APIs
2. **Dual Mode:** Both async and sync methods for different contexts
3. **Observability:** Built-in MLflow tracking for all operations
4. **Modularity:** Each orchestrator handles a specific concern
5. **Composition:** Orchestrators can be combined for complex workflows
6. **Error Resilience:** Consistent error handling and logging
7. **Testability:** Orchestrators are easily testable in isolation

---

## Future Enhancements

- **Streaming Support:** Add streaming responses for long-running workflows
- **Caching:** Cache common workflow results
- **Parallel Execution:** Parallelize independent workflow steps
- **Workflow Templates:** Pre-defined workflow templates for common patterns
- **Monitoring:** Real-time workflow monitoring and metrics dashboard

---

*Last Updated: 2026-01-23*
*Version: 2.0 (Post-Restructure)*
