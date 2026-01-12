"""DSPy signatures for the Guided Creator chat experience."""

from __future__ import annotations

from typing import Literal

import dspy


class GuidedResponseSignature(dspy.Signature):
    """Generate the next agent response in a guided skill creation conversation.

    The agent should be helpful, concise, and focused on moving the user
    through the 3 phases of skill creation:
    1. GATHERING: Understand the user's intent and collect requirements.
    2. PROPOSING: Suggest a taxonomy path and name for the skill.
    3. GENERATING: Inform the user that the skill is being generated.
    """

    history: str = dspy.InputField(desc="Conversation history so far")
    current_state: str = dspy.InputField(
        desc="Current workflow state: GATHERING, PROPOSING, GENERATING"
    )
    user_input: str = dspy.InputField(desc="The latest message from the user")

    agent_message: str = dspy.OutputField(desc="The natural language response to the user")
    action_required: Literal["ask_clarification", "propose_plan", "start_generation", "none"] = (
        dspy.OutputField(desc="Internal action to take based on the conversation")
    )
    rationale: str = dspy.OutputField(desc="Reasoning behind the chosen response and action")
    understanding_summary: str = dspy.OutputField(
        desc="A persistent, evolving summary of the user's intent and requirements"
    )
    confidence_score: float = dspy.OutputField(
        desc="Confidence in understanding (0.0-1.0). >0.9 triggers proposal."
    )


class ClarificationSignature(dspy.Signature):
    """Generate a single focused clarifying question based on current intent.

    Avoid overwhelming the user. Ask only the most critical question needed
    to move to the PROPOSING phase.
    """

    intent_so_far: str = dspy.InputField(desc="The refined understanding of the user's intent")
    history: str = dspy.InputField(desc="Conversation history")

    focused_question: str = dspy.OutputField(desc="A single, clear clarifying question")


class ProposalSignature(dspy.Signature):
    """Propose a taxonomy path and kebab-case name based on refined intent."""

    refined_intent: str = dspy.InputField(desc="The final refined intent of the skill")

    proposed_taxonomy_path: str = dspy.OutputField(desc="e.g., technical_skills/programming/python")
    proposed_name: str = dspy.OutputField(desc="e.g., async-context-managers")
    description: str = dspy.OutputField(desc="1-2 sentence description for the skill")
