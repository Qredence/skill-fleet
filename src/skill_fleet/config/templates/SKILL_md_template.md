---
name: {{skill_name_kebab}}
description: {{description}}
metadata:
  skill_id: {{skill_id}}
  version: {{version}}
  type: {{type}}
  weight: {{weight}}
---

# {{skill_name}}

## Overview

{{overview_description}}

## Capabilities

{{#each capabilities}}
### {{name}}

{{description}}

**Usage:**
```
{{usage_example}}
```
{{/each}}

## Dependencies

{{#if dependencies}}
This skill requires the following skills to be mounted:
{{#each dependencies}}
- `{{this}}` - {{reason}}
{{/each}}
{{else}}
No dependencies - this skill is self-contained.
{{/if}}

## Usage Examples

### Example 1: {{example_1_title}}

```{{example_1_language}}
{{example_1_code}}
```

**Expected Output:**
```
{{example_1_output}}
```

## Best Practices

{{#each best_practices}}
- {{this}}
{{/each}}

## Common Pitfalls

{{#each pitfalls}}
- **{{name}}**: {{description}}
{{/each}}

## Integration Notes

### Composition Patterns

{{composition_notes}}

### Performance Considerations

{{performance_notes}}

## Testing

See `tests/` directory for validation test suite.

## Resources

{{#if external_resources}}
Additional resources required:
{{#each external_resources}}
- {{this}}
{{/each}}
{{/if}}

## Version History

- **{{version}}** ({{created_at}}): Initial generation - {{generation_reason}}
