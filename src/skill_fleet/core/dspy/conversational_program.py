"""Main orchestrator for the Guided Creator chat experience."""

from __future__ import annotations

import logging
from typing import Any, Literal

import dspy
from pydantic import BaseModel, Field

from ..models import SkillMetadata
from .signatures.chat import ClarificationSignature, GuidedResponseSignature, ProposalSignature

logger = logging.getLogger(__name__)


class ChatSessionState(BaseModel):
    """Internal state for a guided chat session."""

    session_id: str
    history: list[dict[str, str]] = Field(default_factory=list)
    current_phase: Literal["GATHERING", "PROPOSING", "GENERATING", "COMPLETED"] = "GATHERING"
    refined_intent: str = ""
    understanding_summary: str = ""  # Persistent summary of understanding
    confidence: float = 0.0  # Current confidence score
    question_count: int = 0  # Track number of clarifying questions asked
    metadata: SkillMetadata | None = None
    job_id: str | None = None  # Link to the actual SkillCreationProgram job


class GuidedCreatorProgram(dspy.Module):
    """DSPy program to guide users through skill creation via chat."""

    def __init__(self):
        super().__init__()
        self.generate_response = dspy.ChainOfThought(GuidedResponseSignature)
        self.generate_question = dspy.Predict(ClarificationSignature)
        self.generate_proposal = dspy.Predict(ProposalSignature)

    async def aforward(self, user_input: str, state: ChatSessionState) -> dict[str, Any]:
        """Process user input and return the next agent message and state update."""
        # Format history for DSPy
        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in state.history])

        # 1. Generate agent response and action
        prediction = await self.generate_response.acall(
            history=history_str,
            current_state=state.current_phase,
            user_input=user_input,
        )

        agent_message = prediction.agent_message
        action = prediction.action_required
        rationale = getattr(prediction, "rationale", "")

        # Update state with new insights
        state.understanding_summary = getattr(
            prediction, "understanding_summary", state.understanding_summary
        )
        state.confidence = getattr(prediction, "confidence_score", 0.0)

        # 2. Handle specific actions and phase transitions
        if action == "ask_clarification":
            # Dynamic Questioning Logic:
            # If confidence is high (>0.9) OR max questions (6) reached, force proposal
            if state.confidence > 0.9 or state.question_count >= 6:
                action = "propose_plan"
                # Fall through to propose_plan logic below
            else:
                state.question_count += 1
                # Use the generated clarification question if available, or generate one
                # For now, let GuidedResponseSignature handle the phrasing
                pass

        if action == "propose_plan":
            # Transition to PROPOSING if not already
            if state.current_phase == "GATHERING":
                state.current_phase = "PROPOSING"

                # Generate proposal details
                proposal = await self.generate_proposal.acall(
                    refined_intent=f"{state.understanding_summary}\nLatest input: {user_input}"
                )

                # Store refined intent
                state.refined_intent = state.understanding_summary

                # Update message to include proposal
                agent_message = (
                    f"Based on our discussion, I propose the following plan:\n\n"
                    f"**Path**: {proposal.proposed_taxonomy_path}\n"
                    f"**Name**: {proposal.proposed_name}\n"
                    f"**Description**: {proposal.description}\n\n"
                    "Does this look correct? (Yes/No)"
                )

        elif action == "start_generation":
            if state.current_phase == "PROPOSING":
                state.current_phase = "GENERATING"
                agent_message = "Excellent! I'm starting the generation process now. You'll see updates as I work."

        # Update history
        state.history.append({"role": "user", "content": user_input})
        state.history.append({"role": "assistant", "content": agent_message})

        return {
            "agent_message": agent_message,
            "action_required": action,
            "updated_state": state,
            "rationale": rationale,
        }
