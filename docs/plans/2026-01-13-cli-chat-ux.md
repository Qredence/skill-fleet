# CLI Chat UX Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade `uv run skill-fleet chat` to (1) show “thinking”/rationale consistently, (2) ask clarifying questions one-at-a-time, (3) support arrow-key selection for multi-choice prompts, and (4) allow a free-text override (“Other…”) anywhere a multi-choice question is shown.

**Architecture:** Introduce a small UI abstraction (`PromptUI`) with a Prompt Toolkit-backed implementation for arrow-key selection and a Rich fallback. Refactor the HITL runner to drive a single-question loop (clarify) and unify action prompts (confirm/preview/validate) through the UI abstraction.

**Tech Stack:** Typer, Rich, prompt-toolkit, httpx.

---

## Current state (baseline)

### Files

- CLI entrypoint: `src/skill_fleet/cli/commands/chat.py`
- HITL runner loop: `src/skill_fleet/cli/hitl/runner.py`
- API prompt endpoint: `src/skill_fleet/api/routes/hitl.py`
- API skill creation job: `src/skill_fleet/api/routes/skills.py`

### Observed UX constraints

- Multi-choice prompts are currently typed (`Prompt.ask(..., choices=[...])`) rather than arrow-key navigable.
- Clarify prompts currently accept a single free-form answer string. If the server returns multiple questions, they are rendered in a single panel.
- “Thinking” is only shown for clarify via the `rationale` field (when present).

## UX requirements (target behavior)

1. **Thinking content shown**

- Display rationale / “why I’m asking” when available.
- If a prompt has no rationale, do not show an empty panel.
- Optional: add `--show-thinking/--no-show-thinking` flag to control this.

2. **One question at a time**

- For clarify prompts that contain multiple questions, present them sequentially.
- After each answer submission, the runner returns to polling until either:
  - the job requests another clarify prompt, or
  - moves to confirm/preview/validate, or
  - completes.

3. **Arrow-key multi choice**

- Use prompt-toolkit dialogs for:
  - single-choice selection (radio list)
  - multi-choice selection (checkbox list)

4. **Plain-text option**

- If a question has options, append an “Other (type my own)” option.
- If selected, open a plain text input prompt.
- When both multi-choice and free-text are supplied, include both in the answer payload.

---

## Approach options (choose one)

### Option A (recommended): prompt-toolkit dialogs + Rich fallback

- Use `prompt_toolkit.shortcuts.radiolist_dialog` / `checkboxlist_dialog` for arrow-key selection.
- Fallback to Rich `Prompt.ask` when:
  - not running in a TTY,
  - prompt-toolkit is unavailable,
  - or `$TERM` indicates limited support.

**Pros:** Best UX with minimal new dependencies (already in deps), easiest to maintain.
**Cons:** Dialog UI differs from current Rich-only styling.

### Option B: Full-screen prompt-toolkit Application

- Build a dedicated TUI view with a single input box + selectable options.

**Pros:** Most polished.
**Cons:** Highest effort; more fragile; larger test surface.

### Option C: “Rich only”

- Keep typed choices.

**Pros:** Minimal change.
**Cons:** Does not meet arrow-key requirement.

Proceed with **Option A**.

---

## Data contracts & compatibility

### Clarify questions

- Short-term: accept whatever API returns in `prompt_data["questions"]` (string OR list).
- Long-term (recommended): update the workflow to return structured questions based on `core.models.ClarifyingQuestion` (includes `options`, `allows_multiple`, `context`).

### Clarify answers

- Short-term: continue sending `{ "answers": {"response": "..."} }` to avoid changing core workflow.
  - Convert selected options into text (e.g., `"Q: <text>\nA: <selected labels>\nOther: <free text>"`).
- Long-term: support structured answers `{ "answers": [QuestionAnswer...] }` and update core workflow to consume it.

---

## Implementation tasks (bite-sized)

### Task 1: Add a Prompt UI abstraction

**Files:**

- Create: `src/skill_fleet/cli/ui/prompts.py`
- Create: `src/skill_fleet/cli/ui/__init__.py`

**Step 1: Write failing tests**

- Create: `tests/unit/test_cli_prompt_ui.py`
- Add tests for:
  - single-choice returns selected ID
  - multi-choice returns list of IDs
  - “Other…” triggers free-text capture

**Step 2: Implement minimal PromptUI protocol**

- `PromptUI.ask_text(prompt, default="") -> str`
- `PromptUI.choose_one(prompt, choices: list[tuple[id, label]], default_id=None) -> str`
- `PromptUI.choose_many(prompt, choices, default_ids=None) -> list[str]`

**Step 3: Implement PromptToolkitUI**

- Use `prompt_toolkit.shortcuts.radiolist_dialog` / `checkboxlist_dialog`.
- Use `prompt_toolkit.shortcuts.prompt` for text input.

**Step 4: Implement RichFallbackUI**

- Use `rich.prompt.Prompt.ask` with `choices=`.

**Step 5: Run tests + commit**

---

### Task 2: Refactor HITL runner to use PromptUI

**Files:**

- Modify: `src/skill_fleet/cli/hitl/runner.py`

**Step 1: Write failing tests**

- Create: `tests/unit/test_cli_hitl_runner.py`
- Use a `FakeClient` that yields a scripted sequence of prompt payloads.
- Assert:
  - For a clarify prompt with multiple questions, the runner prompts one-at-a-time but submits a single combined response payload.
  - For confirm/preview/validate prompts, the runner submits the expected action payload.

**Step 2: Add `ui: PromptUI` parameter to `run_hitl_job(...)`**

- Default to prompt-toolkit UI with fallback.

**Step 3: Implement “clarify: one question at a time”**

- Normalize `prompt_data["questions"]` to `list[object]`:
  - If string => treat as a single prompt.
  - If list => iterate.
- For each question:
  - show rationale panel (if enabled)
  - ask using UI:
    - if options exist => arrow-key selection + “Other…”
    - else => plain text
  - collect answers locally
  - post one combined HITL response after all questions are answered
  - return to polling

**Step 4: Implement arrow-key selection for confirm/preview/validate**

- Replace `Prompt.ask(... choices=...)` with `ui.choose_one(...)`.
- Keep the existing “feedback” follow-up as plain text.

**Step 5: Run tests + commit**

---

### Task 3: Add CLI flags for thinking + input mode

**Files:**

- Modify: `src/skill_fleet/cli/commands/chat.py`

**Step 1: Add flags**

- `--show-thinking/--no-show-thinking` (default: show)
- Optional: `--force-plain-text` to disable arrow-key dialogs for remote terminals/CI.

**Step 2: Thread flags into `run_hitl_job(...)`**

**Step 3: Update docs + commit**

---

### Task 4 (optional, recommended): Upgrade the workflow to return structured questions

**Goal:** Enable true multi-choice questions generated by the model.

**Files:**

- Modify: `src/skill_fleet/core/dspy/skill_creator.py`
- Modify: `src/skill_fleet/core/dspy/modules/hitl.py` (ensure ClarifyingQuestionsModule returns options reliably)
- Modify: `src/skill_fleet/api/routes/hitl.py` (pass through structured questions)

**Steps:**

- Replace ad-hoc clarify generation (`ChainOfThought("requirements, task -> questions")`) with `ClarifyingQuestionsModule` (signature: `GenerateClarifyingQuestions`).
- Ensure the prompt payload includes `questions: list[ClarifyingQuestion]` and each question may include `options`.
- CLI can then render options with arrow keys, and still permit “Other…” free text.

---

## Documentation updates

**Files:**

- Modify: `docs/cli/interactive-chat.md`

Add:

- Arrow-key selection behavior
- “Other (type my own)” behavior
- One-question-at-a-time clarify loop
- New CLI flags

---

## Validation checklist

- `uv run ruff check src/ tests/`
- `uv run pytest -q`
- Manual smoke:
  - Start server: `uv run skill-fleet serve`
  - Run chat: `uv run skill-fleet chat`
  - Verify:
    - rationale panels appear when present
    - clarify presents one question at a time
    - arrow keys work for selection
    - “Other…” lets you type free text

---

## Rollout strategy

1. Land PromptUI + runner refactor first (no API schema changes required).
2. Then optionally upgrade the workflow to emit structured questions for best UX.
3. Keep Rich fallback forever (non-TTY support).
