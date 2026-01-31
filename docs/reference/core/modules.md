# Core Modules Reference

**Last Updated**: 2026-01-31
**Location**: `src/skill_fleet/core/modules/`

## Overview

The Skill Fleet core modules are DSPy-powered components that implement the skill creation workflows. Each module encapsulates a specific capability, using DSPy signatures to define inputs/outputs and ChainOfThought for reasoning.

```
core/modules/
├── base.py                 # BaseModule foundation
├── understanding/          # Phase 1: Understanding
│   ├── requirements.py     # GatherRequirementsModule
│   ├── intent.py           # AnalyzeIntentModule
│   ├── taxonomy.py         # FindTaxonomyPathModule
│   ├── dependencies.py     # AnalyzeDependenciesModule
│   └── plan.py             # SynthesizePlanModule
├── generation/             # Phase 2: Generation
│   ├── content.py          # GenerateSkillContentModule
│   └── templates.py        # Category-specific templates
└── validation/             # Phase 3: Validation
    ├── structure.py        # ValidateStructureModule
    ├── compliance.py       # ValidateComplianceModule
    ├── metrics.py          # AssessQualityModule
    └── test_cases.py       # GenerateTestCasesModule
```

---

## BaseModule

**File**: `src/skill_fleet/core/modules/base.py`

All modules inherit from `BaseModule`, which provides common functionality.

### Features

| Feature | Description |
|---------|-------------|
| Input Sanitization | Automatic cleaning of inputs to prevent injection |
| Result Validation | Ensures required fields are present |
| Execution Logging | Structured logging for observability |
| Error Handling | Graceful fallbacks on failures |

### Usage

```python
from skill_fleet.core.modules.base import BaseModule

class MyModule(BaseModule):
    def forward(self, input_data: str) -> dict:
        # Sanitize input
        clean_input = self._sanitize_input(input_data)

        # Process...

        # Validate output
        output = {"result": processed}
        if not self._validate_result(output, required=["result"]):
            output["result"] = "default"

        return output
```

---

## Phase 1: Understanding Modules

### GatherRequirementsModule

**File**: `src/skill_fleet/core/modules/understanding/requirements.py`

Extracts structured requirements from user task descriptions.

**Signature**: `GatherRequirements`

**Returns**:
```python
{
    "domain": "technical",           # technical, cognitive, domain_knowledge, tool, meta
    "category": "python",            # Specific category
    "target_level": "intermediate",  # beginner, intermediate, advanced, expert
    "topics": ["async", "await"],    # Topics to cover
    "constraints": ["Python 3.11+"], # Technical constraints
    "ambiguities": [],               # Unclear aspects for HITL
    # Validation-oriented outputs
    "suggested_skill_name": "python-async",
    "trigger_phrases": ["create async"],
    "negative_triggers": ["simple queries"],
    "skill_category": "document_creation",
    "requires_mcp": False,
    "suggested_mcp_server": ""
}
```

**Usage**:
```python
module = GatherRequirementsModule()
result = module.forward(
    task_description="Create a Python async/await skill",
    user_context={"experience": "intermediate"}
)
```

---

### AnalyzeIntentModule

**File**: `src/skill_fleet/core/modules/understanding/intent.py`

Determines skill purpose, target audience, and success criteria.

**Signature**: `AnalyzeIntent`

**Returns**:
```python
{
    "purpose": "Help developers write async Python code",
    "problem_statement": "Developers struggle with async patterns",
    "target_audience": "Intermediate Python developers",
    "value_proposition": "Clear async/await patterns",
    "skill_type": "how_to",          # how_to, reference, explanation
    "scope": "Async syntax and patterns",
    "success_criteria": ["User can write async functions"]
}
```

---

### FindTaxonomyPathModule

**File**: `src/skill_fleet/core/modules/understanding/taxonomy.py`

Determines optimal taxonomy placement for the skill.

**Signature**: `FindTaxonomyPath`

**Returns**:
```python
{
    "taxonomy_path": "technical/programming/python/async",
    "parent_category": "technical/programming/python",
    "suggested_name": "python-async-await",
    "placement_rationale": "Fits under Python programming...",
    "similar_skills": ["python-basics"],
    "path_confidence": 0.95
}
```

---

### AnalyzeDependenciesModule

**File**: `src/skill_fleet/core/modules/understanding/dependencies.py`

Identifies prerequisites and related skills.

**Signature**: `AnalyzeDependencies`

**Returns**:
```python
{
    "required_prerequisites": ["python-basics"],
    "suggested_prerequisites": ["python-functions"],
    "related_skills": ["python-concurrency"],
    "dependency_confidence": 0.9
}
```

---

### SynthesizePlanModule

**File**: `src/skill_fleet/core/modules/understanding/plan.py`

Combines all understanding outputs into a coherent generation plan.

**Signature**: `SynthesizePlan`

**Returns**:
```python
{
    "skill_name": "python-async-await",
    "skill_description": "Use when you need to create async Python code...",
    "taxonomy_path": "technical/programming/python/async",
    "content_outline": ["Introduction", "async/await Basics", "..."],
    "generation_guidance": "Focus on practical examples...",
    "success_criteria": ["Clear examples", "Error handling covered"],
    "estimated_length": "medium",    # short, medium, long
    "tags": ["python", "async", "concurrency"],
    "trigger_phrases": ["create async"],
    "negative_triggers": ["sync code"],
    "skill_category": "document_creation"
}
```

---

## Phase 2: Generation Modules

### GenerateSkillContentModule

**File**: `src/skill_fleet/core/modules/generation/content.py`

Generates complete SKILL.md content with category-specific templates.

**Signature**: `GenerateSkillContent`

**Async Usage**:
```python
module = GenerateSkillContentModule()
result = await module.aforward(
    plan={"skill_name": "...", "content_outline": [...]},
    understanding={"requirements": {...}, "intent": {...}},
    skill_style="comprehensive"  # minimal, comprehensive, navigation_hub
)
```

**Returns**:
```python
{
    "skill_content": "# Skill Name\n\nUse when...",  # Full SKILL.md
    "sections_generated": ["Introduction", "Examples"],
    "code_examples_count": 5,
    "estimated_reading_time": 12,
    "category": "document_creation",
    "template_compliance": {
        "compliance_score": 0.92,
        "missing_sections": []
    },
    "missing_sections": []
}
```

---

### Template System

**File**: `src/skill_fleet/core/modules/generation/templates.py`

Category-specific templates ensure skills follow best practices.

| Category | Best For | Required Sections |
|----------|----------|-------------------|
| `document_creation` | Creating documents/assets | Output Format, Examples |
| `workflow_automation` | Multi-step processes | Workflow Steps, Input/Output |
| `mcp_enhancement` | MCP-guided workflows | MCP Tools, Tool Sequences |
| `analysis` | Data/code analysis | Analysis Approach, Output Format |

**Functions**:
- `get_template_for_category(category)` - Get template for skill category
- `validate_against_template(content, template)` - Check compliance

---

## Phase 3: Validation Modules

### ValidateStructureModule

**File**: `src/skill_fleet/core/modules/validation/structure.py`

Combines rule-based and LLM-based validation for skill structure.

**Enforces**:
- **Kebab-case naming**: `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`
- **Description requirements**: Trigger phrases, length limits
- **Security**: No reserved names, no XML tags
- **Size**: < 5,000 words recommended

**Reserved Names**: `claude`, `anthropic`, `claude-code`, `anthropic-ai`

**Returns**:
```python
{
    "name_valid": True,
    "name_errors": [],
    "description_valid": True,
    "description_errors": [],
    "description_warnings": [],
    "has_trigger_conditions": True,
    "estimated_word_count": 2500,
    "size_recommendation": "optimal",
    "security_issues": [],
    "overall_valid": True
}
```

---

### GenerateTestCasesModule

**File**: `src/skill_fleet/core/modules/validation/test_cases.py`

Creates comprehensive test cases for trigger validation.

**Signature**: `GenerateTestCases`

**Returns**:
```python
{
    "positive_tests": ["Create async function", "..."],  # 10 tests
    "negative_tests": ["What's the weather?", "..."],    # 10 tests
    "edge_cases": ["Python async vs threading"],         # 5 cases
    "functional_tests": [{                               # 5 scenarios
        "scenario": "Basic async",
        "input": "Create async function",
        "expected_behavior": "Generate async code",
        "success_criteria": ["Uses async def"]
    }],
    "total_tests": 25
}
```

---

### AssessQualityModule

**File**: `src/skill_fleet/core/modules/validation/metrics.py`

Assesses skill quality across multiple dimensions.

**Metrics**:
| Metric | Target | Description |
|--------|--------|-------------|
| `completeness` | >0.8 | Coverage of plan requirements |
| `clarity` | >0.8 | Readability and organization |
| `usefulness` | >0.8 | Practical value |
| `overall_score` | >0.75 | Weighted aggregate |

**Returns**:
```python
{
    "overall_score": 0.88,
    "completeness": 0.9,
    "clarity": 0.85,
    "usefulness": 0.9,
    "word_count": 2500,
    "size_assessment": "optimal",  # optimal, acceptable, too_large
    "verbosity_score": 0.3,        # 0=concise, 1=verbose
    "strengths": ["Good examples"],
    "improvement_areas": []
}
```

---

## Module Patterns

### Sync vs Async

Most modules support both sync and async execution:

```python
# Sync
result = module.forward(task_description="...")

# Async
result = await module.aforward(task_description="...")
```

Modules that wrap async operations (like LLM calls) typically implement `aforward()` and have `forward()` delegate to it via `asyncio.run()`.

### Error Handling

Modules use graceful fallbacks:

```python
try:
    result = self.generator(...)
except Exception as e:
    self.logger.warning(f"Generation failed: {e}")
    return self._create_fallback_result(...)
```

### Input Sanitization

All inputs are sanitized to prevent injection:

```python
clean_input = self._sanitize_input(user_input, max_length=1000)
```

### Result Validation

Outputs are validated for required fields:

```python
if not self._validate_result(output, required=["skill_content"]):
    output["skill_content"] = "# Default content"
```

---

## Related Documentation

- [Signatures Reference](signatures.md) - DSPy signature definitions
- [Workflows Reference](workflows.md) - Workflow orchestration
- [Architecture](../../explanation/architecture/workflow-engine.md) - System design
