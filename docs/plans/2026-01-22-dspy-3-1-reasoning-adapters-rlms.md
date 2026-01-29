# DSPy 3.1.x Reasoning + Adapters Upgrade Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade Skill Fleet's DSPy integration to correctly support reasoning-model ChainOfThought via `dspy.Reasoning`, align adapter usage with DSPy 3.1.1/3.1.2 streaming + parsing behavior, and review/optionally prepare for newer DSPy modules (GEPA, RL/RLMs).

**Architecture:**
- Treat Chain-of-Thought reasoning as a first-class DSPy type (`dspy.Reasoning`) to support native reasoning-capable models (via LiteLLM `reasoning_effort` and DSPy adapter types).
- Configure and propagate DSPy adapters (`ChatAdapter`, `JSONAdapter`, `TwoStepAdapter`) explicitly via Skill Fleet config (and env overrides) so parsing/streaming is deterministic.
- Keep current Skill Fleet streaming interface stable (`thinking_content` as string), but ensure internal code can accept `dspy.Reasoning` objects.

**Tech Stack:** Python 3.12+, DSPy (>=3.1.2), LiteLLM, FastAPI SSE streaming, Typer CLI, pytest.

## References (Read First)

- `dspy.Reasoning` type source: `https://raw.githubusercontent.com/stanfordnlp/dspy/main/dspy/adapters/types/reasoning.py`
- DSPy adapters guide: `https://dspy.ai/learn/programming/adapters/`
- DSPy `StreamListener` docs (custom streamable types supported): `https://dspy.ai/api/utils/StreamListener/`
- DSPy GEPA docs: `https://dspy.ai/api/optimizers/GEPA/overview/`
- DSPy RL tutorial (RLMs / RL modules ecosystem): `https://dspy.ai/tutorials/rl_ai_program/`

## Current Repo Findings

- Dependency is currently `dspy>=3.0.4` (not pinned to 3.1.1/3.1.2) in `pyproject.toml`.
- We use `dspy.ChainOfThought(...)` widely (conversation, phase modules, optimization).
- We stream `reasoning` via `dspy.streaming.StreamListener(signature_field_name="reasoning")` in `src/skill_fleet/common/streaming.py`.
- Many signatures declare `reasoning: str = dspy.OutputField(...)` which is now incompatible with DSPy 3.1.x’s reasoning-model support (where CoT reasoning is a `dspy.Reasoning` type).
- `configure_dspy()` sets only `lm`, not adapter; streaming supports adapters, but we currently rely on DSPy default adapter selection.
- GEPA is already implemented in `src/skill_fleet/core/optimization/optimizer.py` using `dspy.GEPA`.

## Definition of Done

- ChainOfThought reasoning works with both:
  - non-reasoning models (reasoning appears as normal content), and
  - reasoning-capable models (reasoning delivered as native `reasoning_content`) without breaking CLI/API.
- CLI and FastAPI streaming still show reasoning text.
- No serialization/type errors when `Prediction.reasoning` is a `dspy.Reasoning`.
- Adapter selection is explicit and tested (default remains backward compatible).

---

### Task 1: Pin DSPy to 3.1.x and validate runtime

**Files:**
- Modify: `pyproject.toml`

**Step 1: Write failing test**

Create: `tests/unit/test_dspy_version_guard.py`

```python
import dspy


def test_dspy_version_is_3_1_plus():
    # DSPy 3.1.x introduces dspy.Reasoning type behavior used by our integration.
    assert hasattr(dspy, "Reasoning"), "DSPy >= 3.1.1 required (missing dspy.Reasoning)"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_dspy_version_guard.py -v`
Expected: FAIL if local env is still on DSPy < 3.1.1.

**Step 3: Minimal implementation**

Update `pyproject.toml` dependency from:

`"dspy>=3.0.4",`

to:

`"dspy>=3.1.2,<4",`

**Step 4: Sync environment**

Run: `uv sync --group dev`
Expected: installs DSPy 3.1.2 (or newer 3.1.x) satisfying constraint.

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_dspy_version_guard.py -v`
Expected: PASS

---

### Task 2: Introduce a safe coercion utility for `dspy.Reasoning`

**Files:**
- Create: `src/skill_fleet/common/dspy_compat.py`
- Test: `tests/unit/test_dspy_reasoning_compat.py`

**Step 1: Write failing test**

```python
import dspy

from skill_fleet.common.dspy_compat import coerce_reasoning_text


def test_coerce_reasoning_text_handles_none():
    assert coerce_reasoning_text(None) == ""


def test_coerce_reasoning_text_handles_str():
    assert coerce_reasoning_text(" hi ") == "hi"


def test_coerce_reasoning_text_handles_dspy_reasoning():
    r = dspy.Reasoning(content=" hello ")
    assert coerce_reasoning_text(r) == "hello"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_dspy_reasoning_compat.py -v`
Expected: FAIL (module missing)

**Step 3: Minimal implementation**

Implement `coerce_reasoning_text(value) -> str`:
- if value is `None` -> `""`
- if value is `dspy.Reasoning` -> `value.content`
- else -> `str(value)`
- always `.strip()`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_dspy_reasoning_compat.py -v`
Expected: PASS

---

### Task 3: Update signatures to use `dspy.Reasoning` where appropriate

**Files:**
- Modify: `src/skill_fleet/core/dspy/signatures/chat.py`
- Modify: `src/skill_fleet/core/dspy/signatures/hitl.py`
- Modify: `src/skill_fleet/core/dspy/signatures/signature_tuning.py`

**Notes:**
- Only fields that represent ChainOfThought reasoning streams should use `dspy.Reasoning`.
- Fields like `readiness_reasoning` are NOT chain-of-thought; keep them as `str`.

**Step 1: Write failing test**

Create: `tests/unit/test_signature_reasoning_types.py`

```python
import dspy

from skill_fleet.core.dspy.signatures.chat import DeepUnderstandingSignature


def test_reasoning_field_type_is_dspy_reasoning():
    # We depend on DSPy 3.1.x Reasoning behavior for native reasoning models.
    assert DeepUnderstandingSignature.model_fields["reasoning"].annotation is dspy.Reasoning
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_signature_reasoning_types.py -v`
Expected: FAIL (currently `str`)

**Step 3: Minimal implementation**

Change in signatures:
- `reasoning: str = dspy.OutputField(...)`
to
- `reasoning: dspy.Reasoning = dspy.OutputField(...)`

Update the `desc` to mention:
- reasoning may be a `dspy.Reasoning` object; callers should use `str(reasoning)` or `reasoning.content`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_signature_reasoning_types.py -v`
Expected: PASS

---

### Task 4: Harden module code paths that call `.strip()` on `reasoning`

**Files:**
- Modify: `src/skill_fleet/core/dspy/modules/conversation/*.py`
- Modify: `src/skill_fleet/core/dspy/modules/*.py` (wherever `getattr(result, "reasoning", "").strip()` exists)
- Modify: `src/skill_fleet/core/services/conversation/engine.py` (streamed thinking collection)

**Step 1: Write failing test**

Create: `tests/unit/test_reasoning_field_runtime.py`

```python
import dspy

from skill_fleet.common.dspy_compat import coerce_reasoning_text


def test_existing_strip_calls_can_be_replaced_safely():
    r = dspy.Reasoning(content=" hello ")
    assert coerce_reasoning_text(r) == "hello"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_reasoning_field_runtime.py -v`
Expected: FAIL until compat is used in modules

**Step 3: Minimal implementation**

Replace patterns like:

`getattr(result, "reasoning", "").strip()`

with:

`coerce_reasoning_text(getattr(result, "reasoning", ""))`

In modules that store reasoning in dicts for JSON, ensure it is coerced to string first.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_reasoning_field_runtime.py -v`
Expected: PASS

---

### Task 5: Explicit adapter configuration in Skill Fleet

**Files:**
- Modify: `src/skill_fleet/llm/dspy_config.py`
- Modify: `config/config.yaml` (and `src/skill_fleet/config/` packaged copy, via sync script)
- Test: `tests/unit/test_dspy_adapter_config.py`

**Goal:** Allow selecting adapter globally (and optionally per-task) so that:
- Parsing is more reliable (JSONAdapter for structured outputs)
- Streaming works with either ChatAdapter or JSONAdapter (StreamListener supports both)

**Step 1: Write failing test**

```python
import dspy

from skill_fleet.llm.dspy_config import configure_dspy


def test_configure_dspy_sets_adapter(tmp_path, monkeypatch):
    # Provide a minimal config that specifies adapter=json.
    # This test should validate dspy.settings.adapter is set.
    pass
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_dspy_adapter_config.py -v`
Expected: FAIL

**Step 3: Minimal implementation**

Implement adapter selection in `configure_dspy()`:
- Determine adapter from config (e.g., `dspy.adapter: chat|json|two_step`) or env override.
- Call `dspy.configure(lm=lm, adapter=adapter_instance)`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_dspy_adapter_config.py -v`
Expected: PASS

---

### Task 6: Make streaming robust across adapters and Reasoning models

**Files:**
- Modify: `src/skill_fleet/common/streaming.py`
- Test: `tests/unit/test_streaming_reasoning_type.py`

**Goal:** Ensure our streaming collection still works when:
- adapter is JSONAdapter (different field delimiters)
- reasoning is native `reasoning_content` (Reasoning type parse_stream_chunk)

**Step 1: Write failing test**

The easiest unit test is to validate we build stream listeners for the reasoning field and do not
assume it is plain text elsewhere.

```python
import dspy

from skill_fleet.common.streaming import create_streaming_module


def test_create_streaming_module_accepts_reasoning_field():
    module = dspy.ChainOfThought("question -> answer")
    stream_module = create_streaming_module(module, reasoning_field="reasoning", async_mode=False)
    assert stream_module is not None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_streaming_reasoning_type.py -v`
Expected: FAIL only if our wrapper breaks due to adapter/type assumptions.

**Step 3: Minimal implementation**

If failures occur:
- Avoid hardcoding assumptions about adapter markers.
- Ensure `StreamListener` remains configured by field name ("reasoning") and let DSPy handle type streaming.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_streaming_reasoning_type.py -v`
Expected: PASS

---

### Task 7: Validate GEPA integration against DSPy 3.1.x APIs

**Files:**
- Modify (if needed): `src/skill_fleet/core/optimization/optimizer.py`
- Test: `tests/unit/test_gepa_smoke.py`

**Goal:** Confirm our usage of `dspy.GEPA(...)` remains aligned with the official constructor signature
and that we pass a strong reflection LM (and adapter choices do not break compilation).

**Step 1: Write failing test**

Smoke-test object creation only (no network calls):

```python
import dspy


def test_gepa_class_exists():
    assert hasattr(dspy, "GEPA")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_gepa_smoke.py -v`
Expected: FAIL on older DSPy

**Step 3: Minimal implementation**

This should pass after Task 1.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_gepa_smoke.py -v`
Expected: PASS

---

### Task 8: RLMs / RL modules (optional, gated)

**Goal:** Prepare for DSPy’s RL ecosystem (“RLMs module”) without forcing new heavy dependencies.

**Approach:**
- Add an optional dependency group `rl` (e.g., `arbor`) only if we commit to supporting RL optimizers.
- Add a feature flag in config (e.g., `optimization.enable_rl: true|false`).
- If enabled and deps available, expose new optimizer option in CLI/API; otherwise hide.

**Files:**
- Modify: `pyproject.toml` (optional-dependencies `rl = [...]`)
- Modify: `src/skill_fleet/core/dspy/optimization/selector.py` (add capability detection)
- Docs: `docs/llm/dspy-rl.md`

**Testing:**
- Unit test should verify the feature flag defaults to off and RL code is not imported unless enabled.

---

## Final Verification

Run:

- `uv run pytest tests/unit -v`
- `uv run skill-fleet serve` and verify `/api/v1/chat/stream` still streams reasoning
- `uv run skill-fleet chat "Create a skill for ..."` and verify it progresses through Deep Understanding -> Confirmation -> Creation
