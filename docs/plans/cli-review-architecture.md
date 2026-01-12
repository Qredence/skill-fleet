# CLI Architecture Analysis

## Two CLI Implementations Identified

### main.py (argparse-based)
- Entry point: `cli_entrypoint()`
- Commands: create-skill, validate-skill, onboard, analytics, migrate, generate-xml, optimize, interactive
- Lines: 676

### app.py (Typer-based)
- Entry point: `app()` (not currently registered in pyproject.toml)
- Commands: create, list, serve, chat
- Lines: 65

## Issues to Address
1. Dual CLI implementations create confusion
2. Different command naming conventions (kebab-case vs lowercase)
3. app.py commands duplicate main.py functionality
4. No migration plan from argparse to Typer documented
