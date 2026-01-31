# Core Signatures Reference

**Last Updated**: 2026-01-31
**Location**: `src/skill_fleet/core/signatures/`

## Overview

DSPy signatures define the contract between modules and language models. Each signature specifies:
- **Inputs**: What data the model receives (`dspy.InputField`)
- **Outputs**: What data the model produces (`dspy.OutputField`)
- **Docstring**: Instructions for the model

```
core/signatures/
├── understanding/          # Phase 1 signatures
│   ├── requirements.py     # GatherRequirements
│   ├── intent.py           # AnalyzeIntent
│   ├── taxonomy.py         # FindTaxonomyPath
│   ├── dependencies.py     # AnalyzeDependencies
│   └── plan.py             # SynthesizePlan
├── generation/             # Phase 2 signatures
│   └── content.py          # GenerateSkillContent
└── validation/             # Phase 3 signatures
    ├── structure.py        # ValidateSkillStructure
    ├── compliance.py       # CheckCompliance
    └── quality.py          # AssessQuality
```

---

## Phase 1: Understanding Signatures

### GatherRequirements

**File**: `src/skill_fleet/core/signatures/understanding/requirements.py`

Extracts structured requirements from task descriptions with validation-oriented outputs.

```python
class GatherRequirements(dspy.Signature):
    """Extract structured requirements from user task description..."""

    # Inputs
    task_description: str = dspy.InputField(
        desc="User's task description..."
    )
    user_context: str = dspy.InputField(
        desc="JSON user context...",
        default="{}",
    )

    # Core outputs
    domain: Domain = dspy.OutputField(desc="Primary domain...")
    category: str = dspy.OutputField(desc="Specific category...")
    target_level: TargetLevel = dspy.OutputField(desc="Target expertise...")
    topics: list[str] = dspy.OutputField(desc="3-7 specific topics...")
    constraints: list[str] = dspy.OutputField(desc="Technical constraints...")
    ambiguities: list[str] = dspy.OutputField(desc="Unclear aspects...")

    # Validation-oriented outputs
    suggested_skill_name: str = dspy.OutputField(desc="Kebab-case name...")
    trigger_phrases: list[str] = dspy.OutputField(desc="5-7 trigger phrases...")
    negative_triggers: list[str] = dspy.OutputField(desc="3-5 negative triggers...")
    skill_category: SkillCategory = dspy.OutputField(desc="Category for template...")
    requires_mcp: bool = dspy.OutputField(desc="Needs MCP integration...")
    suggested_mcp_server: str = dspy.OutputField(desc="MCP server name...")
```

**Type Constraints**:
```python
Domain = Literal["technical", "cognitive", "domain_knowledge", "tool", "meta"]
TargetLevel = Literal["beginner", "intermediate", "advanced", "expert"]
SkillCategory = Literal[
    "document_creation",
    "workflow_automation",
    "mcp_enhancement",
    "analysis",
    "other"
]
```

---

### AnalyzeIntent

**File**: `src/skill_fleet/core/signatures/understanding/intent.py`

Determines skill purpose and audience.

```python
class AnalyzeIntent(dspy.Signature):
    """Analyze user intent from task description..."""

    task_description: str = dspy.InputField(desc="User's task...")
    requirements: str = dspy.InputField(desc="Requirements from GatherRequirements...")

    purpose: str = dspy.OutputField(desc="Why this skill exists...")
    problem_statement: str = dspy.OutputField(desc="Specific problem...")
    target_audience: str = dspy.OutputField(desc="Who needs this...")
    value_proposition: str = dspy.OutputField(desc="Unique value...")
    skill_type: str = dspy.OutputField(desc="how_to, reference, explanation...")
    scope: str = dspy.OutputField(desc="What's included/excluded...")
    success_criteria: list[str] = dspy.OutputField(desc="Measurable criteria...")
```

---

### FindTaxonomyPath

**File**: `src/skill_fleet/core/signatures/understanding/taxonomy.py`

Finds optimal taxonomy placement.

```python
class FindTaxonomyPath(dspy.Signature):
    """Find optimal taxonomy path for skill..."""

    skill_name: str = dspy.InputField(desc="Proposed skill name...")
    skill_description: str = dspy.InputField(desc="Skill description...")
    domain: str = dspy.InputField(desc="Domain from requirements...")
    category: str = dspy.InputField(desc="Category from requirements...")
    taxonomy_structure: str = dspy.InputField(desc="Current taxonomy as JSON...")

    taxonomy_path: str = dspy.OutputField(desc="Full path like 'technical/python'...")
    parent_category: str = dspy.OutputField(desc="Parent path...")
    suggested_name: str = dspy.OutputField(desc="Name if different from input...")
    placement_rationale: str = dspy.OutputField(desc="Why this path...")
    similar_skills: list[str] = dspy.OutputField(desc="Similar existing skills...")
    path_confidence: float = dspy.OutputField(desc="Confidence 0.0-1.0...")
```

---

### AnalyzeDependencies

**File**: `src/skill_fleet/core/signatures/understanding/dependencies.py`

Identifies skill prerequisites.

```python
class AnalyzeDependencies(dspy.Signature):
    """Analyze skill dependencies and prerequisites..."""

    skill_name: str = dspy.InputField(desc="Skill name...")
    skill_description: str = dspy.InputField(desc="Skill description...")
    target_level: str = dspy.InputField(desc="Target expertise level...")
    topics: list[str] = dspy.InputField(desc="Topics covered...")
    existing_skills: list[str] = dspy.InputField(desc="Existing skill names...")

    required_prerequisites: list[str] = dspy.OutputField(desc="Must have first...")
    suggested_prerequisites: list[str] = dspy.OutputField(desc="Nice to have...")
    related_skills: list[str] = dspy.OutputField(desc="Similar/complementary...")
    dependency_confidence: float = dspy.OutputField(desc="Confidence 0.0-1.0...")
```

---

### SynthesizePlan

**File**: `src/skill_fleet/core/signatures/understanding/plan.py`

Combines understanding into a generation plan.

```python
class SynthesizePlan(dspy.Signature):
    """Synthesize all understanding into a skill generation plan..."""

    task_description: str = dspy.InputField(desc="Original task...")
    requirements: str = dspy.InputField(desc="JSON from GatherRequirements...")
    intent: str = dspy.InputField(desc="JSON from AnalyzeIntent...")
    taxonomy: str = dspy.InputField(desc="JSON from FindTaxonomyPath...")
    dependencies: str = dspy.InputField(desc="JSON from AnalyzeDependencies...")

    skill_name: str = dspy.OutputField(desc="Final kebab-case name...")
    skill_description: str = dspy.OutputField(desc="Description with triggers...")
    taxonomy_path: str = dspy.OutputField(desc="Final taxonomy path...")
    content_outline: list[str] = dspy.OutputField(desc="Section headers...")
    generation_guidance: str = dspy.OutputField(desc="Instructions for generation...")
    success_criteria: list[str] = dspy.OutputField(desc="Validation criteria...")
    estimated_length: str = dspy.OutputField(desc="short/medium/long...")
    tags: list[str] = dspy.OutputField(desc="Search tags...")
    trigger_phrases: list[str] = dspy.OutputField(desc="User trigger phrases...")
    negative_triggers: list[str] = dspy.OutputField(desc="Non-trigger contexts...")
    skill_category: str = dspy.OutputField(desc="Template category...")
```

---

## Phase 2: Generation Signatures

### GenerateSkillContent

**File**: `src/skill_fleet/core/signatures/generation/content.py`

Creates complete SKILL.md content.

```python
class GenerateSkillContent(dspy.Signature):
    """Generate complete skill content (SKILL.md)..."""

    plan: str = dspy.InputField(desc="JSON with name, outline, guidance...")
    understanding: str = dspy.InputField(desc="JSON with requirements, intent...")
    skill_style: str = dspy.InputField(desc="minimal/comprehensive/navigation_hub...")

    skill_content: str = dspy.OutputField(desc="Complete SKILL.md content...")
    sections_generated: list[str] = dspy.OutputField(desc="Sections created...")
    code_examples_count: int = dspy.OutputField(desc="Number of code examples...")
    estimated_reading_time: int = dspy.OutputField(desc="Minutes to read...")
```

---

## Phase 3: Validation Signatures

### ValidateSkillStructure

**File**: `src/skill_fleet/core/signatures/validation/structure.py`

Validates skill structure requirements.

```python
class ValidateSkillStructure(dspy.Signature):
    """Validate skill structure against Anthropic requirements..."""

    skill_name: str = dspy.InputField(desc="Skill name...")
    description: str = dspy.InputField(desc="Skill description...")
    skill_content: str = dspy.InputField(desc="Full SKILL.md content...")

    name_valid: bool = dspy.OutputField(desc="Name follows kebab-case...")
    name_errors: list[str] = dspy.OutputField(desc="Naming issues...")
    description_valid: bool = dspy.OutputField(desc="Description meets reqs...")
    description_errors: list[str] = dspy.OutputField(desc="Description issues...")
    description_warnings: list[str] = dspy.OutputField(desc="Suggestions...")
    has_trigger_conditions: bool = dspy.OutputField(desc="Has 'Use when'...")
    estimated_word_count: int = dspy.OutputField(desc="Word count estimate...")
    size_recommendation: str = dspy.OutputField(desc="optimal/acceptable/too_large...")
    security_issues: list[str] = dspy.OutputField(desc="Security concerns...")
    overall_valid: bool = dspy.OutputField(desc="Passes all checks...")
```

---

### CheckCompliance

**File**: `src/skill_fleet/core/signatures/validation/compliance.py`

Checks agentskills.io format compliance.

```python
class CheckCompliance(dspy.Signature):
    """Check skill compliance with agentskills.io format..."""

    skill_content: str = dspy.InputField(desc="Full SKILL.md content...")
    skill_category: str = dspy.InputField(desc="Category for requirements...")

    frontmatter_valid: bool = dspy.OutputField(desc="Valid YAML frontmatter...")
    frontmatter_errors: list[str] = dspy.OutputField(desc="YAML issues...")
    required_sections_present: list[str] = dspy.OutputField(desc="Sections found...")
    missing_required_sections: list[str] = dspy.OutputField(desc="Sections missing...")
    markdown_structure_valid: bool = dspy.OutputField(desc="Valid markdown...")
    markdown_errors: list[str] = dspy.OutputField(desc="Markdown issues...")
    compliance_score: float = dspy.OutputField(desc="0.0-1.0 score...")
    passed: bool = dspy.OutputField(desc="Meets all requirements...")
```

---

### AssessQuality

**File**: `src/skill_fleet/core/signatures/validation/quality.py`

Assesses skill quality metrics.

```python
class AssessQuality(dspy.Signature):
    """Assess skill quality across multiple dimensions..."""

    skill_content: str = dspy.InputField(desc="Full SKILL.md content...")
    plan: str = dspy.InputField(desc="Original plan with success criteria...")

    overall_score: float = dspy.OutputField(desc="Weighted aggregate 0.0-1.0...")
    completeness: float = dspy.OutputField(desc="Coverage of plan...")
    clarity: float = dspy.OutputField(desc="Readability...")
    usefulness: float = dspy.OutputField(desc="Practical value...")
    word_count: int = dspy.OutputField(desc="Actual word count...")
    size_assessment: str = dspy.OutputField(desc="optimal/acceptable/too_large...")
    verbosity_score: float = dspy.OutputField(desc="0=concise, 1=verbose...")
    strengths: list[str] = dspy.OutputField(desc="What works well...")
    improvement_areas: list[str] = dspy.OutputField(desc="What to improve...")
```

---

## Signature Design Patterns

### Type Annotations

Use type hints for better validation:

```python
from typing import Literal

Domain = Literal["technical", "cognitive", "domain_knowledge", "tool", "meta"]

domain: Domain = dspy.OutputField(desc="Primary domain...")
```

### Default Values

Provide defaults for optional inputs:

```python
user_context: str = dspy.InputField(
    desc="User context...",
    default="{}",
)
```

### Descriptive Docstrings

Docstrings guide LLM reasoning:

```python
class MySignature(dspy.Signature):
    """
    Clear instruction for the LLM.

    Be specific about what to do and how.
    Include examples if helpful.
    """
```

### Output Field Descriptions

Detailed descriptions improve output quality:

```python
# Good - specific guidance
topics: list[str] = dspy.OutputField(
    desc="3-7 specific topics. Be concrete (not 'basics' but 'async/await'). "
         "Order by importance. Max 7 items."
)

# Less effective - vague
topics: list[str] = dspy.OutputField(desc="Topics to cover")
```

---

## ChainOfThought Usage

Signatures are typically wrapped in ChainOfThought for reasoning:

```python
class MyModule(BaseModule):
    def __init__(self):
        self.generator = dspy.ChainOfThought(MySignature)

    def forward(self, input_data: str) -> dict:
        result = self.generator(input_data=input_data)
        # result has all OutputField attributes
        return {
            "output": result.output_field,
            "reasoning": result.rationale  # ChainOfThought adds this
        }
```

---

## Related Documentation

- [Modules Reference](modules.md) - Module implementations
- [DSPy Documentation](https://dspy-docs.vercel.app/) - Framework reference
- [Workflows Reference](workflows.md) - Workflow orchestration
