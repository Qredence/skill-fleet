# How to Create a Skill

**Last Updated**: 2026-01-31

This guide walks through the complete skill creation workflow, from initial idea to promoted skill.

## Prerequisites

- API server running (`uv run skill-fleet serve`)
- Understanding of [skill concepts](../explanation/concepts/skill-lifecycle.md)

## Quick Start

The fastest way to create a skill:

```bash
uv run skill-fleet chat "Create a skill for [your topic]"
```

Follow the interactive prompts to complete the workflow.

---

## Step-by-Step Workflow

### Step 1: Craft a Good Task Description

A good task description includes:

- **Domain**: Technical, creative, business, etc.
- **Technology/Framework**: Specific tools or languages
- **Target Audience**: Beginner, intermediate, expert
- **Scope**: What to include and exclude

**Examples:**

```
# Good - Clear and specific
"Create a Python async/await programming skill for intermediate developers.
Cover context managers, task groups, and common patterns.
Exclude asyncio internals and low-level event loops."

# Good - Framework-specific
"Create a FastAPI production patterns skill covering dependency injection,
background tasks, and testing. Target developers with basic FastAPI knowledge."

# Vague - Needs more detail
"Create a Python skill"
```

### Step 2: Run the Creation Workflow

Interactive mode (recommended):

```bash
uv run skill-fleet chat "Your task description"
```

Non-interactive mode:

```bash
uv run skill-fleet create "Your task description" --auto-approve
```

### Step 3: Handle HITL Checkpoints

The workflow may pause for human input:

#### Clarifying Questions

If the system needs more information:

```
[system] Clarifying Questions:
1. What Python version should this target? (3.9/3.10/3.11/3.12)
2. Should this include type hints? (Yes/No)
```

Answer to continue.

#### Structure Fixes

If name or description issues are detected:

```
[system] Structure Validation Issues:
- Name contains spaces
- Description missing trigger phrases

Suggested fixes provided. Approve to continue.
```

#### Preview (Optional)

If you enabled preview mode:

```
[system] Content Preview:
[Shows generated SKILL.md]

Approve, provide feedback, or request changes?
```

### Step 4: Review the Generated Skill

After completion, find your skill:

```bash
# List recent jobs
uv run skill-fleet list --format json | jq '.[] | select(.status == "completed")'

# View the skill
ls .skills/drafts/
```

Review:
- `SKILL.md` content
- Validation report
- Generated test cases

### Step 5: Validate

Run validation manually:

```bash
uv run skill-fleet validate .skills/drafts/<skill-name> --json
```

Check for:
- Compliance score > 0.8
- No critical errors
- Trigger coverage > 0.9

### Step 6: Promote to Taxonomy

Once satisfied, promote the skill:

```bash
# Get job ID from output
uv run skill-fleet promote <job_id>

# Or with options
uv run skill-fleet promote <job_id> --delete-draft --overwrite
```

---

## Common Scenarios

### Creating a Technical Skill

```bash
uv run skill-fleet chat "Create a skill for Python decorators and context managers.
Target intermediate developers who know basic Python.
Include practical examples and common patterns."
```

### Creating a Workflow Skill

```bash
uv run skill-fleet chat "Create a CI/CD pipeline optimization skill for GitHub Actions.
Cover caching strategies, parallel jobs, and best practices."
```

### Creating an Analysis Skill

```bash
uv run skill-fleet chat "Create a code review skill for Python.
Analyze for security issues, performance bottlenecks, and style violations."
```

---

## Best Practices

### Task Description Tips

1. **Be specific about technology**
   - ❌ "Create a web framework skill"
   - ✅ "Create a FastAPI dependency injection skill"

2. **Define the audience**
   - ❌ "For developers"
   - ✅ "For backend developers familiar with Python"

3. **Set clear scope**
   - ❌ "Cover everything about Python"
   - ✅ "Cover async/await patterns. Exclude asyncio internals."

4. **Include trigger phrases**
   - Mention how users might request this skill
   - "Use when asking about...", "For when you need to..."

### Content Guidelines

1. **Use clear, actionable language**
   - "Use this skill when..." instead of "This skill helps..."

2. **Include examples**
   - Code examples for technical skills
   - Step-by-step for workflow skills

3. **Structure for scanability**
   - Use headers, bullet points, code blocks
   - Lead with the most important information

4. **Define success**
   - What should the user achieve?
   - How do they know they've succeeded?

### Validation Checklist

Before promoting, verify:

- [ ] Skill name is kebab-case (e.g., `python-async-await`)
- [ ] Description includes trigger phrases
- [ ] Content is 1000-5000 words
- [ ] Has clear "Use when..." statements
- [ ] Includes practical examples
- [ ] Validation score > 0.8
- [ ] No critical errors
- [ ] Test cases cover trigger phrases

---

## Troubleshooting

### "Job failed" Error

Check the job details:

```bash
curl http://localhost:8000/api/v1/jobs/<job_id>
```

Common causes:
- LLM API rate limiting
- Invalid task description
- Module execution error

### Poor Quality Output

If the generated skill doesn't meet expectations:

1. **Refine the task description**
   ```bash
   uv run skill-fleet create "More specific description..."
   ```

2. **Use interactive mode for feedback**
   ```bash
   uv run skill-fleet chat "Same task"  # Provide feedback at preview
   ```

3. **Manual refinement**
   ```bash
   # Edit SKILL.md directly, then revalidate
   vim .skills/drafts/<skill>/SKILL.md
   uv run skill-fleet validate .skills/drafts/<skill>
   ```

### Trigger Phrases Not Working

If the skill doesn't trigger correctly:

1. Check test case coverage:
   ```bash
   uv run skill-fleet validate <path> --json | jq '.test_cases'
   ```

2. Add more trigger phrases to description

3. Regenerate with clearer task description

---

## Advanced Options

### Custom Skill Style

```bash
# Minimal - Quick reference
uv run skill-fleet create "Task" --skill-style minimal

# Comprehensive - Detailed guide (default)
uv run skill-fleet create "Task" --skill-style comprehensive

# Navigation Hub - With subdirectories
uv run skill-fleet create "Task" --skill-style navigation_hub
```

### Skip Preview

```bash
# Faster, but no chance to review
uv run skill-fleet create "Task" --auto-approve
```

### Force Promotion

```bash
# Even if validation had issues
uv run skill-fleet promote <job_id> --force
```

---

## Examples

### Example 1: React Hooks Skill

```bash
uv run skill-fleet chat "Create a React hooks skill covering useState, useEffect,
useContext, and custom hooks. Target developers transitioning from class components.
Include common pitfalls and debugging tips."
```

### Example 2: Database Migration Skill

```bash
uv run skill-fleet chat "Create a database migration skill for Alembic with SQLAlchemy.
Cover creating migrations, auto-generation, and best practices for production."
```

### Example 3: Code Review Skill

```bash
uv run skill-fleet chat "Create a Python code review skill for security scanning.
Check for SQL injection, unsafe eval, and hardcoded secrets.
Provide specific remediation steps."
```

---

## Related Documentation

- [CLI Usage Guide](cli-usage.md) - More CLI examples
- [Validation Guide](validate-a-skill.md) - Deep dive into validation
- [Skill Lifecycle](../explanation/concepts/skill-lifecycle.md) - Understanding skill states
- [Workflow Engine](../explanation/architecture/workflow-engine.md) - How it works
