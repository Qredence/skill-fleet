# DSPy Signatures Reference

**Last Updated**: 2026-01-12
**Location**: `src/skill_fleet/core/signatures/`

## Overview

DSPy signatures define the **input/output contracts** for each step in the skill creation workflow. Each signature specifies:

- **Input Fields**: What data the LLM receives
- **Output Fields**: What the LLM must produce
- **Descriptions**: Context for the LLM to understand the task

`★ Insight ─────────────────────────────────────`
Signatures are the foundation of DSPy's type safety. By using Pydantic models for outputs, skills-fleet ensures structured, parseable results from every LLM interaction. This eliminates the need for fragile string parsing.
`─────────────────────────────────────────────────`

## Phase 1 Signatures

**File**: `src/skill_fleet/core/signatures/phase1_understanding.py`

Phase 1 performs parallel analysis of user intent, taxonomy placement, and dependencies.

### GatherRequirements

Initial requirements gathering before detailed analysis.

```python
class GatherRequirements(dspy.Signature):
    """Initial requirements gathering from task description."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `task_description` | `str` | User's task description (may include clarifications) |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `domain` | `str` | Primary domain: 'technical', 'cognitive', 'domain_knowledge', etc. |
| `category` | `str` | Category within domain: 'programming', 'devops', 'data_science', etc. |
| `target_level` | `str` | Target level: 'beginner', 'intermediate', 'advanced', 'expert' |
| `topics` | `list[str]` | List of specific topics to cover (3-7 items) |
| `constraints` | `list[str]` | Any constraints or preferences |
| `ambiguities` | `list[str]` | Detected ambiguities needing HITL clarification |

**Used by**: `RequirementsGathererModule`

---

### AnalyzeIntent

Deep analysis of user intent to understand what skill is needed.

```python
class AnalyzeIntent(dspy.Signature):
    """Deeply analyze user intent to understand what skill is needed."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `task_description` | `str` | User's task description with any clarifications |
| `user_context` | `str` | JSON user context (user_id, existing skills, preferences) |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `task_intent` | `TaskIntent` | Structured intent with purpose, problem_statement, target_audience, value_proposition |
| `skill_type` | `str` | Type: 'how_to', 'reference', 'concept', 'workflow', 'checklist' |
| `scope` | `str` | Scope description: what's included and excluded |
| `success_criteria` | `list[str]` | How to know this skill is successful (3-5 criteria) |

**Used by**: `IntentAnalyzerModule` with `dspy.ChainOfThought`

---

### FindTaxonomyPath

Determine optimal taxonomy placement for the skill.

```python
class FindTaxonomyPath(dspy.Signature):
    """Determine optimal taxonomy placement for this skill."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `task_description` | `str` | User's task description |
| `taxonomy_structure` | `str` | JSON representation of full taxonomy structure |
| `existing_skills` | `list[str]` | List of existing skill paths for reference |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `recommended_path` | `str` | Recommended taxonomy path (e.g., 'technical_skills/programming/python/async') |
| `alternative_paths` | `list[str]` | 2-3 alternative paths if primary has issues |
| `path_rationale` | `str` | Why this path is optimal |
| `new_directories` | `list[str]` | New directories to create (empty if using existing) |
| `confidence` | `float` | Confidence 0-1. <0.7 means may need user confirmation |

**Rules:**
- Prefer deeper paths (more specific is better)
- Consider existing skills in similar categories
- Follow taxonomy naming conventions
- Avoid creating new top-level categories

**Used by**: `TaxonomyPathFinderModule` with `dspy.ChainOfThought`

---

### AnalyzeDependencies

Analyze skill dependencies and prerequisites.

```python
class AnalyzeDependencies(dspy.Signature):
    """Analyze skill dependencies and prerequisites."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `task_description` | `str` | User's task description |
| `task_intent` | `str` | Analyzed task intent from AnalyzeIntent |
| `taxonomy_path` | `str` | Recommended taxonomy path |
| `existing_skills` | `str` | JSON list of existing skills with metadata |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `dependency_analysis` | `DependencyAnalysis` | Complete analysis with required, recommended, conflicts |
| `prerequisite_skills` | `list[DependencyRef]` | Skills user must know first |
| `complementary_skills` | `list[DependencyRef]` | Skills that complement this one |
| `missing_prerequisites` | `list[str]` | Prerequisites that don't exist yet |

**Used by**: `DependencyAnalyzerModule` with `dspy.Predict`

---

### SynthesizePlan

Synthesize all Phase 1 analyses into a coherent skill creation plan.

```python
class SynthesizePlan(dspy.Signature):
    """Synthesize all Phase 1 analyses into a coherent skill creation plan."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `intent_analysis` | `str` | JSON TaskIntent from AnalyzeIntent |
| `taxonomy_analysis` | `str` | JSON taxonomy path and rationale |
| `dependency_analysis` | `str` | JSON DependencyAnalysis |
| `user_confirmation` | `str` | User's confirmation or feedback from HITL (may be empty) |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `skill_metadata` | `SkillMetadata` | Complete skill metadata: name, description, taxonomy_path, tags |
| `content_plan` | `str` | Outline of skill content: sections, topics, example count |
| `generation_instructions` | `str` | Specific instructions for Phase 2 generation |
| `success_criteria` | `list[str]` | How to evaluate if generated content is successful |
| `estimated_length` | `str` | 'short' (<500 lines), 'medium' (500-1500), 'long' (>1500) |

**Used by**: `PlanSynthesizerModule` with `dspy.ChainOfThought`

---

## Phase 2 Signatures

**File**: `src/skill_fleet/core/signatures/phase2_generation.py`

Phase 2 generates the actual skill content based on the plan from Phase 1.

### GenerateSkillContent

Generate complete SKILL.md content based on the plan.

```python
class GenerateSkillContent(dspy.Signature):
    """Generate complete SKILL.md content based on the plan."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `skill_metadata` | `SkillMetadata` | Complete skill metadata from Phase 1 synthesis |
| `content_plan` | `str` | Detailed content plan: sections, topics, example count |
| `generation_instructions` | `str` | Specific instructions for generation (style, tone, depth) |
| `parent_skills_content` | `str` | Content from parent skills for reference |
| `dependency_summaries` | `str` | Summaries of dependency skills |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `skill_content` | `str` | Complete SKILL.md with YAML frontmatter, all sections, examples |
| `usage_examples` | `list[UsageExample]` | 3-5 concrete usage examples |
| `best_practices` | `list[BestPractice]` | 5-10 best practices and gotchas |
| `test_cases` | `list[TestCase]` | Test cases to verify skill understanding |
| `estimated_reading_time` | `int` | Estimated reading time in minutes |

**Requirements:**
- YAML frontmatter at top (name in kebab-case, description)
- Clear sections with headers
- Code examples with explanations
- Best practices and gotchas
- Usage examples

**Used by**: `ContentGeneratorModule` with `dspy.ChainOfThought`

---

### GenerateSkillSection

Generate a single section of skill content (alternative to full generation).

```python
class GenerateSkillSection(dspy.Signature):
    """Generate a single section of skill content."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `section_name` | `str` | Name of section to generate |
| `section_topics` | `list[str]` | Topics to cover in this section |
| `skill_metadata` | `SkillMetadata` | Skill metadata for context |
| `previous_sections` | `str` | Previously generated sections for consistency |
| `style_guide` | `str` | Style guide from generation instructions |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `section_content` | `str` | Complete markdown content for this section |
| `code_examples` | `list[str]` | Code examples included in this section |
| `internal_links` | `list[str]` | Links to other sections or skills |

**Used for**: Very large skills where full generation would exceed token limits

---

### IncorporateFeedback

Incorporate user feedback from HITL preview checkpoint.

```python
class IncorporateFeedback(dspy.Signature):
    """Incorporate user feedback from HITL preview checkpoint."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `current_content` | `str` | Current skill content |
| `user_feedback` | `str` | User's feedback (free-form text) |
| `change_requests` | `str` | JSON structured change requests |
| `skill_metadata` | `SkillMetadata` | Skill metadata for context |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `refined_content` | `str` | Refined skill content incorporating all feedback |
| `changes_made` | `list[str]` | List of changes made (for user review) |
| `unaddressed_feedback` | `list[str]` | Any feedback that couldn't be addressed |
| `improvement_score` | `float` | Self-assessment of improvement 0-1 |

**Used by**: `FeedbackIncorporatorModule` with `dspy.ChainOfThought`

---

## Phase 3 Signatures

**File**: `src/skill_fleet/core/signatures/phase3_validation.py`

Phase 3 validates the generated skill content and iteratively refines it.

### ValidateSkill

Comprehensive validation of generated skill content.

```python
class ValidateSkill(dspy.Signature):
    """Comprehensive validation of generated skill content."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `skill_content` | `str` | Complete SKILL.md content to validate |
| `skill_metadata` | `SkillMetadata` | Skill metadata |
| `content_plan` | `str` | Original content plan from Phase 1 |
| `validation_rules` | `str` | JSON validation rules and thresholds |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `validation_report` | `ValidationReport` | Complete report with passed, checks, issues, warnings |
| `critical_issues` | `list[ValidationCheckItem]` | Issues that MUST be fixed |
| `warnings` | `list[ValidationCheckItem]` | Issues that SHOULD be fixed |
| `suggestions` | `list[str]` | Optional suggestions for improvement |
| `overall_score` | `float` | Overall quality score 0-1. >0.8 means high quality |

**Validates:**
1. agentskills.io Compliance (YAML frontmatter, naming)
2. Content Quality (sections, examples, code validity)
3. Structural Integrity (markdown formatting, links)
4. Metadata Consistency (matches content, tags, dependencies)

**Used by**: `SkillValidatorModule` with `dspy.Predict`

---

### RefineSkillFromFeedback

Refine skill content based on validation issues and user feedback.

```python
class RefineSkillFromFeedback(dspy.Signature):
    """Refine skill content based on validation issues and user feedback."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `current_content` | `str` | Current skill content |
| `validation_issues` | `str` | JSON list of validation issues to address |
| `user_feedback` | `str` | User's feedback (may be empty for auto-fix) |
| `fix_strategies` | `str` | JSON fix strategies from AnalyzeValidationIssues |
| `iteration_number` | `int` | Current iteration number (1, 2, 3, ...) |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `refined_content` | `str` | Refined skill content with issues addressed |
| `issues_resolved` | `list[str]` | List of issue IDs resolved in this iteration |
| `issues_remaining` | `list[str]` | List of issue IDs still remaining |
| `changes_summary` | `str` | Summary of changes made (for user review) |
| `ready_for_acceptance` | `bool` | True if all critical issues resolved |

**Used by**: `SkillRefinerModule` with `dspy.ChainOfThought`

---

### AssessSkillQuality

Assess overall quality of skill content beyond validation.

```python
class AssessSkillQuality(dspy.Signature):
    """Assess overall quality of skill content beyond validation."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `skill_content` | `str` | Complete skill content |
| `skill_metadata` | `SkillMetadata` | Skill metadata |
| `target_level` | `str` | Target level: beginner/intermediate/advanced |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | `float` | 0-1. >0.8 excellent, 0.6-0.8 good, <0.6 needs improvement |
| `strengths` | `list[str]` | What's good about this skill (3-5 points) |
| `weaknesses` | `list[str]` | What could be improved (3-5 points) |
| `recommendations` | `list[str]` | Specific recommendations for improvement |
| `audience_alignment` | `float` | How well content matches target level 0-1 |

**Used by**: `QualityAssessorModule` with `dspy.ChainOfThought`

---

## Chat Signatures

**File**: `src/skill_fleet/core/signatures/chat.py`

Signatures for the interactive chat mode skill creation.

### GuidedResponseSignature

Generate the next agent response in a guided skill creation conversation.

```python
class GuidedResponseSignature(dspy.Signature):
    """Generate the next agent response in a guided skill creation conversation."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `history` | `str` | Conversation history so far |
| `current_state` | `str` | Current workflow state: GATHERING, PROPOSING, GENERATING |
| `user_input` | `str` | The latest message from the user |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `agent_message` | `str` | The natural language response to the user |
| `action_required` | `Literal` | Internal action: ask_clarification, propose_plan, start_generation, none |
| `rationale` | `str` | Reasoning behind the chosen response and action |
| `understanding_summary` | `str` | Persistent, evolving summary of user's intent |
| `confidence_score` | `float` | Confidence 0.0-1.0. >0.9 triggers proposal |

**Used by**: `GuidedCreatorProgram` with `dspy.ChainOfThought`

---

### ClarificationSignature

Generate a single focused clarifying question.

```python
class ClarificationSignature(dspy.Signature):
    """Generate a single focused clarifying question based on current intent."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `intent_so_far` | `str` | The refined understanding of user's intent |
| `history` | `str` | Conversation history |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `focused_question` | `str` | A single, clear clarifying question |

**Used by**: `GuidedCreatorProgram` with `dspy.Predict`

---

### ProposalSignature

Propose a taxonomy path and kebab-case name.

```python
class ProposalSignature(dspy.Signature):
    """Propose a taxonomy path and kebab-case name based on refined intent."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `refined_intent` | `str` | The final refined intent of the skill |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `proposed_taxonomy_path` | `str` | e.g., technical_skills/programming/python |
| `proposed_name` | `str` | e.g., async-context-managers |
| `description` | `str` | 1-2 sentence description for the skill |

**Used by**: `GuidedCreatorProgram` with `dspy.Predict`

---

## HITL Signatures

**File**: `src/skill_fleet/core/signatures/hitl.py`

Signatures for Human-in-the-Loop interactions throughout the workflow.

### GenerateClarifyingQuestions

Generate focused clarifying questions to better understand user intent.

```python
class GenerateClarifyingQuestions(dspy.Signature):
    """Generate focused clarifying questions to better understand user intent."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `task_description` | `str` | User's initial task description |
| `initial_analysis` | `str` | Initial analysis of the task |
| `ambiguities` | `list[str]` | List of detected ambiguities |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `questions` | `list[ClarifyingQuestion]` | 2-3 focused questions (NOT yes/no) |
| `priority` | `str` | 'critical', 'important', or 'optional' |

**Used by**: `ClarifyingQuestionsModule` with `dspy.ChainOfThought`

---

### SummarizeUnderstanding

Summarize understanding of user intent for confirmation.

```python
class SummarizeUnderstanding(dspy.Signature):
    """Summarize understanding of user intent for confirmation."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `task_description` | `str` | Original task description |
| `user_clarifications` | `str` | JSON of user's answers to clarifying questions |
| `intent_analysis` | `str` | Analyzed intent from Phase 1 |
| `taxonomy_path` | `str` | Determined taxonomy path |
| `dependencies` | `list[str]` | List of skill dependencies |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `summary` | `str` | Concise bullet-point summary (3-5 bullets) |
| `key_assumptions` | `list[str]` | Key assumptions being made |
| `confidence` | `float` | Confidence 0-1. >0.8 means high confidence |

**Used by**: `ConfirmUnderstandingModule` with `dspy.Predict`

---

### GeneratePreview

Generate a preview of skill content for user review.

```python
class GeneratePreview(dspy.Signature):
    """Generate a preview of skill content for user review."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `skill_content` | `str` | Full generated skill content (SKILL.md) |
| `metadata` | `str` | JSON skill metadata |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `preview` | `str` | Concise preview with TOC, key points, stats |
| `highlights` | `list[str]` | 3-5 highlights of what makes this skill valuable |
| `potential_issues` | `list[str]` | Potential issues user might want to address |

**Used by**: `PreviewGeneratorModule` with `dspy.Predict`

---

### AnalyzeFeedback

Analyze user feedback and determine what changes to make.

```python
class AnalyzeFeedback(dspy.Signature):
    """Analyze user feedback and determine what changes to make."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `user_feedback` | `str` | User's feedback (free-form text) |
| `current_content` | `str` | Current skill content |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `change_requests` | `list[dict]` | Structured change requests |
| `scope_change` | `bool` | True if feedback requires major scope change |
| `estimated_effort` | `str` | 'minor', 'moderate', or 'major' |

**Used by**: `FeedbackAnalyzerModule` with `dspy.ChainOfThought`

---

### FormatValidationResults

Format validation results for human-readable display.

```python
class FormatValidationResults(dspy.Signature):
    """Format validation results for human-readable display."""
```

**Inputs:**
| Field | Type | Description |
|-------|------|-------------|
| `validation_report` | `str` | JSON validation report |
| `skill_content` | `str` | The skill content that was validated |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| `formatted_report` | `str` | Human-readable report |
| `critical_issues` | `list[ValidationCheckItem]` | Critical issues that MUST be fixed |
| `warnings` | `list[ValidationCheckItem]` | Warnings that SHOULD be addressed |
| `auto_fixable` | `bool` | True if all issues can be auto-fixed |

**Used by**: `ValidationFormatterModule` with `dspy.Predict`

---

## Pydantic Models

All signatures use Pydantic models for type-safe outputs. Key models are defined in `src/skill_fleet/core/config/models.py`:

- **`TaskIntent`**: Purpose, problem_statement, target_audience, value_proposition
- **`SkillMetadata`**: name, description, taxonomy_path, tags, version, type
- **`DependencyAnalysis`**: required, recommended, conflicts
- **`ValidationReport`**: passed, checks, issues, warnings
- **`ClarifyingQuestion`**: question, rationale, suggested_answers

## See Also

- **[Modules Documentation](modules.md)** - How signatures are used in modules
- **[Programs Documentation](programs.md)** - How modules are orchestrated
- **[DSPy Overview](index.md)** - Architecture and concepts
