"""DSPy signatures for conversational skill creation agent.

These signatures define the input/output contracts for natural language
conversation flow in the interactive CLI. They enable the agent to:
- Understand user intent conversationally
- Ask clarifying questions one at a time
- Detect when multiple skills are needed
- Confirm understanding before creation
- Present results conversationally
- Process feedback naturally
- Enforce TDD checklist workflow

Approved LLM Models:
- gemini-3-flash-preview: Primary model for conversation
- gemini-3-pro-preview: For complex reasoning tasks
- deepseek-v3.2: Cost-effective alternative
"""

from __future__ import annotations

from typing import Literal

import dspy

# =============================================================================
# Intent Understanding and Multi-Skill Detection
# =============================================================================


class InterpretUserIntent(dspy.Signature):
    """Interpret user's skill creation intent from natural language.

    Analyzes user messages to understand what they want to create.
    Handles various forms of natural language input and determines
    the action type (create, clarify, revise, approve, etc.).
    """

    # Inputs
    user_message: str = dspy.InputField(desc="User's message")
    conversation_history: str = dspy.InputField(
        desc="Previous conversation context (last 5-10 messages as JSON)"
    )
    current_state: str = dspy.InputField(
        desc="Current workflow state (EXPLORING, CONFIRMING, CREATING, TDD_RED_PHASE, etc.)"
    )

    # Outputs
    intent_type: Literal[
        "create_skill", "clarify", "revise", "approve", "reject", "confirm", "unknown"
    ] = dspy.OutputField(
        desc="Type of intent: 'create_skill' (new skill request), 'clarify' (seeking clarification), 'revise' (revision request), 'approve' (approval), 'reject' (rejection), 'confirm' (confirmation), 'unknown' (unclear)"
    )
    extracted_task: str = dspy.OutputField(
        desc="Task description extracted or refined from user message"
    )
    confidence: float = dspy.OutputField(
        desc="Confidence in interpretation (0.0-1.0). Low confidence (<0.7) suggests need for clarification."
    )


class DetectMultiSkillNeeds(dspy.Signature):
    """Detect if user's task requires multiple skills to fulfill.

    Analyzes the task description to determine if it encompasses
    multiple distinct capabilities that should be separate skills.
    This ensures skills remain focused and follow single-responsibility principle.
    """

    # Inputs
    task_description: str = dspy.InputField(desc="User's complete task description")
    collected_examples: str = dspy.InputField(
        desc="Examples gathered so far (JSON list of UserExample objects)"
    )
    existing_skills: str = dspy.InputField(
        desc="JSON list of existing skills in taxonomy (for overlap detection)"
    )

    # Outputs
    requires_multiple_skills: bool = dspy.OutputField(
        desc="Whether multiple discrete skills are needed to fulfill this task"
    )
    skill_breakdown: list[str] = dspy.OutputField(
        desc="List of discrete skill names needed (if multiple). Each should be a clear, focused skill (e.g., ['condition-based-waiting', 'error-handling-patterns'])"
    )
    reasoning: str = dspy.OutputField(
        desc="Explanation of why multiple skills are needed (or why one skill is sufficient). Should identify distinct concerns, different triggers, or separate use cases."
    )
    suggested_order: list[str] = dspy.OutputField(
        desc="Recommended order to create skills (same as skill_breakdown if multiple, empty list if single). Order should respect dependencies and logical progression."
    )


# =============================================================================
# Clarification and Readiness Assessment
# =============================================================================


class GenerateClarifyingQuestion(dspy.Signature):
    """Generate one focused clarifying question following brainstorming principles.

    Creates a single, focused question to better understand the user's needs.
    Follows the brainstorming skill pattern: one question at a time,
    prefer multiple choice, focus on understanding purpose and constraints.
    """

    # Inputs
    task_description: str = dspy.InputField(desc="Current understanding of task")
    collected_examples: str = dspy.InputField(
        desc="Examples gathered so far (JSON list of UserExample objects)"
    )
    conversation_context: str = dspy.InputField(
        desc="What's already been discussed (summary of previous questions/answers)"
    )

    # Outputs
    question: str = dspy.OutputField(
        desc="Single focused question to ask the user. Prefer multiple choice format when possible."
    )
    question_options: list[str] = dspy.OutputField(
        desc="Multiple choice options if applicable (empty list for free-form questions). Use when discrete choices help clarify."
    )
    reasoning: str = dspy.OutputField(
        desc="Why this question matters - what gap in understanding it addresses"
    )


class AssessReadiness(dspy.Signature):
    """Assess if we have enough information to proceed with skill creation.

    Evaluates whether sufficient context has been gathered through examples
    and clarification to create a well-crafted skill. Considers example
    coverage, clarity of requirements, and edge case understanding.
    """

    # Inputs
    task_description: str = dspy.InputField(desc="Refined task description")
    examples: str = dspy.InputField(desc="Collected examples (JSON list of UserExample objects)")
    questions_asked: int = dspy.InputField(desc="Number of clarifying questions already asked")

    # Outputs
    readiness_score: float = dspy.OutputField(
        desc="0.0-1.0 score indicating readiness. >= 0.8 means ready to proceed. Based on example coverage (do we have concrete use cases?), clarity (are requirements clear?), and edge cases (do we understand limitations?)."
    )
    readiness_reasoning: str = dspy.OutputField(
        desc="Brief explanation of readiness score (why ready or what's missing). If not ready, specify what information is needed."
    )
    should_proceed: bool = dspy.OutputField(
        desc="Whether to start skill creation workflow. True if readiness_score >= 0.8 and we have at least 2-3 concrete examples."
    )


# =============================================================================
# Deep Understanding Phase
# =============================================================================


class DeepUnderstandingSignature(dspy.Signature):
    """Understand user's actual needs, problems, and goals before creating skill.

    This signature generates contextual multi-choice questions to understand WHY
    the user needs the skill, what problem they're solving, and what their goals are.
    Uses research when needed to provide better context. Asks questions one at a time
    until readiness_score >= 0.8.
    """

    # Inputs
    initial_task: str = dspy.InputField(desc="User's original task description")
    conversation_history: str = dspy.InputField(
        desc="JSON string of previous questions and answers (list of {question_id, answer, timestamp})"
    )
    research_findings: str = dspy.InputField(
        desc="JSON string of research results from web search and filesystem exploration (empty string if none)"
    )
    current_understanding: str = dspy.InputField(
        desc="Current summary of what we understand about user's needs so far (empty string on first call)"
    )

    # Outputs
    next_question: str = dspy.OutputField(
        desc="Next question to ask as JSON string of ClarifyingQuestion object (or empty string if ready). Should have contextual multi-choice options (2-5 options). Empty string if ready to proceed (readiness_score >= 0.8). Format: JSON string that can be parsed into ClarifyingQuestion with id, question, context, options (list of QuestionOption), allows_multiple, required fields."
    )
    reasoning: str = dspy.OutputField(
        desc="Agent's thinking about WHY this question matters (1-3 sentences). Explain what gap in understanding this question addresses and how it helps create a more relevant skill. Display as context before the question."
    )
    research_needed: dict | None = dspy.OutputField(
        desc="JSON dict if research would help answer the question. Format: {'type': 'web'|'filesystem'|'both', 'query': 'specific search query', 'reason': 'why this research is needed'}. None if no research needed. Only include when research would provide valuable context."
    )
    understanding_summary: str = dspy.OutputField(
        desc="Current understanding of user needs (paragraph format). What problem are they solving? What are their goals? What context do we have?"
    )
    readiness_score: float = dspy.OutputField(
        desc="Readiness to proceed (0.0-1.0). >= 0.8 means ready to create skill. Based on: problem clarity (0.3 weight), goal clarity (0.2 weight), context sufficiency (0.2 weight), technical requirements (0.15 weight), examples gathered (0.15 weight)."
    )
    refined_task_description: str = dspy.OutputField(
        desc="Enhanced task description incorporating insights from questions, answers, and research. Should include user's problem, goals, and relevant context."
    )
    user_problem: str = dspy.OutputField(
        desc="Extracted problem statement - what problem is the user actually trying to solve? (empty string if not yet identified)"
    )
    user_goals: list[str] = dspy.OutputField(
        desc="List of user's goals/outcomes they want to achieve (empty list if not yet identified)"
    )


# =============================================================================
# Confirmation Checkpoint (MANDATORY)
# =============================================================================


class ConfirmUnderstandingBeforeCreation(dspy.Signature):
    """Generate confirmation message to verify understanding before creating skill.

    MANDATORY checkpoint before writing any skill directory structure or content.
    Presents a clear summary of what will be created and asks for explicit
    user confirmation. This prevents misunderstandings and ensures alignment.
    """

    # Inputs
    task_description: str = dspy.InputField(desc="Refined task description")
    taxonomy_path: str = dspy.InputField(
        desc="Proposed taxonomy path (e.g., 'technical_skills/testing/async-testing')"
    )
    skill_metadata_draft: str = dspy.InputField(
        desc="Draft skill metadata as JSON (includes name, description, capabilities)"
    )
    collected_examples: str = dspy.InputField(
        desc="Examples collected (JSON list of UserExample objects)"
    )

    # Outputs
    confirmation_summary: str = dspy.OutputField(
        desc="Clear summary of what will be created (2-3 sentences). Should include skill name, what it does, and key capabilities."
    )
    key_points: list[str] = dspy.OutputField(
        desc="Key points to confirm: skill name, description, taxonomy path, main capabilities. User should verify these are correct."
    )
    confirmation_question: str = dspy.OutputField(
        desc="Direct question asking for confirmation (e.g., 'Does this look correct? (yes/no)'). Should be clear and simple."
    )


class UnderstandingSummary(dspy.Signature):
    """Generate structured understanding summary before skill creation.

    Creates a three-part structured summary that clearly communicates:
    1. What was understood: User's problem, goals, and context
    2. What will be created: Skill structure, capabilities, taxonomy placement
    3. How it addresses the task: Alignment with user's goals and problem resolution

    This is displayed BEFORE creation begins to ensure user alignment.
    """

    # Inputs
    task_description: str = dspy.InputField(desc="Refined task description")
    user_problem: str = dspy.InputField(
        desc="User's problem statement (what problem are they solving?)", default=""
    )
    user_goals: list[str] = dspy.InputField(
        desc="User's goals/outcomes (empty list if not identified)", default=[]
    )
    research_context: str = dspy.InputField(
        desc="JSON string of research findings from web/filesystem (empty string if none)",
        default="",
    )
    taxonomy_path: str = dspy.InputField(
        desc="Proposed taxonomy path (e.g., 'technical_skills/testing/async-testing')"
    )
    skill_metadata_draft: str = dspy.InputField(
        desc="Draft skill metadata as JSON (includes name, description, capabilities, type)"
    )
    collected_examples: str = dspy.InputField(
        desc="Examples collected (JSON list of UserExample objects)", default="[]"
    )

    # Outputs
    what_was_understood: str = dspy.OutputField(
        desc="Section 1: Summary of what was understood. Should include: user's problem (what they're solving), their goals (what outcomes they want), and any relevant context from research/questions. Format as markdown with ## What Was Understood heading."
    )
    what_will_be_created: str = dspy.OutputField(
        desc="Section 2: Summary of what will be created. Should include: skill name, description, type (technique/pattern/reference/discipline), main capabilities (3-7 items), taxonomy path. Format as markdown with ## What Will Be Created heading and bullet points for capabilities."
    )
    how_it_addresses_task: str = dspy.OutputField(
        desc="Section 3: Explanation of how the proposed skill addresses the user's task. Should include: alignment with user's goals, how capabilities solve the identified problem, what outcomes the user can expect. Format as markdown with ## How This Addresses Your Task heading."
    )
    alignment_summary: str = dspy.OutputField(
        desc="Brief 1-2 sentence summary of the overall alignment between user needs and the proposed skill. Used as a quick confirmation before diving into details."
    )


# =============================================================================
# Review and Feedback
# =============================================================================


class PresentSkillForReview(dspy.Signature):
    """Format skill creation results for conversational presentation.

    Transforms technical skill creation results into a conversational format
    that's easy for users to understand and review. Highlights key points
    and suggests questions to gather feedback.
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Generated SKILL.md content")
    skill_metadata: str = dspy.InputField(desc="JSON skill metadata")
    validation_report: str = dspy.InputField(desc="JSON validation results")

    # Outputs
    conversational_summary: str = dspy.OutputField(
        desc="Brief summary (2-3 sentences) of what was created. Use natural language, avoid technical jargon unless necessary."
    )
    key_highlights: list[str] = dspy.OutputField(
        desc="Key points to highlight (3-5 items). Focus on what the skill does, main capabilities, and standout features."
    )
    suggested_questions: list[str] = dspy.OutputField(
        desc="Questions to ask user for feedback (2-3 questions). Focus on quality, completeness, and user satisfaction."
    )


class ProcessUserFeedback(dspy.Signature):
    """Process user's feedback and determine revision plan.

    Interprets user feedback (approval, revision requests, rejections) and
    creates a concrete plan for how to proceed. Handles both explicit
    feedback and implicit signals.
    """

    # Inputs
    user_feedback: str = dspy.InputField(
        desc="User's feedback message (approval, revision request, or rejection)"
    )
    current_skill_content: str = dspy.InputField(desc="Current skill content (SKILL.md)")
    validation_errors: str = dspy.InputField(
        desc="Any validation errors (JSON array of error messages, empty if none)"
    )

    # Outputs
    feedback_type: Literal["approve", "revision_request", "rejection"] = dspy.OutputField(
        desc="Type of feedback: 'approve' (ready to save), 'revision_request' (needs changes), 'rejection' (not acceptable)"
    )
    revision_plan: str = dspy.OutputField(
        desc="Specific changes needed if feedback_type is 'revision_request'. Should be actionable and clear. Empty string if approve or reject."
    )
    requires_regeneration: bool = dspy.OutputField(
        desc="Whether skill content needs to be regenerated (True for major changes, False for minor edits)"
    )


# =============================================================================
# TDD Checklist Signatures
# =============================================================================


class SuggestTestScenarios(dspy.Signature):
    """Suggest test scenarios for skill validation following writing-skills TDD.

    Creates pressure scenarios to test the skill according to TDD principles.
    Different skill types require different test approaches:
    - Discipline skills: 3+ combined pressures (time, sunk cost, authority, exhaustion)
    - Technique skills: Application scenarios and variation scenarios
    - Pattern skills: Recognition and application scenarios
    - Reference skills: Retrieval and application scenarios
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Generated skill content (SKILL.md)")
    skill_type: Literal["technique", "pattern", "reference", "discipline"] = dspy.InputField(
        desc="Type of skill: 'technique' (how-to guide), 'pattern' (mental model), 'reference' (documentation), 'discipline' (rules/requirements)"
    )
    skill_metadata: str = dspy.InputField(desc="JSON skill metadata")

    # Outputs
    test_scenarios: list[str] = dspy.OutputField(
        desc="Pressure scenarios to test. For discipline skills: 3+ combined pressures (e.g., 'Time pressure + sunk cost + authority pressure'). For others: application/variation scenarios."
    )
    baseline_predictions: list[str] = dspy.OutputField(
        desc="Expected failures without skill (document verbatim what agents will do wrong). Should match test_scenarios 1-to-1."
    )
    expected_rationalizations: list[str] = dspy.OutputField(
        desc="Patterns in rationalizations/failures to identify. What excuses or workarounds will agents use? (e.g., 'Just this once', 'Too simple to test', 'I'll test after')"
    )


class VerifyTDDPassed(dspy.Signature):
    """Verify TDD checklist is complete before saving skill.

    Checks that all mandatory checklist items are complete according to
    writing-skills TDD requirements. Prevents saving incomplete skills.
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Generated skill content (SKILL.md)")
    checklist_state: str = dspy.InputField(
        desc="JSON checklist completion state with all TDD phases: RED (scenarios created, baseline tests run, behavior documented, patterns identified), GREEN (tests run with skill, compliance verified, failures addressed), REFACTOR (rationalizations identified, counters added, retested), Quality Checks (flowchart if needed, quick reference, common mistakes, no narrative, files appropriate)"
    )

    # Outputs
    all_passed: bool = dspy.OutputField(
        desc="Whether all required checklist items are complete. Must be True to save skill."
    )
    missing_items: list[str] = dspy.OutputField(
        desc="List of incomplete checklist items if all_passed is False. Empty list if all_passed is True."
    )
    ready_to_save: bool = dspy.OutputField(
        desc="Whether skill can be saved. True only if all_passed is True and no critical issues remain."
    )
