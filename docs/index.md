# Skills Fleet Documentation

Welcome to the Skills Fleet documentation hub. This index provides quick access to all documentation for the agentic capability platform.

```markdown
# Skills Fleet Documentation

Version: Post-FastAPI-Centric Restructure
Last updated: 2026-01-27

This hub focuses on concise, role-oriented guides. The canonical, consolidated guides live under `docs/guides/` and deep technical references under `docs/reference/`.

## Quick start

- Getting started (installation & first skill): `docs/getting-started/index.md`
- API (production): `docs/guides/api.md`
- CLI quick reference: `docs/guides/cli.md`
- Workflows & HITL: `docs/guides/workflows.md`, `docs/guides/hitl.md`
- DSPy & optimization: `docs/guides/dspy.md` and `docs/dspy/`

## Navigate by role

### For users

- `docs/getting-started/index.md` — set up, create and promote skills
- `docs/guides/cli.md` — common commands and interactive chat
- `docs/guides/api.md` — programmatic workflows (v2 production API)

### For integrators / CI

- Use the v2 job endpoints (`/api/v2`) for reliable, async integrations
- Export XML: `uv run skill-fleet generate-xml -o available_skills.xml`

### For developers

- Architecture: `docs/architecture/`
- Contributor setup & guides: `docs/development/CONTRIBUTING.md`
- DSPy internals: `docs/dspy/`

## Legacy & detailed references

If you need detailed endpoint references or historical docs, see the legacy folder:

- `docs/archive/LEGACY_README.md` — pointers to archived docs
- Detailed API endpoints & schemas: `docs/api/` (kept for reference)

## Restructuring plan

Full restructuring rationale and implementation plan: `docs/DOCUMENTATION_RESTRUCTURING_PLAN.md`

If something you expect to find is missing, tell me which page and I will merge it into the appropriate consolidated guide.
```

- Detailed API endpoints & schemas: `docs/api/` (kept for reference)
