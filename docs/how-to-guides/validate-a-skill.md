# How to Validate a Skill

**Last Updated**: 2026-01-31

This guide covers validating skills for quality, compliance, and trigger effectiveness.

## Quick Validation

```bash
uv run skill-fleet validate path/to/skill
```

Output:
```
validation: passed
warnings:
- Description could be more specific
```

## Understanding Validation

The validation workflow checks four dimensions:

1. **Structure** - Name, description, security
2. **Compliance** - agentskills.io format requirements
3. **Quality** - Completeness, clarity, size
4. **Trigger Coverage** - Test case effectiveness

## Running Validation

### Basic Validation

```bash
# By path
uv run skill-fleet validate technical/programming/python/async

# By draft directory
uv run skill-fleet validate .skills/drafts/python-async
```

### JSON Output

For scripting and automation:

```bash
uv run skill-fleet validate path/to/skill --json
```

Output:
```json
{
  "passed": true,
  "score": 0.92,
  "errors": [],
  "warnings": [
    "Description could be more specific"
  ],
  "checks_performed": [
    "structure_validation",
    "agentskills.io_compliance",
    "quality_assessment"
  ],
  "structure_valid": true,
  "word_count": 2500,
  "size_assessment": "optimal",
  "verbosity_score": 0.3,
  "trigger_coverage": 0.95
}
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Validation passed |
| 2 | Validation failed |

Use in scripts:
```bash
if uv run skill-fleet validate "$SKILL_PATH" --json | jq -e '.passed'; then
    echo "✅ Valid"
else
    echo "❌ Failed"
fi
```

## Validation Dimensions

### Structure Validation

Checks:
- Kebab-case name (e.g., `python-async`, not `PythonAsync`)
- Description length (50-2000 characters)
- Trigger phrases present ("Use when...", "For when...")
- No reserved names ("claude", "anthropic")
- No XML tags in frontmatter

**Fixing Structure Issues:**

```bash
# Check specific issues
uv run skill-fleet validate path/to/skill --json | jq '.name_errors, .description_errors'
```

Common fixes:
- Rename skill to kebab-case
- Add trigger phrases to description
- Remove XML-like content from frontmatter

### Compliance Validation

Checks agentskills.io format:
- Valid YAML frontmatter
- Required fields (id, name, description)
- Proper markdown structure
- Required sections for category

**Category Requirements:**

| Category | Required Sections |
|----------|-------------------|
| document_creation | Output Format, Examples |
| workflow_automation | Workflow Steps, Input/Output |
| mcp_enhancement | MCP Tools Used, Tool Sequences |
| analysis | Analysis Approach, Output Format |

### Quality Assessment

Metrics:

| Metric | Target | Description |
|--------|--------|-------------|
| overall_score | ≥0.75 | Aggregate quality score |
| completeness | High | Coverage of requirements |
| clarity | High | Readability and structure |
| word_count | <5000 | Size limit |
| verbosity_score | <0.5 | Conciseness (0=concise, 1=verbose) |

**Improving Quality:**

```bash
# Check quality details
uv run skill-fleet validate path/to/skill --json | jq '.quality_score, .word_count, .verbosity_score'
```

Tips:
- Add more examples if completeness is low
- Use bullet points for clarity
- Remove filler phrases for conciseness
- Move detailed content to references/

### Trigger Coverage

Validates that the skill triggers correctly:

- **Positive tests** - Queries that SHOULD trigger
- **Negative tests** - Queries that should NOT trigger
- **Edge cases** - Ambiguous queries for review

**Coverage Target:** ≥90%

```bash
# Check coverage
uv run skill-fleet validate path/to/skill --json | jq '.trigger_coverage, .test_cases'
```

**Improving Coverage:**

1. Add more trigger phrases to description
2. Include paraphrased variations
3. Define negative triggers clearly
4. Add examples of when NOT to use

## Validation Workflows

### Pre-Promotion Validation

Always validate before promoting:

```bash
#!/bin/bash
SKILL_PATH="$1"
JOB_ID="$2"

if uv run skill-fleet validate "$SKILL_PATH" --json | jq -e '.passed'; then
    uv run skill-fleet promote "$JOB_ID"
    echo "✅ Promoted successfully"
else
    echo "❌ Validation failed. Fix issues before promoting."
    exit 1
fi
```

### CI/CD Integration

```yaml
# .github/workflows/validate-skills.yml
name: Validate Skills

on: [push]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Validate all skills
        run: |
          for skill in skills/*; do
            echo "Validating $skill..."
            uv run skill-fleet validate "$skill" --json | jq -e '.passed' || exit 1
          done
```

### Batch Validation

```bash
# Validate all drafts
for draft in .skills/drafts/*/; do
    echo "Validating $draft..."
    uv run skill-fleet validate "$draft" --json | jq '{path: input_filename, passed: .passed, score: .score}'
done
```

## Fixing Common Issues

### Issue: "Name not kebab-case"

```bash
# Before: PythonAsyncAwait
# After: python-async-await

mv skills/PythonAsyncAwait skills/python-async-await
```

### Issue: "Description too short"

Edit SKILL.md:
```yaml
---
description: |
  Use when you need to create Python async/await code.
  Covers context managers, task groups, and error handling.
  For intermediate Python developers.
---
```

### Issue: "Missing trigger phrases"

Add to description:
```yaml
description: |
  Use when you need to create Python async/await code.
  Helps when: building async APIs, handling concurrent tasks,
  or migrating from synchronous code.
```

### Issue: "Verbosity too high"

Remove filler phrases:
- ❌ "It is important to note that..."
- ❌ "In order to..."
- ❌ "Due to the fact that..."
- ✅ Direct, actionable language

### Issue: "Trigger coverage low"

Add more trigger variations:
```yaml
trigger_patterns:
  - "create async"
  - "python async"
  - "async await patterns"
  - "concurrent python"
```

## Advanced Validation

### Custom Thresholds

```bash
# Lower quality threshold (not recommended)
uv run skill-fleet create "Task" --quality-threshold 0.6
```

### Auto-Fix Issues

Some issues can be auto-fixed:

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/quality/fix \
  -H "Content-Type: application/json" \
  -d '{
    "content": "...",
    "issues": ["missing_examples"]
  }'
```

### Manual Review

For skills that fail validation:

1. Review the validation report
2. Check the specific errors
3. Edit SKILL.md directly
4. Re-run validation
5. Iterate until passing

## Related Documentation

- [Create a Skill](create-a-skill.md) - Full creation workflow
- [Promote a Draft](promote-a-draft.md) - After validation
- [API Reference](../reference/api/endpoints.md) - Validation endpoints
