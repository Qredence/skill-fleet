# Skill Creator: User Guide

The **Skill Creator** is the core component of the `skill-fleet` system, responsible for generating new, taxonomy-compliant agent skills from simple task descriptions.

## 🚀 Quick Start

Use the CLI (see the [Getting Started Guide](getting-started/index.md) for a complete walkthrough):

```bash
uv run skill-fleet create-skill --task "Implement a Python FastAPI integration skill"
```

## 📚 Related Documentation

- **[Getting Started Guide](getting-started/index.md)**: Installation, CLI usage, validation, and templates
- **[Skill Creation Guidelines](skill-creation-guidelines.md)**: Comprehensive guide with interrogations, format requirements, and process workflow
- **[Overview](overview.md)**: System architecture and taxonomy design

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

| Option             | Description                                                | Default              |
| ------------------ | ---------------------------------------------------------- | -------------------- |
| `--task`           | Description of the skill to create (Required)              | -                    |
| `--user-id`        | ID of the user creating the skill                          | `default`            |
| `--max-iterations` | Maximum number of feedback loops                           | `3`                  |
| `--feedback-type`  | Interaction mode (`interactive`, `cli`, `auto`, `webhook`) | `interactive`        |
| `--auto-approve`   | Shortcut for `--feedback-type=auto`                        | `False`              |
| `--config`         | Path to the fleet configuration YAML                       | `config/config.yaml` |
| `--skills-root`    | Path to the taxonomy root directory                        | `skills`             |
| `--json`           | Output the result as JSON                                  | `False`              |

## 👥 Feedback Modes (HITL)

The system supports flexible Human-in-the-Loop configurations:

- **`interactive`** (Default): A rich, multi-round QA session where the model may ask you clarifying questions (e.g., "Should this skill focus on async or sync implementations?") before finalizing the plan.
- **`cli`**: A simple Approve/Reject prompt at the end of the process.
- **`auto`**: Fully autonomous mode. The system validates the skill itself and approves it if checks pass.
- **`webhook`**: Sends the review request to an external URL (useful for CI/CD pipelines).

## ⚙️ Configuration

The Skill Creator behavior is controlled by `config/config.yaml`.

### Model & Parameters

It uses `gemini-3-flash-preview` with specialized `thinking_level` settings for each task:

- `high`: Planning, Editing, Validation (Deep reasoning)
- `medium`: Understanding, Packaging (Balanced)
- `minimal`: Initialization (Fast skeleton generation)

## 📝 Generated Skill Format & Metadata

All skills created by the Skill Creator automatically include agentskills.io-compliant YAML frontmatter with **Scalable Discovery** fields:

```yaml
---
name: python-decorators
description: Ability to design, implement, and apply higher-order functions...
metadata:
  skill_id: technical_skills/programming/languages/python/decorators
  version: 1.0.0
  type: technical
  weight: medium
  # Scalable Discovery Fields
  category: "technical/python/core"
  keywords: ["functional-programming", "wrappers", "meta-programming"]
  scope: "Covers function and class decorators. Does NOT cover metaclasses."
  see_also: ["technical_skills/programming/python/context_managers"]
---
```

This extended metadata ensures that even as your fleet grows to 500+ skills, agents can efficiently find and distinguish between similar capabilities.

## 🔍 Troubleshooting

- **Missing API Key**: Ensure `GOOGLE_API_KEY` is set in your `.env` file.
- **Validation Failures**: Check the CLI output for specific errors in metadata or structure. The system enforces strict taxonomy standards.
- **Circular Dependencies**: The Skill Creator will prevent the creation of skills that create loops in the dependency graph.
