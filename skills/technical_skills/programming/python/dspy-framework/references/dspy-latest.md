# DSPy Latest Snapshot (as of 2026-01-10)

## Current release
- **Latest stable release (GitHub):** 3.1.0 (released Jan 6, 2026).
- **PyPI packages:** `dspy-ai` lists 3.1.0 on Jan 6, 2026; `dspy` lists 3.0.1 on Aug 14, 2025. Verify which package name the repo uses before upgrading.

## Core concepts (canonical docs)
- **Modules:** `Predict`, `ChainOfThought`, `ProgramOfThought`, `ReAct`, `MultiChainComparison`, `majority`.
- **Signatures:** `dspy.Signature` with `InputField` and `OutputField`, plus helpers like `append`, `prepend`, and `with_instructions`.
- **Adapters:** `dspy.Adapter` is the interface between signatures/modules and LMs; built-in adapters include chat, JSON, XML, and BAML.
- **Optimizers (formerly teleprompters):** `LabeledFewShot`, `BootstrapFewShot`, `MIPROv2`, `SIMBA`, `GEPA`, `BootstrapFinetune`, plus ensembles.

## 3.x highlights worth knowing
- **3.1.0 notes:** Optimizer/eval doc updates, a MIPROv2 fix, new file type support, reasoning capture, and security guards for pickle loading.
- **3.0.0 highlights:** New/expanded adapters and types, optimizer families (GEPA/SIMBA/GRPO), MLflow 3.0 observability integration, and breaking changes (e.g., drop Python 3.9).

## Where to look for exact APIs
- Official docs: https://dspy.ai/
- Modules: https://dspy.ai/learn/programming/modules/
- Signatures: https://dspy.ai/api/signatures/Signature/
- Adapters: https://dspy.ai/api/adapters/Adapter/
- Optimizers: https://dspy.ai/learn/optimization/optimizers/
- GitHub releases: https://github.com/stanfordnlp/dspy/releases
