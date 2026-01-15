# Interactive Chat Mode

**Last Updated**: 2026-01-14
**Command**: `skill-fleet chat`

## Overview

Interactive chat mode provides a conversational interface for skill creation. Instead of a single command, you engage in a dialogue with the AI to build skills iteratively.

`★ Insight ─────────────────────────────────────`
Chat mode uses the same underlying API as the `create` command, but wraps it in a conversational loop. This allows multiple skills to be created in a single session while maintaining context and preferences.
`─────────────────────────────────────────────────`

## Starting Chat Mode

```bash
# Start chat mode (recommended from repo root)
uv run skill-fleet chat

# Start with an initial task
uv run skill-fleet chat "Create a Python async skill"

# Auto-approve mode (no HITL prompts)
uv run skill-fleet chat --auto-approve
```

## Chat Interface

```
╭─ Skill Fleet — Guided Creator ─────────╮
│ This command uses the FastAPI job +   │
│ HITL workflow.                          │
│ Commands: /help, /exit                  │
╰─────────────────────────────────────────╯

What capability would you like to build?
```

## Chat Commands

| Command   | Alias   | Description        |
| --------- | ------- | ------------------ |
| `/help`   | -       | Show help message  |
| `/exit`   | `/quit` | Exit chat mode     |
| `/cancel` | -       | Cancel current job |

## Workflow

```mermaid
stateDiagram-v2
    [*] --> Welcome: Start chat
    Welcome --> Idle
    Idle --> Creating: User enters task
    Creating --> JobCreated: API call
    JobCreated --> Polling: Poll for status
    Polling --> HITL: pending_hitl status
    HITL --> Collect: Display prompt
    Collect --> Polling: Submit response
    Polling --> Complete: completed/failed status
    Complete --> Idle: Show result
    Idle --> Prompt: "Create another?"
    Prompt --> [*]: User says no
    Prompt --> Idle: User says yes
```

## HITL Interaction Types

### 1. Clarify

The API may return clarifying questions as:

- a structured list (`[{"question": "...", "options": [...]}, ...]`), or
- a single markdown string that contains a numbered list (`"1. ...\n2. ..."`).

The CLI normalizes both formats and presents **one question at a time**.

```
╭─────────────────────────────── 🤔 Clarification Needed ───────────────────────────────╮
│ Answer the following question(s) one at a time.                                       │
╰───────────────────────────────────────────────────────────────────────────────────────╯

╭────────────────────────────── Question 1/3 ──────────────────────────────╮
│ What level of detail should this skill cover?                             │
╰──────────────────────────────────────────────────────────────────────────╯

Your answer (or /cancel):
```

**Response:** One question is shown at a time. You can answer in free-form text or `/cancel`.

If (and only if) the API returns structured `options`, the CLI can use prompt-toolkit dialogs to
select with arrow keys (and supports an **“Other (type my own)”** free-text option). If no
`options` are provided, the CLI falls back to free-text answers.

---

### 2. Confirm

```
╭─ 📋 Understanding Summary ──────────╮
│ • Skill: Python async programming    │
│ • Target: Intermediate developers     │
│ • Path: technical_skills/python/async │
╰──────────────────────────────────────╯

Proposed path: technical_skills/python/async

Proceed? (proceed/revise/cancel) [proceed]:
```

**Options:**

- `proceed` - Continue to next phase
- `revise` - Restart current phase with feedback
- `cancel` - Cancel job

Tip: In supported terminals, selection prompts use arrow keys (prompt-toolkit) instead of requiring typed input.

---

### 3. Preview

```
╭─ 📝 Content Preview ────────────────╮
│ ## Overview                          │
│ Python async/await provides...       │
│                                     │
│ ## Key Concepts                      │
│ - Coroutines                         │
│ - Event loops                        │
│ ...                                 │
╰──────────────────────────────────────╯

Highlights:
  • Clear explanations of async/await
  • Practical examples throughout
  • Common pitfalls covered

Looks good? (proceed/refine/cancel) [proceed]:
```

**Options:**

- `proceed` - Accept and continue
- `refine` - Request changes with feedback
- `cancel` - Cancel job

Tip: In supported terminals, selection prompts use arrow keys.

---

### 4. Validate

```
╭─ ✅ Validation Report ──────────────╮
│ Status: PASSED                        │
│                                     │
│ All checks passed:                   │
│ ✓ YAML frontmatter valid             │
│ ✓ Documentation complete             │
│ ✓ Examples present                   │
╰──────────────────────────────────────╯

Accept? (proceed/refine/cancel) [proceed]:
```

---

## CLI Flags

`skill-fleet chat` supports a couple of UX toggles:

- `--show-thinking/--no-show-thinking`: show or hide rationale panels (when the server provides them).
- `--force-plain-text`: disable arrow-key dialogs and fall back to plain text prompts (useful for limited terminals/CI).

You can also force plain-text prompts via environment variable:

- `SKILL_FLEET_FORCE_PLAIN_TEXT=1`

## Drafts & Promotion

Skill creation is **draft-first**:

- Drafts are written under `skills/_drafts/<job_id>/...` when the job completes.
- Promote into the taxonomy when ready:
  - `uv run skill-fleet promote <job_id>`
  - (API) `POST /api/v2/drafts/{job_id}/promote`

Until you promote, the draft will not appear in `skill-fleet list` and will not be included in generated XML.

## Known Issues (Observed Locally, 2026-01-14)

- **Rich MarkupError**: if an exception message includes markup-like tags (e.g. `[/Input Credentials/]`), Rich can raise `MarkupError` while printing the error. Workaround: `--force-plain-text` or `SKILL_FLEET_FORCE_PLAIN_TEXT=1`.
- **Job state is in-memory**: if the server restarts, the CLI may error with “job not found” while polling HITL prompts.
- **Quality “PASS with warnings”**: validation may pass but still recommend fixes (e.g., example density, plan alignment). Review the draft before promoting.

## Session Example

```bash
$ skill-fleet chat

╭─ Skill Fleet — Guided Creator ─────────╮
│ This command uses the FastAPI job +   │
│ HITL workflow.                         │
│ Commands: /help, /exit                  │
╰─────────────────────────────────────────╯

What capability would you like to build?
Create a Python decorators skill

🚀 Skill creation job started: abc-123-def

╭─ 🤔 Clarification Needed ─────────╮
│ What aspects of decorators should     │
│ this skill cover?                     │
╰──────────────────────────────────────╯

Your answers: Focus on practical examples, function decorators, and class decorators

╭─ 📋 Understanding Summary ──────────╮
│ • Skill: Python decorators             │
│ • Focus: Practical examples            │
│ • Topics: Function, class decorators   │
│ • Path: technical_skills/python/...    │
╰──────────────────────────────────────╯

Proceed? (proceed/revise/cancel) [proceed]: proceed

... (workflow continues)

✨ Skill Creation Completed!
📝 Draft saved to: skills/_drafts/<job_id>/technical_skills/python/decorators
Promote when ready: skill-fleet promote abc-123-def
If the draft failed workflow validation, promotion is blocked unless you pass `--force`.

Create another skill? (y/n) [n]: y

What capability would you like to build?
```

## Auto-Approve Mode

Skip all HITL prompts for CI/CD automation:

```bash
skill-fleet chat --auto-approve
```

In auto-approve mode:

- All clarifications use empty responses
- All confirmations auto-proceed
- All previews auto-proceed
- All validations auto-accept

## Tips and Best Practices

1. **Be Specific**: More detailed task descriptions lead to better skills
2. **Use Clarifications**: The AI will ask clarifying questions—take advantage
3. **Review Previews**: The preview checkpoint shows structure before final generation
4. **Iterate**: Use `refine` to improve skills instead of starting over
5. **Batch Creation**: Create multiple related skills in one session for consistency

## Troubleshooting

### Server Not Running

```
Could not connect to API server at http://localhost:8000
Make sure the server is running:
  uv run skill-fleet serve
```

**Solution:** Start the server in a separate terminal.

### Job Not Found (Server Restart)

If the server restarts mid-job, `skill-fleet chat` may raise an error like:

- `Job <job_id> not found. The server may have restarted and lost the job state.`

**Solution:** Re-run the request (new job) or avoid restarting the server during long-running jobs.

### Rich MarkupError

If you see `MarkupError` while printing an error message, run with:

- `uv run skill-fleet chat --force-plain-text`

or set:

- `SKILL_FLEET_FORCE_PLAIN_TEXT=1`

### Job Timeout

```
Job ended with status: failed
Error: HITL interaction timed out
```

**Solution:** Respond to prompts within 1 hour (default timeout).

### Connection Lost

```
HTTP Error: 503 Service Unavailable
```

**Solution:** Check server status and restart if needed.

## Advanced Usage

### Piping Tasks

```bash
# Create skills from a list
cat tasks.txt | while read task; do
    echo "$task" | skill-fleet chat
done
```

### Custom Prompts

```bash
# Start with pre-defined task
skill-fleet chat "Create a $LANGUAGE skill" --auto-approve
```

## See Also

- **[CLI Overview](index.md)** - Architecture and setup
- **[Commands Reference](commands.md)** - All CLI commands
- **[CLI Architecture](architecture.md)** - Internal structure
- **[HITL System](../hitl/)** - Human-in-the-Loop details
