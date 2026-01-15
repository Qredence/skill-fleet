# DSPy Modules Reference

**Last Updated**: 2026-01-15
**Location**: `src/skill_fleet/core/dspy/modules/`

## Overview

DSPy modules implement the **logic** that processes inputs according to signature contracts. Each module wraps a signature with a DSPy module type (`Predict`, `ChainOfThought`, etc.) and provides both sync and async execution.

`★ Insight ─────────────────────────────────────`
Modules encapsulate the "how" of processing. While signatures define the contract, modules determine the implementation strategy—whether to use chain-of-thought reasoning, direct prediction, or other DSPy patterns.
`─────────────────────────────────────────────────`

## Module Types

DSPy provides several module types, each with different characteristics:

| Module Type | Use Case | Reasoning | Cost |
|-------------|----------|-----------|------|
| **`dspy.Predict`** | Direct transformations | None | Lowest |
| **`dspy.ChainOfThought`** | Complex reasoning | Explicit CoT | Medium |
| **`dspy.Refine`** | Iterative improvement | Comparison-based | Medium |
| **`dspy.BestOfN`** | Quality maximization | N generations + selection | High |

## Phase 1 Modules

**File**: `src/skill_fleet/core/modules/phase1_understanding.py`

Phase 1 performs parallel analysis of user intent, taxonomy placement, and dependencies.

### RequirementsGathererModule

Initial requirements gathering from task description.

```python
class RequirementsGathererModule(dspy.Module):
    """Module for gathering requirements from a task description."""
```

**Implementation**: `dspy.ChainOfThought(GatherRequirements)`

**Input:**
```python
task_description: str
```

**Output:**
```python
{
    "domain": str,           # Primary domain
    "category": str,         # Category within domain
    "target_level": str,     # beginner/intermediate/advanced/expert
    "topics": list[str],     # 3-7 topics to cover
    "constraints": list[str], # Any constraints
    "ambiguities": list[str], # Ambiguities needing clarification
    "rationale": str,        # Chain-of-thought reasoning
}
```

**Usage:**
```python
from skill_fleet.core.modules.phase1_understanding import RequirementsGathererModule

module = RequirementsGathererModule()
result = await module.aforward(task_description="Create a Python async programming skill")
```

---

### IntentAnalyzerModule

Deep analysis of user intent to understand what skill is needed.

```python
class IntentAnalyzerModule(dspy.Module):
    """Module for analyzing user intent."""
```

**Implementation**: `dspy.ChainOfThought(AnalyzeIntent)`

**Input:**
```python
task_description: str
user_context: str  # JSON with user_id, existing skills, preferences
```

**Output:**
```python
{
    "task_intent": TaskIntent,  # Structured intent object
    "skill_type": str,          # how_to/reference/concept/workflow/checklist
    "scope": str,               # What's included/excluded
    "success_criteria": list[str], # 3-5 success criteria
    "rationale": str,           # Chain-of-thought reasoning
}
```

**Usage:**
```python
result = await module.aforward(
    task_description="Create a skill for Python async/await",
    user_context='{"user_id": "user_123", "existing_skills": ["python-basics"]}'
)
```

---

### TaxonomyPathFinderModule

Find the best taxonomy path for a skill.

```python
class TaxonomyPathFinderModule(dspy.Module):
    """Module for finding the best taxonomy path for a skill."""
```

**Implementation**: `dspy.ChainOfThought(FindTaxonomyPath)`

**Input:**
```python
task_description: str
taxonomy_structure: str  # JSON of full taxonomy
existing_skills: list[str]  # List of existing skill paths
```

**Output:**
```python
{
    "recommended_path": str,     # e.g., technical_skills/programming/python/async
    "alternative_paths": list[str], # 2-3 alternatives
    "path_rationale": str,        # Why this path is optimal
    "new_directories": list[str], # New directories to create
    "confidence": float,          # 0-1 confidence score
    "rationale": str,             # Chain-of-thought reasoning
}
```

**Usage:**
```python
result = await module.aforward(
    task_description="Python async context managers",
    taxonomy_structure=json.dumps(taxonomy_tree),
    existing_skills=["technical_skills/programming/python", "technical_skills/programming/python/decorators"]
)
```

---

### DependencyAnalyzerModule

Analyze skill dependencies and prerequisites.

```python
class DependencyAnalyzerModule(dspy.Module):
    """Module for analyzing skill dependencies."""
```

**Implementation**: `dspy.Predict(AnalyzeDependencies)`

**Input:**
```python
task_description: str
task_intent: str
taxonomy_path: str
existing_skills: str  # JSON of skills with metadata
```

**Output:**
```python
{
    "dependency_analysis": DependencyAnalysis,
    "prerequisite_skills": list[DependencyRef],
    "complementary_skills": list[DependencyRef],
    "missing_prerequisites": list[str],
}
```

`★ Insight ─────────────────────────────────────`
This module uses `dspy.Predict` instead of `ChainOfThought` because dependency analysis is more about pattern matching and lookup than complex reasoning. This reduces cost while maintaining accuracy.
`─────────────────────────────────────────────────`

---

### PlanSynthesizerModule

Synthesize all Phase 1 analyses into a coherent plan.

```python
class PlanSynthesizerModule(dspy.Module):
    """Module for synthesizing all analyses into a plan."""
```

**Implementation**: `dspy.ChainOfThought(SynthesizePlan)`

**Input:**
```python
intent_analysis: str      # JSON from IntentAnalyzer
taxonomy_analysis: str    # JSON from TaxonomyPathFinder
dependency_analysis: str  # JSON from DependencyAnalyzer
user_confirmation: str = ""  # Optional HITL feedback
```

**Output:**
```python
{
    "skill_metadata": SkillMetadata,
    "content_plan": str,
    "generation_instructions": str,
    "success_criteria": list[str],
    "estimated_length": str,  # short/medium/long
    "rationale": str,
}
```

---

### Phase1UnderstandingModule

The main Phase 1 orchestrator that runs all analysis in parallel.

```python
class Phase1UnderstandingModule(dspy.Module):
    """Composite module for Phase 1: Understanding."""
```

**Implementation**: Orchestrates all Phase 1 modules with parallel execution.

**Input:**
```python
task_description: str
user_context: str
taxonomy_structure: str
existing_skills: str
user_confirmation: str = ""
```

**Output:**
```python
{
    "requirements": dict,   # From RequirementsGatherer
    "intent": dict,         # From IntentAnalyzer
    "taxonomy": dict,       # From TaxonomyPathFinder
    "dependencies": dict,   # From DependencyAnalyzer
    "plan": dict,           # From PlanSynthesizer
}
```

**Parallel Execution:**
```python
# Intent and Taxonomy run in parallel
intent_future = self.analyze_intent.aforward(...)
taxonomy_future = self.find_taxonomy.aforward(...)
intent_result, taxonomy_result = await asyncio.gather(intent_future, taxonomy_future)

# Dependencies runs after intent (depends on intent result)
deps_result = await self.analyze_dependencies.aforward(...)

# Plan synthesizes all results
plan = await self.synthesize.aforward(...)
```

---

## Phase 2 Modules

**File**: `src/skill_fleet/core/modules/phase2_generation.py`

Phase 2 generates the actual skill content based on the Phase 1 plan.

### ContentGeneratorModule

Generate initial skill content from the Phase 1 plan.

```python
class ContentGeneratorModule(dspy.Module):
    """Generate initial skill content from the Phase 1 plan."""
```

**Implementation**: `dspy.ChainOfThought(GenerateSkillContent)`

**Input:**
```python
skill_metadata: Any
content_plan: str
generation_instructions: str
parent_skills_content: str
dependency_summaries: str
```

**Output:**
```python
{
    "skill_content": str,
    "usage_examples": list[UsageExample],
    "best_practices": list[BestPractice],
    "test_cases": list[TestCase],
    "estimated_reading_time": int,
    "rationale": str,
}
```

---

### FeedbackIncorporatorModule

Apply user feedback and change requests to draft content.

```python
class FeedbackIncorporatorModule(dspy.Module):
    """Apply user feedback and change requests to draft content."""
```

**Implementation**: `dspy.ChainOfThought(IncorporateFeedback)`

**Input:**
```python
current_content: str
user_feedback: str
change_requests: str
skill_metadata: Any
```

**Output:**
```python
{
    "refined_content": str,
    "changes_made": list[str],
    "unaddressed_feedback": list[str],
    "improvement_score": float,
    "rationale": str,
}
```

---

### Phase2GenerationModule

The main Phase 2 orchestrator.

```python
class Phase2GenerationModule(dspy.Module):
    """Phase 2 orchestrator: generate content and optionally incorporate feedback."""
```

**Implementation**: Orchestrates ContentGenerator and FeedbackIncorporator.

**Input:**
```python
skill_metadata: Any
content_plan: str
generation_instructions: str
parent_skills_content: str
dependency_summaries: str
user_feedback: str = ""
change_requests: str = ""
```

**Output:**
```python
{
    "skill_content": str,
    "usage_examples": list[UsageExample],
    "best_practices": list[BestPractice],
    "test_cases": list[TestCase],
    "estimated_reading_time": int,
    "changes_made": list[str] = None,  # If feedback was incorporated
    "improvement_score": float = None,
}
```

---

## Phase 3 Modules

**File**: `src/skill_fleet/core/modules/phase3_validation.py`

Phase 3 validates and refines the generated skill.

### SkillValidatorModule

Validate a draft skill against quality and compliance rules.

```python
class SkillValidatorModule(dspy.Module):
    """Validate a draft skill against quality and compliance rules."""
```

**Implementation**: `dspy.Predict(ValidateSkill)`

**Input:**
```python
skill_content: str
skill_metadata: Any
content_plan: str
validation_rules: str
```

**Output:**
```python
{
    "validation_report": ValidationReport,
    "critical_issues": list[ValidationCheckItem],
    "warnings": list[ValidationCheckItem],
    "suggestions": list[str],
    "overall_score": float,
}
```

---

### SkillRefinerModule

Refine a draft skill based on validation feedback.

```python
class SkillRefinerModule(dspy.Module):
    """Refine a draft skill based on validation feedback."""
```

**Implementation**: `dspy.ChainOfThought(RefineSkillFromFeedback)`

**Input:**
```python
current_content: str
validation_issues: str
user_feedback: str
fix_strategies: str
iteration_number: int = 1
```

**Output:**
```python
{
    "refined_content": str,
    "issues_resolved": list[str],
    "issues_remaining": list[str],
    "changes_summary": str,
    "ready_for_acceptance": bool,
    "rationale": str,
}
```

---

### QualityAssessorModule

Assess skill quality and audience alignment.

```python
class QualityAssessorModule(dspy.Module):
    """Assess skill quality and audience alignment."""
```

**Implementation**: `dspy.ChainOfThought(AssessSkillQuality)`

**Input:**
```python
skill_content: str
skill_metadata: Any
target_level: str  # beginner/intermediate/advanced
```

**Output:**
```python
{
    "quality_score": float,
    "strengths": list[str],
    "weaknesses": list[str],
    "recommendations": list[str],
    "audience_alignment": float,
    "rationale": str,
}
```

---

### Phase3ValidationModule

The main Phase 3 orchestrator.

```python
class Phase3ValidationModule(dspy.Module):
    """Phase 3 orchestrator: validate, refine, and assess quality."""
```

**Implementation**: Orchestrates Validator, Refiner, and QualityAssessor.

**Input:**
```python
skill_content: str
skill_metadata: Any
content_plan: str
validation_rules: str
user_feedback: str = ""
target_level: str = "intermediate"
```

**Output:**
```python
{
    # From validation
    "validation_report": ValidationReport,
    "critical_issues": list[ValidationCheckItem],
    "warnings": list[ValidationCheckItem],
    "suggestions": list[str],
    "overall_score": float,

    # From refinement (if needed)
    "refined_content": str,

    # From quality assessment
    "quality_assessment": dict,
}
```

**Logic:**
1. Always validate the skill
2. If validation fails OR user feedback provided, run refinement
3. Always assess quality of final content

---

## HITL Modules

**File**: `src/skill_fleet/core/modules/hitl.py`

Human-in-the-Loop utility modules for interactive workflows.

### ClarifyingQuestionsModule

Generate clarifying questions to understand user intent better.

```python
class ClarifyingQuestionsModule(dspy.Module):
    """Generate clarifying questions to understand user intent better."""
```

**Implementation**: `dspy.ChainOfThought(GenerateClarifyingQuestions)`

**Input:**
```python
task_description: str
initial_analysis: str
ambiguities: list[str]
```

**Output:**
```python
{
    "questions": list[ClarifyingQuestion],  # 2-3 questions
    "priority": str,  # critical/important/optional
    "rationale": str,
}
```

---

### ConfirmUnderstandingModule

Summarize understanding for user confirmation.

```python
class ConfirmUnderstandingModule(dspy.Module):
    """Summarize understanding for user confirmation."""
```

**Implementation**: `dspy.Predict(SummarizeUnderstanding)`

**Input:**
```python
task_description: str
user_clarifications: str
intent_analysis: str
taxonomy_path: str
dependencies: list[str]
```

**Output:**
```python
{
    "summary": str,
    "key_assumptions": list[str],
    "confidence": float,
}
```

`★ Insight ─────────────────────────────────────`
Uses `dspy.Predict` for fast summarization without chain-of-thought, keeping the checkpoint snappy. The goal is to show users a quick summary for confirmation, not to reason deeply about the task.
`─────────────────────────────────────────────────`

---

### PreviewGeneratorModule

Generate preview of skill content for user review.

```python
class PreviewGeneratorModule(dspy.Module):
    """Generate preview of skill content for user review."""
```

**Implementation**: `dspy.Predict(GeneratePreview)`

**Input:**
```python
skill_content: str
metadata: str
```

**Output:**
```python
{
    "preview": str,
    "highlights": list[str],
    "potential_issues": list[str],
}
```

---

### FeedbackAnalyzerModule

Analyze user feedback and determine changes needed.

```python
class FeedbackAnalyzerModule(dspy.Module):
    """Analyze user feedback and determine changes needed."""
```

**Implementation**: `dspy.ChainOfThought(AnalyzeFeedback)`

**Input:**
```python
user_feedback: str
current_content: str
```

**Output:**
```python
{
    "change_requests": list[dict],
    "scope_change": bool,
    "estimated_effort": str,
    "reasoning": str,
}
```

---

### ValidationFormatterModule

Format validation results for human-readable display.

```python
class ValidationFormatterModule(dspy.Module):
    """Format validation results for human-readable display."""
```

**Implementation**: `dspy.Predict(FormatValidationResults)`

**Input:**
```python
validation_report: str
skill_content: str
```

**Output:**
```python
{
    "formatted_report": str,
    "critical_issues": list[ValidationCheckItem],
    "warnings": list[ValidationCheckItem],
    "auto_fixable": bool,
}
```

---

### RefinementPlannerModule

Generate refinement plan based on validation and feedback.

```python
class RefinementPlannerModule(dspy.Module):
    """Generate refinement plan based on validation and feedback."""
```

**Implementation**: `dspy.ChainOfThought(GenerateRefinementPlan)`

**Input:**
```python
validation_issues: str
user_feedback: str
current_skill: str
```

**Output:**
```python
{
    "refinement_plan": str,
    "changes": list[dict],
    "estimated_iterations": int,
    "reasoning": str,
}
```

---

### ReadinessAssessorModule

Assess if ready to proceed to next phase.

```python
class ReadinessAssessorModule(dspy.Module):
    """Assess if ready to proceed to next phase."""
```

**Implementation**: `dspy.Predict(AssessReadiness)`

**Input:**
```python
phase: str
collected_info: str
min_requirements: str
```

**Output:**
```python
{
    "ready": bool,
    "readiness_score": float,
    "missing_info": list[str],
    "next_questions": list[str],
}
```

---

### HITLStrategyModule

Determine optimal HITL strategy for a task.

```python
class HITLStrategyModule(dspy.Module):
    """Determine optimal HITL strategy for a task."""
```

**Implementation**: `dspy.ChainOfThought(DetermineHITLStrategy)`

**Input:**
```python
task_description: str
task_complexity: str  # simple/moderate/complex
user_preferences: str
```

**Output:**
```python
{
    "strategy": str,  # minimal/standard/thorough
    "checkpoints": list[str],
    "reasoning": str,
}
```

**Strategies:**
- **minimal**: 2 checkpoints (essential only)
- **standard**: 4 checkpoints (recommended)
- **thorough**: 6 checkpoints (comprehensive)

---

## Async Support

All modules support async execution via `aforward()`:

```python
# Preferred for API/CLI (non-blocking)
result = await module.aforward(input="...")

# Sync wrapper (for scripting)
result = module.forward(input="...")
```

`★ Insight ─────────────────────────────────────`
The `aforward()` methods use `asyncio.to_thread()` to run DSPy's synchronous operations in a thread pool. This allows the FastAPI server and CLI to handle multiple concurrent skill creation requests without blocking.
`─────────────────────────────────────────────────`

## Module Selection Guide

| Task | Recommended Module | Rationale |
|------|-------------------|-----------|
| Direct transformation | `dspy.Predict` | Fastest, no reasoning needed |
| Complex decision making | `dspy.ChainOfThought` | Explicit reasoning improves quality |
| Iterative improvement | `dspy.Refine` | Comparison-based refinement |
| Maximizing quality | `dspy.BestOfN` | Generate N candidates, pick best |

## Metrics Module

**File**: `src/skill_fleet/core/dspy/metrics/skill_quality.py`

The metrics module provides quality assessment functions for evaluating generated skills.

### assess_skill_quality

Main entry point for skill quality evaluation.

```python
from skill_fleet.core.dspy.metrics import assess_skill_quality, SkillQualityScores

scores: SkillQualityScores = assess_skill_quality(skill_content)
print(f"Overall: {scores.overall_score}")
print(f"Issues: {scores.issues}")
```

**Input:**
```python
skill_content: str  # Raw SKILL.md content
weights: dict[str, float] | None = None  # Optional custom weights
```

**Output:**
```python
SkillQualityScores(
    # Structure scores
    frontmatter_completeness: float,
    has_overview: bool,
    has_when_to_use: bool,
    has_quick_reference: bool,
    
    # Pattern scores
    pattern_count: int,
    has_anti_patterns: bool,
    has_production_patterns: bool,
    has_key_insights: bool,
    
    # Practical value scores
    has_common_mistakes: bool,
    has_red_flags: bool,
    has_real_world_impact: bool,
    
    # Code quality scores
    code_examples_count: int,
    code_examples_quality: float,
    
    # Obra/superpowers quality indicators
    has_core_principle: bool,
    has_strong_guidance: bool,
    has_good_bad_contrast: bool,
    description_quality: float,
    
    # Overall
    overall_score: float,
    issues: list[str],
    strengths: list[str],
)
```

### skill_quality_metric

DSPy-compatible metric function for use with optimizers.

```python
from skill_fleet.core.dspy.metrics import skill_quality_metric
from dspy.teleprompt import MIPROv2

optimizer = MIPROv2(
    metric=skill_quality_metric,
    auto="medium",
)
```

`★ Insight ─────────────────────────────────────`
The metrics are calibrated against golden skills from [Obra/superpowers](https://github.com/obra/superpowers). A penalty multiplier is applied for missing critical elements (core principle, strong guidance, good/bad contrast), ensuring stricter scoring that differentiates excellent skills from mediocre ones.
`─────────────────────────────────────────────────`

See [Evaluation Documentation](evaluation.md) for detailed metrics information.

---

## See Also

- **[Signatures Documentation](signatures.md)** - Input/output contracts
- **[Programs Documentation](programs.md)** - Module orchestration
- **[Evaluation Documentation](evaluation.md)** - Quality metrics and assessment
- **[DSPy Overview](index.md)** - Architecture and concepts
