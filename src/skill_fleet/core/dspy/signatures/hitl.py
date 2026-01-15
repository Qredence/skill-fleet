"""DSPy signatures for Human-in-the-Loop (HITL) interactions.

These signatures define the contracts for generating questions, confirmations,
previews, and other interactive elements throughout the 3-phase skill creation workflow.

HITL Checkpoints:
- Phase 1: Clarification + Confirmation
- Phase 2: Preview + Feedback
- Phase 3: Validation + Final Review
"""

from __future__ import annotations

import dspy

from ...models import ClarifyingQuestion, ValidationCheckItem

# =============================================================================
# Phase 1 HITL: Understanding & Planning
# =============================================================================


class GenerateClarifyingQuestions(dspy.Signature):
    """Generate focused clarifying questions to better understand user intent.

    Ask 2-3 focused questions to:
    - Clarify ambiguous requirements
    - Understand edge cases
    - Confirm taxonomy placement
    - Verify dependencies

    Keep questions specific and actionable. Avoid yes/no questions.
    """

    # Inputs
    task_description: str = dspy.InputField(desc="User's initial task description")
    initial_analysis: str = dspy.InputField(
        desc="Initial analysis of the task (intent, taxonomy guess, etc.)"
    )
    ambiguities: list[str] = dspy.InputField(
        desc="List of detected ambiguities that need clarification"
    )

    # Outputs
    questions: list[ClarifyingQuestion] = dspy.OutputField(
        desc="2-3 focused clarifying questions (NOT yes/no). Each has: question, rationale, suggested_answers"
    )
    priority: str = dspy.OutputField(
        desc="Priority level: 'critical' (must answer), 'important' (should answer), 'optional' (nice to have)"
    )


class GenerateHITLQuestions(dspy.Signature):
    """Generate HITL clarification questions from gathered requirements.

    This is a simpler signature used during the initial HITL clarification
    checkpoint when ambiguities are detected in the requirements gathering phase.

    Takes the JSON-serialized requirements and original task description,
    and generates focused questions to resolve ambiguities.
    """

    # Inputs
    requirements: str = dspy.InputField(
        desc="JSON string of gathered requirements including domain, category, ambiguities, etc."
    )
    task: str = dspy.InputField(desc="Original user task description")

    # Outputs
    questions: str = dspy.OutputField(
        desc="Focused clarifying questions to resolve ambiguities (2-4 questions, numbered list)"
    )
    rationale: str = dspy.OutputField(
        desc="Brief explanation of why these questions are important for skill creation"
    )


class SummarizeUnderstanding(dspy.Signature):
    """Summarize understanding of user intent for confirmation.

    Create a clear, concise summary of what we understood from the task
    and user's clarifying answers. This is shown to user for confirmation
    before proceeding to expensive generation phase.

    Format as bullet points for easy scanning.
    """

    # Inputs
    task_description: str = dspy.InputField(desc="Original task description")
    user_clarifications: str = dspy.InputField(
        desc="JSON string of user's answers to clarifying questions"
    )
    intent_analysis: str = dspy.InputField(desc="Analyzed intent from Phase 1 parallel analysis")
    taxonomy_path: str = dspy.InputField(
        desc="Determined taxonomy path (e.g., technical_skills/programming/python)"
    )
    dependencies: list[str] = dspy.InputField(desc="List of skill dependencies")

    # Outputs
    summary: str = dspy.OutputField(
        desc="Concise bullet-point summary of understanding (3-5 bullets)"
    )
    key_assumptions: list[str] = dspy.OutputField(
        desc="Key assumptions being made (user should verify these)"
    )
    confidence: float = dspy.OutputField(
        desc="Confidence score 0-1. >0.8 means high confidence, proceed. <0.8 means may need more clarification"
    )


# =============================================================================
# Phase 2 HITL: Content Generation
# =============================================================================


class GeneratePreview(dspy.Signature):
    """Generate a preview of skill content for user review.

    Create a concise preview showing:
    - Skill structure (sections/headings)
    - Key points covered in each section
    - Example count
    - Estimated length

    This helps user verify scope and style before full generation.
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Full generated skill content (SKILL.md)")
    metadata: str = dspy.InputField(desc="JSON skill metadata (name, description, capabilities)")

    # Outputs
    preview: str = dspy.OutputField(
        desc="Concise preview with: 1) Table of contents, 2) Key points per section, 3) Stats (examples, length)"
    )
    highlights: list[str] = dspy.OutputField(
        desc="3-5 highlights of what makes this skill valuable"
    )
    potential_issues: list[str] = dspy.OutputField(
        desc="Potential issues user might want to address (e.g., 'No error handling examples')"
    )


class AnalyzeFeedback(dspy.Signature):
    """Analyze user feedback and determine what changes to make.

    Parse user's free-form feedback and convert it into structured
    change requests that can be used to refine the skill content.
    """

    # Inputs
    user_feedback: str = dspy.InputField(desc="User's feedback on the preview (free-form text)")
    current_content: str = dspy.InputField(desc="Current skill content")

    # Outputs
    change_requests: list[dict] = dspy.OutputField(
        desc="Structured change requests: [{type: 'add/remove/modify', section: '...', details: '...'}]"
    )
    scope_change: bool = dspy.OutputField(
        desc="True if feedback requires major scope change (may need to restart)"
    )
    estimated_effort: str = dspy.OutputField(
        desc="Estimated effort: 'minor' (quick fix), 'moderate' (refinement), 'major' (regeneration)"
    )


# =============================================================================
# Phase 3 HITL: Validation & Iteration
# =============================================================================


class FormatValidationResults(dspy.Signature):
    """Format validation results for human-readable display.

    Convert technical validation output into clear, actionable
    feedback for the user. Group issues by severity and provide
    suggested fixes.
    """

    # Inputs
    validation_report: str = dspy.InputField(
        desc="JSON validation report with checks, failures, warnings"
    )
    skill_content: str = dspy.InputField(desc="The skill content that was validated")

    # Outputs
    formatted_report: str = dspy.OutputField(
        desc="Human-readable report with: 1) Summary (pass/fail), 2) Issues by severity, 3) Suggested fixes"
    )
    critical_issues: list[ValidationCheckItem] = dspy.OutputField(
        desc="Critical issues that MUST be fixed before acceptance"
    )
    warnings: list[ValidationCheckItem] = dspy.OutputField(
        desc="Warnings that SHOULD be addressed but not blocking"
    )
    auto_fixable: bool = dspy.OutputField(
        desc="True if all issues can be auto-fixed without user input"
    )


class GenerateRefinementPlan(dspy.Signature):
    """Generate a refinement plan based on validation issues and user feedback.

    Create a structured plan for how to refine the skill to address
    validation failures and incorporate user's feedback.
    """

    # Inputs
    validation_issues: str = dspy.InputField(desc="JSON list of validation issues")
    user_feedback: str = dspy.InputField(
        desc="User's feedback on how to address issues (may be empty for auto-fix)"
    )
    current_skill: str = dspy.InputField(desc="Current skill content")

    # Outputs
    refinement_plan: str = dspy.OutputField(desc="Step-by-step plan for refining the skill")
    changes: list[dict] = dspy.OutputField(
        desc="Specific changes to make: [{section: '...', change_type: 'add/remove/modify', details: '...'}]"
    )
    estimated_iterations: int = dspy.OutputField(
        desc="Estimated number of refinement iterations needed (1-3)"
    )


# =============================================================================
# Universal HITL Utilities
# =============================================================================


class AssessReadiness(dspy.Signature):
    """Assess if we're ready to proceed to next phase.

    Evaluate whether we have enough information to proceed,
    or if more HITL interaction is needed.
    """

    # Inputs
    phase: str = dspy.InputField(desc="Current phase: 'understanding', 'generation', 'validation'")
    collected_info: str = dspy.InputField(desc="JSON of information collected so far")
    min_requirements: str = dspy.InputField(desc="JSON of minimum requirements needed to proceed")

    # Outputs
    ready: bool = dspy.OutputField(desc="True if ready to proceed to next phase")
    readiness_score: float = dspy.OutputField(desc="Readiness score 0-1. >0.8 means ready")
    missing_info: list[str] = dspy.OutputField(
        desc="List of missing information needed (empty if ready)"
    )
    next_questions: list[str] = dspy.OutputField(
        desc="Suggested next questions to ask user (if not ready)"
    )


class DetermineHITLStrategy(dspy.Signature):
    """Determine optimal HITL strategy for a given task.

    Analyze the task and decide:
    - Which HITL checkpoints are needed
    - How many questions to ask
    - Whether auto-approve is appropriate
    """

    # Inputs
    task_description: str = dspy.InputField(desc="User's task description")
    task_complexity: str = dspy.InputField(
        desc="Complexity assessment: 'simple', 'moderate', 'complex'"
    )
    user_preferences: str = dspy.InputField(
        desc="JSON of user preferences (e.g., prefer_auto_approve, verbose_feedback)"
    )

    # Outputs
    strategy: str = dspy.OutputField(
        desc="Recommended strategy: 'minimal' (2 checkpoints), 'standard' (4 checkpoints), 'thorough' (6 checkpoints)"
    )
    checkpoints: list[str] = dspy.OutputField(
        desc="List of checkpoint names to enable (e.g., ['phase1_clarify', 'phase1_confirm', ...])"
    )
    reasoning: str = dspy.OutputField(desc="Reasoning for this strategy")
