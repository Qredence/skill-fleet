# Skill Creator: User Guide

The **Skill Creator** is the core component of the `skills-fleet` system, responsible for generating new, taxonomy-compliant agent skills from simple task descriptions.

## 🚀 Quick Start

To create a new skill, use the CLI:

```bash
uv run skills-fleet create-skill --task "Implement a Python FastAPI integration skill"
```

## 🧠 Workflow Steps

The Skill Creator follows a modular 6-step workflow, powered by DSPy and Gemini 3:

1.  **Understand**: Analyzes the task and determines the correct position in the hierarchical taxonomy.
2.  **Plan**: Defines the skill's metadata, required dependencies, and discrete capabilities.
3.  **Initialize**: Generates the on-disk directory structure and template files.
4.  **Edit**: Generates the full `SKILL.md` documentation with agentskills.io-compliant YAML frontmatter and detailed capability implementations.
5.  **Package**: Validates the generated skill against system standards (including agentskills.io compliance) and creates a manifest.
6.  **Iterate**: Manages Human-in-the-Loop (HITL) feedback and revisions.

All generated skills are automatically compliant with the [agentskills.io](https://agentskills.io) specification, including kebab-case naming and YAML frontmatter.

## 🛠 CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--task` | Description of the skill to create (Required) | - |
| `--user-id` | ID of the user creating the skill | `default` |
| `--max-iterations` | Maximum number of feedback loops | `3` |
| `--auto-approve` | Skip interactive review and auto-approve if validation passes | `False` |
| `--config` | Path to the fleet configuration YAML | `src/agentic_fleet/config.yaml` |
| `--skills-root` | Path to the taxonomy root directory | `src/agentic_fleet/agentic_skills_system/skills` |
| `--json` | Output the result as JSON | `False` |

## 👥 Human-in-the-Loop (HITL)

By default, the Skill Creator pauses after Step 5 to ask for human feedback. You can review the generated plan and content, then choose to:

*   **Approve**: The skill is registered in the taxonomy.
*   **Request Revision**: Provide feedback for the model to improve the skill content.
*   **Reject**: Discard the skill.

To bypass this for automated workflows, use the `--auto-approve` flag.

## ⚙️ Configuration

The Skill Creator behavior is controlled by `src/agentic_fleet/config.yaml`. 

### Model & Parameters
It uses `gemini-3-flash-preview` with specialized `thinking_level` settings for each task:

*   `high`: Planning, Editing, Validation (Deep reasoning)
*   `medium`: Understanding, Packaging (Balanced)
*   `minimal`: Initialization (Fast skeleton generation)

### Feedback Handlers
The system supports multiple feedback handlers defined in `src/agentic_fleet/agentic_skills_system/workflow/feedback.py`:

*   **CLI Handler**: (Default) Interactive prompts in your terminal.
*   **Auto Handler**: Used when `--auto-approve` is passed.
*   **Webhook Handler**: (Advanced) Can be configured to send review requests to external systems.

## 🐍 Python API

You can also use the Skill Creator directly in your Python code:

```python
from pathlib import Path
from agentic_fleet.agentic_skills_system.taxonomy.manager import TaxonomyManager
from agentic_fleet.agentic_skills_system.workflow.skill_creator import TaxonomySkillCreator

# Initialize
taxonomy = TaxonomyManager(Path("src/agentic_fleet/agentic_skills_system/skills"))
creator = TaxonomySkillCreator(taxonomy_manager=taxonomy)

# Create a skill
result = creator.create_skill(
    task_description="Create a data processing skill",
    user_context={"user_id": "agent_01"},
    max_iterations=2
)

if result["status"] == "approved":
    print(f"Skill created at: {result['path']}")
```

## 🔍 Troubleshooting

*   **Missing API Key**: Ensure `GOOGLE_API_KEY` is set in your `.env` file.
*   **Validation Failures**: Check the CLI output for specific errors in metadata or structure. The system enforces strict taxonomy standards.
*   **Circular Dependencies**: The Skill Creator will prevent the creation of skills that create loops in the dependency graph.

## 📝 Generated Skill Format

All skills created by the Skill Creator automatically include agentskills.io-compliant YAML frontmatter:

```yaml
---
name: python-decorators
description: Ability to design, implement, and apply higher-order functions to extend or modify the behavior of functions and classes in Python.
metadata:
  skill_id: technical_skills/programming/languages/python/decorators
  version: 1.0.0
  type: technical
  weight: medium
---
```

This frontmatter enables:
- **Discoverability**: Skills can be found via XML generation
- **Validation**: Automated compliance checking
- **Interoperability**: Skills work with other agentskills.io-compliant systems
- **Standardization**: Consistent format across all skills

For more details, see the [agentskills.io Compliance Guide](agentskills-compliance.md).
