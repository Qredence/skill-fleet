---
name: dspy-framework
description: Expert guidance for using the DSPy framework to design, optimize, debug, and refactor LLM programs. This skill should be used when asked to use DSPy, when a task involves DSPy components, when changing code that impacts a DSPy implementation, or when analyzing a codebase for DSPy opportunities.
---

# DSPy Framework

## Quick workflow
1. Confirm DSPy scope: identify modules, signatures, optimizers, adapters, datasets, and evaluation flows involved.
2. Check project conventions: locate any DSPy configuration helpers and follow existing patterns before introducing new ones.
3. Use the latest DSPy capabilities: read `references/dspy-latest.md` when you need version-specific APIs, new features, or naming details.
4. Implement the smallest change that preserves program semantics, then validate with existing tests or evaluation routines.

## Guardrails
- Prefer stable, documented DSPy APIs; avoid private or internal attributes unless the repo already relies on them.
- Keep signatures explicit and versioned in code to reduce silent behavior changes.
- When optimizing, capture baseline metrics first; compare before and after.
- If the task is not DSPy-specific, avoid forcing DSPy into the solution.

## Editing guidance
- Update or add DSPy modules in the smallest coherent units (signature, module, optimizer).
- If you introduce a new optimizer or adapter, document rationale and expected benefit in code comments or project docs.
- When changing prompt or signature fields, update downstream evaluation or validation steps.

## Bundled resources
- **Scripts:** Use only when DSPy-related code must be deterministic or frequently repeated. Example: `scripts/check_dspy_version.py` for verifying installed DSPy package/version. Benefits: token efficient, deterministic, executable without loading into context. Note: scripts may still need to be read for patching or environment-specific adjustments.
- **References:** Use `references/dspy-latest.md` to verify current release info and official API docs before making version-sensitive changes.
- **Assets:** None included for this skill. Add only if DSPy-related templates or artifacts become necessary.

## References
- For latest DSPy version, core APIs, and recent changes, read `references/dspy-latest.md`.
