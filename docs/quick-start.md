# Quick Start Guide

Get up and running with the skills-fleet system in minutes.

## Prerequisites

- **Python**: 3.12 or higher
- **uv**: Python package manager ([install](https://github.com/astral-sh/uv))
- **Bun**: For TUI components (optional, [install](https://bun.sh/))
- **Google API Key**: For skill generation

## Installation

### 1. Clone the Repository

```bash
git clone <repo-url>
cd skills-fleet
```

### 2. Install Python Dependencies

```bash
uv sync --group dev
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
# Required
GOOGLE_API_KEY="your_google_api_key_here"

# Optional
DEEPINFRA_API_KEY="your_deepinfra_key"
LITELLM_API_KEY="your_litellm_key"
LANGFUSE_SECRET_KEY="your_langfuse_key"
```

### 4. Verify Installation

```bash
uv run skills-fleet --help
```

You should see the CLI help output.

## Your First Skill

Let's create a simple skill to get familiar with the workflow.

### Create a Skill

```bash
uv run skills-fleet create-skill --task "Create a Python logging utilities skill"
```

The system will:
1. **Understand** the task and determine taxonomy placement
2. **Plan** metadata, dependencies, and capabilities
3. **Initialize** the directory structure
4. **Edit** the SKILL.md with frontmatter and content
5. **Package** and validate the skill
6. **Iterate** and ask for your approval

### Review the Skill

During the HITL (Human-in-the-Loop) phase, you'll see:
```
Review Generated Skill
======================

Skill ID: technical_skills/programming/languages/python/logging
Name: python-logging
Type: technical
Weight: lightweight

Capabilities:
- Basic logger setup
- Custom handlers and formatters
- Log level management

[Approve/Revise/Reject]? 
```

Type `approve` to continue.

### Validate the Skill

```bash
uv run skills-fleet validate-skill src/agentic_fleet/agentic_skills_system/skills/technical_skills/programming/languages/python/logging
```

You should see validation pass with checks for:
- ✅ Metadata structure
- ✅ YAML frontmatter (agentskills.io compliance)
- ✅ Directory structure
- ✅ Documentation completeness

## Working with Existing Skills

### Migrate to agentskills.io Format

If you have existing skills without YAML frontmatter:

```bash
# Preview what will change
uv run skills-fleet migrate --dry-run

# Apply migration
uv run skills-fleet migrate
```

### Generate Skill Catalog

Create an XML catalog of available skills:

```bash
uv run skills-fleet generate-xml -o available_skills.xml
```

This generates agentskills.io-compliant XML that can be injected into agent prompts.

### Validate All Skills

```bash
# Find all skills and validate them
find src/agentic_fleet/agentic_skills_system/skills -name "metadata.json" | while read meta; do
  uv run skills-fleet validate-skill "$(dirname "$meta")"
done
```

## Understanding Skill Structure

A typical skill directory looks like this:

```
python-logging/
├── metadata.json          # Internal metadata
├── SKILL.md              # Main documentation with YAML frontmatter
├── capabilities/         # Detailed capability docs
│   ├── basic_setup.md
│   └── custom_handlers.md
├── examples/             # Usage examples
│   ├── example_1.md
│   └── example_2.md
├── tests/               # Test files
│   └── test_logging.py
└── resources/           # Additional resources
    └── config_template.yaml
```

### SKILL.md Format

```markdown
---
name: python-logging
description: Utilities for setting up and managing Python logging with custom handlers and formatters.
metadata:
  skill_id: technical_skills/programming/languages/python/logging
  version: 1.0.0
  type: technical
  weight: lightweight
---

# Python Logging Utilities

## Overview
This skill provides comprehensive Python logging capabilities...

## Capabilities
...
```

## Common Tasks

### Auto-Approve Skills (for CI/CD)

```bash
uv run skills-fleet create-skill \
  --task "Create data validation utilities" \
  --auto-approve
```

### JSON Output (for Scripting)

```bash
# Create skill and capture result
result=$(uv run skills-fleet create-skill \
  --task "Create API client utilities" \
  --auto-approve \
  --json)

# Parse with jq
echo "$result" | jq '.status'
```

### Custom User Context

```bash
uv run skills-fleet create-skill \
  --task "Create team-specific conventions" \
  --user-id team_backend
```

## Next Steps

### Explore the Documentation

- **[Overview](overview.md)**: Understand the system architecture
- **[CLI Reference](cli-reference.md)**: Complete command reference
- **[Skill Creator Guide](skill-creator-guide.md)**: Deep dive into skill creation
- **[agentskills.io Compliance](agentskills-compliance.md)**: Learn about standardization

### Try Advanced Features

#### User Onboarding
```bash
uv run skills-fleet onboard --user-id developer_123
```

Create a personalized skill profile based on your role and preferences.

#### Analytics
```bash
uv run skills-fleet analytics --user-id developer_123
```

View usage patterns and skill recommendations.

#### Interactive TUI (Optional)
```bash
# Install TUI dependencies
bun install

# Launch interactive interface
bun run tui
```

## Troubleshooting

### "Missing API Key" Error

Ensure `GOOGLE_API_KEY` is set in your `.env` file:
```bash
echo "GOOGLE_API_KEY=your_key_here" >> .env
```

### Validation Failures

Common issues:
- **Missing frontmatter**: Run `uv run skills-fleet migrate`
- **Invalid metadata**: Check `metadata.json` syntax
- **Missing directories**: Ensure `capabilities/`, `examples/`, `tests/`, `resources/` exist

### Skill Creation Hangs

The DSPy workflow may take 30-60 seconds for complex skills. Check:
- Network connectivity
- API rate limits
- System resources

### Permission Errors

Ensure you have write permissions:
```bash
chmod -R u+w src/agentic_fleet/agentic_skills_system/skills
```

## Configuration

### Customize LLM Settings

Edit `src/agentic_fleet/config.yaml`:

```yaml
llm:
  provider: google
  model: gemini-3-flash-preview
  temperature: 0.7
  thinking_level:
    planning: high
    understanding: medium
    initialization: minimal
```

### Environment Variables

```bash
# LLM Configuration
export GOOGLE_API_KEY="..."
export DSPY_TEMPERATURE="0.7"
export DSPY_CACHEDIR="/path/to/cache"

# Logging
export LOG_LEVEL="DEBUG"  # DEBUG, INFO, WARNING, ERROR

# Development
export SKIP_VALIDATION="false"
```

## Best Practices

### 1. Start Small
Create lightweight skills first to understand the workflow.

### 2. Use Descriptive Task Descriptions
```bash
# Good
--task "Create utilities for validating email addresses with regex patterns"

# Less effective
--task "email stuff"
```

### 3. Review Generated Content
Don't blindly approve. Check that:
- Capabilities match your needs
- Examples are relevant
- Documentation is clear

### 4. Validate Early and Often
Run validation after any manual edits:
```bash
uv run skills-fleet validate-skill path/to/skill
```

### 5. Keep Skills Focused
Each skill should have 3-7 capabilities. If you need more, split into multiple skills.

### 6. Use Dependencies Wisely
Reference other skills to avoid duplication:
```json
{
  "dependencies": ["technical_skills/programming/languages/python"]
}
```

### 7. Maintain Compliance
After manual edits, ensure agentskills.io compliance:
```bash
uv run skills-fleet migrate  # Re-run to fix frontmatter
uv run skills-fleet validate-skill path/to/skill
```

## Getting Help

### CLI Help
```bash
uv run skills-fleet --help
uv run skills-fleet create-skill --help
```

### Documentation
- [Full documentation](../README.md#-documentation)
- [CLI Reference](cli-reference.md)

### Community
- GitHub Issues: Report bugs or request features
- Discussions: Ask questions and share experiences

## Example Workflow

Complete workflow from creation to validation:

```bash
# 1. Create skill
uv run skills-fleet create-skill --task "Create REST API client utilities"
# ... follow HITL prompts, approve when satisfied ...

# 2. Validate
uv run skills-fleet validate-skill src/agentic_fleet/agentic_skills_system/skills/technical_skills/programming/api_clients/rest

# 3. Generate XML catalog
uv run skills-fleet generate-xml -o available_skills.xml

# 4. Verify XML contains new skill
grep "rest-api-client" available_skills.xml

# 5. (Optional) Create related skill with dependency
uv run skills-fleet create-skill --task "Create GraphQL API client utilities"
```

## Ready to Build?

You're now ready to create and manage skills! Start with simple skills and gradually explore advanced features.

**Suggested first projects:**
1. Create a skill for your primary programming language
2. Migrate any existing skill documentation
3. Generate an XML catalog for your agents
4. Set up automated validation in your CI/CD pipeline

Happy skill building! 🚀
