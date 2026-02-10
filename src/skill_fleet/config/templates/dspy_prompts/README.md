# DSPy Prompt Templates

This directory contains prompt templates optimized for DSPy-based skill generation workflows.

## Purpose

Unlike Handlebars-style templates (`SKILL_md_template.md`), these prompts are designed to work with DSPy's signature-based programming model. They provide:

- Clear input/output field markers for DSPy signatures
- Structure guidance without rigid templating syntax
- Context for anti-patterns and best practices
- Flexible hints for various skill sizes and styles

## Usage

### In DSPy Modules

Reference these prompts in module docstrings or as context hints:

```python
class GenerateSkillContent(dspy.Module):
    """
    Generate skill content following agentskills.io specifications.

    See: config/templates/dspy_prompts/skill_generation_prompt.txt
    """
    def __init__(self):
        super().__init__()
        self.generator = dspy.ChainOfThought(SkillGenerationSignature)
```

### As Context Files

Load prompts programmatically for few-shot examples:

```python
from pathlib import Path

prompt_path = Path(__file__).parent / "config/templates/dspy_prompts/skill_generation_prompt.txt"
guidance = prompt_path.read_text()

# Use in DSPy context
signature = SkillGenerationSignature.with_instructions(guidance)
```

## Templates

- `skill_generation_prompt.txt` - Core skill content generation guidance
- `skill_validation_prompt.txt` (future) - Validation criteria
- `skill_refinement_prompt.txt` (future) - Iterative refinement hints

## Design Principles

1. **DSPy-Native**: Use input/output field markers, not template variables
2. **Flexible**: Provide guidance, not rigid structure
3. **Example-Rich**: Include diverse examples (minimal, comprehensive, tool-based)
4. **Anti-Pattern Aware**: Explicitly warn against common pitfalls
5. **Size-Conscious**: Optimize for concise, high-density content

## Maintenance

When updating prompts:

1. Test with actual DSPy modules (not just validation)
2. Verify across different skill sizes (50-3000 words)
3. Check compatibility with optimization (MIPROv2, BootstrapFewShot)
4. Update module docstrings to reference changes
