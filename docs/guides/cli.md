# CLI Guide

Last updated: 2026-01-27

This guide covers the most common `skill-fleet` CLI workflows and flags.

## Run commands with `uv run`

All Python CLI commands should be run with the `uv run` prefix to ensure the correct virtual environment:

```bash
uv run skill-fleet --help
uv run skill-fleet serve
uv run skill-fleet chat
```

## Common commands

- `uv run skill-fleet serve` — start the FastAPI server (dev)
- `uv run skill-fleet chat` — interactive chat mode (streaming/CLI)
- `uv run skill-fleet create "Task description"` — start a create job
- `uv run skill-fleet promote <job_id>` — promote a draft into taxonomy
- `uv run skill-fleet validate path/to/skill` — validate a skill
- `uv run skill-fleet migrate` — migrate skills to agentskills.io format
- `uv run skill-fleet generate-xml -o available_skills.xml` — export XML

## Interactive chat

Use `uv run skill-fleet chat` for a guided conversation that drives the three-phase workflow. Use `--auto-approve` to skip HITL prompts in automation.

Flags of note:

- `--auto-approve` — skip HITL prompts (useful for CI)
- `--show-thinking/--no-show-thinking` — enable/disable rationale panels
- `--force-plain-text` — fallback to plain-text prompts (useful in CI/minimal terminals)

## Best practices

- Use `--auto-approve` only in controlled automation.
- Always validate drafts before promoting them to the taxonomy.
- For heavy workloads, run the API server and call the v2 job endpoints instead of local blocking commands.

## See also

- `docs/guides/api.md` — API examples for the same workflows
- `docs/cli/` — original CLI reference (archived; see `docs/archive/LEGACY_README.md`)
