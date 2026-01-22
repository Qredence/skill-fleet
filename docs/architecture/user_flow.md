# User Flow: Interactive Skill Creation

This document outlines the user flow for the interactive skill creation process, highlighting the interaction between the CLI (Client), the FastAPI Backend, the Conversation Service, and the DSPy modules.

## Architecture Overview

The system uses an **API-First Architecture**:
1.  **CLI (Thin Client)**: Handles user input/output, connects to the API via streaming.
2.  **FastAPI Backend**: Exposes endpoints, manages session state (in-memory for MVP).
3.  **Conversation Service**: Orchestrates the state machine and business logic.
4.  **DSPy Modules**: Encapsulate specific LLM tasks (Intent, Understanding, TDD).

## User Flow Diagram

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI (Client)
    participant API as FastAPI /stream
    participant Service as ConversationService
    participant DSPy as DSPy Modules
    participant LLM as LLM (Gemini/DeepSeek)

    User->>CLI: "I want to create a skill for async testing"
    CLI->>API: POST /chat/stream {message, session_id}
    
    API->>Service: respond(message, session)
    
    rect rgb(240, 248, 255)
    Note over Service, LLM: Phase 1: Understanding
    Service->>DSPy: InterpretIntent(message)
    DSPy->>LLM: Analyze intent...
    LLM-->>DSPy: Intent: create_skill
    DSPy-->>Service: Result
    
    Service-->>API: Stream "thinking" event (Intent detected)
    API-->>CLI: Display thinking...
    
    Service->>DSPy: DeepUnderstanding(task)
    DSPy->>LLM: Generate clarifying questions...
    LLM-->>DSPy: Question + Reasoning
    DSPy-->>Service: Result
    end
    
    Service-->>API: Stream "response" event (Question)
    API-->>CLI: Render Question
    CLI-->>User: Display Question
    
    User->>CLI: "Yes, focused on pytest-asyncio"
    CLI->>API: POST /chat/stream {message, session_id}
    
    rect rgb(255, 240, 245)
    Note over Service, LLM: Phase 2: Confirmation & Creation
    Service->>DSPy: AssessReadiness()
    DSPy->>LLM: Score: 0.9 (Ready)
    Service->>DSPy: ConfirmUnderstanding()
    Service-->>API: Stream "response" (Confirmation Summary)
    end
    
    User->>CLI: "Yes, create it"
    CLI->>API: POST /chat/stream {message}
    
    rect rgb(240, 255, 240)
    Note over Service, LLM: Phase 3: Generation & TDD
    Service->>DSPy: SkillCreationProgram()
    Note right of Service: Executing Phase 1, 2, 3...
    Service->>DSPy: SuggestTests(skill_content)
    DSPy->>LLM: Generate Red/Green scenarios...
    Service-->>API: Stream "response" (TDD Checklist)
    end
```

## State Machine Transition

The `ConversationService` manages the following high-level states:

```mermaid
stateDiagram-v2
    [*] --> EXPLORING
    EXPLORING --> DEEP_UNDERSTANDING: Intent = create_skill
    DEEP_UNDERSTANDING --> EXPLORING: Clarification needed
    DEEP_UNDERSTANDING --> MULTI_SKILL_DETECTED: Multiple skills found
    DEEP_UNDERSTANDING --> CONFIRMING: Readiness >= 0.8
    MULTI_SKILL_DETECTED --> DEEP_UNDERSTANDING: User selects single
    CONFIRMING --> CREATING: User confirms
    CONFIRMING --> EXPLORING: User revises
    CREATING --> TDD_RED_PHASE: Draft generated
    TDD_RED_PHASE --> TDD_GREEN_PHASE: Baseline tests run
    TDD_GREEN_PHASE --> TDD_REFACTOR_PHASE: Compliance verified
    TDD_REFACTOR_PHASE --> CHECKLIST_COMPLETE: All checks passed
    CHECKLIST_COMPLETE --> COMPLETE: Skill saved
    COMPLETE --> [*]
```

## Module Organization

The DSPy modules are organized by function in `src/skill_fleet/core/dspy/modules/conversation/`:

| Module | Purpose |
| :--- | :--- |
| `intent.py` | Detect user intent (`InterpretIntentModule`) and multi-skill needs (`DetectMultiSkillModule`). |
| `understanding.py` | Gather context (`DeepUnderstandingModule`), ask questions (`GenerateQuestionModule`), and summarize (`UnderstandingSummaryModule`). |
| `tdd.py` | Generate test scenarios (`SuggestTestsModule`) and verify completion (`VerifyTDDModule`). |
| `feedback.py` | Present results (`PresentSkillModule`) and process user feedback (`ProcessFeedbackModule`). |

## Standards Alignment

### FastAPI
- **Dependencies**: Uses `Depends` for `TaxonomyManager` injection.
- **Pydantic**: Uses `BaseModel` for all request/response schemas.
- **Async**: Fully async route handlers and service methods.
- **Streaming**: Uses `StreamingResponse` with SSE format.

### DSPy
- **Declarative**: Uses `dspy.Signature` for all LLM interfaces.
- **Modular**: Logic encapsulated in `dspy.Module` classes.
- **Optimizable**: Uses `dspy.ChainOfThought` and supports `MultiChainComparison` for critical steps.
- **Typed**: Inputs/outputs are typed (e.g., `list[str]`, `bool`).
