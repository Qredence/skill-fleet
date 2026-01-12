# Plan: Enhanced Transparency & Interactivity for Guided Creator

## Objective
Transform the "Guided Creator" chat experience from a concise, minimal workflow into a **rich, transparent, and highly interactive session**. The agent must explicitly communicate its evolving understanding, detailed plans, and granular progress at every step.

## Critical Issues to Fix
1.  **Too Concise**: Agent jumps to conclusions or next steps without showing its work.
2.  **Hidden Understanding**: User doesn't know *what* the agent actually understood until the end.
3.  **Limited Exploration**: 2 questions are not enough for complex skills.
4.  **Opaque Progress**: "Generating..." hides the actual sub-steps.

## Proposed Architecture Changes

### 1. Core Layer: Enhanced Signatures & Logic
- **Modify `GuidedResponseSignature`**:
    - Add `understanding_summary`: A persistent, evolving summary of what the user wants.
    - Add `plan_preview`: A structured preview of the plan *as it stands now*.
    - Add `next_step_reasoning`: Explicit explanation of *why* the agent is taking the next action.
- **Update `GuidedCreatorProgram`**:
    - **Dynamic Questioning**: Ask questions one-by-one until `understanding_confidence` > 0.9 or max 6 questions reached.
    - **State Persistence**: Store the full `understanding_summary` in the session state and update it on every turn.
    - **Explicit Confirmation**: Force a "Summary Confirmation" step where the agent plays back the *entire* understanding before moving to the Proposal phase.

### 2. API Layer: Richer Response Schema
- Update `ChatSessionResponse` to include:
    - `understanding_summary`: The current understanding text.
    - `plan_details`: Dictionary of plan components (path, name, capabilities).
    - `progress_step`: Current micro-step (e.g., "Analyzing Intent", "Drafting Content").
    - `confidence`: 0-1 score of agent confidence.

### 3. CLI Layer: Dashboard & Visibility
- **Persistent Dashboard**: Instead of just a chat log, render a "Live Dashboard" above the input prompt using `rich.live.Live`.
    - **Top Panel**: "Current Understanding" (updates real-time).
    - **Side Panel**: "Plan Draft" (fills in as we go).
    - **Bottom Panel**: "Progress Bar" (shows phase and confidence).
- **Verbose Thinking**: Render `rationale` in a large, collapsible panel *before* the agent's message.
- **Detailed Summaries**: When the user asks for a summary, dump the *entire* internal state (intent, scope, constraints) in a structured format.

## Implementation Roadmap

### Phase 1: Core Enhancements
1.  Modify `src/skill_fleet/core/signatures/chat.py` to add the new fields.
2.  Update `src/skill_fleet/core/programs/conversational.py` to populate these fields and implement the dynamic questioning logic.

### Phase 2: API Updates
1.  Update `src/skill_fleet/api/routes/chat.py` to pass the new rich data structures.

### Phase 3: CLI Dashboard
1.  Rewrite `src/skill_fleet/cli/commands/chat.py` to use a `Live` display layout.
2.  Implement the "Dashboard" rendering logic.

## Success Criteria
- [ ] Agent asks up to 6 questions if needed to clarify ambiguity.
- [ ] Every response includes an updated "Understanding Summary".
- [ ] User can see the plan evolving in real-time.
- [ ] "Generating" phase shows granular steps (e.g., "Drafting Section 1", "Validating Code").
